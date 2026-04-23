#!/usr/bin/env python3
"""Biomedical epistemic analysis for drug-discovery knowledge graphs.

Extracted from label_epistemic.py to support domain-aware dispatch.
Contains all hedging patterns, document-type inference, contradiction
detection, and hypothesis grouping specific to biomedical literature.

Usage:
    from epistemic_biomedical import analyze_biomedical_epistemic

    claims_layer = analyze_biomedical_epistemic(output_dir, graph_data)
"""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path


# ---------------------------------------------------------------------------
# Hedging / epistemic language patterns
# ---------------------------------------------------------------------------

HEDGING_PATTERNS = [
    (re.compile(r"\b(suggests?|suggested)\b", re.I), "hypothesized"),
    (re.compile(r"\b(may|might|could)\s+(be|have|play|offer|reduce|provide|show)\b", re.I), "hypothesized"),
    (re.compile(r"\b(appears?\s+to|seem(?:s|ed)?\s+to)\b", re.I), "hypothesized"),
    (re.compile(r"\bpotential(?:ly)?\b", re.I), "hypothesized"),
    (re.compile(r"\b(hypothesiz|propos|postulat|conjectur)(ed|es|ing)\b", re.I), "hypothesized"),
    (re.compile(r"\b(preliminary|emerging|early)\s+(data|evidence|results|findings)\b", re.I), "speculative"),
    (re.compile(r"\b(remains?\s+(to be|unclear|unproven|unknown))\b", re.I), "speculative"),
    (re.compile(r"\b(is expected to|would be|may be prepared)\b", re.I), "prophetic"),
    (re.compile(r"\b(prophetic|theoretic(?:al)?|envisaged)\b", re.I), "prophetic"),
    (re.compile(r"\bno\s+(significant\s+)?association\b", re.I), "negative"),
    (re.compile(r"\b(was not|were not|did not|no\s+effect|not\s+observed)\b", re.I), "negative"),
    (re.compile(r"\b(failed to|absence of)\b", re.I), "negative"),
]

# Document type inference from document IDs
PATENT_PATTERN = re.compile(r"^patent", re.I)
PREPRINT_PATTERN = re.compile(r"(biorxiv|medrxiv|arxiv)", re.I)
PUBMED_PATTERN = re.compile(r"^pmid_", re.I)
# FIDL-07 D-05: structural-biology doctype signals.
# Kept in sync with core/label_epistemic.py by convention (not shared import).
PDB_PATTERN = re.compile(r"^pdb[_-]", re.I)
STRUCTURAL_CONTENT_RE = re.compile(r"\b\d+(?:\.\d+)?\s*(?:Å|angstrom)\b", re.I)


def infer_doc_type(doc_id: str) -> str:
    """Infer document type from document ID naming conventions."""
    # FIDL-07 D-05: PDB prefix check runs FIRST (explicit-is-better).
    if PDB_PATTERN.match(doc_id):
        return "structural"
    if PATENT_PATTERN.match(doc_id):
        return "patent"
    if PREPRINT_PATTERN.search(doc_id):
        return "preprint"
    if PUBMED_PATTERN.match(doc_id):
        return "paper"
    return "unknown"


def classify_epistemic_status(evidence: str, confidence: float, doc_type: str) -> str:
    """Classify a single mention's epistemic status from evidence text + metadata."""
    if not evidence:
        return "asserted" if confidence >= 0.8 else "unclassified"

    # FIDL-07 D-06: structural (crystallography/cryo-EM) papers are evidence-grade;
    # high-confidence claims beat hedging-regex false positives like
    # "hypothesized structure". Short-circuit BEFORE the hedging scan.
    if doc_type == "structural" and confidence >= 0.9:
        return "asserted"

    # Check hedging patterns (order matters -- first match wins)
    for pattern, status in HEDGING_PATTERNS:
        if pattern.search(evidence):
            return status

    # Patent-sourced claims below high confidence are prophetic
    if doc_type == "patent" and confidence < 0.9:
        return "prophetic"

    # High-confidence with no hedging = asserted (brute fact)
    if confidence >= 0.8:
        return "asserted"

    # Low confidence without matching hedging patterns
    if confidence < 0.5:
        return "speculative"

    return "asserted"


def _detect_structural_content(evidence: str) -> bool:
    """Detect structural-biology content signals in first 800 chars of evidence.

    FIDL-07 D-05: Signals are "crystal structure", "x-ray crystallograph",
    "cryo-em", "electron microscop", plus a resolution regex matching
    `N Å` / `N.N angstrom` etc. The helper is exposed for rule authors
    who want to short-circuit doctype classification when the document
    ID prefix is generic (e.g., a PMID paper whose body is a crystal-
    structure report). Not called in the main dispatch path — rule
    authors opt in by importing.

    Empty/None evidence returns False without raising. Scan is confined
    to the first 800 chars to bound cost on very long evidence strings.
    """
    if not evidence:
        return False
    snippet = evidence[:800].lower()
    keyword_signals = (
        "crystal structure",
        "x-ray crystallograph",
        "cryo-em",
        "electron microscop",
    )
    if any(kw in snippet for kw in keyword_signals):
        return True
    return bool(STRUCTURAL_CONTENT_RE.search(snippet))


