# Project Research Summary

**Project:** Epistract Scenario 7 -- Cross-Domain Contract KG Extension
**Domain:** Contract analysis knowledge graph extraction (event planning contracts)
**Researched:** 2026-03-29
**Confidence:** HIGH

## Executive Summary

Epistract Scenario 7 extends the existing biomedical KG extraction pipeline to analyze 62 event-planning contracts (PDF, XLS, EML) for a 2026 conference. The core insight from research is that the existing architecture is well-suited for this extension -- the pipeline already supports domain-configurable extraction via `domain.yaml` and `SKILL.md`. The primary work is not building new infrastructure but carefully abstracting the hardcoded biomedical assumptions distributed across 5+ scripts, then adding a contract-specific domain config, a web dashboard (Streamlit), and optionally a Telegram query bot.

The recommended approach is to treat this as a domain-configuration problem, not a rewrite. Only 3 new dependencies are needed (pymupdf4llm, streamlit, python-telegram-bot). The extraction pipeline, graph construction (sift-kg), and visualization (pyvis) all carry over unchanged. The killer differentiator is cross-contract conflict detection -- surfacing contradictions between vendors that a spreadsheet cannot reveal. This justifies the KG approach over simpler alternatives.

The top risks are: (1) hardcoded biomedical assumptions silently corrupting contract outputs if not systematically audited, (2) PDF extraction failures on large/scanned contracts destroying downstream quality, (3) entity resolution failure across 62 documents creating a fragmented, unusable graph, and (4) chunking strategies that sever cross-clause references critical to contract analysis. All four are preventable with upfront triage and careful Phase 1 design.

## Key Findings

### Recommended Stack

The stack strategy is "extend, don't replace." Eight existing dependencies (Kreuzberg, Pydantic, NetworkX, pyvis, LiteLLM, PyYAML, sift-kg, Rich) carry over unchanged. Only three new packages are required, plus two optional ones.

**Core technologies:**
- **Kreuzberg + pymupdf4llm**: Document parsing -- Kreuzberg handles format detection and non-PDF files; pymupdf4llm produces LLM-optimized Markdown from PDFs preserving clause structure
- **Streamlit + Plotly**: Interactive web dashboard -- best Python dashboard framework for filterable tables, drill-down, and chart views for committee chairs
- **python-telegram-bot**: Chat query interface -- simpler than aiogram, adequate for ~10 users, integrates with existing MCP Telegram plugin
- **NetworkX (existing)**: Graph store -- 62 contracts produce ~500-2000 nodes, no database server needed
- **sift-kg (existing)**: Graph construction -- already accepts arbitrary domain.yaml; no patches needed

**Critical decision: No graph database.** Neo4j/ArangoDB are overkill at this scale. Revisit only if graph exceeds 10K nodes.

### Expected Features

**Must have (table stakes):**
- Multi-format document ingestion (PDF, XLS, EML)
- Entity extraction: parties, obligations, deadlines, costs, clauses
- Cross-contract entity resolution ("Aramark" = "ARAMARK" = "the Caterer")
- Knowledge graph construction with deduplication
- Graph visualization with drill-down to source contract text
- Obligation tracking per party
- Deadline and timeline extraction with date normalization
- Cost extraction and aggregation
- Basic search/query over the KG

**Should have (differentiators):**
- Cross-contract conflict detection (the killer feature)
- Coverage gap analysis (what is NOT covered)
- Timeline conflict visualization (Gantt-style)
- Risk scoring per contract
- Interactive web report with vendor/date/risk filters
- Financial dashboard (spend by vendor, budget comparison)

**Defer (v2+):**
- Telegram NL Q&A (requires stable KG first; high complexity GraphRAG integration)
- Coverage gap analysis (requires domain expertise codification)
- Clause comparison matrix (nice-to-have after core analysis works)
- Vendor dependency mapping (derive from extracted DEPENDS_ON relations later)

### Architecture Approach

Extend the existing three-layer pipeline (extraction, validation, graph construction) with two new concepts: a domain configuration layer that swaps ontologies via `skills/{domain}-extraction/` directories, and a presentation layer (web dashboard + Telegram) on top of the graph. Cross-reference analysis runs as a post-build overlay on the constructed graph, following the same pattern as the existing epistemic analysis (`claims_layer.json`).

**Major components:**
1. **Domain Config Layer** -- `domain.yaml` + `SKILL.md` per domain; resolver function routes to correct config
2. **Document Ingestion** -- Kreuzberg + pymupdf4llm; large PDF chunking at paragraph boundaries
3. **Extraction Layer** -- Claude agents with domain-aware prompts; 1 agent per document, up to 4 concurrent
4. **Contract Validation** -- Date/currency/party normalization (replaces biomedical RDKit/Biopython validators)
5. **Graph Construction** -- sift-kg build (unchanged); SemHash deduplication; community detection
6. **Cross-Reference Engine** -- Post-build analysis: obligation conflicts, timeline overlaps, coverage gaps
7. **Web Report Dashboard** -- Streamlit with filterable tables, embedded graph viz, drill-down
8. **Telegram Bot** -- NL query proxy to graph via Claude (optional, last phase)

