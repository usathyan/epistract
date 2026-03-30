#!/usr/bin/env python3
"""Contract epistemic analysis for cross-domain knowledge graph framework.

Performs cross-contract entity linking, conflict detection, coverage gap
analysis, and risk scoring. All findings are written as Super Domain overlays
in claims_layer.json, complementing the Louvain community structure.

Called by label_epistemic.py dispatcher when domain == "contract".

Usage (via dispatcher):
    python label_epistemic.py <output_dir> --domain contract

Entry point:
    analyze_contract_epistemic(output_dir, graph_data, master_doc_path=None) -> dict
"""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

import yaml


# ---------------------------------------------------------------------------
# Stopwords for fuzzy matching
# ---------------------------------------------------------------------------

_STOPWORDS = frozenset({
    "a", "an", "the", "and", "or", "of", "for", "to", "in", "on", "at",
    "by", "is", "be", "are", "was", "were", "with", "from", "as", "that",
    "this", "all", "per", "any", "each", "no", "not", "shall", "must",
    "will", "may", "can", "should",
})


def _significant_words(text: str) -> set[str]:
    """Extract significant lowercase words from text, removing stopwords."""
    words = set(re.findall(r"[a-z0-9]+", text.lower()))
    return words - _STOPWORDS


def _get_nested_attr(node: dict, dotted_path: str) -> str | None:
    """Resolve a dotted attribute path like 'attributes.clause_type' on a node dict."""
    parts = dotted_path.split(".")
    current = node
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    if current is None:
        return None
    return str(current).lower().strip() if current is not None else None


# ---------------------------------------------------------------------------
# XREF-01: Cross-contract entity linking
# ---------------------------------------------------------------------------


def find_cross_contract_entities(nodes: list[dict], links: list[dict] | None = None) -> list[dict]:
    """Identify entities appearing in multiple contracts.

    Entities are cross-contract if their source_documents list has 2+ entries,
    or if links referencing them come from 2+ different source_documents.

    Args:
        nodes: Graph nodes from graph_data.json.
        links: Graph links (optional) for additional provenance tracking.

    Returns:
        List of cross-contract entity dicts sorted by contract_count descending:
        [{"entity_id", "entity_name", "entity_type", "contracts", "contract_count"}]
    """
    entity_docs: dict[str, set[str]] = defaultdict(set)
    entity_info: dict[str, dict] = {}

    # Gather source_documents from nodes
    for node in nodes:
        nid = node.get("id", "")
        entity_info[nid] = {
            "entity_name": node.get("name", ""),
            "entity_type": node.get("entity_type", ""),
        }
        src_docs = node.get("source_documents", [])
        if isinstance(src_docs, list):
            for doc in src_docs:
                if doc:
                    entity_docs[nid].add(doc)
        # Also check single source_document field
        single_doc = node.get("source_document", "")
        if single_doc:
            entity_docs[nid].add(single_doc)

    # Gather additional provenance from links
    if links:
        for link in links:
            src_doc = link.get("source_document", "")
            if src_doc:
                for eid in (link.get("source", ""), link.get("target", "")):
                    if eid:
                        entity_docs[eid].add(src_doc)
            # Also check mentions
            for mention in link.get("mentions", []):
                m_doc = mention.get("source_document", "")
                if m_doc:
                    for eid in (link.get("source", ""), link.get("target", "")):
                        if eid:
                            entity_docs[eid].add(m_doc)

    # Filter to entities in 2+ contracts
    cross_contract = []
    for eid, docs in entity_docs.items():
        if len(docs) >= 2:
            info = entity_info.get(eid, {})
            cross_contract.append({
                "entity_id": eid,
                "entity_name": info.get("entity_name", eid),
                "entity_type": info.get("entity_type", ""),
                "contracts": sorted(docs),
                "contract_count": len(docs),
            })

    cross_contract.sort(key=lambda x: x["contract_count"], reverse=True)
    return cross_contract


# ---------------------------------------------------------------------------
# Conflict rules loader
# ---------------------------------------------------------------------------


def load_conflict_rules(domain_yaml_path: Path) -> dict:
    """Load conflict_rules section from a domain.yaml file.

    Args:
        domain_yaml_path: Path to domain.yaml file.

    Returns:
        Dict of conflict rules, or empty dict if no conflict_rules key exists.
    """
    try:
        data = yaml.safe_load(domain_yaml_path.read_text())
    except Exception:
        return {}
    if not isinstance(data, dict):
        return {}
    return data.get("conflict_rules", {})


