"""Clinical-trials epistemic analysis — phase-based evidence grading.

Called by core/label_epistemic.py's convention-based dispatcher:
- Domain slug "clinicaltrials" -> function name "analyze_clinicaltrials_epistemic"
  (derived via slug.replace("-", "_")).
- Returns a claims_layer dict with the standard {metadata, summary,
  base_domain, super_domain} envelope consumed by /epistract-epistemic.

Evidence grading rules:
1. Phase III trials -> high_evidence
2. Phase II -> medium_evidence
3. Phase I or observational -> low_evidence
4. Randomized or double-blind signals bump up one tier
5. Large enrollment (>=300) bumps up one tier; small (<50) bumps down
"""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path


# ---------------------------------------------------------------------------
# Phase classification constants
# ---------------------------------------------------------------------------

PHASE3_VALUES = {"PHASE3", "Phase 3", "Phase III", "PHASE_3"}
PHASE2_VALUES = {"PHASE2", "Phase 2", "Phase II", "PHASE_2"}
PHASE1_VALUES = {"PHASE1", "Phase 1", "Phase I", "PHASE_1"}
OBSERVATIONAL_VALUES = {"OBSERVATIONAL", "Observational"}

BLINDING_RE = re.compile(
    r"\b(randomi[sz]ed|double[- ]blind|single[- ]blind|placebo[- ]controlled)\b",
    re.IGNORECASE,
)

EVIDENCE_TIERS = ("low_evidence", "medium_evidence", "high_evidence")


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _trial_phase(node: dict) -> str | None:
    """Return normalized phase ('PHASE3'|'PHASE2'|'PHASE1'|'OBSERVATIONAL') or None.

    Reads node['ct_phase'] first (set by enrich.py in Plan 21-02), then falls
    back to node['attributes']['phase'] if present.
    """
    # Check ct_phase attribute first (set by enrichment)
    ct_phase = node.get("ct_phase")
    if ct_phase:
        if ct_phase in PHASE3_VALUES:
            return "PHASE3"
        if ct_phase in PHASE2_VALUES:
            return "PHASE2"
        if ct_phase in PHASE1_VALUES:
            return "PHASE1"
        if ct_phase in OBSERVATIONAL_VALUES:
            return "OBSERVATIONAL"

    # Fallback to attributes dict
    attrs = node.get("attributes", {}) or {}
    phase = attrs.get("phase", "")
    if phase:
        if phase in PHASE3_VALUES:
            return "PHASE3"
        if phase in PHASE2_VALUES:
            return "PHASE2"
        if phase in PHASE1_VALUES:
            return "PHASE1"
        if phase in OBSERVATIONAL_VALUES:
            return "OBSERVATIONAL"

    return None


def _enrollment(node: dict) -> int | None:
    """Return enrollment count from Trial node — ct_enrollment or attributes.enrollment."""
    # Check ct_enrollment first (set by enrichment)
    ct_enrollment = node.get("ct_enrollment")
    if ct_enrollment is not None:
        try:
            return int(ct_enrollment)
        except (ValueError, TypeError):
            pass

    # Fallback to attributes dict
    attrs = node.get("attributes", {}) or {}
    enrollment = attrs.get("enrollment")
    if enrollment is not None:
        try:
            return int(enrollment)
        except (ValueError, TypeError):
            pass

    return None


def _bump_tier(tier: str, delta: int) -> str:
    """Move tier up (+1) or down (-1) within EVIDENCE_TIERS; clamp at endpoints.

    Input 'unclassified' returns unchanged.
    """
    if tier == "unclassified":
        return "unclassified"
    try:
        idx = EVIDENCE_TIERS.index(tier)
    except ValueError:
        return "unclassified"
    new_idx = max(0, min(len(EVIDENCE_TIERS) - 1, idx + delta))
    return EVIDENCE_TIERS[new_idx]


