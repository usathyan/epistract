#!/usr/bin/env python3
"""Write Claude's extraction output to sift-kg DocumentExtraction format.

Usage:
    python build_extraction.py <doc_id> <output_dir> [--domain <name>] --json '{"entities": [...], "relations": [...]}'
    echo '{"entities": [...]}' | python build_extraction.py <doc_id> <output_dir> [--domain <name>]
    python build_extraction.py <doc_id> <output_dir> --model <model_id> --cost 0.012 --json '...'
    EPISTRACT_MODEL=claude-opus-4-7 python build_extraction.py <doc_id> <output_dir> --json '...'
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Allow running as a plain script (python3 core/build_extraction.py ...) in addition
# to module import. Agents invoke this directly via an absolute path, so the package
# root must be on sys.path for the `core.domain_resolver` import below.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# noqa: E402 — these must follow the sys.path insertion above.
import yaml  # noqa: E402
from core.domain_resolver import resolve_domain  # noqa: E402

try:
    from sift_kg.extract.models import DocumentExtraction
    HAS_SIFT_EXTRACTION_MODEL = True
except ImportError:
    HAS_SIFT_EXTRACTION_MODEL = False


def _normalize_fields(entities, relations):
    """Normalize 'type' → 'entity_type'/'relation_type' and coerce schema drift.

    Drift handled:
    - numeric-string confidence ("0.9" → 0.9)
    - unparseable-string confidence → 0.5 (Pydantic default, maximizes recovery)
    - missing context / evidence → ""
    - missing attributes → {}
    """
    for e in entities:
        if "type" in e and "entity_type" not in e:
            e["entity_type"] = e.pop("type")
        if "confidence" in e and isinstance(e["confidence"], str):
            try:
                e["confidence"] = float(e["confidence"])
            except ValueError:
                e["confidence"] = 0.5  # Pydantic default
        if "context" not in e:
            e["context"] = ""
        if "attributes" not in e:
            e["attributes"] = {}
    for r in relations:
        if "type" in r and "relation_type" not in r:
            r["relation_type"] = r.pop("type")
        if "confidence" in r and isinstance(r["confidence"], str):
            try:
                r["confidence"] = float(r["confidence"])
            except ValueError:
                r["confidence"] = 0.5  # Pydantic default
        if "evidence" not in r:
            r["evidence"] = ""
    return entities, relations


def write_extraction(
    doc_id,
    output_dir,
    entities,
    relations,
    document_path="",
    chunks_processed=1,
    chunk_size=10000,
    domain_name=None,
    model_used: str | None = None,
    cost_usd: float | None = None,
):
    """Write extraction JSON to disk in sift-kg DocumentExtraction format.

    Args:
        doc_id: Document identifier.
        output_dir: Root output directory.
        entities: List of entity dicts.
        relations: List of relation dicts.
        document_path: Original document path.
        chunks_processed: Number of chunks processed.
        chunk_size: Size of each chunk.
        domain_name: Domain name for resolution (default: drug-discovery).
        model_used: Actual model id that produced the extraction (None if unknown).
        cost_usd: Actual cost of the extraction in USD (None if unknown).

    Returns:
        Path to written extraction JSON file.
    """
    entities, relations = _normalize_fields(entities, relations)

    # Resolve domain name from domain.yaml
    domain_info = resolve_domain(domain_name)
    domain_data = domain_info.get("schema")
    if domain_data is None:
        with open(domain_info["yaml_path"]) as f:
            domain_data = yaml.safe_load(f)

    extraction = {
        "document_id": doc_id,
        "document_path": document_path,
        "chunks_processed": chunks_processed,
        "entities": entities,
        "relations": relations,
        "cost_usd": cost_usd,
        "model_used": model_used,
        "domain_name": domain_data["name"],
        "chunk_size": chunk_size,
        "extracted_at": datetime.now(timezone.utc).isoformat(),
        "error": None,
    }
    # Substitute sift-kg DocumentExtraction defaults for unknown provenance so
    # the on-disk file loads cleanly via `sift_kg.graph.builder.load_extractions`
    # without requiring a prior normalize_extractions pass. Mirrors the fix Plan
    # 13-04 applied in core/normalize_extractions.py for the ingest pipeline.
    if extraction.get("cost_usd") is None:
        extraction["cost_usd"] = 0.0
    if extraction.get("model_used") is None:
        extraction["model_used"] = ""
    if HAS_SIFT_EXTRACTION_MODEL:
        try:
            DocumentExtraction(**extraction)
        except Exception as exc:
            raise ValueError(
                f"Extraction for doc_id={doc_id!r} failed DocumentExtraction validation: {exc}"
            ) from exc
    out_path = Path(output_dir) / "extractions" / f"{doc_id}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(extraction, indent=2))
    return str(out_path)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python build_extraction.py <doc_id> <output_dir> [--domain <name>] [--json '<json>']", file=sys.stderr)
        sys.exit(1)
    doc_id, output_dir = sys.argv[1], sys.argv[2]

    def _flag_value(flag: str) -> str | None:
        """Return the value following `flag`, None if absent; exit 2 if
        the flag is present but trailing (no value to consume).

        Mirrors the helper in core/okf_export.py. Without it, a trailing
        `--model` (easy to produce from a malformed agent dispatch, which is
        how this script is normally invoked) raised an uncaught IndexError
        instead of a usage message.
        """
        if flag not in sys.argv:
            return None
        index = sys.argv.index(flag)
        if index + 1 >= len(sys.argv):
            print(f"Error: {flag} requires a value", file=sys.stderr)
            sys.exit(2)
        return sys.argv[index + 1]

    domain_name = _flag_value("--domain")

    model_used: str | None = _flag_value("--model")
    if model_used is None and os.environ.get("EPISTRACT_MODEL"):
        model_used = os.environ["EPISTRACT_MODEL"]

    cost_usd: float | None = None
    cost_str = _flag_value("--cost")
    if cost_str is not None:
        try:
            cost_usd = float(cost_str)
        except ValueError:
            print(f"Error: --cost must be a number, got {cost_str!r}", file=sys.stderr)
            sys.exit(2)

    json_str = _flag_value("--json")
    if json_str is not None:
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as exc:
            print(f"Error: --json is not valid JSON: {exc}", file=sys.stderr)
            sys.exit(2)
    else:
        data = json.load(sys.stdin)
    path = write_extraction(
        doc_id, output_dir,
        data.get("entities", []), data.get("relations", []),
        data.get("document_path", ""),
        data.get("chunks_processed", 1),
        domain_name=domain_name,
        model_used=model_used,
        cost_usd=cost_usd,
    )
    print(f"Written: {path}")
