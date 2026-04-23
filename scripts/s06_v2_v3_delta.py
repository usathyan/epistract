#!/usr/bin/env python3
"""Capture V2 vs V3 delta for Scenario 6 GLP-1 corpus.

Reads graph_data.json, communities.json, claims_layer.json (if present)
from both output-v2/ and output-v3/, prints a Markdown comparison table
and writes JSON summary to output-v3/s06_delta.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "tests" / "corpora" / "06_glp1_landscape"


def load_json(path: Path):
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"WARN: could not read {path}: {e}", file=sys.stderr)
        return None


def count_communities(communities_obj) -> int:
    if communities_obj is None:
        return 0
    if isinstance(communities_obj, list):
        return len(communities_obj)
    if isinstance(communities_obj, dict):
        unique = set()
        for v in communities_obj.values():
            if isinstance(v, (int, str)):
                unique.add(v)
            elif isinstance(v, dict):
                unique.add(
                    v.get("community_id")
                    or v.get("community")
                    or v.get("label")
                )
        return len([u for u in unique if u is not None])
    return 0


def count_prophetic(claims_obj) -> int:
    if claims_obj is None:
        return 0
    return (
        claims_obj.get("summary", {})
        .get("epistemic_status_counts", {})
        .get("prophetic", 0)
    )


def count_hypotheses(claims_obj) -> int:
    if claims_obj is None:
        return 0
    return len(claims_obj.get("super_domain", {}).get("hypotheses", []))


def count_contradictions(claims_obj) -> int:
    if claims_obj is None:
        return 0
    return len(claims_obj.get("super_domain", {}).get("contradictions", []))


def count_contested(claims_obj) -> int:
    if claims_obj is None:
        return 0
    return len(claims_obj.get("super_domain", {}).get("contested_claims", []))


def summarize(out_dir: Path) -> dict:
    graph = load_json(out_dir / "graph_data.json") or {}
    communities = load_json(out_dir / "communities.json")
    claims = load_json(out_dir / "claims_layer.json")
    validation = load_json(out_dir / "validation_report.json")

    nodes = graph.get("nodes", [])
    edges = graph.get("links", graph.get("edges", []))
    metadata = graph.get("metadata") or {}

    return {
        "path": str(out_dir.relative_to(ROOT)),
        "nodes": len(nodes),
        "edges": len(edges),
        "communities": count_communities(communities),
        "metadata_domain": metadata.get("domain"),
        "has_metadata": bool(metadata),
        "prophetic": count_prophetic(claims),
        "hypotheses": count_hypotheses(claims),
        "contradictions": count_contradictions(claims),
        "contested": count_contested(claims),
        "has_validation_report": validation is not None,
        "validation_status": (validation or {}).get("overall_status") or (validation or {}).get("status"),
    }


def main() -> int:
    v2 = summarize(CORPUS / "output-v2")
    v3 = summarize(CORPUS / "output-v3")

    print("# Scenario 6 — V2 vs V3 Delta\n")
    fields = [
        ("Nodes", "nodes"),
        ("Edges", "edges"),
        ("Communities", "communities"),
        ("Prophetic claims", "prophetic"),
        ("Hypotheses", "hypotheses"),
        ("Contradictions", "contradictions"),
        ("Contested claims", "contested"),
        ("metadata.domain populated", "metadata_domain"),
        ("validation_report.json present", "has_validation_report"),
    ]
    print("| Metric | V2 (Opus 4.6) | V3 (Sonnet 4.6) | Delta |")
    print("|---|---:|---:|---:|")
    for label, key in fields:
        a = v2.get(key)
        b = v3.get(key)
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            delta = f"{b - a:+}"
        else:
            delta = "—"
        print(f"| {label} | {a!r} | {b!r} | {delta} |")

    out = CORPUS / "output-v3" / "s06_delta.json"
    out.write_text(json.dumps({"v2": v2, "v3": v3}, indent=2))
    print(f"\nWrote summary to {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