# ---------------------------------------------------------------------------
# Contradiction detection
# ---------------------------------------------------------------------------


def detect_contradictions(links: list[dict]) -> list[dict]:
    """Find relations where mentions provide opposing evidence.

    Looks for:
    - Same relation with negative + positive evidence across mentions
    - Same entity pair with opposing relation directions
    """
    contradictions = []

    for link in links:
        mentions = link.get("mentions", [])
        if len(mentions) < 2:
            continue

        # Check for mixed positive/negative evidence within the same relation
        statuses = []
        for m in mentions:
            evidence = m.get("evidence", "")
            doc_type = infer_doc_type(m.get("source_document", ""))
            status = classify_epistemic_status(evidence, m.get("confidence", 0.5), doc_type)
            statuses.append((status, m))

        positive = [(s, m) for s, m in statuses if s not in ("negative",)]
        negative = [(s, m) for s, m in statuses if s == "negative"]

        if positive and negative:
            contradictions.append({
                "type": "evidence_direction",
                "relation_id": link.get("relation_id", ""),
                "source": link.get("source", ""),
                "target": link.get("target", ""),
                "relation_type": link.get("relation_type", ""),
                "positive_mentions": [
                    {"document": m.get("source_document"), "evidence": m.get("evidence"), "confidence": m.get("confidence")}
                    for _, m in positive
                ],
                "negative_mentions": [
                    {"document": m.get("source_document"), "evidence": m.get("evidence"), "confidence": m.get("confidence")}
                    for _, m in negative
                ],
            })

    # Check for opposing confidence divergence (same relation, large confidence gap)
    for link in links:
        mentions = link.get("mentions", [])
        if len(mentions) < 2:
            continue
        confidences = [m.get("confidence", 0.5) for m in mentions]
        if max(confidences) - min(confidences) > 0.3:
            # Already captured as contradiction above? Skip duplicates.
            rel_id = link.get("relation_id", "")
            if not any(c["relation_id"] == rel_id for c in contradictions):
                contradictions.append({
                    "type": "confidence_divergence",
                    "relation_id": rel_id,
                    "source": link.get("source", ""),
                    "target": link.get("target", ""),
                    "relation_type": link.get("relation_type", ""),
                    "confidence_range": [min(confidences), max(confidences)],
                    "mentions": [
                        {"document": m.get("source_document"), "evidence": m.get("evidence"), "confidence": m.get("confidence")}
                        for m in mentions
                    ],
                })

    return contradictions


# ---------------------------------------------------------------------------
# Claim grouping (hypothesis detection)
# ---------------------------------------------------------------------------


def group_hypotheses(links: list[dict], nodes: list[dict]) -> list[dict]:
    """Identify clusters of hedged relations that may form hypotheses.

    A hypothesis is a group of relations that:
    - Share source/target entities (connected subgraph)
    - Have epistemic_status in (hypothesized, speculative, prophetic)
    - Come from overlapping document sets
    """
    # Build entity -> epistemic links index
    entity_links: dict[str, list[dict]] = defaultdict(list)
    for link in links:
        if link.get("epistemic_status") in ("hypothesized", "speculative", "prophetic"):
            entity_links[link["source"]].append(link)
            entity_links[link["target"]].append(link)

    # BFS to find connected components of epistemic links
    visited_links: set[str] = set()
    hypotheses = []

    for link in links:
        lid = link.get("relation_id", "")
        if lid in visited_links:
            continue
        if link.get("epistemic_status") not in ("hypothesized", "speculative", "prophetic"):
            continue

        # BFS from this link
        cluster = []
        queue = [link]
        visited_entities: set[str] = set()

        while queue:
            current = queue.pop(0)
            clid = current.get("relation_id", "")
            if clid in visited_links:
                continue
            visited_links.add(clid)
            cluster.append(current)

            for entity_id in (current["source"], current["target"]):
                if entity_id in visited_entities:
                    continue
                visited_entities.add(entity_id)
                for neighbor_link in entity_links.get(entity_id, []):
                    nlid = neighbor_link.get("relation_id", "")
                    if nlid not in visited_links:
                        queue.append(neighbor_link)

        if len(cluster) >= 2:
            # Determine hypothesis label from member entities
            member_entities: set[str] = set()
            docs: set[str] = set()
            for c in cluster:
                member_entities.add(c["source"])
                member_entities.add(c["target"])
                for m in c.get("mentions", []):
                    docs.add(m.get("source_document", ""))
                if c.get("source_document"):
                    docs.add(c["source_document"])

            # Build label from node names
            node_lookup = {n["id"]: n for n in nodes}
            entity_names = []
            for eid in sorted(member_entities):
                node = node_lookup.get(eid)
                if node:
                    entity_names.append(node.get("name", eid))

            # Use the highest-confidence relation's evidence as the summary
            cluster_sorted = sorted(cluster, key=lambda x: x.get("confidence", 0), reverse=True)
            summary_evidence = cluster_sorted[0].get("evidence", "")

            hypotheses.append({
                "id": f"hypothesis:{len(hypotheses) + 1}",
                "label": " — ".join(entity_names[:4]),
                "status": "proposed",
                "member_relations": [c.get("relation_id") for c in cluster],
                "member_entities": sorted(member_entities),
                "support_documents": sorted(docs - {""}),
                "evidence_summary": summary_evidence,
                "relation_count": len(cluster),
                "entity_count": len(member_entities),
            })

    return hypotheses


