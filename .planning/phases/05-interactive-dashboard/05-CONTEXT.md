# Phase 5: Interactive Dashboard - Context

**Gathered:** 2026-03-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Build the **Sample Contract Analysis Workbench** — a FastAPI-powered web application that serves as a KG-driven contract analysis tool. The workbench provides a chat-first interface backed by Claude Sonnet, with an interactive knowledge graph browser and source document viewer as supporting panels. Users ask natural language questions about 62+ vendor contracts and receive cross-document answers with inline citations, cost estimations, todo/don't lists, and conflict analysis.

This phase also expands the contract domain schema to include organizational (committees, people) and program (events, stages, rooms) entity types extracted from the Master planning document, enriching the KG as a prerequisite for the workbench.

**Two-fold purpose:**
1. Epistract framework demonstration — proves cross-domain KG extraction works on a real problem
2. Practical event management tool — usable for actual Sample 2026 planning (Sep 4-6, 2026)

</domain>

<decisions>
## Implementation Decisions

### Technology Stack
- **D-01:** FastAPI backend + vanilla HTML/JS frontend. Python API server proxies Claude API calls, serves the HTML app, serves source documents and KG data. No additional web framework dependencies beyond FastAPI.
- **D-02:** Single-page web application served by FastAPI. Not a static HTML file — the chat interface requires a live backend for Claude API calls.
- **D-03:** Claude Sonnet as the chat LLM model. Balances speed, cost, and reasoning quality for a personal analysis tool with frequent queries.
- **D-04:** ANTHROPIC_API_KEY provided via environment variable. Matches existing codebase convention for LLM access.

### Application Architecture
- **D-05:** Chat-first layout with collapsible side panels (Graph, Sources). Chat is the main column; side panels expand on click. Graph and source viewer are supporting views, not primary.
- **D-06:** Separate extract-then-serve workflow. Run epistract extraction pipeline first (produces graph_data.json, claims_layer.json, etc.), then launch workbench server pointing at the output directory. Two distinct commands.
- **D-07:** Personal tool, localhost only. No authentication, no multi-user support, no sharing infrastructure needed.
- **D-08:** Session-only chat history. No persistence between server restarts. No database required.

### Chat Interface
- **D-09:** Full KG + relevant doc chunks as context for every chat question. System prompt includes complete graph_data.json (entities, relations, communities), claims_layer.json (risks, conflicts, gaps), and per-query matched source text chunks for cross-document reasoning.
- **D-10:** Starter prompts on first load (4-6 suggested questions), then free-form input. Suggested questions showcase capabilities: risks, deadlines, union labor, cost estimation, checklist generation.
- **D-11:** Rich markdown responses with tables for cost breakdowns, bullet lists for todos/don'ts, and inline citations [Contract Name section-ref] that link to the source panel. Structured enough to scan, detailed enough to act on.
- **D-12:** Chat-based what-if reasoning. Users can ask hypothetical questions ("What if we add a show on Stage B?") and the SME reasons about costs/conflicts without modifying the KG.

### SME Persona
- **D-13:** Senior contract analyst persona with functional title ("Sample Contract Analyst" or similar). No personal name. Authoritative but advisory tone — gives direct advice with contract citations, always flags when extrapolating beyond contract text.
- **D-14:** Honest boundary + redirect for out-of-scope questions. Deflects legal/insurance/compliance questions to appropriate professionals, but pivots to what the contracts DO say about the topic.
- **D-15:** Cost estimation capability. The SME calculates cost estimates from extracted contract data (hourly rates, equipment costs, labor minimums), showing the math with source references. Flags variables like Labor Day premium rates.

### Graph Panel
- **D-16:** Interactive vis.js network graph with search bar + entity type toggle buttons + severity filter. Click any node to see attributes and connected nodes. "Ask about this" button bridges graph exploration to chat.
- **D-17:** Double-click to recenter on a node's neighborhood. Node details show type, source documents, community, and connected entities with relation types.

