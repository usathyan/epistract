#!/usr/bin/env python3
"""crosswalk_output -- render a crosswalk spine (and, optionally, the
cross-domain findings computed from it) into the artifacts the rest of
epistract already knows how to display: a ``graph_data.json`` and a
``claims_layer.json`` in a project-shaped output directory.

Why a separate module. ``core/crosswalk.py``'s docstring is explicit that
``spine.json`` is a join TABLE, not a graph, and ``core/cross_domain.py``
emits its findings as their own artifact rather than as a modification to
any existing consumer. Both are correct, and both leave the crosswalk
invisible: no ``/epistract:*`` command produces it, the workbench cannot
load it, and ``docs/ADDING-DOMAINS.md`` lists "nothing consumes it yet"
under Not yet built. This module is that consumer. It reads the two
artifacts and writes new ones; it never modifies either input, and neither
input module imports this one.

What it does NOT do: merge the source graphs. ``docs/ADDING-DOMAINS.md``
records the blocker on a merged ``graph_data.json`` -- the registry assumes
one domain per project directory and a union graph has no domain to
validate against. The graph written here sidesteps that entirely: it is a
graph ABOUT the joins, whose nodes are canonical spine keys (typed by axis)
and source graphs, and whose links are membership and cross-domain
findings. It unions nothing, so it validates against exactly one domain --
``crosswalk`` -- and the blocker never fires.

Graph shape:

  nodes
    - one per source graph      entity_type "Graph",  id "graph::<key>"
    - one per (axis, key) pair  entity_type <Axis>,   id "<axis>::<key>"
  links
    - PRESENT_IN   axis-key node -> graph node, one per graph holding the key
    - <RULE_NAME>  axis-key node -> axis-key node, one per cross-domain
                   finding whose subject and object keys both landed in the
                   spine

Usage:
    python3 -m core.crosswalk_output render --spine spine.json \\
        --findings cross_domain_findings.json --out ./crosswalk-project
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

__all__ = [
    "GENERATOR",
    "CrosswalkOutputError",
    "axis_entity_type",
    "load_findings",
    "load_spine",
    "build_claims_layer",
    "build_crosswalk_graph",
    "build_parser",
    "graph_node_id",
    "key_node_id",
    "load_json",
    "main",
    "render",
    "write_crosswalk_output",
]

DOMAIN_NAME = "crosswalk"
# Stamped into the claims_layer.json this module writes so
# core/label_epistemic.py can tell it did not author it and refuse to
# overwrite it. See build_claims_layer.
GENERATOR = "crosswalk_output"
GRAPH_ENTITY_TYPE = "Graph"
MEMBERSHIP_RELATION = "PRESENT_IN"

# Node-id namespace separator. Double-colon, because a single colon appears
# inside real canonical keys (URLs, "phase 2: extension") and would make the
# id ambiguous to split on.
_ID_SEP = "::"


class CrosswalkOutputError(Exception):
    """Raised for user-facing render failures (bad or missing artifacts)."""


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def load_json(path: str | Path, label: str) -> dict:
    """Read a JSON object from ``path``, failing loudly and specifically.

    Every failure mode names the file and what was expected -- a missing or
    truncated spine must never degrade into an empty graph that reads as
    "the crosswalk found nothing".
    """
    p = Path(path)
    if not p.is_file():
        raise CrosswalkOutputError(f"{label} not found: {p}")
    try:
        payload = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise CrosswalkOutputError(f"Could not parse {label} at {p}: {e}") from e
    if not isinstance(payload, dict):
        raise CrosswalkOutputError(
            f"{label} at {p} must be a JSON object, got {type(payload).__name__}"
        )
    return payload


def load_spine(path: str | Path) -> dict:
    """Load and structurally validate a spine.json.

    Parseability is not enough. Every artifact in a crosswalk run is a JSON
    object with a ``graphs`` block, so a findings file (or one of the review
    artifacts written alongside it) handed to ``--spine`` parses cleanly and
    renders a three-node, zero-axis graph that exits 0 and reads as a
    successful run. Requiring the key ``core/crosswalk.py`` always emits
    turns that into a named error.

    An ``axes`` block that is present but EMPTY is accepted: that is a real
    spine whose graphs declared no common axis, which is a finding about the
    corpora, not a malformed file.
    """
    payload = load_json(path, "spine.json")
    axes = payload.get("axes")
    if not isinstance(axes, dict):
        raise CrosswalkOutputError(
            f"{Path(path)} is not a spine: no 'axes' object (found keys: "
            f"{sorted(payload)}). Build one with `python3 -m core.crosswalk build`."
        )
    return payload


def load_findings(path: str | Path) -> dict:
    """Load and structurally validate a cross_domain_findings.json.

    Same reasoning as ``load_spine``, and the same failure observed in
    practice: the review artifacts written beside a real findings file carry
    their own top-level ``findings`` key in a different shape, so pointing
    ``--findings`` at one silently produced a graph with zero finding links.

    A ``custom_findings`` block that is present but EMPTY is accepted: that
    is what a run whose every rule was skipped as advisory legitimately
    emits.
    """
    payload = load_json(path, "cross-domain findings")
    custom = (payload.get("super_domain") or {}).get("custom_findings")
    if not isinstance(custom, dict):
        raise CrosswalkOutputError(
            f"{Path(path)} is not a cross-domain findings file: no "
            f"'super_domain.custom_findings' object (found keys: {sorted(payload)}). "
            "Produce one with `python3 -m core.cross_domain analyze`."
        )
    return payload


# ---------------------------------------------------------------------------
# Naming
# ---------------------------------------------------------------------------


def axis_entity_type(axis_name: str) -> str:
    """Map an axis name to a graph entity type: ``adverse_event`` -> ``AdverseEvent``.

    The workbench colours nodes by ``entity_type`` and builds its legend and
    type filter from the distinct values, so axes become first-class filter
    facets for free. CamelCase matches the entity-type casing the pharma
    domains already use (``AdverseEvent``, ``Drug``, ``Trial``).
    """
    parts = [p for p in str(axis_name).split("_") if p]
    if not parts:
        return "Axis"
    return "".join(p[:1].upper() + p[1:] for p in parts)


def graph_node_id(graph_key: str) -> str:
    return f"graph{_ID_SEP}{graph_key}"


def key_node_id(axis_name: str, canonical_key: str) -> str:
    return f"{axis_name}{_ID_SEP}{canonical_key}"


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------


def _graph_nodes(spine: dict) -> list[dict]:
    """One node per source graph, carrying the axes it declared."""
    graphs = spine.get("graphs") or {}
    stats = spine.get("stats") or {}

    axes_declared: dict[str, list[str]] = {key: [] for key in graphs}
    for axis_name, axis_stats in stats.items():
        for key in axis_stats.get("declared_by") or []:
            axes_declared.setdefault(key, []).append(axis_name)

    nodes = []
    for key in sorted(graphs):
        declared = sorted(axes_declared.get(key, []))
        nodes.append(
            {
                "id": graph_node_id(key),
                "name": key,
                "entity_type": GRAPH_ENTITY_TYPE,
                "confidence": 1.0,
                "context": (
                    f"Source knowledge graph '{key}' "
                    f"({len(declared)} crosswalk axes declared)."
                ),
                "attributes": {
                    "directory": str(graphs.get(key, "")),
                    "axes_declared": declared,
                    "axes_declared_count": len(declared),
                },
                "source_documents": [],
            }
        )
    return nodes


def _key_nodes(spine: dict) -> tuple[list[dict], set[str]]:
    """One node per (axis, canonical key). Returns (nodes, node_id set)."""
    nodes: list[dict] = []
    node_ids: set[str] = set()

    for axis_name in sorted(spine.get("axes") or {}):
        entity_type = axis_entity_type(axis_name)
        axis_entries = (spine["axes"][axis_name]) or {}
        for canonical_key in sorted(axis_entries):
            entry = axis_entries[canonical_key] or {}
            member_graphs = entry.get("graphs") or {}
            members = {g: list(ids or []) for g, ids in sorted(member_graphs.items())}
            member_count = sum(len(ids) for ids in members.values())
            node_id = key_node_id(axis_name, canonical_key)
            node_ids.add(node_id)

            attributes: dict = {
                "axis": axis_name,
                "canonical_key": canonical_key,
                "graphs": sorted(members),
                "graph_count": len(members),
                "member_node_count": member_count,
                "shared": len(members) >= 2,
                "members": members,
            }
            # External identifiers ride onto the node as flat attributes so
            # they show up in the workbench detail panel without a nested
            # dict the frontend would have to special-case. Prefixed to keep
            # them from colliding with the structural keys above.
            for label, values in sorted((entry.get("identifiers") or {}).items()):
                attributes[f"id_{label}"] = list(values or [])

            shared_note = (
                f"shared by {len(members)} graphs: {', '.join(sorted(members))}"
                if len(members) >= 2
                else f"only in {', '.join(sorted(members)) or 'no graph'}"
            )
            nodes.append(
                {
                    "id": node_id,
                    "name": canonical_key,
                    "entity_type": entity_type,
                    "confidence": 1.0,
                    "context": f"Canonical {axis_name} key '{canonical_key}' -- {shared_note}.",
                    "attributes": attributes,
                    "source_documents": [],
                }
            )
    return nodes, node_ids


def _membership_links(spine: dict) -> list[dict]:
    """axis-key -> graph, one per graph holding that key."""
    links: list[dict] = []
    for axis_name in sorted(spine.get("axes") or {}):
        axis_entries = (spine["axes"][axis_name]) or {}
        for canonical_key in sorted(axis_entries):
            entry = axis_entries[canonical_key] or {}
            for graph_key, member_ids in sorted((entry.get("graphs") or {}).items()):
                ids = list(member_ids or [])
                links.append(
                    {
                        "source": key_node_id(axis_name, canonical_key),
                        "target": graph_node_id(graph_key),
                        "relation_type": MEMBERSHIP_RELATION,
                        "confidence": 1.0,
                        "evidence": (
                            f"{len(ids)} node(s) in graph '{graph_key}' canonicalise "
                            f"to {axis_name} key '{canonical_key}'."
                        ),
                        "attributes": {
                            "axis": axis_name,
                            "graph": graph_key,
                            "member_node_ids": ids,
                            "member_count": len(ids),
                        },
                    }
                )
    return links


def _finding_links(findings: dict, node_ids: set[str]) -> tuple[list[dict], int]:
    """axis-key -> axis-key, one per cross-domain finding.

    A finding whose subject or object key is not in the spine cannot be
    drawn (there is no node to attach it to). Those are counted and
    reported rather than dropped silently -- a rules spec pointed at a
    stale spine would otherwise render as a clean, finding-free graph.
    """
    links: list[dict] = []
    unattached = 0
    custom = ((findings.get("super_domain") or {}).get("custom_findings")) or {}

    for rule_name in sorted(custom):
        rule_findings = custom[rule_name]
        if not isinstance(rule_findings, list):
            continue
        for finding in rule_findings:
            if not isinstance(finding, dict):
                continue
            evidence = finding.get("evidence") or {}
            subject_axis = evidence.get("subject_axis")
            object_axis = evidence.get("object_axis")
            subject_key = evidence.get("subject_key")
            object_key = evidence.get("object_key")
            if not (subject_axis and object_axis and subject_key and object_key):
                # Rule-level error records ({"status": "error", ...}) land
                # here; they belong in the claims layer, not the graph.
                continue
            source = key_node_id(subject_axis, subject_key)
            target = key_node_id(object_axis, object_key)
            if source not in node_ids or target not in node_ids:
                unattached += 1
                continue
            links.append(
                {
                    "source": source,
                    "target": target,
                    "relation_type": str(rule_name).upper(),
                    "confidence": 1.0,
                    "evidence": finding.get("description", ""),
                    "severity": finding.get("severity", ""),
                    "attributes": {
                        "rule_name": rule_name,
                        "finding_type": finding.get("type", ""),
                        "severity": finding.get("severity", ""),
                        "subtype": evidence.get("subtype", ""),
                        "probe_graph": evidence.get("probe_graph", ""),
                        "reference_graph": evidence.get("reference_graph", ""),
                        "description": finding.get("description", ""),
                    },
                }
            )
    return links, unattached


def build_crosswalk_graph(spine: dict, findings: dict | None = None) -> dict:
    """Render a spine (+ optional findings) as a workbench-loadable graph.

    Builds new structures throughout -- neither input is mutated.
    """
    findings = findings or {}

    graph_nodes = _graph_nodes(spine)
    key_nodes, node_ids = _key_nodes(spine)
    links = _membership_links(spine)
    finding_links, unattached = _finding_links(findings, node_ids)
    links.extend(finding_links)

    axes = sorted(spine.get("axes") or {})
    shared_keys = sum(1 for n in key_nodes if n["attributes"]["shared"])

    return {
        "nodes": graph_nodes + key_nodes,
        "links": links,
        "metadata": {
            "domain": DOMAIN_NAME,
            "generated_at": datetime.now(UTC).isoformat(),
            "spine_version": spine.get("spine_version", ""),
            "cross_domain_version": findings.get("cross_domain_version", ""),
            "source_graphs": dict(spine.get("graphs") or {}),
            "axes": axes,
            "entity_types": sorted({n["entity_type"] for n in graph_nodes + key_nodes}),
            "total_nodes": len(graph_nodes) + len(key_nodes),
            "total_links": len(links),
            "canonical_keys": len(key_nodes),
            "shared_keys": shared_keys,
            "finding_links": len(finding_links),
            "findings_unattached": unattached,
            "spine_stats": spine.get("stats") or {},
            "cross_domain_stats": findings.get("stats") or {},
        },
    }


# ---------------------------------------------------------------------------
# Claims layer
# ---------------------------------------------------------------------------


def build_claims_layer(spine: dict, findings: dict | None = None) -> dict:
    """Render a spine (+ optional findings) as a claims_layer.json.

    Two channels, both already read by existing consumers:

    - ``super_domain.custom_findings`` -- the cross-domain findings, carried
      through verbatim in the shape ``core/cross_domain.py`` already emits.
    - top-level ``cross_references`` -- every canonical key present in two
      or more graphs, in the ``{entity, appears_in}`` shape the workbench
      chat prompt already renders under the domain's cross-references
      heading. This is what makes the join itself, not just its findings,
      answerable in chat.
    """
    findings = findings or {}
    raw_custom = ((findings.get("super_domain") or {}).get("custom_findings")) or {}

    # Carry the findings through in the shape core/cross_domain.py emits, with
    # one addition: `affected_entities`, holding the two crosswalk node IDs the
    # finding spans. The graph panel's severity filter already reads that field
    # to decide which nodes a claim touches; deriving the IDs here keeps that
    # frontend code generic instead of teaching it the "<axis>::<key>" scheme.
    # The source artifact on disk is not modified — this is a new file.
    custom_findings: dict[str, list[dict]] = {}
    for rule_name in sorted(raw_custom):
        rule_findings = raw_custom[rule_name]
        if not isinstance(rule_findings, list):
            custom_findings[rule_name] = rule_findings
            continue
        enriched: list[dict] = []
        for finding in rule_findings:
            if not isinstance(finding, dict):
                enriched.append(finding)
                continue
            evidence = finding.get("evidence") or {}
            affected = [
                key_node_id(evidence[axis_field], evidence[key_field])
                for axis_field, key_field in (
                    ("subject_axis", "subject_key"),
                    ("object_axis", "object_key"),
                )
                if evidence.get(axis_field) and evidence.get(key_field)
            ]
            enriched.append({**finding, "affected_entities": affected} if affected else dict(finding))
        custom_findings[rule_name] = enriched

    cross_references: list[dict] = []
    for axis_name in sorted(spine.get("axes") or {}):
        for canonical_key in sorted((spine["axes"][axis_name]) or {}):
            entry = (spine["axes"][axis_name])[canonical_key] or {}
            member_graphs = sorted((entry.get("graphs") or {}))
            if len(member_graphs) < 2:
                continue
            cross_references.append(
                {
                    "entity": f"{canonical_key} ({axis_name})",
                    "appears_in": member_graphs,
                    "axis": axis_name,
                    "canonical_key": canonical_key,
                }
            )

    return {
        "domain": DOMAIN_NAME,
        # Authorship stamp. `claims_layer.json` is a fixed filename, and
        # core/label_epistemic.py rewrites it unconditionally — without this
        # stamp a routine `/epistract:epistemic` run on a crosswalk output
        # directory silently replaced every join and finding below with a
        # biomedical-fallback summary. That module refuses to overwrite a
        # layer stamped by a different generator.
        "generator": GENERATOR,
        "generated_at": datetime.now(UTC).isoformat(),
        "super_domain": {
            "custom_findings": custom_findings,
            "conflicts": [],
            "coverage_gaps": [],
            "risks": [],
            "cross_contract_entities": cross_references,
        },
        # Top-level mirrors: examples/workbench/system_prompt.py reads the
        # claims layer at top level, while api_graph.py reads it under
        # super_domain. Writing both is what makes the same artifact visible
        # in the chat panel and over the HTTP API without changing either
        # reader's contract.
        "conflicts": [],
        "gaps": [],
        "risks": [],
        "cross_references": cross_references,
    }


# ---------------------------------------------------------------------------
# Writing
# ---------------------------------------------------------------------------


def write_crosswalk_output(
    out_dir: str | Path,
    spine: dict,
    findings: dict | None = None,
) -> dict:
    """Write graph_data.json + claims_layer.json into ``out_dir``.

    Returns a summary dict (also printed by the CLI). The directory is
    created if absent; it is shaped exactly like any other epistract project
    output directory, so `/epistract:dashboard`, `/epistract:view` and
    `/epistract:export` all accept it unchanged.
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    graph = build_crosswalk_graph(spine, findings)
    claims = build_claims_layer(spine, findings)

    (out / "graph_data.json").write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")
    (out / "claims_layer.json").write_text(json.dumps(claims, indent=2) + "\n", encoding="utf-8")

    meta = graph["metadata"]
    return {
        "output_dir": str(out.resolve()),
        "domain": DOMAIN_NAME,
        "graphs": sorted(meta["source_graphs"]),
        "axes": meta["axes"],
        "entity_types": meta["entity_types"],
        "nodes": meta["total_nodes"],
        "links": meta["total_links"],
        "canonical_keys": meta["canonical_keys"],
        "shared_keys": meta["shared_keys"],
        "finding_links": meta["finding_links"],
        "findings_unattached": meta["findings_unattached"],
        "cross_references": len(claims["cross_references"]),
    }


