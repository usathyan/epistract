# Phase 5: Interactive Dashboard - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md -- this log preserves the alternatives considered.

**Date:** 2026-03-31
**Phase:** 05-interactive-dashboard
**Areas discussed:** Technology approach, Dashboard layout & views, Filtering & interaction, Data freshness & generation, Program metadata model, SME persona design, Deployment & sharing, Testing strategy, Domain schema expansion, Chat response format, Workbench branding & visual design, Scope boundary for v1

---

## Technology Approach

| Option | Description | Selected |
|--------|-------------|----------|
| Static HTML + vanilla JS | Generate self-contained HTML file, zero dependencies, matches existing viewer | |
| Streamlit app | Python-native dashboard, requires local server, ~200MB dep | |
| Flask/FastAPI + HTML templates | Traditional web app, full control, server required | |

**User's choice:** Initially selected Static HTML + vanilla JS, then revised when chat interface requirements emerged. Final: FastAPI + vanilla HTML/JS.
**Notes:** User clarified the vision is a chat-driven contract analysis workbench, not a static dashboard. Chat requires a live LLM backend, making static HTML insufficient.

### Follow-up: Packaging
| Option | Description | Selected |
|--------|-------------|----------|
| Single HTML file | Everything inlined, shareable | (superseded) |
| Small folder | Separate CSS/JS files | |

**Notes:** Single file was selected but became moot when architecture shifted to FastAPI server.

### Follow-up: Chat Engine
**User's clarification:** The workbench needs to be a KG-powered SME that can reason across 62 contracts, answer cross-document questions, estimate costs, generate todo/don't lists. This is the core value -- not filterable tables.

---

## Dashboard Layout & Views

### Reframing
**User's input:** Envisioned chat interface + source browsing + graph visualization. Not traditional dashboard tables. The tool should demonstrate epistract's effectiveness in solving real event management problems.

### Primary Interface
| Option | Description | Selected |
|--------|-------------|----------|
| Chat-first with side panels | Chat main column, graph/sources as collapsible panels | ✓ |
| Graph-first with chat overlay | Interactive KG fills screen, chat as floating panel | |
| Tabbed equal views | Three equal tabs: Chat, Graph, Sources | |

**User's choice:** Chat-first with side panels

### Source Linking
| Option | Description | Selected |
|--------|-------------|----------|
| Inline links that open side panel | Chat citations clickable, open sources panel | ✓ |
| New tab/window for full doc | References open in new browser tab | |
| Split view: chat + source side by side | Clicking reference splits screen | |

### Chat Context Strategy
| Option | Description | Selected |
|--------|-------------|----------|
| Full KG + relevant doc chunks | Complete graph data + matched source chunks | ✓ |
| Targeted subgraph per question | Only relevant KG portion per query | |
| You decide | Claude's discretion | |

### Graph Interaction
| Option | Description | Selected |
|--------|-------------|----------|
| Click node -> details + neighbors | Click shows attributes, connections, "Ask about this" | ✓ |
| Hover tooltip, click to filter chat | Hover for quick info, click pre-fills chat | |
| You decide | Claude's discretion | |

### SME Persona Name
| Option | Description | Selected |
|--------|-------------|----------|
| I'll pick the name | User chooses | |
| Claude picks during implementation | Defer to implementation | |
| No name, just 'Contract Analyst' | Functional title only | ✓ |

