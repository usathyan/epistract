---
phase: 10-documentation-refresh
plan: 02
subsystem: docs
tags: [readme, claude-md, framework-identity, showcases]

# Dependency graph
requires: [10-01]
provides:
  - Framework-first README with dual-path quick-start
  - Drug discovery and contract analysis showcase pages
  - Updated CLAUDE.md with framework identity
affects: []

# Tech tracking
tech-stack: [markdown]
---

## What was built

Rewrote README.md from a biomedical-specific document to a framework-first presentation of Epistract. Created two showcase detail pages in docs/showcases/ and updated CLAUDE.md to reflect framework identity.

## Key files

### Created
- `docs/showcases/drug-discovery.md` — Detailed drug discovery scenario write-up
- `docs/showcases/contracts.md` — Contract analysis showcase with aggregate stats

### Modified
- `README.md` — Complete rewrite as framework-first document
- `CLAUDE.md` — Project and Architecture sections updated for framework identity

## Decisions

- README leads with "Turn any document corpus into a structured knowledge graph"
- Dual-path quick-start: pre-built domain (3 steps) vs create-your-own (5 steps)
- Showcase section uses aggregate stats only for contracts (no vendor names per D-16)
- No demo video links (per D-04)

## Self-Check: PASSED

- [x] README contains framework identity opening
- [x] Dual-path quick-start present
- [x] No demo video links
- [x] No STA vendor names in any documentation
- [x] Showcase pages created with appropriate content
- [x] CLAUDE.md reflects framework identity