# ---------------------------------------------------------------------------
# XREF-02: Conflict detection
# ---------------------------------------------------------------------------


def detect_conflicts(nodes: list[dict], links: list[dict], rules: dict) -> list[dict]:
    """Detect conflicts across contracts based on conflict rules.

    Four conflict types:
    - exclusive_use: Two contracts claiming exclusive use of same space
    - schedule_contradiction: Different dates for same deliverable
    - term_contradiction: Conflicting terms between obligations/clauses
    - cost_budget_mismatch: Cost discrepancies for similar services

    Args:
        nodes: Graph nodes from graph_data.json.
        links: Graph links from graph_data.json.
        rules: Conflict rules dict loaded from domain.yaml.

    Returns:
        List of conflict finding dicts with id, type, severity, description,
        entities_involved, contracts_involved, evidence, suggested_action, confidence.
    """
    if not rules:
        return []

    conflicts: list[dict] = []
    seq = 0

    # Build indexes
    nodes_by_type: dict[str, list[dict]] = defaultdict(list)
    nodes_by_id: dict[str, dict] = {}
    for node in nodes:
        nodes_by_type[node.get("entity_type", "")].append(node)
        nodes_by_id[node.get("id", "")] = node

    links_by_source: dict[str, list[dict]] = defaultdict(list)
    for link in links:
        links_by_source[link.get("source", "")].append(link)

    # Process each rule
    for rule_name, rule in rules.items():
        severity = rule.get("severity", "WARNING")
        template = rule.get("suggested_action_template", "Review conflict")

        if rule_name == "exclusive_use":
            conflicts.extend(
                _detect_exclusive_use(nodes_by_type, links_by_source, nodes_by_id, severity, template, seq)
            )
            seq += len([c for c in conflicts if c["type"] == "exclusive_use"])

        elif rule_name == "schedule_contradiction":
            new_conflicts = _detect_schedule_contradictions(nodes_by_type, severity, template, seq)
            conflicts.extend(new_conflicts)
            seq += len(new_conflicts)

        elif rule_name == "term_contradiction":
            new_conflicts = _detect_term_contradictions(nodes_by_type, severity, template, seq)
            conflicts.extend(new_conflicts)
            seq += len(new_conflicts)

        elif rule_name == "cost_budget_mismatch":
            new_conflicts = _detect_cost_mismatches(nodes_by_type, severity, template, seq)
            conflicts.extend(new_conflicts)
            seq += len(new_conflicts)

    return conflicts


def _detect_exclusive_use(
    nodes_by_type: dict,
    links_by_source: dict,
    nodes_by_id: dict,
    severity: str,
    template: str,
    seq: int,
) -> list[dict]:
    """Find exclusive-use conflicts: two clauses restricting the same venue space."""
    conflicts = []
    # Find CLAUSE nodes with clause_type == "exclusivity"
    exclusivity_clauses = [
        n for n in nodes_by_type.get("CLAUSE", [])
        if _get_nested_attr(n, "attributes.clause_type") == "exclusivity"
    ]

    # For each exclusivity clause, find what VENUE it restricts via RESTRICTS links
    clause_venues: list[tuple[dict, str, str]] = []  # (clause_node, venue_id, source_doc)
    for clause in exclusivity_clauses:
        clause_id = clause.get("id", "")
        src_doc = clause.get("source_document", "")
        # Also check source_documents
        src_docs = clause.get("source_documents", [])
        if src_doc:
            all_docs = [src_doc]
        elif src_docs:
            all_docs = src_docs
        else:
            all_docs = ["unknown"]

        for link in links_by_source.get(clause_id, []):
            if link.get("relation_type") == "RESTRICTS":
                target = link.get("target", "")
                target_node = nodes_by_id.get(target, {})
                if target_node.get("entity_type") == "VENUE":
                    link_doc = link.get("source_document", all_docs[0] if all_docs else "unknown")
                    clause_venues.append((clause, target, link_doc))

    # Group by venue and check for conflicts
    venue_clauses: dict[str, list[tuple[dict, str]]] = defaultdict(list)
    for clause, venue_id, doc in clause_venues:
        venue_clauses[venue_id].append((clause, doc))

    for venue_id, clause_list in venue_clauses.items():
        if len(clause_list) < 2:
            continue
        # Check if clauses come from different contracts
        docs = {doc for _, doc in clause_list}
        if len(docs) >= 2:
            venue_node = nodes_by_id.get(venue_id, {})
            space = venue_node.get("name", venue_id)
            seq += 1
            conflicts.append({
                "id": f"conflict:exclusive_use:{seq:03d}",
                "type": "exclusive_use",
                "severity": severity,
                "description": f"Multiple contracts claim exclusive use of {space}",
                "entities_involved": [c.get("id", "") for c, _ in clause_list] + [venue_id],
                "contracts_involved": sorted(docs),
                "evidence": {
                    f"source_{i}": {"contract": doc, "clause": c.get("name", "")}
                    for i, (c, doc) in enumerate(clause_list)
                },
                "suggested_action": template.format(
                    source=clause_list[0][0].get("name", ""),
                    conflict=clause_list[1][0].get("name", ""),
                    space=space,
                ),
                "confidence": 0.9,
            })

    return conflicts


