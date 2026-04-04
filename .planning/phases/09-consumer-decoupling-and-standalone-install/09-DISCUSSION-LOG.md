# Phase 9: Consumer Decoupling and Standalone Install - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-03
**Phase:** 09-consumer-decoupling-and-standalone-install
**Areas discussed:** Workbench generalization, Telegram bot scope, Standalone install mechanism, Demo data exclusion

---

## Workbench Generalization

### Adaptation Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Domain config driven | Workbench reads domain.yaml for persona, starter questions, UI labels, entity categories. Falls back to sensible defaults. | |
| Template per domain | Each domain ships its own workbench template (HTML, system prompt). More customizable but more files per domain. | ✓ |
| Runtime auto-detect | Workbench inspects loaded graph data to infer domain context and generates UI dynamically. | |

**User's choice:** Template per domain
**Notes:** Maximum flexibility for domain-specific customization.

### Template Contents

| Option | Description | Selected |
|--------|-------------|----------|
| System prompt | Domain-specific persona and instructions for chat AI | ✓ |
| Starter questions | Domain-relevant example queries for new users | ✓ |
| UI labels and branding | Page title, subtitle, placeholder text, loading messages, color theme | ✓ |
| Dashboard categories | Entity type groupings for dashboard tabs | ✓ |

**User's choice:** All four — full template customization
**Notes:** Workbench becomes a shell that loads everything from domain template.

### Template Location

| Option | Description | Selected |
|--------|-------------|----------|
| domains/<name>/workbench/ | Co-located with domain package, keeps domains self-contained | ✓ |
| examples/workbench/templates/<name>/ | Centralized in workbench directory | |

**User's choice:** domains/<name>/workbench/
**Notes:** Consistent with Phase 6 D-06 self-contained domain principle.

### Fallback Behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Generic fallback | Works with any domain using generic labels, auto-generated starters, neutral prompt | ✓ |
| Require templates | Domain must provide templates to use workbench | |

**User's choice:** Generic fallback
**Notes:** New domains can visualize immediately without extra setup.

---

## Telegram Bot Scope

### Implementation Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Reference implementation | Working bot, loads any domain's graph, answers via LLM, ships with README | ✓ |
| Minimal stub | Just enough to show pattern — /start and simple query | |
| Full-featured bot | Production-ready with history, inline keyboards, graph images, multi-domain | |

**User's choice:** Reference implementation
**Notes:** Functional but not production-grade.

### Template Reuse

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, shared templates | Bot reads same domain workbench templates (system_prompt, starters) | ✓ |
| Separate bot config | Bot has own template format in domains/<name>/telegram/ | |

**User's choice:** Shared templates
**Notes:** One template system, two consumers.

---

## Standalone Install Mechanism

### Install Path

| Option | Description | Selected |
|--------|-------------|----------|
| Marketplace only | claude plugin install epistract. /epistract:setup handles Python deps. | ✓ |
| Marketplace + pip | Plugin from marketplace + pip install for Python core | |
| Git clone only | Keep current model | |

**User's choice:** Marketplace only
**Notes:** Single install step, zero git clone.

### Pre-built Domain Delivery

| Option | Description | Selected |
|--------|-------------|----------|
| Bundled in plugin | Pre-built domains ship with plugin package, available immediately | ✓ |
| Downloaded on demand | /epistract:setup downloads domains from registry | |
| Separate domain packages | Each domain is its own plugin | |

**User's choice:** Bundled in plugin
**Notes:** Zero-config, available immediately after install.

---

## Demo Data Exclusion

### Exclusions

| Option | Description | Selected |
|--------|-------------|----------|
| tests/ directory | Test files, fixtures, corpora, scenarios | ✓ |
| docs/ directory | Plans, analysis, diagrams, demo video | ✓ |
| .planning/ directory | GSD workflow artifacts | ✓ |
| .claude/ worktrees | Agent worktree leftovers | ✓ |

**User's choice:** All four excluded
**Notes:** None needed by end users.

### Domain References

| Option | Description | Selected |
|--------|-------------|----------|
| Include references | Essential for extraction quality | ✓ |
| Exclude references | Smaller package but worse out-of-box accuracy | |
| Include slim references | Curated subset | |

**User's choice:** Include references
**Notes:** Essential for pre-built domains to work well.

### Makefile

| Option | Description | Selected |
|--------|-------------|----------|
| Exclude from package | Developer tool, users use /epistract:* commands | ✓ |
| Include it | Some power users may want it | |

**User's choice:** Exclude from package

### Exclusion Mechanism

| Option | Description | Selected |
|--------|-------------|----------|
| .pluginignore file | Similar to .gitignore, list patterns to exclude | ✓ |
| marketplace.json includes | Whitelist approach | |
| You decide | Claude picks best mechanism | |

**User's choice:** .pluginignore file

---

## Claude's Discretion

- Workbench template discovery mechanism
- Telegram bot library choice
- Generic fallback implementation details
- .pluginignore syntax specifics

## Deferred Ideas

None — discussion stayed within phase scope