### Source Document Viewer
- **D-18:** Extracted text display (from Phase 2 ingested/*.txt files) with section highlighting when navigated from chat citations. "Open original PDF" link for full document access. No embedded PDF rendering.
- **D-19:** Inline citation links in chat answers open the Sources panel scrolled to the referenced section. Esc returns to chat.

### Domain Schema Expansion
- **D-20:** Add new entity types to domain.yaml: COMMITTEE, PERSON, EVENT/PROGRAM, STAGE, ROOM. Add new relation types: CHAIRED_BY, CO_CHAIRED_BY, RESPONSIBLE_FOR, MANAGES_VOLUNTEERS, HOSTED_AT, REQUIRES, SCHEDULED.
- **D-21:** Programs/events are KG nodes linked to contracts. Events have physical requirements (AV, catering, security) that map to contract obligations. Enables questions like "What does this show cost?" and "Which contracts cover this event?"
- **D-22:** Committees and people are KG nodes. Committees have chairs/co-chairs and responsibility areas linked to vendor contracts. Enables "Which committee owns the Aramark relationship?" and "Can volunteers handle this task?"
- **D-23:** Schema expansion as first plan in Phase 5. Extract org/program data from Master doc as reference layer nodes (non-authoritative, like Phase 4's PLANNING_ITEM pattern). Existing 62 contract extractions preserved as-is — no re-extraction needed.

### Volunteer/Labor Analysis
- **D-24:** SME reasoning from KG + contract text for volunteer-vs-union-labor questions. No hardcoded rules — Claude interprets PCC union jurisdiction clauses (5 trade unions) in context of specific tasks. The KG provides the structured contract data; Claude provides the nuanced interpretation.

### Visual Design
- **D-25:** Clean & professional visual design. Dark sidebar (#1a1a2e navy), light main area (#ffffff), severity-coded colors (red for critical, amber for warning, blue for info). System sans-serif typography, monospace for data. GitHub-like clean layout with subtle shadows. No animations or flashy effects.

### Testing
- **D-26:** Synthetic fixtures for automated tests (sample graph_data.json, claims_layer.json, ingested text files). Mock Claude API responses for chat tests. Manual integration testing against real corpus (not committed).

### Scope Boundary
- **D-27:** v1 essential features: Chat with SME persona + Claude API, Graph panel with search/filter, Source document viewer.
- **D-28:** Deferred to v1.1: Dedicated Risk panel (severity-grouped findings from claims_layer.json with "Ask about this" bridge). Risk data accessible via chat in v1.

### Claude's Discretion
- Starter prompt question selection (which 4-6 questions best showcase capabilities)
- Graph layout algorithm and physics settings for vis.js
- Source panel search/navigation UX details
- System prompt engineering for the SME persona (wording, examples, boundary handling)
- FastAPI project structure (single file vs. modular)
- Exact API endpoint design beyond the core routes
- HTML/CSS implementation details within the visual direction specified

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Contract Domain Schema (expand this)
- `skills/contract-extraction/domain.yaml` — Contract domain schema. Needs new entity types (COMMITTEE, PERSON, EVENT, STAGE, ROOM) and relation types (CHAIRED_BY, RESPONSIBLE_FOR, HOSTED_AT, REQUIRES, SCHEDULED, MANAGES_VOLUNTEERS).
- `skills/contract-extraction/SKILL.md` — Contract extraction prompt. May need Master doc extraction guidance.
- `skills/contract-extraction/references/entity-types.md` — Entity type reference. Must be expanded with new types.
- `skills/contract-extraction/references/relation-types.md` — Relation type reference. Must be expanded with new relations.

### Graph Data (consumed by workbench)
- `scripts/run_sift.py` — sift-kg wrapper. Produces graph_data.json that workbench reads.
- `scripts/label_epistemic.py` — Produces claims_layer.json that workbench reads.
- `scripts/label_communities.py` — Produces communities.json that workbench reads.
- `scripts/extract_contracts.py` — End-to-end orchestrator. Workbench serves artifacts this pipeline produces.

### Existing Visualization (reference pattern)
- `lib/vis-9.1.2/vis-network.min.js` — vis.js already bundled. Reuse for graph panel.
- `scripts/run_sift.py:cmd_view()` — Existing pyvis viewer pattern. Reference for how graph HTML is generated.

### Document Ingestion (source text)
- `scripts/ingest_documents.py` — Produces ingested/*.txt files that the source viewer displays.

### Coverage Gap Baseline (org/program data source)
- External: `Sample_Conference_Master.md` from `akka-2026-dashboard` project — Master planning document. Source for committee structures, program schedules, event details. Extract as reference layer nodes.

### Prior Phase Context
- `.planning/phases/04-cross-reference-analysis/04-CONTEXT.md` — D-08 (Master doc as reference layer), D-09 (contracts override), D-10 (severity categories CRITICAL/WARNING/INFO), D-11 (suggested actions)
- `.planning/phases/03-entity-extraction-and-graph-construction/03-CONTEXT.md` — D-07 (cross-refs as attributes), D-14 (structured typed attributes)

### Requirements
- `.planning/REQUIREMENTS.md` — DASH-01, DASH-02 define Phase 5 acceptance criteria. Note: scope has expanded beyond original requirements to include chat interface and org/program layer.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `lib/vis-9.1.2/vis-network.min.js` — vis.js network visualization library already bundled. Reuse directly in the graph panel.
- `scripts/run_sift.py:cmd_view()` — Existing HTML graph viewer using pyvis + vis.js. Reference for graph rendering approach.
- `scripts/extract_contracts.py` — End-to-end extraction orchestrator. Workbench reads its output artifacts.
- `scripts/ingest_documents.py` — Produces ingested/*.txt files. Source panel displays these.
- `scripts/label_epistemic.py` — Produces claims_layer.json. Chat context includes this for risk/conflict awareness.
- Pydantic models throughout codebase — natural fit for FastAPI request/response models.

### Established Patterns
- CLI scripts with `sys.argv`, pathlib, Rich progress — workbench server script follows same entry point pattern
- JSON data files (graph_data.json, claims_layer.json, communities.json) as interchange format — workbench reads these
- Domain-aware dispatch via `domain_resolver.py` — may be relevant for future multi-domain workbench support
- Reference layer nodes with `source=reference, confidence=0.5` — pattern for Master doc org/program nodes

### Integration Points
- `output/<project>/graph_data.json` — Knowledge graph data consumed by workbench API
- `output/<project>/claims_layer.json` — Risk/conflict findings consumed by workbench API
- `output/<project>/communities.json` — Community assignments consumed by workbench API
- `output/<project>/ingested/*.txt` — Source document text served by workbench source viewer
- `ANTHROPIC_API_KEY` env var — Used by chat backend for Claude Sonnet calls

</code_context>

<specifics>
## Specific Ideas

- **The workbench IS the Scenario 7 deliverable** — it demonstrates epistract's cross-domain capability by solving a real event management problem, not just showing a graph.
- **The chat SME should feel like talking to a real contract analyst** who has read every document and can cross-reference them instantly. Cost estimation with math shown, do's/don'ts with citations, conflict detection with source references.
- **Programs contain entertainment shows across several stages**, forums across ballrooms, dining events — each with specific AV, infrastructure, catering, and staffing needs that intersect multiple contracts.
- **Committee structure is essential** — 14 committees (Food, Programs, Infrastructure, Registration, Sponsorship, Vendor Management, etc.), each chaired/co-chaired, staffed by 350-450 volunteers. The KG must support questions about which committees own which contract relationships and where volunteers can/can't be used.
- **PCC union labor jurisdiction** (5 trade unions: electrical, rigging, plumbing, carpentry, freight) is a key constraint that affects volunteer assignments and cost estimations.
- **This is a confidential feature branch** — real contract data never committed. Synthetic fixtures for tests, manual integration testing against real corpus.

</specifics>

<deferred>
## Deferred Ideas

- **Dedicated Risk Panel (v1.1)** — Severity-grouped CRITICAL/WARNING/INFO findings with suggested actions and "Ask about this" bridge to chat. Risk data accessible via chat questions in v1.
- **Telegram chat interface (v2)** — Query the contract KG via Telegram bot. Already in REQUIREMENTS.md as TELE-01 through TELE-04.
- **Persistent what-if scenarios** — Save hypothetical event changes as KG overlays, compare scenarios side-by-side. v1 uses chat-based what-if reasoning only.
- **Multi-user access / sharing** — Authentication, shared server deployment for committee chairs. v1 is localhost personal tool.
- **Persistent chat history** — Save conversations to local JSON for cross-session continuity.
- **Committee-oriented dashboard views (PRES-01)** — Filter entire workbench by committee responsibility area. In v2 requirements.
- **Source provenance drill-down (PRES-02, PRES-03)** — Navigate from graph nodes to original contract text with page/section reference. Partially delivered via source panel in v1.

</deferred>

---

*Phase: 05-interactive-dashboard*
*Context gathered: 2026-03-31*