def _detect_schedule_contradictions(
    nodes_by_type: dict,
    severity: str,
    template: str,
    seq: int,
) -> list[dict]:
    """Find schedule contradictions: different dates for same deliverable."""
    conflicts = []
    deadlines = nodes_by_type.get("DEADLINE", [])

    # Group deadlines by what_is_due (fuzzy: lowercase strip)
    by_deliverable: dict[str, list[dict]] = defaultdict(list)
    for dl in deadlines:
        what = _get_nested_attr(dl, "attributes.what_is_due")
        if what:
            by_deliverable[what].append(dl)

    for deliverable, dl_list in by_deliverable.items():
        if len(dl_list) < 2:
            continue
        # Compare dates across different contracts
        date_groups: dict[str, list[dict]] = defaultdict(list)
        for dl in dl_list:
            date_val = _get_nested_attr(dl, "attributes.date") or "unknown"
            date_groups[date_val].append(dl)

        if len(date_groups) >= 2:
            # Different dates for same deliverable
            all_entities = [dl.get("id", "") for dl in dl_list]
            all_contracts = set()
            for dl in dl_list:
                src = dl.get("source_document", "")
                if src:
                    all_contracts.add(src)
                for s in dl.get("source_documents", []):
                    if s:
                        all_contracts.add(s)

            seq += 1
            evidence = {}
            for date_val, dls in date_groups.items():
                for dl in dls:
                    evidence[dl.get("id", "")] = {
                        "date": date_val,
                        "contract": dl.get("source_document", ""),
                    }

            conflicts.append({
                "id": f"conflict:schedule_contradiction:{seq:03d}",
                "type": "schedule_contradiction",
                "severity": severity,
                "description": f"Conflicting dates for '{deliverable}': {', '.join(sorted(date_groups.keys()))}",
                "entities_involved": all_entities,
                "contracts_involved": sorted(all_contracts),
                "evidence": evidence,
                "suggested_action": template.format(
                    entity_a=dl_list[0].get("name", ""),
                    entity_b=dl_list[1].get("name", ""),
                    what_is_due=deliverable,
                ),
                "confidence": 0.85,
            })

    return conflicts


