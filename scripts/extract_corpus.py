#!/usr/bin/env python3
"""Direct-call corpus extraction via OpenRouter (Option B — no subagents).

Reads ingested/<doc_id>.txt, chunks via core.chunk_document (exercises
FIDL-03 overlap), calls the configured model via OpenRouter's OpenAI-compatible
endpoint, merges and dedupes entities/relations across chunks, persists via
core/build_extraction.py subprocess (same Pydantic validation path the agent
uses). Resume-safe: skips documents whose extraction JSON already exists.

Usage:
    python scripts/extract_corpus.py <output_dir> --domain drug-discovery
    python scripts/extract_corpus.py tests/corpora/06_glp1_landscape/output-v3 \\
        --domain drug-discovery \\
        --model anthropic/claude-sonnet-4.6

Expects ingested/<doc_id>.txt to already exist under <output_dir>. Run
`python -m core.ingest_documents <corpus_dir> --output <output_dir>
--domain <domain>` first.

Env:
    OPENROUTER_API_KEY — required.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from core.chunk_document import chunk_document  # noqa: E402
from core.domain_resolver import resolve_domain  # noqa: E402

try:
    from openai import OpenAI
except ImportError as e:
    raise SystemExit(
        "openai SDK is required. Install with: uv pip install openai"
    ) from e


USER_PROMPT_TEMPLATE = """Extract entities and relations from the following document chunk using the domain schema above.

Return ONLY a single JSON object with exactly two top-level fields: `entities` (array) and `relations` (array). No markdown fences, no commentary, no explanation — just the JSON.

