# Epistract — Domain-Agnostic Knowledge Graph Framework

## What This Is

Epistract is a **knowledge extraction framework** that goes beyond traditional RAG by building structured knowledge graphs from document corpora. It extracts not just information, but *knowledge* — grounded to domain ontologies, with an epistemic super-domain layer that surfaces hypotheses, contradictions, gaps, and risks across documents.

The framework is domain-agnostic: plug in a domain schema and ontology, feed it documents, and get a two-layer knowledge graph:
- **Layer 1 — Brute Facts KG:** Domain-specific entities and relations grounded to established standards
- **Layer 2 — Epistemic Super-Domain:** Domain-agnostic analysis that works on any brute facts KG — detecting what's asserted vs hypothesized, what contradicts, what's missing

Demonstrated via two use cases: biomedical drug discovery literature and Sample 2026 event contract management.

## Core Value

**Extract knowledge, not information.** Any corpus, any domain — plug in a schema, get a knowledge graph grounded to ontology standards, plus an epistemic layer that reveals what documents say, what they contradict, and what they're missing.

## Vision

| Milestone | Focus | Proves |
|-----------|-------|--------|
| **V1** (current) | STA contract extraction + dashboard + Telegram | End-to-end pipeline works for a new domain |
| **V2** | Framework reorganization + domain abstraction | Pluggable architecture, example consumers, repo structure reflects framework identity |
| **V3** | Biomedical domain migrated to V2 architecture | Backward compatibility, framework maturity, two production domains |

### Target Architecture (V2)

```
epistract/
├── core/              # Domain-agnostic: extraction engine, graph builder, epistemic layer
├── domains/           # Example domain configurations
│   ├── drug-discovery/    # Biomedical KG (17 entity types, 30 relation types)
│   └── contracts/         # Event contract KG (grounded to contract standards)
└── examples/          # Example consumers of the KG
    ├── viewer/            # Web-based KG explorer
    └── telegram-bot/      # Chat interface
```

## Requirements

### Validated

- Existing biomedical KG extraction pipeline (Scenarios 1-6)
- Entity/relation extraction from scientific documents
- Knowledge graph construction and visualization
- Epistemic analysis (hypotheses, contradictions, conditional claims)
- Molecular identifier validation (SMILES, sequences)

### Active (V1 Milestone)

- [x] Domain configuration system — pluggable entity/relation type definitions per domain
- [x] Contract domain schema — entity types (Party, Obligation, Deadline, Cost, Clause, Venue, Service) and relation types (OBLIGATES, CONFLICTS_WITH, DEPENDS_ON, COSTS, PROVIDES, RESTRICTS)
- [x] PDF/XLS/EML document ingestion for contract files
- [x] Contract entity extraction using domain-configured prompts — Validated in Phase 3
- [x] Knowledge graph construction from contract extractions — Validated in Phase 3
- [x] Cross-reference analysis — connecting obligations, deadlines, and costs across vendors — Validated in Phase 4
- [x] Risk and conflict detection — flagging contradictions, missing coverage, timeline conflicts — Validated in Phase 4
- [x] Dashboard master data as reference layer — import Sample_Conference_Master.md as contextual nodes — Validated in Phase 4
- [ ] Interactive web workbench — chat-first interface with graph visualization and source document viewer
- [ ] Telegram chat interface — query the contract KG via natural language

### Future (V2/V3)

- [ ] Repo reorganization into core/domains/examples structure
- [ ] Domain-agnostic consumer apps (viewer, telegram-bot) decoupled from specific domains
- [ ] Biomedical domain migrated to V2 architecture with full backward compatibility
- [ ] Domain registry — discover and load domains dynamically

### Out of Scope

- Modifying existing biomedical scenarios (1-6) during V1 — they remain as-is until V3
- Regulatory compliance domain — future domain, not this milestone
- Mobile app — Telegram serves as the mobile interface
- Contract editing or document management — read-only analysis
- Real-time contract monitoring — batch extraction, not live updates
- Vercel/cloud deployment — local workbench sufficient for V1
- 2016 Atlantic City data as source — historical reference only

## Context

**The Framework:** Epistract creates a unique architecture blend — brute facts knowledge graphs grounded to domain ontologies, plus an epistemic super-domain layer that builds higher-order knowledge (contradictions, gaps, risks, hypotheses) from the brute facts. The epistemic layer is the same machinery regardless of domain.

**The STA Use Case (V1):** Silver Jubilee Annual Conference (13th WKC), September 4-6, 2026, Pennsylvania Convention Center, Philadelphia. 3,000-5,000 expected attendees, $805K-$1.17M budget, 14 planning committees, 350-450 volunteers. 62+ vendor contracts in `data/ub/STA-2026-INFRASTRUCTURE/` — hotel blocks, venue license, AV equipment, catering (exclusive Aramark), security, EMS.

**Key Venue Constraints:** Union labor (5 trades), exclusive caterer (Aramark), Labor Day teardown (double-time rates), freight elevator bottlenecks, TANA 2023 food disaster lessons at same venue.

**Dashboard Reference:** The `akka-2026-dashboard` project contains `Sample_Conference_Master.md` — a comprehensive planning document derived from contracts, serving as reference context (not authoritative source).

**Biomedical Use Case (V3):** Drug discovery literature extraction across 6 scenarios — from single-paper analysis to multi-source competitive intelligence with molecular validation. Currently runs on the original architecture; V3 migrates it to the V2 framework.

## Constraints

- **Tech stack**: Python 3.11+, uv for package management, existing epistract architecture
- **Contract formats**: Primarily PDF (60 files), 1 XLS, 1 EML — need robust document parsing
- **Large files**: Some contracts are 12-31 MB PDFs — extraction must handle large documents
- **Telegram**: Bot API integration for chat interface, existing MCP server available
- **Timeline**: Event is Sep 4-6, 2026 — contract analysis should be actionable well before event
- **Existing codebase**: Must preserve backward compatibility with biomedical scenarios

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Domain config system over hardcoded types | Enables cross-domain use without forking; contracts, regulatory, biomedical all use same pipeline | ✓ Good — proven in Phase 1 |
| Contracts as source of truth, dashboard as reference | Master data was derived from contracts; contracts have authoritative terms/dates/costs | ✓ Good |
| Two-layer KG architecture (brute facts + epistemic) | Epistemic layer is domain-agnostic — same contradiction/gap/risk detection for any domain | ✓ Good — core differentiator |
| V1→V2→V3 milestone arc | Prove with contracts first, reorganize framework, then migrate biomedical | — Pending |
| No Vercel deployment for V1 | Local workbench sufficient for STA use case; deployment is a V2 concern | — Pending |
| Interactive web over PDF report | Committee chairs need to explore and drill down, not just read a static report | — Pending |
| Telegram for mobile/chat access | User already has Telegram MCP integration; natural interface for on-the-go queries | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-02 after vision update — reframed as domain-agnostic knowledge graph framework with V1/V2/V3 milestone arc*
