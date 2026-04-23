#!/usr/bin/env python3
"""Domain-aware epistemic analysis dispatcher for epistract knowledge graphs.

Routes epistemic analysis to the appropriate domain-specific module based on
the domain metadata in graph_data.json. Biomedical graphs use hedging patterns,
document-type inference, and hypothesis grouping. Contract graphs use
cross-reference conflict detection (when available).

Complements (does not replace) the Louvain community structure. Communities
group by topology; this groups by epistemology.

Usage:
    python label_epistemic.py <output_dir> [--domain contract] [--master-doc path]

Output:
    <output_dir>/claims_layer.json  -- Super Domain overlay
    Updates graph_data.json links with epistemic_status field

Reference:
    Eric Little, "Reasoning with Knowledge Graphs -- Super Domains"
    https://www.linkedin.com/posts/eric-little-71b2a0b_pleased-to-announce-that-i-will-be-speaking-activity-7442581339096313856-wEFc
"""

import importlib.util
import inspect
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import yaml


# ---------------------------------------------------------------------------
# Dynamic domain epistemic module loader
# ---------------------------------------------------------------------------


def _load_domain_epistemic(domain_name: str):
    """Load the epistemic analysis function for a domain.

    Domain epistemic modules live at domains/<name>/epistemic.py.
    Uses domain_resolver aliases for known domains, falls back to
    using domain_name directly as directory name for wizard-generated domains.
    Returns the loaded module or None if not found.
    """
    domains_dir = Path(__file__).parent.parent / "domains"

    # Try domain_resolver aliases first (handles "contract" -> "contracts", etc.)
    from core.domain_resolver import DOMAIN_ALIASES

    resolved_name = DOMAIN_ALIASES.get(domain_name, domain_name)
    module_path = domains_dir / resolved_name / "epistemic.py"

    if not module_path.exists():
        # Fall back to using domain name directly as directory
        module_path = domains_dir / domain_name / "epistemic.py"

    if not module_path.exists():
        return None

    spec = importlib.util.spec_from_file_location(
        f"domains.{module_path.parent.name}.epistemic", module_path
    )
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


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
# Kept in sync with domains/drug-discovery/epistemic.py by convention
# (not shared import). Any drift between the two copies is caught by UT-049.
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

    # Check hedging patterns (order matters — first match wins)
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
    `N Å` / `N.N angstrom` etc. Mirrored from
    domains/drug-discovery/epistemic.py by convention (two-site sync, D-05).
    Exposed for rule authors; not called in the dispatch path.
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
    # Build entity → epistemic links index
    entity_links = defaultdict(list)
    for link in links:
        if link.get("epistemic_status") in ("hypothesized", "speculative", "prophetic"):
            entity_links[link["source"]].append(link)
            entity_links[link["target"]].append(link)

    # BFS to find connected components of epistemic links
    visited_links = set()
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
        visited_entities = set()

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
            member_entities = set()
            docs = set()
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
    profile = defaultdict(lambda: defaultdict(int))

    for link in links:
        for mention in link.get("mentions", []):
            doc_type = infer_doc_type(mention.get("source_document", ""))
            evidence = mention.get("evidence", "")
            status = classify_epistemic_status(evidence, mention.get("confidence", 0.5), doc_type)
            profile[doc_type][status] += 1

    return {dt: dict(counts) for dt, counts in profile.items()}


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------