# ---------------------------------------------------------------------------
# Document-type epistemic profile
# ---------------------------------------------------------------------------


def build_doc_type_profile(links: list[dict]) -> dict:
    """Summarize epistemic signatures by document type."""
    profile: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for link in links:
        for mention in link.get("mentions", []):
            doc_type = infer_doc_type(mention.get("source_document", ""))
            evidence = mention.get("evidence", "")
            status = classify_epistemic_status(evidence, mention.get("confidence", 0.5), doc_type)
            profile[doc_type][status] += 1

    return {dt: dict(counts) for dt, counts in profile.items()}


# ---------------------------------------------------------------------------
# Main biomedical epistemic analysis
# ---------------------------------------------------------------------------


def analyze_biomedical_epistemic(output_dir: Path, graph_data: dict) -> dict:
    """Run full biomedical epistemic analysis on a built graph.

    Args:
        output_dir: Directory containing graph_data.json (used for metadata).
        graph_data: Parsed graph_data.json dict with nodes and links.

    Returns:
        Claims layer dict with metadata, summary, base_domain, super_domain.
    """
    graph_path = output_dir / "graph_data.json"
    nodes = graph_data.get("nodes", [])
    links = graph_data.get("links", [])

    # Step 1: Classify each link's epistemic status
    status_counts: dict[str, int] = defaultdict(int)
    for link in links:
        mentions = link.get("mentions", [])
        if not mentions:
            # Single-mention link -- use top-level fields
            doc_type = infer_doc_type(link.get("source_document", ""))
            status = classify_epistemic_status(
                link.get("evidence", ""),
                link.get("confidence", 0.5),
                doc_type,
            )
        else:
            # Multi-mention: classify each, take the most "epistemic" status
            # Priority: negative > prophetic > speculative > hypothesized > asserted
            priority = {"negative": 5, "prophetic": 4, "speculative": 3, "hypothesized": 2, "asserted": 1, "unclassified": 0}
            mention_statuses = []
            for m in mentions:
                doc_type = infer_doc_type(m.get("source_document", ""))
                ms = classify_epistemic_status(m.get("evidence", ""), m.get("confidence", 0.5), doc_type)
                mention_statuses.append(ms)

            # If ANY mention is epistemic, the link is epistemic
            # (a relation that's hypothesized in one paper and asserted in another is contested)
            if len(set(mention_statuses)) > 1 and "asserted" in mention_statuses:
                status = "contested"
            else:
                status = max(mention_statuses, key=lambda s: priority.get(s, 0))

        link["epistemic_status"] = status
        status_counts[status] += 1

    # Step 2: Detect contradictions
    contradictions = detect_contradictions(links)

    # Step 3: Group hypotheses
    hypotheses = group_hypotheses(links, nodes)

    # Step 4: Document-type profile
    doc_profile = build_doc_type_profile(links)

    # Step 5: Build claims layer
    claims_layer = {
        "metadata": {
            "description": "Super Domain epistemic layer — complements Louvain community structure",
            "reference": "Eric Little, 'Reasoning with Knowledge Graphs — Super Domains', https://www.linkedin.com/posts/eric-little-71b2a0b_pleased-to-announce-that-i-will-be-speaking-activity-7442581339096313856-wEFc",
            "generated_from": str(graph_path),
            "total_relations": len(links),
        },
        "summary": {
            "epistemic_status_counts": dict(status_counts),
            "contradictions_found": len(contradictions),
            "hypotheses_found": len(hypotheses),
            "document_types": doc_profile,
        },
        "base_domain": {
            "description": "Brute facts — asserted with high confidence, no hedging",
            "relation_count": status_counts.get("asserted", 0),
        },
        "super_domain": {
            "description": "Epistemic facts — hypothesized, speculative, prophetic, negative, or contested",
            "relation_count": sum(v for k, v in status_counts.items() if k != "asserted"),
            "hypotheses": hypotheses,
            "contradictions": contradictions,
        },
    }

    return claims_layer
