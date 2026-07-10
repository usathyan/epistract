#!/usr/bin/env python3
"""Bi-temporal epistemic layer: contradiction-driven edge invalidation.

Implements the Graphiti/Zep pattern (arXiv 2501.13956) for the epistemic
"super domain": when a newer relation contradicts an existing one, the older
edge is *invalidated* (marked superseded) rather than deleted, so the graph
retains full provenance of what changed and when. Combined with a lexical
contradiction cascade (LegalWiz filter→judge shape, arXiv 2510.03418) that can
optionally defer to an NLI/LLM adjudicator for borderline pairs.

Pure logic + injectable adjudicator — no model downloads required. A caller
with a DeBERTa-MNLI model or an LLM passes `adjudicate_fn(a, b) -> verdict`
to upgrade the lexical decision.

A "claim" here is a graph link: {source, target, relation_type, confidence,
evidence, (optional) valid_at, epistemic_status}.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

# Relation-type pairs that are mutually exclusive by meaning. Extend per domain.
_ANTONYM_RELATIONS = {
    frozenset({"INCREASES", "DECREASES"}),
    frozenset({"ACTIVATES", "INHIBITS"}),
    frozenset({"UPREGULATES", "DOWNREGULATES"}),
    frozenset({"CAUSES", "PREVENTS"}),
    frozenset({"SUPPORTS", "REFUTES"}),
    frozenset({"AGONIST", "ANTAGONIST"}),
    frozenset({"EFFECTIVE", "INEFFECTIVE"}),
}

_NEGATION = re.compile(
    r"\b(no|not|never|without|absence\s+of|failed?\s+to|did\s+not|does\s+not|"
    r"was\s+not|were\s+not|lack(?:s|ed|ing)?\s+of?|neither|nor|un(?:able|likely))\b",
    re.I,
)


def _polarity(evidence: str) -> int:
    """Rough evidence polarity: -1 if negated, +1 otherwise."""
    return -1 if _NEGATION.search(evidence or "") else 1


def relations_contradict(a: dict, b: dict, adjudicate_fn=None) -> bool:
    """Decide whether two relations over the same node pair contradict.

    Lexical cascade:
      1. Different antonym relation types over the same (source, target)
         → contradiction.
      2. Same relation type but opposite evidence polarity (one negated,
         one not) → contradiction.
    If `adjudicate_fn(a, b) -> bool` is supplied, it overrides the lexical
    verdict (use it to plug in NLI/LLM adjudication for the borderline set).
    """
    if (a.get("source"), a.get("target")) != (b.get("source"), b.get("target")):
        return False

    rel_a = (a.get("relation_type") or "").upper()
    rel_b = (b.get("relation_type") or "").upper()

    lexical = False
    if frozenset({rel_a, rel_b}) in _ANTONYM_RELATIONS:
        lexical = True
    elif rel_a == rel_b and _polarity(a.get("evidence", "")) != _polarity(
        b.get("evidence", "")
    ):
        lexical = True

    if adjudicate_fn is not None and lexical:
        # Only spend the expensive adjudicator on lexically-flagged pairs
        # (LegalWiz filter→judge cost structure).
        return bool(adjudicate_fn(a, b))
    return lexical


def _edge_time(link: dict) -> str:
    """Sort key for recency: explicit valid_at, else empty (treated oldest)."""
    return link.get("valid_at") or ""


def _edge_confidence(link: dict) -> float:
    """Tie-break key: confidence, coercing explicit null to the 0.0 default."""
    confidence = link.get("confidence", 0.0)
    return 0.0 if confidence is None else confidence


def _edge_identity(link: dict) -> str:
    """Stable identity for an edge: 'source|relation_type|target'.

    Used for superseded_by references and contradiction reports so they
    survive edge reordering/filtering, unlike array indices.
    """
    return f"{link.get('source')}|{link.get('relation_type')}|{link.get('target')}"


def apply_temporal_layer(
    links: list[dict],
    adjudicate_fn=None,
    now: str | None = None,
) -> dict:
    """Detect contradictions and invalidate superseded edges in place-ish.

    Returns {"links": [...annotated...], "contradictions": [...],
    "invalidated": n}. For each contradicting pair, the more recent edge
    (by valid_at, tie-broken by higher confidence) stays active; the other
    gets epistemic_status="superseded", invalid_at=now, and superseded_by
    pointing at the winner's stable edge identity
    ("source|relation_type|target").

    Never deletes edges — invalidation is annotation only, preserving the
    full provenance trail.
    """
    stamp = now or datetime.now(timezone.utc).isoformat()
    annotated = [dict(link) for link in links]
    contradictions: list[dict] = []
    invalidated = 0

    # Group by (source, target): relations_contradict is always False across
    # different node pairs, so scoping the pairwise scan to each group is
    # behavior-preserving while avoiding the all-pairs O(n^2) sweep. Groups
    # keep original edge ordering so tie-breaks match the previous scan.
    groups: dict[tuple, list[int]] = {}
    for idx, link in enumerate(annotated):
        groups.setdefault((link.get("source"), link.get("target")), []).append(idx)

    for indices in groups.values():
        for pos_i in range(len(indices)):
            for pos_j in range(pos_i + 1, len(indices)):
                a, b = annotated[indices[pos_i]], annotated[indices[pos_j]]
                if (
                    a.get("epistemic_status") == "superseded"
                    or b.get("epistemic_status") == "superseded"
                ):
                    continue
                if not relations_contradict(a, b, adjudicate_fn=adjudicate_fn):
                    continue

                # Winner = more recent, tie-broken by confidence.
                a_key = (_edge_time(a), _edge_confidence(a))
                b_key = (_edge_time(b), _edge_confidence(b))
                winner, loser = (a, b) if a_key >= b_key else (b, a)
                loser["epistemic_status"] = "superseded"
                loser["invalid_at"] = stamp
                loser["superseded_by"] = _edge_identity(winner)
                invalidated += 1
                contradictions.append(
                    {
                        "source": a.get("source"),
                        "target": a.get("target"),
                        "active": _edge_identity(winner),
                        "superseded": _edge_identity(loser),
                        "active_relation": winner.get("relation_type"),
                        "superseded_relation": loser.get("relation_type"),
                    }
                )

    return {
        "links": annotated,
        "contradictions": contradictions,
        "invalidated": invalidated,
    }
