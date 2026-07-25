#!/usr/bin/env python3
"""Post-extraction normalization for the epistract pipeline.

Runs as Step 3.5 of /epistract:ingest (see commands/ingest.md). Walks
output_dir/extractions/*.json and applies the D-03 rules from
.planning/phases/13-extraction-pipeline-reliability/13-CONTEXT.md:

  1. Rename variant filenames -> <doc_id>.json
     (*_raw.json, *_extraction_input.json, *-extraction.json)
  2. Infer missing document_id from filename stem
  3. Dedupe same-doc_id via composite score
     (has_document_id*1000 + len(entities) + len(relations))
     -- winners stay, losers move to extractions/_dedupe_archive/
  4. Delegate schema-drift coercion to build_extraction._normalize_fields
  5. Validate against sift-kg DocumentExtraction Pydantic model
  6. Write extractions/_normalization_report.json (indent=2)

Usage:
    python3 core/normalize_extractions.py <output_dir>
    python3 core/normalize_extractions.py <output_dir> --fail-threshold 0.95

Exit codes:
    0 -- pass_rate >= fail_threshold
    1 -- pass_rate < fail_threshold (caller should abort pipeline)
    2 -- I/O, import, or usage error (e.g. no args)

Returns (Python API):
    dict with keys: pass_rate, report_path, total, passed, recovered,
                   unrecoverable, actions
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

# Allow running as a plain script (python3 core/normalize_extractions.py ...) in
# addition to module import. Mirrors core/build_extraction.py preamble so sibling
# imports (build_extraction) resolve regardless of invocation style.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))
_CORE_DIR = Path(__file__).resolve().parent
if str(_CORE_DIR) not in sys.path:
    sys.path.insert(0, str(_CORE_DIR))

# Reuse the coercion helper from build_extraction -- do not duplicate
from build_extraction import _normalize_fields  # noqa: E402 — follows the sys.path insertion above

try:
    from sift_kg.extract.models import DocumentExtraction
    HAS_SIFT_EXTRACTION_MODEL = True
except ImportError:
    HAS_SIFT_EXTRACTION_MODEL = False

# Variant filename suffix patterns -- applied to Path.stem
_VARIANT_SUFFIX_RE = re.compile(r"^(.+?)(_raw|_extraction_input|-extraction)$")

# Infrastructure files we skip (report + archive + any future underscore-prefixed)
_SKIP_PREFIXES = ("_",)

# Dedupe archive dir (relative to extractions/)
_DEDUPE_ARCHIVE = "_dedupe_archive"

# Report filename
_REPORT_NAME = "_normalization_report.json"


def _canonical_stem(stem: str) -> str:
    """Strip known variant suffixes from a filename stem.

    Examples:
        "foo_raw"              -> "foo"
        "bar_extraction_input" -> "bar"
        "baz-extraction"       -> "baz"
        "plain"                -> "plain"
    """
    m = _VARIANT_SUFFIX_RE.match(stem)
    return m.group(1) if m else stem


def _score(record: dict) -> int:
    """Composite dedupe score per RESEARCH.md Open Question 3."""
    has_doc_id = 1 if record.get("document_id") else 0
    n_entities = len(record.get("entities", []) or [])
    n_relations = len(record.get("relations", []) or [])
    return has_doc_id * 1000 + n_entities + n_relations


def _load_and_coerce(path: Path) -> tuple[dict | None, str | None]:
    """Load JSON at path, apply normalization coercions. Returns (record, error)."""
    try:
        record = json.loads(path.read_text())
    except Exception as exc:
        return None, f"unparseable_json: {exc}"

    if not isinstance(record, dict):
        return None, f"not_a_json_object: got {type(record).__name__}"

    # Infer document_id from canonical stem if missing
    canonical = _canonical_stem(path.stem)
    if "document_id" not in record or not record.get("document_id"):
        record["document_id"] = canonical

    # Ensure document_path is present (required by Pydantic)
    record.setdefault("document_path", "")

    # Delegate schema-drift coercion for entities/relations
    entities = record.get("entities", []) or []
    relations = record.get("relations", []) or []
    try:
        entities, relations = _normalize_fields(entities, relations)
    except Exception as exc:
        return None, f"normalize_fields_failed: {exc}"
    record["entities"] = entities
    record["relations"] = relations

    return record, None


def _validate(record: dict) -> str | None:
    """Run Pydantic validation. Returns error string or None on success."""
    if not HAS_SIFT_EXTRACTION_MODEL:
        return None  # skip validation when sift-kg missing (caller's problem)
    # Substitute sift-kg defaults for honest-null provenance fields so
    # validation enforces required fields (document_id, entity_type, etc.)
    # without rejecting legitimately-unknown model_used/cost_usd.
    payload = dict(record)
    if payload.get("cost_usd") is None:
        payload["cost_usd"] = 0.0
    if payload.get("model_used") is None:
        payload["model_used"] = ""
    try:
        DocumentExtraction(**payload)
    except Exception as exc:
        return f"pydantic_validation_failed: {exc}"
    return None


def normalize_extractions(
    output_dir: str | Path,
    fail_threshold: float = 0.95,
) -> dict:
    """Normalize output_dir/extractions in place.

    Returns dict: {
        pass_rate: float,
        report_path: str,
        total: int,
        passed: int,
        recovered: int,
        unrecoverable: int,
        actions: list[dict],
    }
    """
    out = Path(output_dir)
    ext_dir = out / "extractions"
    if not ext_dir.is_dir():
        raise FileNotFoundError(f"extractions dir not found: {ext_dir}")

    archive_dir = ext_dir / _DEDUPE_ARCHIVE

    # Collect candidate files, skipping underscore-prefixed infrastructure
    inputs = sorted(
        p for p in ext_dir.glob("*.json")
        if not p.name.startswith(_SKIP_PREFIXES)
    )

    # First pass: load + coerce + infer doc_id, group by canonical doc_id
    loaded: dict[str, list[tuple[Path, dict]]] = {}
    actions: list[dict] = []
    unrecoverable = 0
    for path in inputs:
        record, err = _load_and_coerce(path)
        if err or record is None:
            actions.append({
                "file": path.name,
                "action": "unrecoverable_load",
                "reason": err,
            })
            unrecoverable += 1
            continue
        doc_id = record["document_id"]
        loaded.setdefault(doc_id, []).append((path, record))

    # Second pass: resolve duplicates per doc_id group
    survivors: dict[str, tuple[Path, dict]] = {}
    for doc_id, candidates in loaded.items():
        if len(candidates) == 1:
            survivors[doc_id] = candidates[0]
            continue
        # Rank by composite score desc, tie-break by lexicographic filename asc
        candidates.sort(key=lambda pair: (-_score(pair[1]), pair[0].name))
        winner_path, winner_record = candidates[0]
        survivors[doc_id] = (winner_path, winner_record)
        # Move losers into dedupe archive
        archive_dir.mkdir(parents=True, exist_ok=True)
        for loser_path, _ in candidates[1:]:
            dest = archive_dir / loser_path.name
            shutil.move(str(loser_path), str(dest))
            actions.append({
                "file": loser_path.name,
                "action": "dedupe_archived",
                "reason": f"lost tie-break for doc_id={doc_id}",
                "archive_path": str(dest.relative_to(out)),
            })

    # Third pass: validate + rename survivors, write canonical files
    passed = 0
    recovered = 0
    for doc_id, (src_path, record) in survivors.items():
        err = _validate(record)
        if err:
            actions.append({
                "file": src_path.name,
                "action": "unrecoverable_validation",
                "reason": err,
            })
            unrecoverable += 1
            continue

        # Decide final filename
        canonical_path = ext_dir / f"{doc_id}.json"
        was_renamed = (src_path.name != canonical_path.name)

        # Substitute sift-kg defaults for honest-null provenance fields BEFORE
        # writing to disk. sift-kg's DocumentExtraction declares
        # cost_usd: float = 0.0 and model_used: str = "" as non-nullable, so
        # sift_kg.graph.builder.load_extractions silently drops any file with
        # null provenance (the 30% silent-drop bug Phase 13 fixes). The on-disk
        # canonical file MUST be loader-compatible for the normalization step
        # to actually accomplish its purpose: files reaching the graph builder.
        # Agents still WRITE null per D-07/D-08 honest-null contract;
        # normalization rescues that into loadable form here.
        if record.get("cost_usd") is None:
            record["cost_usd"] = 0.0
        if record.get("model_used") is None:
            record["model_used"] = ""

        # Rewrite body (with inferred doc_id + coerced fields) to canonical path
        canonical_path.write_text(json.dumps(record, indent=2))

        # If source differed from canonical, remove source
        if was_renamed and src_path.exists() and src_path != canonical_path:
            src_path.unlink()

        if was_renamed:
            actions.append({
                "file": src_path.name,
                "action": "renamed",
                "to": canonical_path.name,
            })
            recovered += 1
        else:
            actions.append({
                "file": canonical_path.name,
                "action": "passed",
            })
            passed += 1

    total = passed + recovered + unrecoverable
    pass_rate = (passed + recovered) / total if total > 0 else 0.0

    report = {
        "total": total,
        "passed": passed,
        "recovered": recovered,
        "unrecoverable": unrecoverable,
        "pass_rate": round(pass_rate, 4),
        "fail_threshold": fail_threshold,
        "above_threshold": pass_rate >= fail_threshold,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "actions": actions,
    }
    report_path = ext_dir / _REPORT_NAME
    report_path.write_text(json.dumps(report, indent=2))

    return {
        "pass_rate": pass_rate,
        "report_path": str(report_path),
        "total": total,
        "passed": passed,
        "recovered": recovered,
        "unrecoverable": unrecoverable,
        "actions": actions,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Usage: python3 normalize_extractions.py <output_dir> [--fail-threshold 0.95]",
            file=sys.stderr,
        )
        sys.exit(2)
    output_dir = sys.argv[1]

    fail_threshold = 0.95
    if "--fail-threshold" in sys.argv:
        try:
            fail_threshold = float(sys.argv[sys.argv.index("--fail-threshold") + 1])
        except (IndexError, ValueError) as exc:
            print(f"Invalid --fail-threshold: {exc}", file=sys.stderr)
            sys.exit(2)
        if not (0.0 <= fail_threshold <= 1.0):
            print(
                f"--fail-threshold must be in [0.0, 1.0], got {fail_threshold}",
                file=sys.stderr,
            )
            sys.exit(2)

    try:
        result = normalize_extractions(output_dir, fail_threshold=fail_threshold)
    except Exception as exc:
        print(f"normalize_extractions failed: {exc}", file=sys.stderr)
        sys.exit(2)

    print(
        f"Normalized {result['total']} files: "
        f"{result['passed']} pass, {result['recovered']} recovered, "
        f"{result['unrecoverable']} unrecoverable "
        f"(pass_rate={result['pass_rate']:.2%})"
    )
    if result["pass_rate"] < fail_threshold:
        print(
            f"ABORT: pass_rate {result['pass_rate']:.2%} below --fail-threshold "
            f"{fail_threshold:.2%}. See {result['report_path']}",
            file=sys.stderr,
        )
        sys.exit(1)
    sys.exit(0)
