# Phase 9: Consumer Decoupling and Standalone Install - Context

**Gathered:** 2026-04-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Decouple the workbench and telegram bot into domain-agnostic examples, enable standalone plugin install via Claude Code marketplace without repo clone, and ship pre-built domains (drug-discovery, contracts) bundled in the plugin package.

</domain>

<decisions>
## Implementation Decisions

### Workbench Generalization
- **D-01:** Template per domain — each domain ships its own workbench template package in `domains/<name>/workbench/`, co-located with domain config per Phase 6 decision D-06.
- **D-02:** Templates include: system prompt (persona), starter questions, UI labels and branding (title, subtitle, placeholder text, loading messages, color theme), and dashboard categories (entity type groupings for tabs).
- **D-03:** Generic fallback — workbench works with any domain using generic labels ("Knowledge Graph Explorer"), auto-generated starter questions from entity types, and a neutral system prompt. Domain templates override these defaults.
- **D-04:** The workbench shell in `examples/workbench/` discovers and loads templates from `domains/<name>/workbench/` at runtime.

### Telegram Bot
- **D-05:** Reference implementation — a working bot that loads any domain's graph, answers questions via LLM, and demonstrates the pattern. Not production-grade but functional. Ships with README.
- **D-06:** Bot reuses the workbench domain template system (system prompt, starter questions) from `domains/<name>/workbench/`. One template system, two consumers (workbench + telegram bot).

### Standalone Install
- **D-07:** Marketplace-only install — `claude plugin install epistract`. Plugin includes core scripts, pre-built domains, commands, agents. `/epistract:setup` handles Python deps (sift-kg, etc.). No git clone needed.
- **D-08:** Pre-built domains (drug-discovery, contracts) bundled in the plugin package. Available immediately after install, zero additional setup.

### Demo Data Exclusion
- **D-09:** Excluded from plugin package via `.pluginignore` file: `tests/`, `docs/`, `.planning/`, `.claude/` worktrees, `Makefile`.
- **D-10:** Domain reference documents (`domains/<name>/references/`) are included — they're essential for extraction quality.
- **D-11:** Makefile excluded — end users use `/epistract:*` commands, not make targets.

### Claude's Discretion
- Workbench template discovery mechanism (file convention, config entry, or directory scan)
- Telegram bot library choice (python-telegram-bot, aiogram, or similar)
- Generic fallback implementation details (how to auto-generate starter questions from entity types)
- `.pluginignore` syntax and pattern specifics

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` — CONS-01, CONS-02, INST-01, INST-02, INST-03 acceptance criteria
- `.planning/ROADMAP.md` §Phase 9 — Success criteria (5 items)

### Prior Phase Decisions
- `.planning/phases/06-repo-reorganization-and-cleanup/06-CONTEXT.md` — D-04 (self-contained domains), D-06 (domain directory layout), D-11 (commands at root), D-12 (domains own everything)

### Current Workbench Code
- `examples/workbench/server.py` — Flask server entry point
- `examples/workbench/system_prompt.py` — STA-hardcoded persona (must be generalized)
- `examples/workbench/static/index.html` — STA-hardcoded starter questions and UI text
- `examples/workbench/static/chat.js` — STA-hardcoded loading messages
- `examples/workbench/api_graph.py` — Cross-contract reference handling
- `examples/workbench/data_loader.py` — Graph data loading

### Plugin Packaging
- `.claude-plugin/plugin.json` — Current plugin manifest
- `.claude-plugin/marketplace.json` — Marketplace metadata
- `scripts/setup.sh` — Current setup script (must work post-marketplace-install)

### Domain Structure
- `domains/drug-discovery/` — Pre-built biomedical domain
- `domains/contracts/` — Pre-built contract domain

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `examples/workbench/` — Complete working workbench, needs generalization not rewrite
- `examples/workbench/data_loader.py` — Already loads graph data generically from JSON
- `examples/workbench/api_graph.py` — Graph API endpoints, mostly domain-agnostic except cross-contract references
- `core/domain_resolver.py` — Existing domain discovery mechanism, can inform template discovery

### Established Patterns
- Domain packages are self-contained under `domains/<name>/` with domain.yaml + SKILL.md + references/ + Python modules
- Plugin commands are markdown files in `commands/` at repo root
- Setup script handles dependency installation with optional packages (RDKit, Biopython)

### Integration Points
- Workbench template loading connects to `core/domain_resolver.py` for domain discovery
- Telegram bot connects to the same graph data format the workbench uses (`data_loader.py`)
- `.pluginignore` integrates with Claude Code plugin packaging system
- `/epistract:setup` must work both from repo clone and marketplace install

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 09-consumer-decoupling-and-standalone-install*
*Context gathered: 2026-04-03*