### Source Document Display
| Option | Description | Selected |
|--------|-------------|----------|
| Extracted text with section highlighting | Show ingested/*.txt with highlighted sections | ✓ |
| Embedded PDF viewer | Render actual PDFs in iframe | |
| Text preview + link to open original | Short excerpt + open full file button | |

### Risk Panel
| Option | Description | Selected |
|--------|-------------|----------|
| Grouped by severity with actions | CRITICAL/WARNING/INFO collapsible sections | ✓ (deferred to v1.1) |
| Timeline view | Risks plotted on timeline | |
| You decide | Claude's discretion | |

---

## Filtering & Interaction

### Graph Filtering
| Option | Description | Selected |
|--------|-------------|----------|
| Search bar + entity type toggles | Text search + type toggle buttons + severity filter | ✓ |
| Full filter panel | Dropdowns, date range, category selector | |
| You decide | Claude's discretion | |

### Chat Interaction Model
| Option | Description | Selected |
|--------|-------------|----------|
| Starter prompts + free-form | 4-6 suggested questions on first load, then free-form | ✓ |
| Free-form only | Just text input, persona greeting sets expectations | |
| Command palette style | Slash commands + free-form | |

---

## Data Freshness & Generation

### Pipeline Coupling
| Option | Description | Selected |
|--------|-------------|----------|
| Separate steps: extract then serve | Two distinct commands, clean separation | ✓ |
| All-in-one: extract + serve | Single command for both | |
| You decide | Claude's discretion | |

### Chat Persistence
| Option | Description | Selected |
|--------|-------------|----------|
| Session-only | Browser memory, refresh starts fresh | ✓ |
| Persist to local JSON | Save/reload across restarts | |
| You decide | Claude's discretion | |

### LLM Model
| Option | Description | Selected |
|--------|-------------|----------|
| Claude Sonnet | Fast, good reasoning, lower cost | ✓ |
| Claude Opus | Most capable, slower, more expensive | |
| Configurable at startup | CLI flag to choose | |

---

## Program Metadata Model

**User's clarification:** Programs are entertainment shows, forums, dining events across stages and ballrooms. Each requires AV, infrastructure, catering, security. 14 committees manage these with chairs/co-chairs and 350-450 volunteers. The KG should support questions about contract compliance, volunteer assignments, and cost estimation per event.

### Program Representation
| Option | Description | Selected |
|--------|-------------|----------|
| KG nodes linked to contracts | EVENT/PROGRAM as entity types with HOSTED_AT, REQUIRES, etc. | ✓ |
| Reference context only | Programs in system prompt, not graph-native | |
| You decide | Claude's discretion | |

### Cost Estimation
| Option | Description | Selected |
|--------|-------------|----------|
| Estimate from contract data | SME calculates using extracted rates, shows math | ✓ |
| Point to sections, no calculation | Identify relevant sections, user does math | |
| You decide | Claude's discretion | |

### What-If Scenarios
| Option | Description | Selected |
|--------|-------------|----------|
| Chat-based what-if only | SME reasons about hypotheticals, no KG modification | ✓ |
| Persistent scenario builder | Save overlays, compare side-by-side | |
| Defer to future version | Skip what-if entirely | |

### Volunteer/Labor Analysis
| Option | Description | Selected |
|--------|-------------|----------|
| SME reasoning from KG + contract text | Claude interprets union jurisdiction clauses in context | ✓ |
| Automated rule engine | Codify union rules in domain.yaml | |

---

## SME Persona Design

### Expertise Level
| Option | Description | Selected |
|--------|-------------|----------|
| Senior contract analyst | Authoritative, direct advice with caveats and citations | ✓ |
| Helpful assistant (cautious) | Tentative, reference-oriented | |
| You decide | Claude's discretion | |

### Out-of-Scope Handling
| Option | Description | Selected |
|--------|-------------|----------|
| Honest boundary + redirect | Deflect to professionals, pivot to contract data | ✓ |
| Strict: only from KG data | If not in contracts, stop | |
| You decide | Claude's discretion | |

---

## Deployment & Sharing

### Target Users
| Option | Description | Selected |
|--------|-------------|----------|
| Just you (personal tool) | Localhost only, no auth needed | ✓ |
| You + a few committee chairs | Shared access, API key management | |
| All committee members | Broad access, authentication needed | |

### API Key
| Option | Description | Selected |
|--------|-------------|----------|
| ANTHROPIC_API_KEY env var | Standard pattern, matches codebase | ✓ |
| CLI flag --api-key | Convenient but shows in history | |
| You decide | Claude's discretion | |

---

## Testing Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Synthetic fixtures + real integration | Automated tests with fake data, manual testing with real corpus | ✓ |
| Real data only | No fixtures, only test against real corpus | |
| You decide | Claude's discretion | |

---

## Domain Schema Expansion

| Option | Description | Selected |
|--------|-------------|----------|
| Phase 5 prerequisite task | First plan expands domain.yaml, then build workbench | ✓ |
| Separate Phase 4.1 (inserted) | Decimal phase for schema only | |
| You decide | Claude's discretion | |

### Extraction Scope
| Option | Description | Selected |
|--------|-------------|----------|
| Master doc layer only | Keep existing extractions, add org/program on top | ✓ |
| Full re-extraction | Re-run pipeline with expanded schema | |
| You decide | Claude's discretion | |

---

## Chat Response Format

| Option | Description | Selected |
|--------|-------------|----------|
| Rich markdown with tables + citations | Tables for costs, bullets for todos, inline citations | ✓ |
| Plain conversational text | Natural paragraphs, no structure | |
| You decide | Claude's discretion | |

---

## Workbench Branding & Visual Design

| Option | Description | Selected |
|--------|-------------|----------|
| Clean & professional | Dark sidebar, light main, severity colors, clean typography | ✓ |
| Minimal functional | Bare-bones, browser defaults | |
| You decide | Claude's discretion | |

---

## Scope Boundary for v1

### Essential Features
- [x] Chat with SME persona + Claude API
- [x] Graph panel with search/filter
- [x] Source document viewer
- [ ] Risk panel (deferred to v1.1)

---

## Claude's Discretion

- Starter prompt question selection
- Graph layout algorithm and vis.js physics settings
- Source panel search/navigation UX details
- System prompt engineering for SME persona
- FastAPI project structure
- Exact API endpoint design
- HTML/CSS implementation details

## Deferred Ideas

- Dedicated Risk Panel (v1.1)
- Telegram chat interface (v2)
- Persistent what-if scenarios
- Multi-user access / sharing
- Persistent chat history
- Committee-oriented dashboard views
- Source provenance drill-down with page/section references