def _builtin_biomedical_epistemic(output_dir: Path, graph_data: dict) -> dict:
    """Built-in biomedical epistemic analysis using hedging patterns."""
    links = graph_data.get("links", [])
    nodes = graph_data.get("nodes", [])

    # Step 1: Classify each link
    for link in links:
        mentions = link.get("mentions", [])
        if mentions:
            doc_type = infer_doc_type(mentions[0].get("source_document", ""))
            evidence = mentions[0].get("evidence", link.get("evidence", ""))
        else:
            doc_type = "unknown"
            evidence = link.get("evidence", "")
        confidence = link.get("confidence", 0.5)
        link["epistemic_status"] = classify_epistemic_status(evidence, confidence, doc_type)

    # Step 2: Detect contradictions
    contradictions = detect_contradictions(links)

    # Step 3: Group hypotheses
    hypotheses = group_hypotheses(links, nodes)

    # Step 4: Build document type profile
    doc_profile = build_doc_type_profile(links)

    # Step 5: Build summary
    status_counts = defaultdict(int)
    for link in links:
        status_counts[link.get("epistemic_status", "unclassified")] += 1

    return {
        "metadata": {
            "domain": "drug-discovery",
            "analysis_type": "biomedical_epistemic",
        },
        "summary": {
            "total_relations": len(links),
            "epistemic_status_counts": dict(status_counts),
            "contradictions_found": len(contradictions),
            "hypotheses_found": len(hypotheses),
            "document_types": doc_profile,
        },
        "base_domain": {
            "asserted_relations": [
                l for l in links if l.get("epistemic_status") == "asserted"
            ],
        },
        "super_domain": {
            "contradictions": contradictions,
            "hypotheses": hypotheses,
            "contested_claims": [
                l for l in links if l.get("epistemic_status") in ("hypothesized", "speculative")
            ],
        },
    }


