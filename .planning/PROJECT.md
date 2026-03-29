# Epistract Cross-Domain Knowledge Graph Framework

## What This Is

Epistract evolves from a biomedical-specific literature extraction tool into a **cross-domain knowledge graph framework** with a pluggable domain configuration system. The first cross-domain application (Scenario 7) extracts structured knowledge from 62+ Sample 2026 event contracts (PDFs, XLS, emails) to build an interactive analysis dashboard and Telegram-connected chat interface for event planning intelligence.

## Core Value

**Contracts are the source of truth.** Every obligation, deadline, cost, and party relationship across 62+ vendor contracts must be extractable, queryable, and cross-referenced — so event organizers can spot conflicts, gaps, and risks before they become problems on-site at the Pennsylvania Convention Center.

## Requirements

### Validated

- Existing biomedical KG extraction pipeline (Scenarios 1-6)
- Entity/relation extraction from scientific documents
- Knowledge graph construction and visualization
- Epistemic analysis (hypotheses, contradictions, conditional claims)
- Molecular identifier validation (SMILES, sequences)

### Active

- [ ] Domain configuration system — pluggable entity/relation type definitions per domain
- [ ] Contract domain schema — entity types (Party, Obligation, Deadline, Cost, Clause, Venue, Service) and relation types (OBLIGATES, CONFLICTS_WITH, DEPENDS_ON, COSTS, PROVIDES, RESTRICTS)
- [ ] PDF/XLS/EML document ingestion for contract files
- [ ] Contract entity extraction using domain-configured prompts
- [ ] Knowledge graph construction from contract extractions
- [ ] Cross-reference analysis — connecting obligations, deadlines, and costs across vendors
- [ ] Risk and conflict detection — flagging contradictions, missing coverage, timeline conflicts
- [ ] Dashboard master data as reference layer — import Sample_Conference_Master.md as contextual nodes (not authoritative; contracts override)
- [ ] Interactive web report — filterable tables, graph visualization, drill-down into contract details
- [ ] Telegram chat interface — query the contract KG via natural language (quick lookups + cross-contract reasoning)

### Out of Scope

- Modifying existing biomedical scenarios (1-6) — they remain as-is
- Regulatory compliance domain (clinical development) — future Scenario 8, not this milestone
- Mobile app — Telegram serves as the mobile interface
- Contract editing or document management — read-only analysis
- Real-time contract monitoring — batch extraction, not live updates
- 2016 Atlantic City data as source — historical reference only, not extracted into KG

## Context

**The Event:** STA Silver Jubilee Annual Conference (Sample Annual Conference), September 4-6, 2026, Pennsylvania Convention Center, Philadelphia. 3,000-5,000 expected attendees, $805K-$1.17M budget, 14 planning committees, 350-450 volunteers.

**The Contracts:** 62+ documents in `data/ub/STA-2026- INFRASTRUCTURE/` organized by category:
- Hotel contracts (Marriott, Sheraton, Notary Hotel) — room blocks, rates, cancellation policies
- PCC venue contract — license agreement, floor plans, capacity charts, event profile
- PCC guidelines — labor jurisdictions, safety, electrical, drone policy, tax exemptions
- AV contracts (Prime AV, Black & White AV) — equipment, rigging, labor pricing
- Catering (Aramark) — exclusive caterer agreement, menus (veg/non-veg), kitchen buyout, labor
- Security — vendor proposals, approved vendor lists
- EMS — approved medical services list

**Key Venue Constraints:** Union labor (5 trades), exclusive caterer (Aramark), Labor Day teardown (double-time rates), freight elevator bottlenecks, TANA 2023 food disaster lessons at same venue.

**Dashboard Reference:** The `akka-2026-dashboard` project contains `Sample_Conference_Master.md` — a comprehensive planning document with budgets, timelines, risks, committee structures, and lessons learned. This data was derived from the contracts and serves as reference context, not authoritative source.

**Cross-Domain Vision:** This project proves epistract works beyond biomedical literature. The domain config system being built here will support future domains (regulatory compliance for clinical development is next).

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
| Domain config system over hardcoded types | Enables cross-domain use without forking; contracts, regulatory, biomedical all use same pipeline | -- Pending |
| Contracts as source of truth, dashboard as reference | Master data was derived from contracts; contracts have authoritative terms/dates/costs | -- Pending |
| Interactive web over PDF report | Committee chairs need to explore and drill down, not just read a static report | -- Pending |
| Telegram for mobile/chat access | User already has Telegram MCP integration; natural interface for on-the-go queries | -- Pending |
| Scenario 7 positioning | Demonstrates cross-domain capability without modifying existing biomedical scenarios | -- Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? -> Move to Out of Scope with reason
2. Requirements validated? -> Move to Validated with phase reference
3. New requirements emerged? -> Add to Active
4. Decisions to log? -> Add to Key Decisions
5. "What This Is" still accurate? -> Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check -- still the right priority?
3. Audit Out of Scope -- reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-03-29 after initialization*