def _grade_relation(link: dict, trial_lookup: dict) -> str:
    """Return evidence tier for one relation.

    Apply phase -> blinding -> enrollment bumps in that order.
    If no connected Trial node is found, return 'unclassified'.
    """
    # Find a connected Trial node by checking source and target
    source = link.get("source", "")
    target = link.get("target", "")

    trial_node: dict | None = trial_lookup.get(source) or trial_lookup.get(target)

    if trial_node is None:
        return "unclassified"

    # Step 1: Determine starting tier from trial phase
    phase = _trial_phase(trial_node)
    if phase == "PHASE3":
        tier = "high_evidence"
    elif phase == "PHASE2":
        tier = "medium_evidence"
    elif phase in ("PHASE1", "OBSERVATIONAL"):
        tier = "low_evidence"
    else:
        # No phase info available — start at low
        tier = "low_evidence"

    # Step 2: Apply blinding/randomization bump
    evidence_text = link.get("evidence", "") or ""
    if BLINDING_RE.search(evidence_text):
        tier = _bump_tier(tier, +1)

    # Step 3: Apply enrollment bump
    enrollment = _enrollment(trial_node)
    if enrollment is not None:
        if enrollment >= 300:
            tier = _bump_tier(tier, +1)
        elif enrollment < 50:
            tier = _bump_tier(tier, -1)

    return tier


# ---------------------------------------------------------------------------
# Main epistemic analysis function
# ---------------------------------------------------------------------------


def analyze_clinicaltrials_epistemic(output_dir: Path, graph_data: dict) -> dict:
    """Run clinical-trial epistemic analysis on a built graph.

    Args:
        output_dir: directory containing graph_data.json (used for metadata paths only).
        graph_data: parsed graph_data.json dict with 'nodes' and 'links'.

    Returns:
        claims_layer dict with keys: metadata, summary, base_domain, super_domain.
    """
    nodes = graph_data.get("nodes", [])
    links = graph_data.get("links", [])

    # Build Trial lookup (accept both capitalized 'Trial' and upper 'TRIAL')
    trial_lookup: dict[str, dict] = {
        n["id"]: n for n in nodes
        if str(n.get("entity_type", "")).lower() == "trial"
    }

    evidence_counts: dict[str, int] = defaultdict(int)
    for link in links:
        tier = _grade_relation(link, trial_lookup)
        link["evidence_tier"] = tier
        evidence_counts[tier] += 1

    # Contradiction detection: same (source, target, relation_type) with conflicting tiers
    triple_to_tiers: dict[tuple, list[str]] = defaultdict(list)
    for link in links:
        key = (link.get("source"), link.get("target"), link.get("relation_type"))
        triple_to_tiers[key].append(link.get("evidence_tier", "unclassified"))
    contradictions = []
    for key, tiers in triple_to_tiers.items():
        if "high_evidence" in tiers and "low_evidence" in tiers:
            contradictions.append({
                "source": key[0], "target": key[1], "relation_type": key[2],
                "tiers": tiers,
            })

    return {
        "metadata": {
            "description": "Clinical-trial epistemic layer — phase-based evidence grading",
            "generated_from": str(output_dir / "graph_data.json"),
            "total_relations": len(links),
            "trial_count": len(trial_lookup),
        },
        "summary": {
            "evidence_tier_counts": dict(evidence_counts),
            "contradictions_found": len(contradictions),
            "trials_with_phase": sum(1 for n in trial_lookup.values() if _trial_phase(n)),
            "trials_with_enrollment": sum(1 for n in trial_lookup.values() if _enrollment(n) is not None),
        },
        "base_domain": {
            "description": "High-evidence relations from Phase 3, randomized, or large-enrollment trials",
            "relation_count": evidence_counts.get("high_evidence", 0),
        },
        "super_domain": {
            "description": "Medium/low/unclassified-evidence relations — smaller trials, early phase, or unclassifiable",
            "relation_count": sum(v for k, v in evidence_counts.items() if k != "high_evidence"),
            "contradictions": contradictions,
        },
    }
