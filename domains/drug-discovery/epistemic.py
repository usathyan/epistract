#!/usr/bin/env python3
"""Drug-discovery domain epistemic analysis.

Provides biomedical-specific epistemic classification patterns that
complement the core epistemic analysis in core/label_epistemic.py.

The core module handles domain-agnostic hedging detection. This module
adds drug-discovery-specific patterns: clinical trial phases, regulatory
status, mechanism confidence levels.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path


# ---------------------------------------------------------------------------
# Biomedical-specific epistemic patterns
# ---------------------------------------------------------------------------

BIOMEDICAL_HEDGING_PATTERNS = [
    (re.compile(r"\b(phase\s+[I1])\b", re.I), "early_clinical"),
    (re.compile(r"\b(phase\s+[II2][Ii]?[Ii]?)\b", re.I), "mid_clinical"),
    (re.compile(r"\b(phase\s+[III3][Ii]?[Ii]?)\b", re.I), "late_clinical"),
    (re.compile(r"\b(FDA[\s-]?approved|EMA[\s-]?approved)\b", re.I), "approved"),
    (re.compile(r"\b(preclinical|pre-clinical|in\s+vitro|in\s+vivo)\b", re.I), "preclinical"),
    (re.compile(r"\b(withdrawn|discontinued|terminated)\b", re.I), "terminated"),
    (re.compile(r"\b(off-label|compassionate\s+use)\b", re.I), "off_label"),
    (re.compile(r"\b(GWAS|genome-wide)\b", re.I), "genetic_association"),
]


def analyze_biomedical_epistemic(output_dir: Path) -> dict:
    """Run biomedical-specific epistemic analysis on a built graph.

    Args:
        output_dir: Directory containing graph_data.json.

    Returns:
        Dict with biomedical epistemic analysis results.
    """
    graph_path = output_dir / "graph_data.json"
    if not graph_path.exists():
        return {"error": f"No graph found at {graph_path}"}

    graph_data = json.loads(graph_path.read_text())
    links = graph_data.get("links", [])

    status_counts: dict[str, int] = defaultdict(int)

    for link in links:
        evidence = link.get("evidence", "")
        status = _classify_biomedical_epistemic(evidence)
        if status != "unclassified":
            link.setdefault("biomedical_epistemic", status)
            status_counts[status] += 1

    # Write updated graph
    graph_path.write_text(json.dumps(graph_data, indent=2))

    return {
        "total_relations": len(links),
        "biomedical_status_counts": dict(status_counts),
    }


def _classify_biomedical_epistemic(evidence: str) -> str:
    """Classify biomedical-specific epistemic status from evidence text."""
    if not evidence:
        return "unclassified"

    for pattern, status in BIOMEDICAL_HEDGING_PATTERNS:
        if pattern.search(evidence):
            return status

    return "unclassified"
