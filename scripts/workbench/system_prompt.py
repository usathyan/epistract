"""System prompt construction for the Sample Contract Analyst."""
from __future__ import annotations

import json

from scripts.workbench.data_loader import WorkbenchData

# ---------------------------------------------------------------------------
# Persona (D-13, D-14, D-15, D-24)
# ---------------------------------------------------------------------------

PERSONA_PROMPT = """You are the Sample Contract Analyst — a senior contract analysis specialist who has thoroughly reviewed all vendor contracts for the Sample 2026 event at the Pennsylvania Convention Center (September 4-6, 2026).

ROLE AND TONE:
- You are authoritative but advisory. Give direct, actionable advice backed by specific contract citations.
- Always cite the source contract when referencing specific terms, costs, or obligations. Use the format [Contract Name] (e.g., [PCC License Agreement], [Aramark Catering Agreement]).
- When you extrapolate beyond what contracts explicitly state, clearly flag it: "Based on the contract terms, I estimate..." or "The contracts don't explicitly address this, but..."
- For cost estimation (D-15): Show your math. Break down calculations with per-unit costs from contracts, quantities, and totals. Flag variables like Labor Day premium rates or headcount uncertainty.

BOUNDARIES (D-14):
- For legal, insurance, or compliance questions: Acknowledge the question, share what the contracts DO say about the topic, then redirect: "For a definitive legal opinion, consult your legal counsel."
- For questions outside the contract scope: Say what you can observe from the data, then note the limitation.

UNION LABOR (D-24):
- The Pennsylvania Convention Center has 5 trade unions: electrical (IBEW), rigging, plumbing, carpentry, and freight handling.
- When asked about volunteer tasks vs. union labor, interpret the PCC union jurisdiction clauses in context. Don't give blanket rules — analyze the specific task against contract language.

WHAT-IF REASONING (D-12):
- When users ask hypothetical questions ("What if we add a show on Stage B?"), reason about costs, conflicts, and logistics using the contract data. Don't modify the knowledge graph — just reason about implications.

RESPONSE FORMAT (D-11):
- Use markdown tables for cost breakdowns and comparisons.
- Use bullet lists for to-do items, don't-do items, and risk summaries.
- Use inline citations [Contract Name] that the frontend will make clickable.
- Be detailed enough to act on, but scannable with headers and structure."""


def build_system_prompt(data: WorkbenchData) -> str:
    """Assemble the full system prompt with KG context.

    Per D-09: Include full KG summary + claims layer for every query.
    Per research pitfall 1: If graph is very large, use summarized format.
    """
    parts = [PERSONA_PROMPT]

    # --- KG Summary ---
    nodes = data.graph_data.get("nodes", [])
    edges = data.graph_data.get("edges", [])

    # Group nodes by type
    by_type: dict[str, list[dict]] = {}
    for n in nodes:
        t = n.get("entity_type", "UNKNOWN")
        by_type.setdefault(t, []).append(n)

    parts.append("## CONTRACT KNOWLEDGE GRAPH SUMMARY")
    parts.append(f"Total entities: {len(nodes)} | Total relationships: {len(edges)}")
    parts.append("")

    for entity_type, type_nodes in sorted(by_type.items()):
        parts.append(f"### {entity_type} ({len(type_nodes)} entities)")
        for n in type_nodes:
            name = n.get("name", n.get("id", "unknown"))
            attrs = n.get("attributes", {})
            docs = n.get("source_documents", [])
            line = f"- **{name}**"
            if attrs:
                # Include key attributes inline
                attr_parts = []
                for k, v in list(attrs.items())[:4]:
                    if v:
                        attr_parts.append(f"{k}: {v}")
                if attr_parts:
                    line += f" ({', '.join(attr_parts)})"
            if docs:
                line += f" — from {', '.join(docs)}"
            parts.append(line)
        parts.append("")

    # --- Claims Layer (D-09) ---
    if data.claims_layer:
        parts.append("## ANALYSIS FINDINGS")

        conflicts = data.claims_layer.get("conflicts", [])
        if conflicts:
            parts.append(f"### CONFLICTS ({len(conflicts)} found)")
            for c in conflicts:
                severity = c.get("severity", "INFO")
                desc = c.get("description", "")
                parts.append(f"- [{severity}] {desc}")
            parts.append("")

        gaps = data.claims_layer.get("gaps", [])
        if gaps:
            parts.append(f"### COVERAGE GAPS ({len(gaps)} found)")
            for g in gaps:
                severity = g.get("severity", "INFO")
                desc = g.get("description", "")
                parts.append(f"- [{severity}] {desc}")
            parts.append("")

        risks = data.claims_layer.get("risks", [])
        if risks:
            parts.append(f"### RISKS ({len(risks)} found)")
            for r in risks:
                severity = r.get("severity", "INFO")
                desc = r.get("description", "")
                parts.append(f"- [{severity}] {desc}")
            parts.append("")

        xrefs = data.claims_layer.get("cross_references", [])
        if xrefs:
            parts.append(f"### CROSS-CONTRACT REFERENCES ({len(xrefs)} entities)")
            for x in xrefs:
                entity = x.get("entity", "")
                appears = x.get("appears_in", [])
                parts.append(f"- {entity} appears in: {', '.join(appears)}")
            parts.append("")

    # --- Communities ---
    if data.communities:
        communities = data.communities.get("communities", [])
        if communities:
            parts.append("## ENTITY COMMUNITIES")
            for comm in communities:
                label = comm.get("label", f"Community {comm.get('id', '?')}")
                members = comm.get("members", [])
                parts.append(f"- **{label}**: {len(members)} members")
            parts.append("")

    # --- Full node data as structured JSON (for precise lookups) ---
    # Estimate token count (~4 chars per token for JSON)
    node_json = json.dumps(nodes, indent=2)
    estimated_tokens = len(node_json) // 4

    if estimated_tokens < 50000:
        parts.append("## FULL ENTITY DATA (JSON)")
        parts.append("Use this for precise attribute lookups and cost calculations:")
        parts.append(f"```json\n{node_json}\n```")
    else:
        parts.append(
            f"## NOTE: Full entity data ({estimated_tokens} est. tokens) "
            "omitted for context efficiency. Use the summary above."
        )

    return "\n\n".join(parts)


def get_matched_source_chunks(
    data: WorkbenchData, question: str, max_chunks: int = 3
) -> str:
    """Find relevant source document chunks for the question.

    Simple keyword matching against ingested text files.
    Returns formatted text to append to user message context.
    """
    # Extract keywords from question (simple: words > 3 chars, not stopwords)
    stopwords = {
        "what", "which", "where", "when", "that", "this", "with", "from",
        "have", "does", "about", "there", "their", "they", "would", "could",
        "should", "these", "those", "been", "being", "were", "will", "than",
    }
    words = [w.lower().strip("?.!,;:") for w in question.split() if len(w) > 3]
    keywords = [w for w in words if w not in stopwords]

    if not keywords:
        return ""

    matches = []
    for doc in data.documents:
        text = data.get_document_text(doc["doc_id"])
        if not text:
            continue
        text_lower = text.lower()
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            matches.append((score, doc["doc_id"], text))

    matches.sort(key=lambda x: -x[0])

    if not matches:
        return ""

    parts = ["## RELEVANT SOURCE DOCUMENTS"]
    for score, doc_id, text in matches[:max_chunks]:
        # Include first 2000 chars of matching docs
        snippet = text[:2000]
        if len(text) > 2000:
            snippet += "\n... (truncated)"
        parts.append(f"### [{doc_id}]")
        parts.append(snippet)

    return "\n\n".join(parts)
