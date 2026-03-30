#!/usr/bin/env python3
"""Domain-aware epistemic analysis dispatcher for epistract knowledge graphs.

Routes epistemic analysis to the appropriate domain-specific module based on
the domain metadata in graph_data.json. Biomedical graphs use hedging patterns,
document-type inference, and hypothesis grouping. Contract graphs use
cross-reference conflict detection (when available).

Complements (does not replace) the Louvain community structure. Communities
group by topology; this groups by epistemology.

Usage:
    python label_epistemic.py <output_dir> [--domain contract]

Output:
    <output_dir>/claims_layer.json  -- Super Domain overlay
    Updates graph_data.json links with epistemic_status field

Reference:
    Eric Little, "Reasoning with Knowledge Graphs -- Super Domains"
    https://www.linkedin.com/posts/eric-little-71b2a0b_pleased-to-announce-that-i-will-be-speaking-activity-7442581339096313856-wEFc
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from domain_resolver import resolve_domain  # noqa: F401 — domain dispatch architecture
from epistemic_biomedical import analyze_biomedical_epistemic


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------


def analyze_epistemic(output_dir: Path, domain_name: str | None = None) -> dict:
    """Run full epistemic analysis on a built graph.

    Dispatches to the appropriate domain-specific analysis module based on
    graph metadata or explicit domain_name parameter.

    Args:
        output_dir: Directory containing graph_data.json.
        domain_name: Explicit domain override. If None, detected from
            graph_data.json metadata.domain field (defaults to "drug-discovery").

    Returns:
        Claims layer dict with metadata, summary, base_domain, super_domain.
    """
    graph_path = output_dir / "graph_data.json"
    if not graph_path.exists():
        print(f"Error: {graph_path} not found. Run /epistract-build first.", file=sys.stderr)
        sys.exit(1)

    graph_data = json.loads(graph_path.read_text())

    # Detect domain from graph metadata if not explicitly provided
    if domain_name is None:
        domain_name = graph_data.get("metadata", {}).get("domain", "drug-discovery")

    # Dispatch to domain-specific analysis module
    if domain_name == "contract":
        try:
            from epistemic_contract import analyze_contract_epistemic
        except ImportError:
            return {
                "error": "Contract epistemic module not yet available. Run Plan 02 first.",
                "summary": {"status": "unavailable"},
            }
        claims_layer = analyze_contract_epistemic(output_dir, graph_data)
    else:
        # Default: biomedical (drug-discovery) or any other domain
        claims_layer = analyze_biomedical_epistemic(output_dir, graph_data)

    # Write claims layer
    claims_path = output_dir / "claims_layer.json"
    claims_path.write_text(json.dumps(claims_layer, indent=2))

    # Update graph_data.json with epistemic_status on links
    graph_path.write_text(json.dumps(graph_data, indent=2))

    # Print summary
    summary = claims_layer.get("summary", {})
    status_counts = summary.get("epistemic_status_counts", {})
    links = graph_data.get("links", [])
    print(json.dumps({
        "claims_layer": str(claims_path),
        "domain": domain_name,
        "total_relations": len(links),
        "base_domain_relations": status_counts.get("asserted", 0),
        "super_domain_relations": sum(v for k, v in status_counts.items() if k != "asserted"),
        "status_breakdown": status_counts,
        "contradictions": summary.get("contradictions_found", 0),
        "hypotheses": summary.get("hypotheses_found", 0),
        "document_types": list(summary.get("document_types", {}).keys()),
    }, indent=2))

    return claims_layer


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python label_epistemic.py <output_dir> [--domain <name>]", file=sys.stderr)
        sys.exit(1)

    out_dir = Path(sys.argv[1])
    domain = None
    if "--domain" in sys.argv:
        idx = sys.argv.index("--domain")
        if idx + 1 < len(sys.argv):
            domain = sys.argv[idx + 1]

    analyze_epistemic(out_dir, domain_name=domain)
