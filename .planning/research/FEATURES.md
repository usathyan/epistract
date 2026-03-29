# Feature Landscape

**Domain:** Cross-domain contract knowledge graph extraction and analysis (event planning contracts)
**Researched:** 2026-03-29

## Table Stakes

Features users expect from a contract analysis KG system. Missing any of these and the tool feels incomplete for event organizers managing 62+ vendor contracts.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Entity extraction from contracts** | Core capability -- parties, obligations, deadlines, costs, clauses must be machine-readable | High | LLM-based extraction with domain-configured prompts; GRAPH-GRPO-LEX and Neo4j GraphRAG both use CLAUSE, PARTY, OBLIGATION, VALUE node types |
| **Multi-format document ingestion** | Contracts arrive as PDF (60), XLS (1), EML (1) -- must handle all three | Medium | PDF is the hard one (12-31 MB files); use chunking strategy for large docs |
| **Cross-contract entity resolution** | "Aramark" in catering contract must link to "Aramark" in PCC venue contract | Medium | Fuzzy matching + canonical name resolution; critical for cross-reference queries |
| **Obligation tracking per party** | Users need "show me everything Aramark must do" across all contracts | Low | Query pattern over extracted OBLIGATES relations; straightforward once extraction works |
| **Deadline and timeline extraction** | Every contract has dates -- cancellation windows, payment schedules, setup times | Medium | Temporal parsing is tricky (relative dates like "90 days prior to event"); normalize to absolute dates anchored to Sep 4-6 2026 |
| **Cost extraction and aggregation** | Budget visibility: what does each vendor cost, what are the totals, where are overruns | Medium | Extract currency values + link to line items; must handle rate tables (per-hour, per-plate, per-room-night) |
| **Knowledge graph construction** | Extracted entities/relations stored as queryable graph | Medium | Existing epistract pipeline does this for biomedical; extend with contract domain schema |
| **Graph visualization** | Users need to see the contract network visually | Medium | Existing epistract has visualization; adapt for contract entity types and color coding |
| **Basic search/query** | "What are our cancellation policies?" must be answerable | Low | Keyword + entity-type filtering over the KG |
| **Contract-level drill-down** | Click a node/obligation and see the source contract text | Low | Store source provenance (contract name, page, clause) with every extracted entity |

## Differentiators

Features that set this apart from generic contract management tools. Not expected by default, but deliver outsized value for multi-vendor event planning.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Cross-contract conflict detection** | Surface contradictions automatically: vendor A says teardown at 6pm, venue says midnight cutoff but Labor Day double-time kicks in at 5pm | High | Requires semantic comparison of obligations across contracts; academic research (Fenech & Pace) shows rule-based + NLP hybrid works best; this is the killer feature |
| **Coverage gap analysis** | Identify what is NOT covered: "no contract addresses wheelchair accessibility for 5000 attendees" | High | Requires domain knowledge of what SHOULD exist; compare extracted obligations against a checklist derived from event requirements |
| **Timeline conflict visualization** | Gantt-style view showing overlapping vendor obligations, setup/teardown windows, and labor jurisdiction conflicts | Medium | Visual layer over extracted temporal data; particularly valuable for Labor Day weekend logistics at PCC |
| **Risk scoring per contract** | Aggregate risk indicators: missing insurance clauses, no force majeure, ambiguous cancellation terms | Medium | Pattern matching against expected clause types; flag deviations from standard contract playbooks |
| **Natural language Q&A (Telegram)** | "What happens if we cancel the Marriott block?" answered from the KG via chat | High | GraphRAG approach: embed contract chunks, retrieve via KG structure + semantic search, generate answer with LLM |
| **Vendor dependency mapping** | Show that AV setup depends on PCC freight elevator access which depends on union labor scheduling | Medium | Derive from extracted DEPENDS_ON relations + temporal sequencing |
| **Financial dashboard** | Total spend by vendor, category breakdown, budget vs. contracted amounts, payment schedule calendar | Medium | Aggregation queries over extracted cost entities; reference layer from Sample_Conference_Master.md for budget comparison |
| **Clause comparison across vendors** | Side-by-side: how do cancellation policies differ between Marriott, Sheraton, and Notary Hotel? | Medium | Group extracted clauses by type, present in comparison matrix |
| **Epistemic analysis for contracts** | Flag hedging language ("best efforts"), conditional obligations, ambiguous terms | Low | Existing epistract epistemic pipeline can be adapted -- it already detects hypotheses, contradictions, conditional claims |
| **Interactive web report with filters** | Committee chairs filter by vendor, obligation type, date range, risk level | Medium | Standard dashboard patterns; more valuable than static PDF report |

## Anti-Features

