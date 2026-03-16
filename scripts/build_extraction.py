#!/usr/bin/env python3
"""Write Claude's extraction output to sift-kg DocumentExtraction format.

Usage:
    python build_extraction.py <doc_id> <output_dir> --json '{"entities": [...], "relations": [...]}'
    echo '{"entities": [...]}' | python build_extraction.py <doc_id> <output_dir>
"""
import json, sys
from datetime import datetime, timezone
from pathlib import Path


def write_extraction(doc_id, output_dir, entities, relations, document_path="", chunks_processed=1, chunk_size=10000):
    extraction = {
        "document_id": doc_id,
        "document_path": document_path,
        "chunks_processed": chunks_processed,
        "entities": entities,
        "relations": relations,
        "cost_usd": 0.0,
        "model_used": "claude-code",
        "domain_name": "Drug Discovery",
        "chunk_size": chunk_size,
        "extracted_at": datetime.now(timezone.utc).isoformat(),
        "error": None,
    }
    out_path = Path(output_dir) / "extractions" / f"{doc_id}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(extraction, indent=2))
    return str(out_path)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python build_extraction.py <doc_id> <output_dir> [--json '<json>']", file=sys.stderr)
        sys.exit(1)
    doc_id, output_dir = sys.argv[1], sys.argv[2]
    if "--json" in sys.argv:
        data = json.loads(sys.argv[sys.argv.index("--json") + 1])
    else:
        data = json.load(sys.stdin)
    path = write_extraction(doc_id, output_dir, data.get("entities", []), data.get("relations", []),
                            data.get("document_path", ""), data.get("chunks_processed", 1))
    print(f"Written: {path}")
