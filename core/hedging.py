#!/usr/bin/env python3
"""Graded epistemic-hedge scoring for claim evidence.

The existing `core/label_epistemic.py` classifies a relation as "hypothesized"
on the first matching hedge regex — binary and order-dependent. This module
computes a *graded* hedge score in [0, 1] from cue density, following the
lexical-cue approach in hedge-detection research (arXiv 2405.13319; BioScope /
UnScientify cue inventories), so downstream code can calibrate "asserted" vs
"hypothesized" vs "speculative" on a continuum instead of a single regex hit.

Pure Python, no dependencies — runs wherever the plugin runs. An optional
`classifier_fn(text) -> float` hook lets callers blend in an NLI/transformer
hedge classifier when one is available, without changing the call sites.
"""

from __future__ import annotations

import re

# Cue inventories weighted by strength of epistemic hedging.
# Strong cues (explicit hypothesis framing) outweigh weak modal cues.
_STRONG_CUES = [
    r"hypothesiz(?:e|ed|es|ing)",
    r"speculat(?:e|ed|es|ing|ive)",
    r"conjectur(?:e|ed|es|ing|al)",
    r"postulat(?:e|ed|es|ing)",
    r"propos(?:e|ed|es|ing)\s+that",
    r"remains?\s+(?:unclear|unknown|to\s+be\s+(?:seen|determined|established))",
    r"not\s+(?:yet\s+)?(?:established|confirmed|proven|demonstrated)",
]
_MEDIUM_CUES = [
    r"suggest(?:s|ed|ing)?",
    r"indicat(?:e|es|ed|ing)\s+(?:that\s+)?(?:a\s+)?possib",
    r"appears?\s+to",
    r"seem(?:s|ed|ing)?\s+to",
    r"likely",
    r"presumabl[ye]",
    r"potential(?:ly)?",
    r"hypothet",
]
_WEAK_CUES = [
    r"\bmay\b",
    r"\bmight\b",
    r"\bcould\b",
    r"\bpossibl[ye]\b",
    r"\bperhaps\b",
    r"\bprobabl[ye]\b",
    r"\bunclear\b",
]

_WEIGHTED = (
    [(re.compile(p, re.I), 0.55) for p in _STRONG_CUES]
    + [(re.compile(p, re.I), 0.30) for p in _MEDIUM_CUES]
    + [(re.compile(p, re.I), 0.15) for p in _WEAK_CUES]
)

# Cues that DE-hedge: explicit certainty markers pull the score back down.
_CERTAINTY = re.compile(
    r"\b(demonstrat\w+|confirm\w+|establish\w+|prov(?:e|ed|en)|"
    r"clearly|definitively|significantly\s+(?:increased|decreased|reduced)|"
    r"we\s+show|results\s+show)\b",
    re.I,
)


def hedge_score(text: str, classifier_fn=None) -> float:
    """Return a hedge score in [0, 1]; higher = more hedged/uncertain.

    Score accumulates from weighted lexical cues (saturating, so a
    pile-up of weak modals cannot exceed one strong hypothesis cue) and
    is discounted by explicit certainty markers. When `classifier_fn` is
    provided, its output is averaged with the lexical score.
    """
    if not text:
        return 0.0
    accumulated = 0.0
    for pattern, weight in _WEIGHTED:
        if pattern.search(text):
            # Diminishing returns: each additional cue adds less.
            accumulated = accumulated + weight * (1.0 - accumulated)
    if _CERTAINTY.search(text):
        accumulated *= 0.5
    accumulated = max(0.0, min(1.0, accumulated))

    if classifier_fn is not None:
        model_score = max(0.0, min(1.0, float(classifier_fn(text))))
        accumulated = (accumulated + model_score) / 2.0
    return round(accumulated, 4)


def status_from_score(score: float, confidence: float = 1.0) -> str:
    """Map a hedge score (+ extraction confidence) to an epistemic status.

    Thresholds chosen to stay compatible with the existing status
    vocabulary in label_epistemic.py (asserted / hypothesized / speculative).
    """
    if score >= 0.55:
        return "speculative"
    if score >= 0.25:
        return "hypothesized"
    if confidence < 0.5:
        return "hypothesized"
    return "asserted"


def score_relation(link: dict, classifier_fn=None) -> dict:
    """Annotate a graph link with hedge_score and a graded epistemic_status.

    Returns a new dict (does not mutate the input) so callers control
    when the change is applied to the graph. A pre-existing
    epistemic_status of "superseded" is preserved (the hedge_score is
    still attached) so re-scoring cannot resurrect invalidated edges.
    """
    evidence = link.get("evidence", "") or ""
    score = hedge_score(evidence, classifier_fn=classifier_fn)
    if link.get("epistemic_status") == "superseded":
        return {**link, "hedge_score": score, "epistemic_status": "superseded"}
    confidence = link.get("confidence", 1.0)
    if confidence is None:  # explicit JSON null; 0.0 stays a valid value
        confidence = 1.0
    status = status_from_score(score, confidence)
    return {**link, "hedge_score": score, "epistemic_status": status}