def _detect_term_contradictions(
    nodes_by_type: dict,
    severity: str,
    template: str,
    seq: int,
) -> list[dict]:
    """Find term contradictions: conflicting terms between obligations/clauses."""
    conflicts = []
    candidates = nodes_by_type.get("OBLIGATION", []) + nodes_by_type.get("CLAUSE", [])

    # Group by similar action/key_terms (keyword overlap)
    for i, node_a in enumerate(candidates):
        words_a = _significant_words(
            (_get_nested_attr(node_a, "attributes.action") or "")
            + " "
            + (_get_nested_attr(node_a, "attributes.key_terms") or "")
            + " "
            + (node_a.get("name", ""))
        )
        if not words_a:
            continue

        for node_b in candidates[i + 1:]:
            # Must be from different contracts
            doc_a = node_a.get("source_document", "") or (
                (node_a.get("source_documents", []) or [""])[0]
            )
            doc_b = node_b.get("source_document", "") or (
                (node_b.get("source_documents", []) or [""])[0]
            )
            if doc_a == doc_b and doc_a:
                continue

            words_b = _significant_words(
                (_get_nested_attr(node_b, "attributes.action") or "")
                + " "
                + (_get_nested_attr(node_b, "attributes.key_terms") or "")
                + " "
                + (node_b.get("name", ""))
            )
            if not words_b:
                continue

            overlap = words_a & words_b
            if len(overlap) >= 2:
                # Check for contradictory indicators
                text_a = (node_a.get("name", "") + " " + str(node_a.get("attributes", {}))).lower()
                text_b = (node_b.get("name", "") + " " + str(node_b.get("attributes", {}))).lower()

                contradiction_pairs = [
                    ("exclusive", "non-exclusive"),
                    ("restrict", "permit"),
                    ("prohibit", "allow"),
                    ("required", "optional"),
                ]

                is_contradiction = False
                for term_x, term_y in contradiction_pairs:
                    if (term_x in text_a and term_y in text_b) or (term_y in text_a and term_x in text_b):
                        is_contradiction = True
                        break

                if is_contradiction:
                    seq += 1
                    all_contracts = set()
                    if doc_a:
                        all_contracts.add(doc_a)
                    if doc_b:
                        all_contracts.add(doc_b)

                    conflicts.append({
                        "id": f"conflict:term_contradiction:{seq:03d}",
                        "type": "term_contradiction",
                        "severity": severity,
                        "description": f"Contradictory terms between '{node_a.get('name', '')}' and '{node_b.get('name', '')}'",
                        "entities_involved": [node_a.get("id", ""), node_b.get("id", "")],
                        "contracts_involved": sorted(all_contracts),
                        "evidence": {
                            "source_a": {"entity": node_a.get("name", ""), "contract": doc_a},
                            "source_b": {"entity": node_b.get("name", ""), "contract": doc_b},
                        },
                        "suggested_action": template.format(
                            entity_a=node_a.get("name", ""),
                            entity_b=node_b.get("name", ""),
                        ),
                        "confidence": 0.8,
                    })

    return conflicts


def _detect_cost_mismatches(
    nodes_by_type: dict,
    severity: str,
    template: str,
    seq: int,
) -> list[dict]:
    """Find cost/budget mismatches: different amounts for similar services."""
    conflicts = []
    costs = nodes_by_type.get("COST", [])

    # Group costs by what they cover (fuzzy match)
    for i, cost_a in enumerate(costs):
        covers_a = _get_nested_attr(cost_a, "attributes.covers") or cost_a.get("name", "")
        words_a = _significant_words(covers_a)
        if not words_a:
            continue

        for cost_b in costs[i + 1:]:
            # Must be from different contracts
            doc_a = cost_a.get("source_document", "") or (
                (cost_a.get("source_documents", []) or [""])[0]
            )
            doc_b = cost_b.get("source_document", "") or (
                (cost_b.get("source_documents", []) or [""])[0]
            )
            if doc_a == doc_b and doc_a:
                continue

            covers_b = _get_nested_attr(cost_b, "attributes.covers") or cost_b.get("name", "")
            words_b = _significant_words(covers_b)
            if not words_b:
                continue

            overlap = words_a & words_b
            if len(overlap) >= 2:
                amount_a = _get_nested_attr(cost_a, "attributes.amount")
                amount_b = _get_nested_attr(cost_b, "attributes.amount")

                if amount_a and amount_b and amount_a != amount_b:
                    seq += 1
                    all_contracts = set()
                    if doc_a:
                        all_contracts.add(doc_a)
                    if doc_b:
                        all_contracts.add(doc_b)

                    conflicts.append({
                        "id": f"conflict:cost_budget_mismatch:{seq:03d}",
                        "type": "cost_budget_mismatch",
                        "severity": severity,
                        "description": f"Cost mismatch for similar services: {amount_a} vs {amount_b}",
                        "entities_involved": [cost_a.get("id", ""), cost_b.get("id", "")],
                        "contracts_involved": sorted(all_contracts),
                        "evidence": {
                            "source_a": {"entity": cost_a.get("name", ""), "amount": amount_a, "contract": doc_a},
                            "source_b": {"entity": cost_b.get("name", ""), "amount": amount_b, "contract": doc_b},
                        },
                        "suggested_action": template.format(
                            cost_entity=cost_a.get("name", ""),
                            amount=f"{amount_a} vs {amount_b}",
                        ),
                        "confidence": 0.75,
                    })

    return conflicts
