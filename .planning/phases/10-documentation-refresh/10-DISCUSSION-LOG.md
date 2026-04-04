# Phase 10: Documentation Refresh - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-04
**Phase:** 10-documentation-refresh
**Areas discussed:** README narrative, Architecture diagrams, Domain developer guide, Paper reframing, STA data gitignore audit, README sections beyond quick-start, CLAUDE.md update, Demo video strategy

---

## README Lead / Framework Pitch

| Option | Description | Selected |
|--------|-------------|----------|
| Knowledge framework lead | "Turn any document corpus into a structured knowledge graph" — framework-first | ✓ |
| Dual identity lead | "From drug discovery to any domain" — acknowledge roots | |
| Problem-first lead | "Documents contain knowledge trapped in prose" — narrative approach | |

**User's choice:** Knowledge framework lead
**Notes:** None

## Quick Start Structure

| Option | Description | Selected |
|--------|-------------|----------|
| Dual-path tabs | Two paths: "Use a Pre-Built Domain" and "Create Your Own Domain" | ✓ |
| Single linear path | One example path with callout to wizard | |
| Interactive chooser | Branch based on document type | |

**User's choice:** Dual-path tabs
**Notes:** None

## Scenario Documentation

| Option | Description | Selected |
|--------|-------------|----------|
| Collapse into showcase section | Brief summaries + links to detailed write-ups in docs/showcases/ | ✓ |
| Keep inline but shortened | Reduce each to 3-4 lines in README | |
| Remove from README entirely | All use case docs in docs/ only | |

**User's choice:** Collapse into showcase section
**Notes:** None

## Demo Video Positioning

| Option | Description | Selected |
|--------|-------------|----------|
| Keep prominent but re-label | Video stays near top, labeled "Drug Discovery Demo" | |
| Move to showcase section | Video moves into Drug Discovery showcase | ✓ |

**User's choice:** Move to showcase section
**Notes:** Later changed to "Remove video entirely" in the demo video strategy discussion

## Architecture Diagrams

| Option | Description | Selected |
|--------|-------------|----------|
| Three-layer framework diagram | core/ → domains/ → examples/ separation | ✓ |
| Two-layer KG diagram | Brute facts → epistemic super-domain | ✓ |
| Data flow / pipeline diagram | Domain-agnostic pipeline update | ✓ |
| Domain package anatomy | Contents of a domain package | ✓ |

**User's choice:** All four diagrams
**Notes:** None

## Diagram Rendering

| Option | Description | Selected |
|--------|-------------|----------|
| Mermaid + beautiful-mermaid | .mmd source + SVG rendering via beautiful-mermaid | ✓ |
| Mermaid source only | Let GitHub/viewers render on the fly | |
| Hand-drawn SVG | Polished SVGs via Excalidraw or similar | |

**User's choice:** Mermaid + beautiful-mermaid
**Notes:** None

## Domain Developer Guide Structure

| Option | Description | Selected |
|--------|-------------|----------|
| Wizard-first, manual-second | Lead with wizard, manual as advanced path | ✓ |
| Separate guides | Two files: WIZARD-GUIDE.md and MANUAL-DOMAINS.md | |
| Tutorial-style walkthrough | Single narrative with example domain | |

**User's choice:** Wizard-first, manual-second
**Notes:** None

## Manual Domain Reference Depth

| Option | Description | Selected |
|--------|-------------|----------|
| Schema reference + examples | Field-by-field reference with annotated examples from both domains | ✓ |
| Minimal — point to existing domains | Brief overview + "see domains/ for examples" | |
| You decide | Claude's discretion | |

**User's choice:** Schema reference + examples
**Notes:** None

## Paper Location and Scope

**User's input:** Paper is on remote main at https://github.com/usathyan/epistract/tree/main/paper. Was removed locally but still exists on remote.

## Paper Reframing Approach

| Option | Description | Selected |
|--------|-------------|----------|
| Update title, abstract, architecture | Reframe framing sections, add Case Study 2, keep evaluations | ✓ |
| Light touch — abstract + intro only | Minimal reframing | |
| Full rewrite | Restructure entire paper | |

**User's choice:** Update title, abstract, architecture
**Notes:** None

## STA Case Study Detail in Paper

| Option | Description | Selected |
|--------|-------------|----------|
| Aggregate stats only | 62 contracts, 341 nodes, 663 edges, etc. No vendor names/amounts | ✓ |
| Schema + methodology only | No real stats, only synthetic examples | |
| Skip STA from paper entirely | 1-line mention only | |

**User's choice:** Aggregate stats only
**Notes:** User emphasized STA contract sources, graphs, and demos cannot be shared publicly

## Test Fixture Safety

| Option | Description | Selected |
|--------|-------------|----------|
| They're synthetic — safe to keep | Fabricated test documents, not real contracts | ✓ |
| They contain real data — need removal | | |
| Not sure — let me check | | |

**User's choice:** Synthetic — safe to keep
**Notes:** None

## STA Gitignore Audit

| Option | Description | Selected |
|--------|-------------|----------|
| Verify + add explicit rules | Audit tracked vs local-only, add explicit .gitignore entries | ✓ |
| Verify only | Current gitignore is enough | |
| Create audit checklist | Review before adding rules | |

**User's choice:** Verify + add explicit rules
**Notes:** None

## README Additional Sections

| Option | Description | Selected |
|--------|-------------|----------|
| How It Works | Two-layer KG explanation + pipeline + domain pluggability | ✓ |
| Pre-built Domains | Table of available domains | ✓ |
| Commands Reference | All /epistract:* commands | ✓ |
| Contributing / Development | Setup, tests, project structure | ✓ |

**User's choice:** All four sections
**Notes:** None

## CLAUDE.md Update

| Option | Description | Selected |
|--------|-------------|----------|
| Update in Phase 10 | Reframe Project, Architecture, conventions for framework identity | ✓ |
| Separate task after Phase 10 | | |
| You decide | | |

**User's choice:** Update in Phase 10
**Notes:** None

## Demo Video Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Document gap, defer recording | Note in README, add backlog item | |
| Record new framework video | Record in Phase 10 | |
| Remove video entirely for now | Drop video link until framework video exists | ✓ |

**User's choice:** Remove video entirely
**Notes:** Avoids confusion from biomedical-only video on framework README

---

## Claude's Discretion

- README section ordering beyond decisions
- Exact wording of framework pitch and showcase summaries
- Mermaid diagram styling and layout
- Commands Reference detail level
- Paper section restructuring beyond title/abstract/architecture

## Deferred Ideas

- Framework demo video — record when both domains + wizard can be demonstrated
- Interactive GitHub-rendered Mermaid diagrams in README