### Critical Pitfalls

1. **Hardcoded biomedical assumptions** -- Domain logic is embedded in 5+ scripts (build_extraction.py, label_communities.py, scan_patterns.py, validators). Audit every shared script and make domain-conditional before any contract extraction. Phase 1 blocker.
2. **PDF extraction failure on large/scanned contracts** -- 12-31 MB PDFs may be scanned images or have complex layouts. Triage all 62 documents first (text-native vs. scanned vs. mixed). Use OCR fallback for scanned pages. Phase 2 blocker.
3. **Entity resolution without canonical IDs** -- Unlike biomedical entities (SMILES, InChIKeys), contract parties lack universal IDs. Build a seed registry from Sample_Conference_Master.md, instruct LLM to normalize, then run fuzzy matching post-extraction.
4. **Chunking destroys cross-clause references** -- Contracts cross-reference internally ("Subject to Section 12.4..."). Pass full documents to LLM where possible (most are <50 pages); prepend Definitions section to every chunk for larger ones.
5. **Backward compatibility breakage** -- Refactoring shared code for domain configs can break Scenarios 1-6. Snapshot all biomedical outputs as regression baselines before any changes.

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Domain Configuration and Pipeline Abstraction
**Rationale:** Everything downstream depends on the domain schema. Also must audit and abstract hardcoded biomedical assumptions before any contract data flows through the pipeline.
**Delivers:** `skills/contract-extraction/domain.yaml`, `SKILL.md`, domain resolver utility, `--domain` flag on pipeline commands, regression baselines for Scenarios 1-6.
**Addresses:** KG construction foundation, entity/relation type definitions
**Avoids:** Pitfall 1 (hardcoded biomedical assumptions), Pitfall 5 (over-engineering -- keep it simple, two concrete configs), Pitfall 8 (backward compatibility -- baselines first)

### Phase 2: Document Ingestion and Extraction
**Rationale:** Need parsed documents before graph analysis. Large PDF handling is the primary technical risk.
**Delivers:** Parsed text from all 62 documents, extraction JSON per contract, contract validation scripts (date/currency/party normalization).
**Uses:** Kreuzberg, pymupdf4llm, Claude extraction agents
**Addresses:** Multi-format ingestion, entity extraction, deadline extraction, cost extraction
**Avoids:** Pitfall 2 (PDF failures -- triage first), Pitfall 4 (chunking -- full-doc where possible), Pitfall 10 (prompt drift -- version prompts)

### Phase 3: Graph Construction and Entity Resolution
**Rationale:** Entity resolution is the bridge between raw extractions and useful graph analysis. Must deduplicate before any cross-reference work.
**Delivers:** Deduplicated KG with resolved entities, community detection, graph visualization.
**Uses:** sift-kg, NetworkX, pyvis, SemHash
**Addresses:** Cross-contract entity resolution, KG construction, graph visualization, contract drill-down
**Avoids:** Pitfall 3 (entity resolution -- seed registry + fuzzy matching), Pitfall 11 (master data as ground truth -- tag source provenance)

### Phase 4: Cross-Reference Analysis and Risk Detection
**Rationale:** The differentiating value layer. Requires a built and deduplicated graph.
**Delivers:** `cross_references.json` with conflicts, gaps, and risk scores. Obligation tracking, timeline conflict detection, coverage gap identification.
**Addresses:** Cross-contract conflict detection (killer feature), obligation tracking, risk scoring, coverage gap analysis
**Avoids:** Pitfall 6 (wrong epistemic model -- build contract-specific analysis, not reuse biomedical epistemic layer)

### Phase 5: Interactive Web Dashboard
**Rationale:** Presentation layer for committee chairs. Needs analysis results to display.
**Delivers:** Streamlit dashboard with filterable tables, embedded graph visualization, drill-down to source text, financial views.
**Uses:** Streamlit, Plotly, pyvis
**Addresses:** Interactive web report, financial dashboard, timeline visualization, basic search/query

### Phase 6: Telegram Chat Interface
**Rationale:** Optional enhancement. Everything works without it. Can develop in parallel with Phase 5 once graph exists.
**Delivers:** NL query bot for committee chairs on mobile.
**Uses:** python-telegram-bot, LiteLLM
**Addresses:** Natural language Q&A
**Avoids:** Pitfall 7 (query timeouts -- async pattern, pre-computed aggregations)

### Phase Ordering Rationale

