"""System prompt construction for the Epistract Workbench."""
from __future__ import annotations

import json
import sys

from examples.workbench.data_loader import WorkbenchData

# Default persona used when template has no persona field
_DEFAULT_PERSONA = (
    "You are a knowledge graph analyst. "
    "Answer questions using the graph data provided."
)

# FIDL-06 D-06: Guard — emit the "missing analysis_patterns" warning at most
# once per process so chat logs don't spam on every chat turn.
_warned_about_missing_analysis_patterns: bool = False


def _warn_missing_analysis_patterns() -> None:
    """Emit a one-shot warning when a template lacks analysis_patterns (FIDL-06 D-06)."""
    global _warned_about_missing_analysis_patterns
    if _warned_about_missing_analysis_patterns:
        return
    _warned_about_missing_analysis_patterns = True
    print(
        "Warning: workbench template has no analysis_patterns block; "
        "chat will use contracts-default vocabulary ('CROSS-CONTRACT REFERENCES'). "
        "Add analysis_patterns to domains/<name>/workbench/template.yaml to "
        "customize cross-reference wording for your domain.",
        file=sys.stderr,
    )


def build_system_prompt(data: WorkbenchData, template: dict) -> str:
    """Assemble the full system prompt with KG context.

    Per D-09: Include full KG summary + claims layer for every query.
    Per research pitfall 1: If graph is very large, use summarized format.
    """
    parts = [template.get("persona", _DEFAULT_PERSONA)]

    # --- KG Summary ---
    nodes = data.graph_data.get("nodes", [])
    edges = data.graph_data.get("edges", [])

    # Group nodes by type
    by_type: dict[str, list[dict]] = {}
    for n in nodes:
        t = n.get("entity_type", "UNKNOWN")
        by_type.setdefault(t, []).append(n)

    parts.append("## KNOWLEDGE GRAPH SUMMARY")
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
            # FIDL-06 D-06: domain-specific heading from template.analysis_patterns.
            # Missing template block → fall back to hardcoded contracts wording
            # (matches pre-Phase-17 behavior) with a one-time visible warning.
            patterns = template.get("analysis_patterns")
            if patterns:
                heading = patterns.get(
                    "cross_references_heading", "CROSS-CONTRACT REFERENCES"
                )
                appears_in_phrase = patterns.get("appears_in_phrase", "appears in")
            else:
                heading = "CROSS-CONTRACT REFERENCES"
                appears_in_phrase = "appears in"
                _warn_missing_analysis_patterns()
            parts.append(f"### {heading} ({len(xrefs)} entities)")
            for x in xrefs:
                entity = x.get("entity", "")
                appears = x.get("appears_in", [])
                parts.append(
                    f"- {entity} {appears_in_phrase}: {', '.join(appears)}"
                )
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
