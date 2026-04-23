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
import re
import sys
from pathlib import Path

from core.domain_resolver import resolve_domain, list_domains, DOMAINS_DIR


def resolve_domain_arg(value: str) -> str:
    """Shim for --domain CLI arg: accepts a name OR a path to domains/<name>/domain.yaml.

    FIDL-08 D-07, D-08:
      - Bare name (no '/' and not ending in '.yaml') → return unchanged. The
        bare-name branch never touches the filesystem (D-08 explicit
        non-ambiguity).
      - Path inside DOMAINS_DIR matching `<DOMAINS_DIR>/<name>/domain.yaml`
        → return `<name>`.
      - Path outside DOMAINS_DIR → print error to stderr and sys.exit(1) with
        a clear "use --domain <inferred_name>" message.
    """
    # D-08: bare-name path never touches the filesystem
    if "/" not in value and not value.endswith(".yaml"):
        return value

    path = Path(value).resolve()
    domains_root = DOMAINS_DIR.resolve()

    try:
        rel = path.relative_to(domains_root)
    except ValueError:
        # Path is outside DOMAINS_DIR — clear error
        inferred = path.parent.name if path.name == "domain.yaml" else path.stem
        print(
            f"Error: --domain expects a name registered under domains/, "
            f"not an arbitrary path. Try --domain {inferred} after registering the domain.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Path inside DOMAINS_DIR — must be <name>/domain.yaml to be valid
    parts = rel.parts
    if len(parts) >= 2 and parts[-1] == "domain.yaml":
        return parts[0]

    # Inside DOMAINS_DIR but not a valid <name>/domain.yaml location
    print(
        f"Error: --domain expects a name registered under domains/, "
        f"not an arbitrary path. Try --domain "
        f"{parts[0] if parts else 'unknown'} after registering the domain.",
        file=sys.stderr,
    )
    sys.exit(1)


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


def _load_validation_module(validation_dir: Path):
    """Dynamically load validation/run_validation.py (FIDL-07 D-04).

    Mirrors core.label_epistemic._load_domain_epistemic — uses
    importlib.util.spec_from_file_location so the module loads regardless
    of Python's package context.

    Args:
        validation_dir: Path to the domain's validation/ directory.

    Returns:
        The loaded module, or None if ``run_validation.py`` is absent or the
        spec fails to load.
    """
    import importlib.util
    module_path = validation_dir / "run_validation.py"
    if not module_path.is_file():
        return None
    spec = importlib.util.spec_from_file_location(
        f"domains.{validation_dir.parent.name}.validation.run_validation",
        module_path,
    )
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def cmd_build(output_dir: str, domain_name: str | None = None):
    run_build, load_domain = _import_sift(["run_build", "load_domain"])

    if domain_name:
        domain_info = resolve_domain(domain_name)
        domain = load_domain(domain_path=Path(domain_info["yaml_path"]))
    else:
        domain = load_domain(domain_path=Path(__file__).parent.parent / "domains" / "drug-discovery" / "domain.yaml")
    kg = run_build(Path(output_dir), domain)

    # FIDL-06 (D-01, D-02): persist the build-time domain into graph_data.json
    # metadata so every downstream consumer (workbench, graph.html, chat system
    # prompt) has a single source of truth for "what domain is this graph?"
    # Post-process pattern rather than monkey-patching sift-kg — keeps us
    # decoupled from sift_kg.graph.knowledge_graph.save().
    graph_path = Path(output_dir) / "graph_data.json"
    if graph_path.exists():
        try:
            graph_json = json.loads(graph_path.read_text(encoding="utf-8"))
            metadata = graph_json.setdefault("metadata", {})
            metadata["domain"] = domain_name  # str or None; JSON null on None
            graph_path.write_text(
                json.dumps(graph_json, indent=2, default=str),
                encoding="utf-8",
            )
        except (OSError, ValueError, json.JSONDecodeError) as e:
            # Non-fatal: graph still usable, just missing the domain field.
            # Consumers fall back via resolve_domain's D-08 legacy path.
            print(
                f"Warning: failed to persist domain into graph_data.json: {e}",
                file=sys.stderr,
            )

    # Auto-label communities with descriptive names
    try:
        from core.label_communities import label_communities  # noqa: E402
        label_communities(Path(output_dir))
    except Exception as e:
        print(f"Warning: community labeling failed: {e}", file=sys.stderr)

    # FIDL-07 (D-04, D-08): post-build validation dispatch.
    # If the domain ships a validation/run_validation.py convention entry
    # point, call it with the output_dir and write its return dict to
    # validation_report.json. Non-fatal: exceptions write an error-status
    # report but do NOT abort cmd_build. Domains without a validation/ dir
    # (e.g. contracts) silently skip — no warning, no report.
    if domain_name:
        try:
            domain_info = resolve_domain(domain_name)
        except FileNotFoundError:
            domain_info = {"validation_dir": None}
    else:
        # Default-domain path — mirror the load_domain default above so a
        # `cmd_build <out>` (no --domain flag) still triggers drug-discovery
        # validation.
        try:
            domain_info = resolve_domain("drug-discovery")
        except FileNotFoundError:
            domain_info = {"validation_dir": None}

    validation_dir_str = domain_info.get("validation_dir")
    if validation_dir_str:
        validation_dir = Path(validation_dir_str)
        report_path = Path(output_dir) / "validation_report.json"
        try:
            val_mod = _load_validation_module(validation_dir)
            if val_mod is None or not hasattr(val_mod, "run_validation"):
                report = {
                    "status": "error",
                    "error": "run_validation callable not found",
                    "domain": domain_name,
                }
            else:
                report = val_mod.run_validation(Path(output_dir))
                if not isinstance(report, dict):
                    report = {
                        "status": "error",
                        "error": f"run_validation returned non-dict: {type(report).__name__}",
                        "domain": domain_name,
                    }
        except Exception as e:  # noqa: BLE001 — validator failures are non-fatal
            report = {
                "status": "error",
                "error": str(e),
                "domain": domain_name,
            }
            print(
                f"Warning: validation dispatch for {domain_name!r} failed: {e}",
                file=sys.stderr,
            )

        try:
            report_path.write_text(
                json.dumps(report, indent=2, default=str),
                encoding="utf-8",
            )
        except OSError as e:
            print(
                f"Warning: could not write {report_path}: {e}",
                file=sys.stderr,
            )

    print(json.dumps({
        "entities": kg.entity_count,
        "relations": kg.relation_count,
        "graph_path": str(Path(output_dir) / "graph_data.json"),
    }))


def cmd_view(output_dir: str, **kwargs):
    """Generate graph.html; post-process it to inject domain-aware title + entity colors (FIDL-06)."""
    (run_view,) = _import_sift(["run_view"])
    run_view(Path(output_dir), **{k: v for k, v in kwargs.items() if v is not None})

    # FIDL-06 D-04 + D-05: post-process the pyvis-generated graph.html to
    # inject domain-specific title into the empty <h1></h1> and override
    # entity colors from the domain's template.yaml. Both are additive —
    # pyvis's HTML structure and vis.js initialization are not touched.
    graph_html = Path(output_dir) / "graph.html"
    if not graph_html.exists():
        # run_view didn't produce the file; nothing to post-process.
        return

    # Resolve domain from graph metadata (reuses Plan 17-01's precedence).
    # We add the project root to sys.path so `examples.workbench.*` imports
    # work regardless of caller cwd.
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    try:
        from examples.workbench.template_loader import (
            load_template,
            resolve_domain,
        )
    except ImportError as e:
        print(
            f"Warning: could not import workbench helpers for graph.html "
            f"post-process: {e}. Skipping FIDL-06 title/color injection.",
            file=sys.stderr,
        )
        return

    resolved_domain, _source = resolve_domain(Path(output_dir), None)
    template = load_template(resolved_domain)
    title_text = template.get("title") or "Knowledge Graph"
    entity_colors: dict[str, str] = template.get("entity_colors") or {}

    try:
        html = graph_html.read_text(encoding="utf-8")
    except OSError as e:
        print(
            f"Warning: could not read {graph_html} for post-process: {e}",
            file=sys.stderr,
        )
        return

    # FIDL-06 D-04: replace pyvis's empty <h1></h1> with our domain-aware title.
    # pyvis emits <h1></h1> twice — both inside <center> blocks, and rendering
    # both produces the title visibly twice. Fill the first occurrence with
    # the domain title; strip the second centered empty block so the visible
    # page shows the title exactly once.
    new_h1 = f"<h1>{title_text}</h1>"
    html = html.replace("<h1></h1>", new_h1, 1)
    html = re.sub(
        r"[\t ]*<center>\s*<h1>\s*</h1>\s*</center>[\t ]*\n?",
        "",
        html,
        count=1,
    )
    # Safety net: any remaining <h1></h1> (unusual pyvis versions) — drop them.
    html = html.replace("<h1></h1>", "")

    # FIDL-06 D-05: entity_colors overlay — append a <script> block right before
    # </body> that iterates the existing vis.js `nodes` DataSet on DOMContentLoaded
    # and updates color.background for nodes whose entity_type matches a key
    # in our template.yaml entity_colors dict. Existing color pickers in
    # _inject_ui's sidebar still work; they just start from our overrides.
    if entity_colors:
        overrides_js = json.dumps(entity_colors)
        overlay_script = (
            f'<script>\n'
            f'// FIDL-06 D-05: domain entity_colors overlay injected by cmd_view.\n'
            f'(function() {{\n'
            f'  var overrides = {overrides_js};\n'
            f'  function applyOverrides() {{\n'
            f'    if (typeof nodes === "undefined" || !nodes.forEach) return;\n'
            f'    var updates = [];\n'
            f'    nodes.forEach(function(n) {{\n'
            f'      var et = n.entity_type;\n'
            f'      if (et && overrides[et]) {{\n'
            f'        var color = overrides[et];\n'
            f'        updates.push({{id: n.id, color: {{\n'
            f'          background: color,\n'
            f'          border: (n.color &amp;&amp; n.color.border) || color,\n'
            f'          highlight: {{background: color, border: (n.color &amp;&amp; n.color.border) || color}}\n'
            f'        }}}});\n'
            f'      }}\n'
            f'    }});\n'
            f'    if (updates.length) nodes.update(updates);\n'
            f'  }}\n'
            f'  if (document.readyState === "loading") {{\n'
            f'    document.addEventListener("DOMContentLoaded", applyOverrides);\n'
            f'  }} else {{\n'
            f'    setTimeout(applyOverrides, 100);\n'
            f'  }}\n'
            f'}})();\n'
            f'</script>'
        )
        # Inject BEFORE </body> so _inject_ui's sidebar is already in place;
        # if </body> is missing (highly unusual), append at the end instead.
        if "</body>" in html:
            html = html.replace("</body>", overlay_script + "\n</body>")
        else:
            html = html + "\n" + overlay_script

    try:
        graph_html.write_text(html, encoding="utf-8")
    except OSError as e:
        print(
            f"Warning: could not write {graph_html} after post-process: {e}",
            file=sys.stderr,
        )


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
            raw_domain_arg = sys.argv[sys.argv.index("--domain") + 1]
            domain = resolve_domain_arg(raw_domain_arg)  # FIDL-08 D-07: accept name or path
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
