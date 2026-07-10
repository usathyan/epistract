#!/usr/bin/env python3
"""epistract CLI — multi-project dataset management, indexing, and search.

Usage:
    python3 -m core.cli init <name> [--domain D] [--dir PATH]
    python3 -m core.cli add project <name> [--domain D] [--dir PATH]
    python3 -m core.cli add files <path>... [--project NAME]
    python3 -m core.cli add url <url>... [--project NAME]
    python3 -m core.cli index [--project NAME] [--rebuild]
    python3 -m core.cli search <query> [--project NAME] [--type T] [-k N] [--expand]
    python3 -m core.cli enhance [--project NAME] [--judge] [--resolve] [--epistemic]
    python3 -m core.cli projects list|info <name>|delete <name> [--purge]
    python3 -m core.cli status [--project NAME]

Project resolution order: --project flag > $EPISTRACT_PROJECT > nearest
ancestor directory containing .epistract/project.json.

All subcommands accept --json for machine-readable output.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import index_db
from . import registry
from .graph_retrieval import expand_from_seeds
from .registry import ProjectError


def _emit(payload: dict | list, as_json: bool, human: str) -> None:
    print(json.dumps(payload, indent=2) if as_json else human)


# ---------------------------------------------------------------------------
# Subcommand handlers
# ---------------------------------------------------------------------------


def cmd_init(args) -> int:
    project = registry.init_project(args.name, root=args.dir, domain=args.domain)
    _emit(
        {"name": project["name"], "root": project["root"], "domain": project["domain"]},
        args.json,
        f"Initialized project '{project['name']}' ({project['domain']}) at {project['root']}",
    )
    return 0


def cmd_add_files(args) -> int:
    project = registry.resolve_project(args.project)
    report = registry.add_files(project, args.paths)
    human = (
        f"Project '{project['name']}': "
        f"{len(report['added'])} added, "
        f"{len(report['skipped_duplicate'])} duplicate(s) skipped, "
        f"{len(report['missing'])} missing"
    )
    for path in report["missing"]:
        human += f"\n  missing: {path}"
    _emit(report, args.json, human)
    return 1 if report["missing"] and not report["added"] else 0


def cmd_add_url(args) -> int:
    project = registry.resolve_project(args.project)
    results = [registry.add_url(project, url) for url in args.urls]
    lines = [f"  {r['url']}: {r['status']}" for r in results]
    _emit(results, args.json, f"Project '{project['name']}':\n" + "\n".join(lines))
    return 0


def cmd_index(args) -> int:
    project = registry.resolve_project(args.project)
    stats = index_db.index_project(project, rebuild=args.rebuild)
    human = (
        f"Project '{project['name']}': indexed {len(stats['indexed'])} document(s) "
        f"({stats['chunks']} chunks), skipped {stats['skipped']} unchanged, "
        f"{stats['entities']} entities from graph"
    )
    if stats["failed"]:
        human += f"\n  extraction failed: {', '.join(stats['failed'])}"
    _emit(stats, args.json, human)
    return 0


def cmd_search(args) -> int:
    project = registry.resolve_project(args.project)
    results = index_db.search_index(
        project, args.query, k=args.k, entity_type=args.type
    )
    if args.expand:
        graph_path = Path(project["root"]) / "graph_data.json"
        seeds = [e["node_id"] for e in results["entities"] if e.get("node_id")]
        results["expanded"] = (
            expand_from_seeds(graph_path, seeds, top_k=args.k)
            if graph_path.exists() and seeds
            else []
        )
    if args.json:
        print(json.dumps(results, indent=2))
        return 0
    if not results["fused"]:
        print(f"No results for '{args.query}' in project '{project['name']}'")
        return 0
    print(f"Results for '{args.query}' in project '{project['name']}':")
    for item in results["fused"]:
        if item["kind"] == "entity":
            print(f"  [entity] {item['name']} ({item['entity_type']})")
        else:
            snippet = " ".join(item["snippet"].split())[:120]
            print(f"  [chunk]  {item['doc_id']}#{item['chunk_no']}: {snippet}")
    for item in results.get("expanded", []):
        print(
            f"  [graph]  {item['name']} ({item['entity_type']}) score={item['score']}"
        )
    return 0


def cmd_enhance(args) -> int:
    """Run arXiv-backed quality passes over the project's built graph.

    Passes (opt-in; if none selected, all run):
      --judge      LLM-as-judge triple gate (GraphJudge / GraphEval)
      --resolve    two-stage entity resolution (ComEM)
      --epistemic  bi-temporal contradiction layer + graded hedge scoring (Zep)

    Operates on <root>/graph_data.json and writes back in place, plus an
    enhancement_report.json. Uses lexical fallbacks unless an LLM is
    configured, so it runs offline.
    """
    from . import entity_resolution_v2 as erv2
    from . import epistemic_temporal as et
    from . import hedging
    from . import triple_judge

    project = registry.resolve_project(args.project)
    graph_path = Path(project["root"]) / "graph_data.json"
    if not graph_path.exists():
        print(
            f"Error: no graph_data.json in project '{project['name']}'. "
            "Build the graph first (/epistract:build).",
            file=sys.stderr,
        )
        return 1

    graph = json.loads(graph_path.read_text())
    link_key = "links" if "links" in graph else "edges"
    run_all = not (args.judge or args.resolve or args.epistemic)
    report: dict = {"project": project["name"]}

    if args.resolve or run_all:
        # Lexical/embedding cascade; an LLM entity-verifier can be plugged in
        # here via verify_fn once configured (kept lexical for offline default).
        res = erv2.resolve_entities(graph.get("nodes", []))
        graph = erv2.apply_merge_map(graph, res["merge_map"])
        report["resolve"] = {
            "auto_merged": res["auto_merged"],
            "clusters": len(res["clusters"]),
            "merged_ids": len(res["merge_map"]),
        }

    if args.judge or run_all:
        judge_fn = None
        if args.llm:
            try:
                judge_fn = triple_judge.make_llm_judge()
            except ImportError as e:
                print(
                    f"Error: --llm requires an LLM client but it could not be "
                    f"imported ({e}). Install the LLM dependencies or omit "
                    "--llm to use the offline lexical fallback.",
                    file=sys.stderr,
                )
                return 1
        report["judge"] = triple_judge.judge_graph(graph, judge_fn=judge_fn)

    if args.epistemic or run_all:
        links = graph.get(link_key, [])
        scored = [hedging.score_relation(link) for link in links]
        temporal = et.apply_temporal_layer(scored)
        graph[link_key] = temporal["links"]
        status_counts: dict[str, int] = {}
        for link in temporal["links"]:
            status = link.get("epistemic_status", "unclassified")
            status_counts[status] = status_counts.get(status, 0) + 1
        report["epistemic"] = {
            "status_counts": status_counts,
            "contradictions": len(temporal["contradictions"]),
            "invalidated": temporal["invalidated"],
        }

    graph_path.write_text(json.dumps(graph, indent=2) + "\n")
    (Path(project["root"]) / "enhancement_report.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )

    if args.json:
        print(json.dumps(report, indent=2))
        return 0
    print(f"Enhanced project '{project['name']}':")
    if "resolve" in report:
        r = report["resolve"]
        print(
            f"  entity resolution: merged {r['merged_ids']} into {r['clusters']} cluster(s)"
        )
    if "judge" in report:
        j = report["judge"]
        print(
            f"  triple judge: {j['verdict_counts']} — {j['gated_count']} gated "
            f"(score < {j['min_score']})"
        )
    if "epistemic" in report:
        e = report["epistemic"]
        print(
            f"  epistemic: {e['status_counts']}; "
            f"{e['contradictions']} contradiction(s), {e['invalidated']} superseded"
        )
    return 0


def cmd_projects(args) -> int:
    if args.action == "list":
        projects = registry.list_projects()
        human = (
            "\n".join(
                f"  {p['name']:24s} {p.get('domain', ''):18s} {p['root']}"
                for p in projects
            )
            or "  (no projects — run `epistract init <name>`)"
        )
        _emit(projects, args.json, f"Registered projects:\n{human}")
        return 0
    if args.action == "info":
        project = registry.get_project(args.name)
        sources = project["manifest"]["sources"]
        _emit(
            project,
            args.json,
            f"{project['name']} ({project['domain']}) at {project['root']}\n"
            f"  sources: {len(sources)}",
        )
        return 0
    if args.action == "delete":
        removed = registry.delete_project(args.name, purge=args.purge)
        _emit(
            removed,
            args.json,
            f"Removed '{args.name}' from registry"
            + (" and purged .epistract state" if args.purge else "")
            + f" (files at {removed['root']} untouched)",
        )
        return 0
    return 2


def cmd_status(args) -> int:
    project = registry.resolve_project(args.project)
    root = Path(project["root"])
    graph_path = root / "graph_data.json"
    graph_nodes = (
        len(json.loads(graph_path.read_text()).get("nodes", []))
        if graph_path.exists()
        else 0
    )
    indexed = 0
    if index_db.index_path(project).exists():
        db = index_db.open_index(project)
        indexed = db.execute("SELECT count(*) FROM documents").fetchone()[0]
        db.close()
    payload = {
        "name": project["name"],
        "root": project["root"],
        "domain": project["domain"],
        "sources": len(project["manifest"]["sources"]),
        "indexed_documents": indexed,
        "graph_nodes": graph_nodes,
        "claims_layer": (root / "claims_layer.json").exists(),
    }
    _emit(
        payload,
        args.json,
        f"{payload['name']} ({payload['domain']}) at {payload['root']}\n"
        f"  sources: {payload['sources']}  indexed: {indexed}  "
        f"graph nodes: {graph_nodes}  claims layer: "
        f"{'yes' if payload['claims_layer'] else 'no'}",
    )
    return 0


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="epistract", description="Multi-project knowledge graph datasets"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Create a new project")
    p_init.add_argument("name")
    p_init.add_argument("--domain", default=None, help="Domain package name")
    p_init.add_argument(
        "--dir", default=None, help="Project directory (default ./<name>)"
    )
    p_init.add_argument("--json", action="store_true")
    p_init.set_defaults(func=cmd_init)

    p_add = sub.add_parser("add", help="Add a project, files, or URLs")
    add_sub = p_add.add_subparsers(dest="what", required=True)

    p_add_project = add_sub.add_parser("project", help="Register a new project")
    p_add_project.add_argument("name")
    p_add_project.add_argument("--domain", default=None)
    p_add_project.add_argument("--dir", default=None)
    p_add_project.add_argument("--json", action="store_true")
    p_add_project.set_defaults(func=cmd_init)

    p_add_files = add_sub.add_parser("files", help="Add source files to the corpus")
    p_add_files.add_argument("paths", nargs="+")
    p_add_files.add_argument("--project", default=None)
    p_add_files.add_argument("--json", action="store_true")
    p_add_files.set_defaults(func=cmd_add_files)

    p_add_url = add_sub.add_parser("url", help="Fetch URLs into the corpus")
    p_add_url.add_argument("urls", nargs="+")
    p_add_url.add_argument("--project", default=None)
    p_add_url.add_argument("--json", action="store_true")
    p_add_url.set_defaults(func=cmd_add_url)

    p_index = sub.add_parser("index", help="Incrementally index the project")
    p_index.add_argument("--project", default=None)
    p_index.add_argument(
        "--rebuild", action="store_true", help="Drop and rebuild the index"
    )
    p_index.add_argument("--json", action="store_true")
    p_index.set_defaults(func=cmd_index)

    p_search = sub.add_parser("search", help="Hybrid search (entities + chunks)")
    p_search.add_argument("query")
    p_search.add_argument("--project", default=None)
    p_search.add_argument("--type", default=None, help="Filter entities by type")
    p_search.add_argument("-k", type=int, default=10, help="Max results")
    p_search.add_argument(
        "--expand",
        action="store_true",
        help="Graph expansion via personalized PageRank",
    )
    p_search.add_argument("--json", action="store_true")
    p_search.set_defaults(func=cmd_search)

    p_enhance = sub.add_parser(
        "enhance", help="Run KG quality passes (judge / resolve / epistemic)"
    )
    p_enhance.add_argument("--project", default=None)
    p_enhance.add_argument(
        "--judge", action="store_true", help="LLM-as-judge triple gate"
    )
    p_enhance.add_argument(
        "--resolve", action="store_true", help="Entity resolution merge"
    )
    p_enhance.add_argument(
        "--epistemic",
        action="store_true",
        help="Bi-temporal contradiction + hedge layer",
    )
    p_enhance.add_argument(
        "--llm",
        action="store_true",
        help="Use the configured LLM (default: lexical fallback)",
    )
    p_enhance.add_argument("--json", action="store_true")
    p_enhance.set_defaults(func=cmd_enhance)

    p_projects = sub.add_parser("projects", help="Manage the project registry")
    projects_sub = p_projects.add_subparsers(dest="action", required=True)
    p_list = projects_sub.add_parser("list")
    p_list.add_argument("--json", action="store_true")
    p_info = projects_sub.add_parser("info")
    p_info.add_argument("name")
    p_info.add_argument("--json", action="store_true")
    p_delete = projects_sub.add_parser("delete")
    p_delete.add_argument("name")
    p_delete.add_argument(
        "--purge", action="store_true", help="Also remove .epistract state"
    )
    p_delete.add_argument("--json", action="store_true")
    p_projects.set_defaults(func=cmd_projects)

    p_status = sub.add_parser("status", help="Show project status")
    p_status.add_argument("--project", default=None)
    p_status.add_argument("--json", action="store_true")
    p_status.set_defaults(func=cmd_status)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except ProjectError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
