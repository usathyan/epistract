# Phase 10: Documentation Refresh - Context

**Gathered:** 2026-04-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Reframe all documentation from "biomedical extraction tool" to "domain-agnostic knowledge graph framework." README, architecture diagrams, domain developer guide, paper, and CLAUDE.md all get updated. Demo video removed until a framework-appropriate recording exists. STA contract data stays private — public docs show aggregate stats and schema structure only.

</domain>

<decisions>
## Implementation Decisions

### README Narrative
- **D-01:** Framework-first lead — open with "Turn any document corpus into a structured knowledge graph." No biomedical-specific framing in the pitch.
- **D-02:** Dual-path quick-start — Path A: "Use a Pre-Built Domain" (3 commands to first graph), Path B: "Create Your Own Domain" (wizard workflow, 5 steps). Both paths end at graph exploration.
- **D-03:** Scenarios collapse into a "Showcase" section — drug discovery gets 2-3 paragraphs, STA contracts gets 2-3 paragraphs (aggregate stats only, no vendor/amount details). Detailed write-ups move to docs/showcases/.
- **D-04:** Demo video removed from README entirely — current video is biomedical-only and doesn't represent the framework. Will be re-added when a framework demo is recorded.

### README Additional Sections
- **D-05:** "How It Works" section — brief explanation of two-layer KG (brute facts + epistemic), extraction pipeline, domain pluggability. 1-2 paragraphs + architecture diagram inline.
- **D-06:** "Pre-built Domains" table — available domains with entity/relation counts, document format support, links to domain docs.
- **D-07:** "Commands Reference" — all /epistract:* commands with one-line descriptions, updated for new commands (domain wizard, dashboard, etc.).
- **D-08:** "Contributing / Development" section — setup instructions, test commands, project structure overview. Link to CLAUDE.md for AI-assisted development.

### Architecture Diagrams
- **D-09:** Four diagrams to produce:
  1. Three-layer framework diagram (core/ → domains/ → examples/) — replaces current architecture.mmd
  2. Two-layer KG diagram (brute facts → epistemic super-domain)
  3. Data flow / pipeline diagram — update existing data-flow.mmd for domain-agnostic pipeline
  4. Domain package anatomy — contents of a domain package (domain.yaml, SKILL.md, epistemic.py, references/, workbench/)
- **D-10:** Rendering: Mermaid .mmd source files rendered to SVG via beautiful-mermaid. Consistent with existing toolchain.

### Domain Developer Guide
- **D-11:** Wizard-first, manual-second structure. Rewrite docs/ADDING-DOMAINS.md in place.
  - Quick path: domain wizard (5-step happy path)
  - Advanced: manual domain creation for power users
- **D-12:** Manual section includes schema reference with annotated examples from both existing domains (drug-discovery and contracts). Field-by-field reference for domain.yaml, section guide for SKILL.md, function signature for epistemic.py.

### Paper Reframing
- **D-13:** Paper lives on remote main at paper/ (gitignored locally, needs pull from remote). Update title, abstract, introduction, architecture sections, conclusion. Keep scenario evaluations as-is.
- **D-14:** New title direction: "Epistract: A Domain-Agnostic Framework for Agentic Knowledge Graph Construction from Document Corpora" (replaces "Beyond RAG: Domain-Specific Agentic Architecture for Biomedical KG Construction").
- **D-15:** Add Case Study 2: Event Contract Management — aggregate stats only (62 contracts, 341 nodes, 663 edges, 53 conflicts, 11 entity types, 11 relation types). No vendor names, dollar amounts, or specific contract terms.

### STA Privacy & Git Audit
- **D-16:** All real STA contract data, output graphs, and demos must stay local-only. Public repo shows capability (schema, aggregate stats) not content.
- **D-17:** Verify + add explicit .gitignore rules for STA-related paths. Document what's safe (schema definitions, synthetic test fixtures) vs excluded (real contract PDFs, extraction output, demo recordings).
- **D-18:** Test fixtures (sample_contract_a.pdf, sample_contract_b.pdf, marriott_contract.txt) are synthetic — safe to keep in repo.

### CLAUDE.md Update
- **D-19:** Update CLAUDE.md Project section, Architecture section, and conventions to reflect framework identity. Part of Phase 10 scope.

### Claude's Discretion
- README section ordering beyond the decisions above
- Exact wording of framework pitch and showcase summaries
- Mermaid diagram styling and layout choices
- Level of detail in Commands Reference (terse vs annotated)
- Paper section restructuring details beyond title/abstract/architecture

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Current Documentation (to be updated)
- `README.md` — Current 514-line biomedical-framed README (full rewrite)
- `docs/ADDING-DOMAINS.md` — Current 323-line domain guide (rewrite with wizard-first structure)
- `CLAUDE.md` — Project instructions (reframe for framework identity)

### Architecture Diagrams (to be updated/replaced)
- `docs/diagrams/architecture.mmd` — Current single-domain architecture diagram (replace)
- `docs/diagrams/data-flow.mmd` — Current data flow diagram (update)
- `docs/diagrams/architecture.svg` — Rendered output (regenerate)
- `docs/diagrams/data-flow.svg` — Rendered output (regenerate)

### Domain Package References (examples for guide)
- `domains/drug-discovery/domain.yaml` — Drug discovery schema (17 entity types, 30 relation types)
- `domains/drug-discovery/SKILL.md` — Full-featured extraction prompt
- `domains/drug-discovery/epistemic.py` — Epistemic analysis rules
- `domains/contracts/domain.yaml` — Contract schema (11 entity types, 11 relation types)
- `domains/contracts/SKILL.md` — Contract extraction prompt
- `domains/contracts/epistemic.py` — Contract epistemic rules
- `domains/contracts/workbench/template.yaml` — Workbench domain template

### Paper (on remote)
- `paper/main.tex` — LaTeX source (on remote main branch, needs pull)

### Project Context
- `.planning/PROJECT.md` — Framework vision, V1/V2/V3 arc
- `.planning/REQUIREMENTS.md` — DOCS-01 through DOCS-04 acceptance criteria
- `.planning/phases/08-domain-creation-wizard/08-CONTEXT.md` — Wizard decisions (D-01 through D-16)
- `.planning/phases/09-consumer-decoupling-and-standalone-install/09-CONTEXT.md` — Consumer decoupling decisions

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `docs/diagrams/*.mmd` — Existing Mermaid source files with established style
- `beautiful-mermaid` — Already in toolchain for SVG rendering
- `domains/*/` — Two complete domain packages to use as reference examples in guide

### Established Patterns
- Mermaid flowchart TB layout in architecture diagrams
- `*.mp4` already gitignored (covers demo videos)
- `epistract-output/` already gitignored (covers real extraction data)

### Integration Points
- README links to docs/ subdirectories
- Paper references architecture diagrams
- CLAUDE.md Architecture section documents the codebase for AI assistants

</code_context>

<specifics>
## Specific Ideas

- README showcase preview format: brief stats + "Read the full evaluation →" links
- Paper Case Study 2 format: "We applied epistract to a corpus of 62 event planning contracts..." with aggregate results table
- Domain guide preview: wizard 5-step happy path shown in quick-start, manual path as reference appendix
- Video: removed entirely, not replaced with placeholder — clean README without dead links

</specifics>

<deferred>
## Deferred Ideas

- **Framework demo video** — Record new video showing both domains + wizard workflow. Separate phase/backlog item when ready.
- **Interactive README** — GitHub-rendered Mermaid diagrams directly in README (depends on GitHub Mermaid support quality)

</deferred>

---

*Phase: 10-documentation-refresh*
*Context gathered: 2026-04-04*
