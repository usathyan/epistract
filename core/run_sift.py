#!/usr/bin/env python3
"""sift-kg Python API wrapper.

Usage:
    python run_sift.py --list-domains
    python run_sift.py build <output_dir> [--domain <name>]
    python run_sift.py view <output_dir> [--neighborhood <entity>] [--top <n>]
    python run_sift.py export <output_dir> <format>
    python run_sift.py info <output_dir>
    python run_sift.py search <output_dir> <query> [--type TYPE]

The --domain flag accepts a domain name (e.g. "drug-discovery", "contract"),
not a file path. Use --list-domains to see available domains.
"""

import json
import sys
from pathlib import Path

from core.domain_resolver import resolve_domain, list_domains


def _import_sift(names: list[str]):
    """Import sift-kg components with user-friendly error on missing install."""
    try:
        import sift_kg
    except ImportError:
        print(
            "Error: sift-kg is not installed.\n"
            "Run /epistract-setup or: uv pip install sift-kg",
            file=sys.stderr,
        )
        sys.exit(1)
    return tuple(getattr(sift_kg, n) for n in names)


def cmd_build(output_dir: str, domain_name: str | None = None):
    run_build, load_domain = _import_sift(["run_build", "load_domain"])

    if domain_name:
        domain_info = resolve_domain(domain_name)
        domain = load_domain(domain_path=Path(domain_info["yaml_path"]))
    else:
        domain = load_domain(domain_path=Path(__file__).parent.parent / "domains" / "drug-discovery" / "domain.yaml")
    kg = run_build(Path(output_dir), domain)

    # Auto-label communities with descriptive names
    try:
        from core.label_communities import label_communities  # noqa: E402
        label_communities(Path(output_dir))
    except Exception as e:
        print(f"Warning: community labeling failed: {e}", file=sys.stderr)

    print(json.dumps({
        "entities": kg.entity_count,
        "relations": kg.relation_count,
        "graph_path": str(Path(output_dir) / "graph_data.json"),
    }))


def cmd_view(output_dir: str, **kwargs):
    (run_view,) = _import_sift(["run_view"])
    run_view(Path(output_dir), **{k: v for k, v in kwargs.items() if v is not None})


def cmd_export(output_dir: str, fmt: str):
    (run_export,) = _import_sift(["run_export"])
    path = run_export(Path(output_dir), fmt)
    print(f"Exported: {path}")


def cmd_info(output_dir: str):
    (KnowledgeGraph,) = _import_sift(["KnowledgeGraph"])
    graph_path = Path(output_dir) / "graph_data.json"
    if not graph_path.exists():
        print(json.dumps({"error": "No graph found"}))
        return
    kg = KnowledgeGraph.load(graph_path)
    data = kg.export()
    print(json.dumps(data["metadata"], indent=2))


def cmd_search(output_dir: str, query: str, entity_type: str | None = None):
    (KnowledgeGraph,) = _import_sift(["KnowledgeGraph"])
    graph_path = Path(output_dir) / "graph_data.json"
    if not graph_path.exists():
        print(json.dumps({"error": "No graph found"}))
        return
    kg = KnowledgeGraph.load(graph_path)
    query_lower = query.lower()
    results = []
    for node_id, data in kg.graph.nodes(data=True):
        name = data.get("name", "")
        if query_lower in name.lower() or query_lower in node_id.lower():
            if entity_type and data.get("entity_type", "").upper() != entity_type.upper():
                continue
            results.append({"id": node_id, "name": name, "type": data.get("entity_type", ""), "confidence": data.get("confidence", 0)})
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    # --list-domains: print available domains and exit (no subcommand needed)
    if "--list-domains" in sys.argv:
        domains = list_domains()
        for name in domains:
            info = resolve_domain(name)
            schema = info.get("schema") or {}
            print(f"  {name:20s} v{schema.get('version', '?')}  {schema.get('description', '')}")
        sys.exit(0)

    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "build":
        domain = None
        if "--domain" in sys.argv:
            domain = sys.argv[sys.argv.index("--domain") + 1]
        cmd_build(sys.argv[2], domain)
    elif cmd == "view":
        kwargs = {}
        if "--neighborhood" in sys.argv:
            kwargs["neighborhood"] = sys.argv[sys.argv.index("--neighborhood") + 1]
        if "--top" in sys.argv:
            kwargs["top_n"] = int(sys.argv[sys.argv.index("--top") + 1])
        cmd_view(sys.argv[2], **kwargs)
    elif cmd == "export":
        cmd_export(sys.argv[2], sys.argv[3])
    elif cmd == "info":
        cmd_info(sys.argv[2])
    elif cmd == "search":
        entity_type = None
        if "--type" in sys.argv:
            type_idx = sys.argv.index("--type")
            entity_type = sys.argv[type_idx + 1]
            # Remove --type and its value from argv before joining query
            args = sys.argv[3:type_idx] + sys.argv[type_idx + 2:]
        else:
            args = sys.argv[3:]
        cmd_search(sys.argv[2], " ".join(args), entity_type)
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
