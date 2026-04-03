#!/usr/bin/env python3
"""Contract-domain epistemic analysis.

Analyzes contract knowledge graphs for epistemic patterns specific to
legal/contractual language: conditional obligations, ambiguous terms,
conflicting clauses, and temporal dependencies.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path


# ---------------------------------------------------------------------------
# Contract-specific epistemic patterns
# ---------------------------------------------------------------------------

CONTRACT_HEDGING_PATTERNS = [
    (re.compile(r"\b(shall|must)\b", re.I), "obligatory"),
    (re.compile(r"\b(may|can)\s+(be|provide|request)\b", re.I), "permissive"),
    (re.compile(r"\b(subject\s+to|contingent\s+upon|provided\s+that)\b", re.I), "conditional"),
    (re.compile(r"\b(best\s+efforts?|reasonable\s+efforts?)\b", re.I), "soft_obligation"),
    (re.compile(r"\b(notwithstanding|except\s+as|unless)\b", re.I), "exception"),
    (re.compile(r"\b(approximately|estimated|about)\b", re.I), "approximate"),
    (re.compile(r"\b(to be determined|TBD|TBA)\b", re.I), "unresolved"),
]


def analyze_contract_epistemic(output_dir: Path) -> dict:
    """Run contract-specific epistemic analysis on a built graph.

    Args:
        output_dir: Directory containing graph_data.json.

    Returns:
        Dict with epistemic analysis results.
    """
    graph_path = output_dir / "graph_data.json"
    if not graph_path.exists():
        return {"error": f"No graph found at {graph_path}"}

    graph_data = json.loads(graph_path.read_text())
    links = graph_data.get("links", [])

    status_counts: dict[str, int] = defaultdict(int)

    for link in links:
        evidence = link.get("evidence", "")
        status = _classify_contract_epistemic(evidence)
        link["epistemic_status"] = status
        status_counts[status] += 1

    # Write updated graph
    graph_path.write_text(json.dumps(graph_data, indent=2))

    return {
        "total_relations": len(links),
        "status_counts": dict(status_counts),
    }


def _classify_contract_epistemic(evidence: str) -> str:
    """Classify epistemic status of a contract relation from its evidence text."""
    if not evidence:
        return "stated"

    for pattern, status in CONTRACT_HEDGING_PATTERNS:
        if pattern.search(evidence):
            return status

    return "stated"
