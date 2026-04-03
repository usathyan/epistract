#!/usr/bin/env python3
"""Write Claude's extraction output to sift-kg DocumentExtraction format.

Usage:
    python build_extraction.py <doc_id> <output_dir> [--domain <name>] --json '{"entities": [...], "relations": [...]}'
    echo '{"entities": [...]}' | python build_extraction.py <doc_id> <output_dir> [--domain <name>]
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml
from core.domain_resolver import resolve_domain


def _normalize_fields(entities, relations):
    """Normalize 'type' → 'entity_type'/'relation_type' for sift-kg compatibility.

    LLM agents sometimes use 'type' instead of the required field names.
    """
    for e in entities:
        if "type" in e and "entity_type" not in e:
            e["entity_type"] = e.pop("type")
    for r in relations:
        if "type" in r and "relation_type" not in r:
            r["relation_type"] = r.pop("type")
    return entities, relations


def write_extraction(doc_id, output_dir, entities, relations, document_path="", chunks_processed=1, chunk_size=10000, domain_name=None):
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
        "cost_usd": 0.0,
        "model_used": "claude-opus-4-6",
        "domain_name": domain_data["name"],
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
        print("Usage: python build_extraction.py <doc_id> <output_dir> [--domain <name>] [--json '<json>']", file=sys.stderr)
        sys.exit(1)
    doc_id, output_dir = sys.argv[1], sys.argv[2]

    domain_name = None
    if "--domain" in sys.argv:
        domain_name = sys.argv[sys.argv.index("--domain") + 1]

    if "--json" in sys.argv:
        data = json.loads(sys.argv[sys.argv.index("--json") + 1])
    else:
        data = json.load(sys.stdin)
    path = write_extraction(doc_id, output_dir, data.get("entities", []), data.get("relations", []),
                            data.get("document_path", ""), data.get("chunks_processed", 1),
                            domain_name=domain_name)
    print(f"Written: {path}")
