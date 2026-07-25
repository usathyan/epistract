#!/usr/bin/env python3
"""LLM-as-judge triple gate: score each relation against its evidence span.

Implements the GraphJudge (arXiv 2411.17388) / GraphEval (arXiv 2407.10793)
quality pattern: after extraction, each candidate triple is judged for whether
its evidence actually entails it. Verdicts convert the epistemic layer from
regex heuristics into per-edge, evidence-grounded scores.

Design: a dependency-free *lexical* judge runs by default (checks whether the
subject, object, and a relation cue appear in the evidence span) so the gate
works offline and is fully testable. Pass `judge_fn(triple, evidence) -> dict`
to defer to an LLM (via core/llm_client.call_llm) for calibrated judgments.

Verdict schema: {"verdict": "supported"|"unsupported"|"partial",
"score": float in [0,1], "reason": str}.
"""

from __future__ import annotations

import json
import re

from .hedging import hedge_score

_JUDGE_SYSTEM = (
    "You are a knowledge-graph triple validator. Given a (subject, relation, "
    "object) triple and the evidence sentence it was extracted from, decide "
    "whether the evidence entails the triple. Respond with ONLY a JSON object: "
    '{"verdict": "supported"|"unsupported"|"partial", "score": 0.0-1.0, '
    '"reason": "<= 15 words"}. "supported" = evidence clearly states the '
    'relation; "partial" = related but hedged/indirect; "unsupported" = '
    "evidence does not back the triple."
)


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", (text or "").lower()) if len(t) > 2}


def _name_of(node_id: str) -> str:
    """Strip a 'type:slug' node id down to human words for matching."""
    slug = node_id.split(":", 1)[-1] if ":" in node_id else node_id
    return slug.replace("_", " ").replace("-", " ")


def lexical_judge(triple: dict, evidence: str) -> dict:
    """Offline judge: score by subject/object token overlap with evidence.

    A triple is "supported" when both endpoints are grounded in the evidence;
    "partial" when only one is (or the evidence is hedged); "unsupported"
    when neither endpoint appears.
    """
    ev_tokens = _tokens(evidence)
    if not ev_tokens:
        return {"verdict": "unsupported", "score": 0.0, "reason": "no evidence text"}

    subj = _tokens(_name_of(triple.get("source", "")))
    obj = _tokens(_name_of(triple.get("target", "")))
    subj_hit = bool(subj & ev_tokens)
    obj_hit = bool(obj & ev_tokens)

    hedged = hedge_score(evidence)
    if subj_hit and obj_hit:
        score = max(0.5, 1.0 - hedged)
        verdict = "supported" if hedged < 0.25 else "partial"
        reason = "both endpoints grounded in evidence"
    elif subj_hit or obj_hit:
        score = 0.4 * (1.0 - hedged)
        verdict = "partial"
        reason = "one endpoint grounded in evidence"
    else:
        score = 0.0
        verdict = "unsupported"
        reason = "endpoints absent from evidence"
    return {"verdict": verdict, "score": round(score, 4), "reason": reason}


def make_llm_judge(call_fn=None):
    """Build a judge_fn backed by an LLM. call_fn defaults to llm_client.call_llm.

    The returned judge falls back to the lexical judge if the LLM output
    cannot be parsed, so a flaky endpoint never crashes the gate.
    """
    if call_fn is None:
        from .llm_client import call_llm as call_fn  # noqa: PLC0415

    def _judge(triple: dict, evidence: str) -> dict:
        user = json.dumps(
            {
                "subject": _name_of(triple.get("source", "")),
                "relation": triple.get("relation_type", ""),
                "object": _name_of(triple.get("target", "")),
                "evidence": evidence,
            }
        )
        try:
            # effort="low" replaces temperature=0.0 as the determinism control on
            # the Anthropic path (temperature is rejected by current models).
            # temperature is still passed for the OpenRouter path.
            #
            # max_tokens was 200. On current models thinking is on by default and
            # shares this budget, so 200 tokens could be consumed entirely by
            # thinking, leaving no JSON verdict — json.loads would then fail and
            # silently degrade every judgment to lexical_judge below. 2048 leaves
            # room for low-effort thinking plus the small JSON payload.
            raw = call_fn(
                _JUDGE_SYSTEM,
                user,
                max_tokens=2048,
                temperature=0.0,
                effort="low",
            )
            parsed = json.loads(raw)
            return {
                "verdict": parsed.get("verdict", "partial"),
                "score": max(0.0, min(1.0, float(parsed.get("score", 0.5)))),
                "reason": str(parsed.get("reason", ""))[:120],
            }
        except Exception:  # noqa: BLE001 — any failure degrades to lexical
            return lexical_judge(triple, evidence)

    return _judge


def judge_graph(
    graph_data: dict,
    judge_fn=None,
    min_score: float = 0.35,
) -> dict:
    """Judge every relation in a graph and annotate edges with the verdict.

    Mutates each link with judge_verdict / judge_score / judge_reason and a
    boolean `gated` (True when score < min_score → the triple is a
    filtering candidate). Returns a summary with counts and the flagged list.
    """
    judge = judge_fn or lexical_judge
    links = graph_data.get("links", graph_data.get("edges", []))
    counts = {"supported": 0, "partial": 0, "unsupported": 0}
    flagged: list[dict] = []

    for link in links:
        verdict = judge(link, link.get("evidence", ""))
        link["judge_verdict"] = verdict["verdict"]
        link["judge_score"] = verdict["score"]
        link["judge_reason"] = verdict["reason"]
        link["gated"] = verdict["score"] < min_score
        counts[verdict["verdict"]] = counts.get(verdict["verdict"], 0) + 1
        if link["gated"]:
            flagged.append(
                {
                    "source": link.get("source"),
                    "target": link.get("target"),
                    "relation_type": link.get("relation_type"),
                    "score": verdict["score"],
                    "reason": verdict["reason"],
                }
            )

    return {
        "total": len(links),
        "verdict_counts": counts,
        "gated_count": len(flagged),
        "min_score": min_score,
        "flagged": flagged,
    }