def render(
    spine_path: str | Path,
    out_dir: str | Path,
    findings_path: str | Path | None = None,
) -> dict:
    """Load the artifacts named by path and write the rendered output."""
    spine = load_spine(spine_path)
    findings = load_findings(findings_path) if findings_path else None
    return write_crosswalk_output(out_dir, spine, findings)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="crosswalk_output",
        description="Render a crosswalk spine as a viewable knowledge graph",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("render", help="Render spine.json into a viewable output directory")
    p.add_argument("--spine", required=True, help="Path to spine.json")
    p.add_argument(
        "--findings",
        default=None,
        help="Optional path to cross_domain_findings.json",
    )
    p.add_argument("--out", required=True, help="Output directory to write")
    p.add_argument("--json", action="store_true", help="Print the summary as JSON")
    p.set_defaults(func=_cmd_render)
    return parser


def _cmd_render(args: argparse.Namespace) -> int:
    try:
        summary = render(args.spine, args.out, args.findings)
    except CrosswalkOutputError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print(f"Wrote crosswalk graph to {summary['output_dir']}")
        print(f"  graphs:          {', '.join(summary['graphs']) or '(none)'}")
        print(f"  axes:            {', '.join(summary['axes']) or '(none)'}")
        print(f"  nodes / links:   {summary['nodes']} / {summary['links']}")
        print(
            f"  canonical keys:  {summary['canonical_keys']} "
            f"({summary['shared_keys']} shared by 2+ graphs)"
        )
        print(f"  finding links:   {summary['finding_links']}")
        # A spine that loaded three graphs and joined nothing renders as a
        # perfectly valid graph of isolated keys. Say so rather than letting
        # the node count imply a successful join.
        if not summary["canonical_keys"]:
            print(
                "  WARNING: the spine holds no canonical keys at all — the graphs "
                "loaded but no axis produced a single key."
            )
        elif not summary["shared_keys"]:
            print(
                "  WARNING: no canonical key is held by two or more graphs — nothing "
                "joined. Check each axis's `declared_by` list in the spine stats."
            )
        if summary["findings_unattached"]:
            print(
                f"  WARNING: {summary['findings_unattached']} finding(s) referenced a "
                "canonical key absent from the spine and were not drawn."
            )
        print(f"\nView it with:  /epistract:dashboard --output {summary['output_dir']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