Document chunk:
---
{chunk_text}
---
"""


def _strip_fences(text: str) -> str:
    """Strip optional ```json ... ``` fences."""
    text = text.strip()
    if text.startswith("```"):
        # Remove leading ```json or ``` and trailing ```
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```\s*$", "", text)
    return text.strip()


def call_llm(
    client: OpenAI,
    model: str,
    system_prompt: str,
    chunk_text: str,
    max_retries: int = 3,
) -> tuple[list, list, float, int]:
    """Call the model once; return (entities, relations, cost_usd, total_tokens).

    Retries on transient errors (5xx, rate-limit, JSON parse failure) up to
    max_retries with exponential backoff.
    """
    last_err: Exception | None = None
    for attempt in range(max_retries):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": USER_PROMPT_TEMPLATE.format(chunk_text=chunk_text),
                    },
                ],
                temperature=0.0,
                max_tokens=8192,
            )
            content = resp.choices[0].message.content or ""
            content = _strip_fences(content)
            data = json.loads(content)

            # OpenRouter returns `usage.total_tokens`; cost may be under
            # `usage.cost` (some models) or in response headers. Fall back to 0.
            usage = getattr(resp, "usage", None)
            total_tokens = getattr(usage, "total_tokens", 0) if usage else 0
            # OpenRouter-specific: cost is sometimes available on usage
            cost = 0.0
            if usage is not None:
                cost = getattr(usage, "cost", 0.0) or 0.0

            return (
                data.get("entities", []),
                data.get("relations", []),
                float(cost),
                int(total_tokens),
            )
        except (json.JSONDecodeError, Exception) as e:  # noqa: BLE001
            last_err = e
            if attempt + 1 < max_retries:
                time.sleep(2**attempt)
            continue

    raise RuntimeError(f"LLM call failed after {max_retries} retries: {last_err}")


def _dedupe_entities(entities: list[dict]) -> list[dict]:
    """Dedupe by (name, entity_type); keep the first occurrence, merge attributes."""
    out: list[dict] = []
    index: dict[tuple[str, str], int] = {}
    for e in entities:
        key = (str(e.get("name", "")).strip(), str(e.get("entity_type") or e.get("type") or "").strip())
        if not key[0]:
            continue
        if key in index:
            # merge attributes (prefer existing values)
            existing = out[index[key]]
            for k, v in (e.get("attributes") or {}).items():
                existing.setdefault("attributes", {}).setdefault(k, v)
        else:
            index[key] = len(out)
            out.append(e)
    return out


def _dedupe_relations(relations: list[dict]) -> list[dict]:
    """Dedupe by (source, target, relation_type)."""
    seen: set[tuple[str, str, str]] = set()
    out: list[dict] = []
    for r in relations:
        key = (
            str(r.get("source_entity", "")).strip(),
            str(r.get("target_entity", "")).strip(),
            str(r.get("relation_type") or r.get("type") or "").strip(),
        )
        if key in seen or not all(key):
            continue
        seen.add(key)
        out.append(r)
    return out


def extract_document(
    doc_id: str,
    ingested_dir: Path,
    client: OpenAI,
    model: str,
    system_prompt: str,
    output_dir: Path,
    domain: str,
) -> dict:
    """Extract one document end-to-end. Returns run metadata."""
    text_path = ingested_dir / f"{doc_id}.txt"
    if not text_path.exists():
        return {"doc_id": doc_id, "error": f"missing ingested text: {text_path}"}

    text = text_path.read_text(encoding="utf-8")
    chunks = chunk_document(text, doc_id)

    all_entities: list[dict] = []
    all_relations: list[dict] = []
    total_cost = 0.0
    total_tokens = 0

    for chunk in chunks:
        entities, relations, cost, tokens = call_llm(
            client, model, system_prompt, chunk["text"]
        )
        all_entities.extend(entities)
        all_relations.extend(relations)
        total_cost += cost
        total_tokens += tokens

    entities = _dedupe_entities(all_entities)
    relations = _dedupe_relations(all_relations)

    payload = json.dumps({"entities": entities, "relations": relations})
    cmd = [
        sys.executable,
        str(_PROJECT_ROOT / "core" / "build_extraction.py"),
        doc_id,
        str(output_dir),
        "--domain",
        domain,
        "--model",
        model,
        "--cost",
        f"{total_cost:.6f}",
        "--json",
        payload,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)

    return {
        "doc_id": doc_id,
        "chunks": len(chunks),
        "entities": len(entities),
        "relations": len(relations),
        "cost_usd": total_cost,
        "total_tokens": total_tokens,
        "build_extraction_rc": result.returncode,
        "build_extraction_stderr": result.stderr.strip() if result.stderr else "",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "output_dir",
        help="Output directory containing ingested/ (from core.ingest_documents)",
    )
    parser.add_argument("--domain", default="drug-discovery")
    parser.add_argument(
        "--model",
        default="anthropic/claude-sonnet-4.6",
        help="OpenRouter model ID (e.g. anthropic/claude-sonnet-4.6)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-extract even when output-dir/extractions/<doc_id>.json exists",
    )
    parser.add_argument(
        "--limit", type=int, default=0, help="Stop after N docs (0 = all)"
    )
    args = parser.parse_args()

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("ERROR: OPENROUTER_API_KEY not set", file=sys.stderr)
        return 2

    domain_info = resolve_domain(args.domain)
    skill_path = Path(domain_info["skill_path"])
    system_prompt = skill_path.read_text(encoding="utf-8")

    output_dir = Path(args.output_dir).resolve()
    ingested_dir = output_dir / "ingested"
    extractions_dir = output_dir / "extractions"
    extractions_dir.mkdir(parents=True, exist_ok=True)

    doc_files = sorted(ingested_dir.glob("*.txt"))
    if not doc_files:
        print(f"ERROR: no ingested/*.txt under {output_dir}", file=sys.stderr)
        return 2

    client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")

    total_cost = 0.0
    total_tokens = 0
    results: list[dict] = []
    skipped = 0
    failed = 0
    done = 0

    count = 0
    for doc_path in doc_files:
        doc_id = doc_path.stem
        extraction_file = extractions_dir / f"{doc_id}.json"
        count += 1
        if args.limit and count > args.limit:
            break
        if extraction_file.exists() and not args.force:
            print(f"[{count}/{len(doc_files)}] SKIP {doc_id}")
            skipped += 1
            continue

        print(
            f"[{count}/{len(doc_files)}] EXTRACT {doc_id} ...", end=" ", flush=True
        )
        start = time.time()
        try:
            r = extract_document(
                doc_id, ingested_dir, client, args.model, system_prompt, output_dir, args.domain
            )
            elapsed = time.time() - start
            if "error" in r:
                print(f"FAIL: {r['error']} ({elapsed:.1f}s)")
                failed += 1
            else:
                print(
                    f"{r['entities']}E/{r['relations']}R "
                    f"tok={r['total_tokens']} ${r['cost_usd']:.4f} "
                    f"rc={r['build_extraction_rc']} ({elapsed:.1f}s)"
                )
                total_cost += r["cost_usd"]
                total_tokens += r["total_tokens"]
                done += 1
            results.append(r)
        except Exception as e:
            elapsed = time.time() - start
            print(f"FAIL: {e} ({elapsed:.1f}s)")
            failed += 1
            results.append({"doc_id": doc_id, "error": str(e)})

    summary = {
        "docs_total": len(doc_files),
        "docs_done": done,
        "docs_skipped": skipped,
        "docs_failed": failed,
        "total_cost_usd": total_cost,
        "total_tokens": total_tokens,
        "model": args.model,
        "domain": args.domain,
        "results": results,
    }
    (output_dir / "extract_run.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(
        f"\n=== DONE: {done} new, {skipped} skipped, {failed} failed "
        f"| ${total_cost:.4f} | {total_tokens} tokens ==="
    )
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