def _load_domain_persona(domain_name: str | None) -> str | None:
    """Load persona from domains/<name>/workbench/template.yaml. Returns None if absent.

    The persona is used two ways:
      1. Workbench chat system prompt (reactive — reads same YAML directly).
      2. Automatic narrator in this module (below).
    Single source of truth across both surfaces.
    """
    if not domain_name:
        return None
    # Mirror _load_domain_epistemic alias handling
    try:
        from core.domain_resolver import DOMAIN_ALIASES
        resolved = DOMAIN_ALIASES.get(domain_name, domain_name)
    except ImportError:
        resolved = domain_name

    domains_dir = Path(__file__).parent.parent / "domains"
    candidates = [
        domains_dir / resolved / "workbench" / "template.yaml",
        domains_dir / domain_name / "workbench" / "template.yaml",
    ]
    for path in candidates:
        if path.exists():
            try:
                data = yaml.safe_load(path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    persona = data.get("persona")
                    if isinstance(persona, str) and persona.strip():
                        return persona.strip()
            except Exception as e:  # noqa: BLE001
                print(
                    f"Warning: could not parse persona from {path}: {e}",
                    file=sys.stderr,
                )
    return None


def _summarize_graph_for_narrator(graph_data: dict, claims_layer: dict) -> str:
    """Compact structured summary of graph + claims for the narrator prompt."""
    nodes = graph_data.get("nodes", [])
    links = graph_data.get("links", graph_data.get("edges", []))

    by_type: dict[str, int] = defaultdict(int)
    for n in nodes:
        by_type[n.get("entity_type") or "UNKNOWN"] += 1

    status_counts = claims_layer.get("summary", {}).get("epistemic_status_counts", {})
    super_domain = claims_layer.get("super_domain", {})
    contradictions = super_domain.get("contradictions", []) or []
    hypotheses = super_domain.get("hypotheses", []) or []
    contested = super_domain.get("contested_claims", []) or []
    custom = super_domain.get("custom_findings", {}) or {}

    prophetic = [
        l for l in links if l.get("epistemic_status") == "prophetic"
    ]

    parts: list[str] = []
    parts.append("## GRAPH SUMMARY")
    parts.append(f"- Entities: {len(nodes)} across {len(by_type)} types")
    parts.append(f"- Relations: {len(links)}")
    parts.append("- Entity type distribution (top 10):")
    for k, v in sorted(by_type.items(), key=lambda kv: -kv[1])[:10]:
        parts.append(f"  - {k}: {v}")

    if status_counts:
        parts.append("")
        parts.append("## EPISTEMIC STATUS COUNTS")
        for k, v in sorted(status_counts.items(), key=lambda kv: -kv[1]):
            parts.append(f"- {k}: {v}")

    if contradictions:
        parts.append("")
        parts.append(f"## CONTRADICTIONS ({len(contradictions)} total; first 5 shown)")
        for c in contradictions[:5]:
            parts.append(f"- {json.dumps(c, default=str)[:400]}")

    if hypotheses:
        parts.append("")
        parts.append(f"## HYPOTHESIS GROUPS ({len(hypotheses)} total; first 5 shown)")
        for h in hypotheses[:5]:
            label = h.get("label") or h.get("title") or "(unlabeled)"
            members = h.get("members") or h.get("evidence") or []
            parts.append(
                f"- **{label}** ({len(members) if hasattr(members, '__len__') else '?'} members)"
            )

    if prophetic:
        parts.append("")
        parts.append(
            f"## PROPHETIC CLAIMS ({len(prophetic)} total; first 15 shown)"
        )
        for p in prophetic[:15]:
            src = p.get("source_entity") or p.get("source") or "?"
            tgt = p.get("target_entity") or p.get("target") or "?"
            rt = p.get("relation_type") or p.get("label") or "?"
            docs = p.get("source_documents") or []
            ev = (p.get("evidence") or "")[:180]
            doc_tail = f" docs={docs[:2]}" if docs else ""
            parts.append(f"- `{src}` --[{rt}]--> `{tgt}`{doc_tail}\n  evidence: \"{ev}\"")

    if contested:
        parts.append("")
        parts.append(
            f"## CONTESTED CLAIMS ({len(contested)} total; first 10 shown)"
        )
        for c in contested[:10]:
            src = c.get("source_entity") or c.get("source") or "?"
            tgt = c.get("target_entity") or c.get("target") or "?"
            rt = c.get("relation_type") or c.get("label") or "?"
            status = c.get("epistemic_status", "?")
            parts.append(f"- `{src}` --[{rt}]--> `{tgt}` status=`{status}`")

    if custom:
        parts.append("")
        parts.append(f"## CUSTOM RULE FINDINGS ({len(custom)} rules fired)")
        for rule_name, findings in custom.items():
            count = len(findings) if hasattr(findings, "__len__") else "?"
            parts.append(f"- {rule_name}: {count} findings")

    return "\n".join(parts)


_NARRATOR_USER_PROMPT = (
    "Produce a structured analyst briefing based on the knowledge graph and "
    "epistemic findings summarized in your system prompt.\n\n"
    "Structure (use markdown headings exactly in this order):\n\n"
    "# Epistemic Briefing\n\n"
    "## Executive Summary\n"
    "3-5 bullet points capturing the most decision-relevant findings.\n\n"
    "## Prophetic Claim Landscape\n"
    "Which assertions in the corpus are forward-looking (patent language, "
    "'is expected to', 'may be prepared by') rather than empirically "
    "established? Group by patent family / compound class / topic where "
    "possible. Call out the gap between prophetic language and asserted "
    "evidence.\n\n"
    "## Contested Claims & Contradictions\n"
    "Relations where different sources disagree or where opposing evidence "
    "exists. Name source IDs on both sides. If none exist, state so "
    "briefly and move on.\n\n"
    "## Coverage Gaps\n"
    "What is the graph silent on that a domain analyst would expect? "
    "Missing trial phases, absent companion diagnostics, no head-to-head "
    "comparisons, unattributed claims — name specifically.\n\n"
    "## Recommended Follow-Ups\n"
    "Specific next actions — documents to pull, relations to manually "
    "review, assumptions to verify.\n\n"
    "Rules:\n"
    "- Do NOT repeat the raw counts from the summary; synthesize instead.\n"
    "- Cite source document IDs inline in backticks when making claims.\n"
    "- Use the epistemic-status vocabulary from your system prompt: "
    "asserted, prophetic, hypothesized, contested, contradictions.\n"
    "- Keep total under ~1500 words.\n"
    "- Return only the markdown briefing, no preamble."
)


def narrate_claims_layer(
    graph_data: dict,
    claims_layer: dict,
    persona: str,
) -> str:
    """Generate the narrative briefing via LLM. Returns markdown string.

    Raises core.llm_client.LLMConfigError when no credentials are set, and
    core.llm_client.LLMCallError when the API call itself fails. Callers
    should catch both and fall back to rule-only output.
    """
    from core.llm_client import call_llm

    context = _summarize_graph_for_narrator(graph_data, claims_layer)
    system_prompt = f"{persona}\n\n---\n\n{context}"
    narrative = call_llm(
        system=system_prompt,
        user=_NARRATOR_USER_PROMPT,
        max_tokens=4096,
        temperature=0.3,
    )
    return narrative


def analyze_epistemic(
    output_dir: Path,
    domain_name: str | None = None,
    master_doc_path: Path | None = None,
    narrate: bool = True,
) -> dict:
    """Run full epistemic analysis on a built graph.

    Dispatches to the appropriate domain-specific analysis module based on
    graph metadata or explicit domain_name parameter. Optionally runs the
    LLM narrator afterward to produce an analyst briefing.

    Args:
        output_dir: Directory containing graph_data.json.
        domain_name: Explicit domain override. If None, detected from
            graph_data.json metadata.domain field (defaults to "drug-discovery").
        master_doc_path: Optional path to master reference document (e.g.,
            Sample_Conference_Master.md) for coverage gap analysis in contract domain.
        narrate: When True (default), calls the domain persona + LLM to
            produce epistemic_narrative.md alongside claims_layer.json.
            Set False to skip the LLM call entirely (offline runs,
            no credentials available).

    Returns:
        Claims layer dict with metadata, summary, base_domain, super_domain.
    """
    graph_path = output_dir / "graph_data.json"
    if not graph_path.exists():
        print(
            f"Error: {graph_path} not found. Run /epistract-build first.",
            file=sys.stderr,
        )
        sys.exit(1)

    graph_data = json.loads(graph_path.read_text())

    # Detect domain from graph metadata if not explicitly provided
    if domain_name is None:
        domain_name = graph_data.get("metadata", {}).get("domain", "drug-discovery")

    # Dispatch to domain-specific analysis module via dynamic loading
    effective_domain = domain_name or "drug-discovery"
    domain_mod = _load_domain_epistemic(effective_domain)

    # Convention-based dispatch: look for analyze_<slug>_epistemic()
    slug = effective_domain.replace("-", "_")
    func_name = f"analyze_{slug}_epistemic"

    if domain_mod is not None and hasattr(domain_mod, func_name):
        func = getattr(domain_mod, func_name)
        # Check if function accepts master_doc_path
        sig = inspect.signature(func)
        if "master_doc_path" in sig.parameters and master_doc_path is not None:
            claims_layer = func(output_dir, graph_data, master_doc_path=master_doc_path)
        else:
            claims_layer = func(output_dir, graph_data)
    elif domain_mod is not None and hasattr(domain_mod, "analyze_epistemic"):
        # Generic fallback: domain provides analyze_epistemic() without slug
        claims_layer = domain_mod.analyze_epistemic(output_dir, graph_data)
    else:
        # Final fallback: built-in biomedical analysis
        claims_layer = _builtin_biomedical_epistemic(output_dir, graph_data)

    # FIDL-07 (D-01, D-02, D-09): iterate CUSTOM_RULES after domain dispatch.
    # Each rule is called with (nodes, links, context); findings merge into
    # claims_layer.super_domain.custom_findings keyed by rule.__name__.
    # Per-rule try/except isolates failures — one bad rule cannot abort the
    # phase. Absent CUSTOM_RULES attribute → empty list → no custom_findings
    # key added (D-07 backward-compat: V2 baseline JSON is byte-identical
    # when no domain has adopted the hook).
    if domain_mod is not None:
        custom_rules = getattr(domain_mod, "CUSTOM_RULES", [])
        if custom_rules:
            nodes = graph_data.get("nodes", [])
            links = graph_data.get("links", [])
            context = {
                "output_dir": output_dir,
                "graph_data": graph_data,
                "domain_name": effective_domain,
            }
            super_domain = claims_layer.setdefault("super_domain", {})
            custom_findings = super_domain.setdefault("custom_findings", {})
            for rule in custom_rules:
                rule_name = getattr(rule, "__name__", "<anonymous>")
                try:
                    findings = rule(nodes, links, context)
                    if not isinstance(findings, list):
                        findings = []
                    custom_findings[rule_name] = findings
                except Exception as e:  # noqa: BLE001 — rule isolation is the whole point
                    custom_findings[rule_name] = [
                        {
                            "rule_name": rule_name,
                            "status": "error",
                            "error": str(e),
                        }
                    ]
                    print(
                        f"Warning: CUSTOM_RULE {rule_name!r} failed: {e}",
                        file=sys.stderr,
                    )

    # Write claims layer
    claims_path = output_dir / "claims_layer.json"
    claims_path.write_text(json.dumps(claims_layer, indent=2))

    # Update graph_data.json with epistemic_status on links
    graph_path.write_text(json.dumps(graph_data, indent=2))

    # Optional: LLM narrator using the domain persona. Non-blocking — any
    # failure leaves claims_layer.json on disk as the authoritative rule
    # output; the narrative is additive.
    narrative_path = output_dir / "epistemic_narrative.md"
    narrative_status = "skipped"
    if narrate:
        persona = _load_domain_persona(effective_domain)
        if persona is None:
            narrative_status = "no-persona"
            print(
                f"Note: no persona in domains/{effective_domain}/workbench/"
                f"template.yaml — skipping narrator. Add a persona field to "
                f"enable automatic briefings.",
                file=sys.stderr,
            )
        else:
            try:
                narrative = narrate_claims_layer(graph_data, claims_layer, persona)
                narrative_path.write_text(narrative, encoding="utf-8")
                narrative_status = "ok"
            except Exception as e:  # noqa: BLE001 — narrator is additive, failure is non-fatal
                # core.llm_client raises LLMConfigError / LLMCallError; also
                # catch generic to prevent any narrator bug from blocking
                # claims_layer.json writes.
                narrative_status = f"error: {type(e).__name__}"
                print(
                    f"Note: narrator skipped ({type(e).__name__}: {e}). "
                    f"claims_layer.json is authoritative.",
                    file=sys.stderr,
                )
    else:
        narrative_status = "disabled"

    # Print summary
    summary = claims_layer.get("summary", {})
    status_counts = summary.get("epistemic_status_counts", {})
    links = graph_data.get("links", [])
    print(
        json.dumps(
            {
                "claims_layer": str(claims_path),
                "narrative": (
                    str(narrative_path) if narrative_status == "ok" else None
                ),
                "narrative_status": narrative_status,
                "domain": domain_name,
                "total_relations": len(links),
                "base_domain_relations": status_counts.get("asserted", 0),
                "super_domain_relations": sum(
                    v for k, v in status_counts.items() if k != "asserted"
                ),
                "status_breakdown": status_counts,
                "contradictions": summary.get("contradictions_found", 0),
                "hypotheses": summary.get("hypotheses_found", 0),
                "document_types": list(summary.get("document_types", {}).keys()),
            },
            indent=2,
        )
    )

    return claims_layer


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Usage: python label_epistemic.py <output_dir> [--domain <name>] "
            "[--master-doc <path>] [--no-narrate]",
            file=sys.stderr,
        )
        sys.exit(1)

    out_dir = Path(sys.argv[1])
    domain = None
    if "--domain" in sys.argv:
        idx = sys.argv.index("--domain")
        if idx + 1 < len(sys.argv):
            domain = sys.argv[idx + 1]

    master_doc = None
    if "--master-doc" in sys.argv:
        idx = sys.argv.index("--master-doc")
        if idx + 1 < len(sys.argv):
            master_doc = Path(sys.argv[idx + 1])

    narrate_flag = "--no-narrate" not in sys.argv

    analyze_epistemic(
        out_dir,
        domain_name=domain,
        master_doc_path=master_doc,
        narrate=narrate_flag,
    )