- **Strict dependency chain:** Domain config -> Extraction -> Graph -> Analysis -> Presentation. Each phase produces artifacts consumed by the next.
- **Risk-first:** The two highest-risk phases (PDF extraction, entity resolution) are in Phases 2-3, where failures are caught before investing in downstream features.
- **Value delivery:** Phase 4 (cross-reference analysis) is the earliest phase that delivers unique value beyond what a spreadsheet provides. Phases 1-3 are infrastructure.
- **Parallel opportunity:** Phases 5 and 6 can run in parallel once Phase 4 completes. The Telegram bot and web dashboard both consume the same graph + analysis artifacts.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 2:** PDF extraction quality varies wildly across the 62 documents. Need a triage pass before committing to a chunking strategy. May need OCR integration research.
- **Phase 4:** Cross-contract conflict detection is the novel component with no existing epistract precedent. Research on rule-based vs. LLM-based conflict detection needed (Fenech & Pace paper provides a starting framework).
- **Phase 6:** Telegram bot deployment model (long-polling vs. webhook, hosting) needs research if standalone bot is chosen over MCP integration.

Phases with standard patterns (skip research-phase):
- **Phase 1:** Domain config is a YAML + directory pattern. Existing code provides the exact template.
- **Phase 3:** sift-kg graph construction is unchanged. Entity resolution via fuzzy matching is well-documented.
- **Phase 5:** Streamlit dashboards have extensive documentation and examples. Standard data dashboard patterns apply.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All recommended technologies verified on PyPI (March 2026). 8 of 11 already in stack. Only 3 new deps. |
| Features | HIGH | Multiple academic sources (GRAPH-GRPO-LEX, Neo4j GraphRAG) and industry tools (Icertis, Spellbook) confirm feature taxonomy. |
| Architecture | HIGH | Architecture is an extension of existing proven pipeline. Codebase inspection confirms feasibility of domain abstraction. |
| Pitfalls | HIGH | Pitfalls identified by direct codebase inspection (line-level references) and corroborated by academic literature on cross-domain KG challenges. |

**Overall confidence:** HIGH

### Gaps to Address

- **PDF quality across 62 documents:** Unknown how many are scanned vs. text-native. Must triage before Phase 2 planning.
- **Contract domain ontology completeness:** The entity/relation types in domain.yaml are based on academic literature, not the actual STA contracts. May need iteration after initial extraction reveals domain-specific patterns.
- **Cross-reference detection accuracy:** No benchmark exists for this specific task. Plan for iterative prompt refinement in Phase 4.
- **Streamlit vs. static HTML:** Architecture research suggests static HTML (Jinja2) while stack research recommends Streamlit. Recommendation: use Streamlit for interactive dashboard (committee chairs explore data), generate static HTML export for sharing. Resolve during Phase 5 planning.

## Sources

### Primary (HIGH confidence)
- Epistract codebase inspection -- `scripts/build_extraction.py`, `label_communities.py`, `scan_patterns.py`, `run_sift.py` (line-level analysis of hardcoded assumptions)
- [Kreuzberg PyPI](https://pypi.org/project/kreuzberg/) -- v4.6.3, 91+ format support
- [pymupdf4llm PyPI](https://pypi.org/project/pymupdf4llm/) -- v1.27.2.2
- [Streamlit PyPI](https://pypi.org/project/streamlit/) -- v1.55.0
- [python-telegram-bot PyPI](https://pypi.org/project/python-telegram-bot/) -- v22.7

### Secondary (MEDIUM confidence)
- [GRAPH-GRPO-LEX](https://arxiv.org/html/2511.06618) -- Contract graph entity modeling (CLAUSE, PARTY, DEFINED_TERM, VALUE)
- [Neo4j GraphRAG for Commercial Contracts](https://neo4j.com/blog/developer/graphrag-in-action/) -- Agreement, ContractClause, Organization node types
- [Automating construction contract review using KG-enhanced LLMs](https://www.sciencedirect.com/science/article/abs/pii/S0926580525002195) -- F1=0.85 for risk identification
- [Fenech & Pace: Automatic Conflict Detection](https://link.springer.com/chapter/10.1007/978-3-642-03466-4_13) -- Rule-based conflict detection across composite contracts
- [Frontiers: KG + LLM Fusion Challenges](https://www.frontiersin.org/journals/computer-science/articles/10.3389/fcomp.2025.1590632/full) -- 40% cross-domain performance degradation

### Tertiary (LOW confidence)
- [Explosion: From PDFs to AI-ready Structured Data](https://explosion.ai/blog/pdfs-nlp-structured-data) -- General PDF extraction guidance
- [Unstract: Contract OCR Guide](https://unstract.com/blog/contract-ocr-guide-to-extracting-data-from-contracts/) -- Scanned contract challenges

---
*Research completed: 2026-03-29*
*Ready for roadmap: yes*