Features to explicitly NOT build. These would add complexity without matching the project's read-only analysis mission.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Contract editing / redlining** | Scope creep into contract management (CLM) territory; epistract is analysis, not authoring | Surface findings that humans act on; link to source contract for manual review |
| **Workflow / approval routing** | Requires user management, permissions, notifications -- a whole product category | Telegram bot for alerts is sufficient for this team size |
| **Template generation** | Creating new contracts from templates is a different product | Focus on understanding existing contracts |
| **Regulatory compliance checking** | Out of scope per PROJECT.md (future Scenario 8) | Flag as future domain config, not this milestone |
| **Real-time contract monitoring** | Batch extraction is sufficient; contracts don't change daily | Run extraction pipeline on-demand or scheduled |
| **E-signature integration** | Not relevant for analysis of already-signed contracts | N/A |
| **Vendor scoring / rating system** | Subjective; would require data beyond contract text | Show objective contract terms for manual comparison |
| **AI-generated contract summaries as authoritative** | LLM summaries can hallucinate; contracts are the source of truth | Always link summaries to source text; label as AI-generated |
| **Mobile app** | Telegram serves as mobile interface per PROJECT.md | Telegram bot + responsive web report |

## Feature Dependencies

```
Multi-format document ingestion
  -> Entity extraction from contracts
    -> Cross-contract entity resolution
      -> Knowledge graph construction
        -> Graph visualization
        -> Basic search/query
        -> Contract-level drill-down
        -> Obligation tracking per party
        -> Cross-contract conflict detection
        -> Coverage gap analysis
        -> Vendor dependency mapping
        -> Clause comparison across vendors

Deadline and timeline extraction (part of entity extraction)
  -> Timeline conflict visualization

Cost extraction (part of entity extraction)
  -> Financial dashboard

Knowledge graph construction
  -> Natural language Q&A (Telegram)
  -> Risk scoring per contract
  -> Epistemic analysis for contracts
  -> Interactive web report with filters
```

## MVP Recommendation

Prioritize in this order:

1. **Multi-format document ingestion** -- nothing works without parsing the 62 contract files
2. **Entity extraction** -- core value; parties, obligations, deadlines, costs, clauses
3. **Cross-contract entity resolution** -- "Aramark" must be one node, not sixty
4. **Knowledge graph construction** -- leverage existing epistract pipeline
5. **Graph visualization + drill-down** -- immediate visual value for committee chairs
6. **Cross-contract conflict detection** -- the killer differentiator that justifies a KG approach over a spreadsheet

Defer to later phases:
- **Telegram Q&A**: Requires stable KG first; GraphRAG integration is high complexity
- **Financial dashboard**: Valuable but secondary to obligation/risk analysis
- **Coverage gap analysis**: Requires domain expertise codification; do after basic extraction proves reliable
- **Timeline conflict visualization**: Nice-to-have Gantt view; basic timeline extraction comes first

## Sources

- [Automating construction contract review using KG-enhanced LLMs](https://www.sciencedirect.com/science/article/abs/pii/S0926580525002195) -- F1=0.85 for risk identification with GraphRAG
- [Contract Knowledge Graphs Overview](https://www.emergentmind.com/topics/contract-knowledge-graphs) -- Entity/relation taxonomy
- [GraphRAG for Commercial Contracts (Neo4j)](https://neo4j.com/blog/developer/graphrag-in-action/) -- Node types: Agreement, ContractClause, Organization, Country; Relationship types: HAS_CLAUSE, IS_PARTY_TO
- [GRAPH-GRPO-LEX Contract Graph Modeling](https://arxiv.org/html/2511.06618) -- CLAUSE, PARTY, DEFINED_TERM, VALUE node types
- [Automatic Conflict Detection on Contracts (Fenech & Pace)](https://link.springer.com/chapter/10.1007/978-3-642-03466-4_13) -- Rule-based conflict detection across composite contracts
- [Conflict detection in obligation with deadline policies](https://link.springer.com/article/10.1186/s13635-014-0013-5) -- Temporal conflict detection patterns
- [AI Contract Management (Spellbook)](https://www.spellbook.legal/learn/ai-contract-management) -- Industry feature expectations 2026
- [Contract Analytics (Icertis)](https://www.icertis.com/contracting-basics/contract-analytics-software/) -- Table stakes: obligation tracking, deadline alerts, risk flagging
- [Contract Management Dashboards (Concord)](https://www.concord.app/contract-management-dashboard-examples/) -- Dashboard KPIs and visualization patterns
- [AI-Powered Contract Clause Conflict Detection (Contractize)](https://blog.contractize.app/ai-powered-contract-clause-conflict-detection-and-automated-) -- Cross-contract conflict resolution metrics
