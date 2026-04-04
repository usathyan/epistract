# Phase 9: Consumer Decoupling and Standalone Install - Research

**Researched:** 2026-04-03
**Domain:** Plugin packaging, workbench generalization, Telegram bot reference implementation
**Confidence:** HIGH

## Summary

Phase 9 decouples two consumers (workbench, Telegram bot) from STA-specific hardcoding, enables standalone plugin install, and bundles pre-built domains. The workbench is a complete, working FastAPI application that needs generalization -- not rewrite. Every STA reference lives in a small, well-defined set of files: `system_prompt.py` (persona), `index.html` (starter questions, dashboard, entity toggles), `chat.js` (loading message), `graph.js` (entity color map), and `server.py` (app title). The domain template system proposed in D-01 through D-04 creates a clean separation where each domain supplies its own persona, starter questions, UI labels, and dashboard content.

For plugin packaging, Claude Code copies marketplace plugins to `~/.claude/plugins/cache` during install. There is no `.pluginignore` convention in the official plugin system. Instead, file exclusion must be handled through `.gitignore` (since marketplace install clones via git) or by structuring the repo so plugin-irrelevant files live outside the plugin root. The recommended approach is to configure the marketplace `source` field to point to a subdirectory or use `.gitignore` to exclude non-essential files from the git clone.

The Telegram bot is a new reference implementation that reuses the existing `data_loader.py` and the domain template system. `python-telegram-bot` 22.7 is the standard choice -- mature, well-documented, async-native since v20.

**Primary recommendation:** Introduce a `workbench/` template directory in each domain package, build a template loader in the workbench shell, and create a `.claudeignore`-style exclusion strategy for plugin packaging since `.pluginignore` does not exist as a first-class concept.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Template per domain -- each domain ships its own workbench template package in `domains/<name>/workbench/`, co-located with domain config per Phase 6 decision D-06.
- **D-02:** Templates include: system prompt (persona), starter questions, UI labels and branding (title, subtitle, placeholder text, loading messages, color theme), and dashboard categories (entity type groupings for tabs).
- **D-03:** Generic fallback -- workbench works with any domain using generic labels ("Knowledge Graph Explorer"), auto-generated starter questions from entity types, and a neutral system prompt. Domain templates override these defaults.
- **D-04:** The workbench shell in `examples/workbench/` discovers and loads templates from `domains/<name>/workbench/` at runtime.
- **D-05:** Reference implementation -- a working bot that loads any domain's graph, answers questions via LLM, and demonstrates the pattern. Ships with README.
- **D-06:** Bot reuses the workbench domain template system (system prompt, starter questions) from `domains/<name>/workbench/`. One template system, two consumers.
- **D-07:** Marketplace-only install -- `claude plugin install epistract`. Plugin includes core scripts, pre-built domains, commands, agents. `/epistract:setup` handles Python deps. No git clone needed.
- **D-08:** Pre-built domains (drug-discovery, contracts) bundled in the plugin package. Available immediately after install, zero additional setup.
- **D-09:** Excluded from plugin package via `.pluginignore` file: `tests/`, `docs/`, `.planning/`, `.claude/` worktrees, `Makefile`.
- **D-10:** Domain reference documents (`domains/<name>/references/`) are included -- essential for extraction quality.
- **D-11:** Makefile excluded -- end users use `/epistract:*` commands, not make targets.

### Claude's Discretion
- Workbench template discovery mechanism (file convention, config entry, or directory scan)
- Telegram bot library choice (python-telegram-bot, aiogram, or similar)
- Generic fallback implementation details (how to auto-generate starter questions from entity types)
- `.pluginignore` syntax and pattern specifics

### Deferred Ideas (OUT OF SCOPE)
None.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CONS-01 | Workbench in `examples/`, works with any domain | Template system in D-01..D-04; workbench already in `examples/workbench/`, needs generalization of 5 hardcoded files |
| CONS-02 | Telegram bot in `examples/`, works with any domain | D-05, D-06; new `examples/telegram-bot/` using shared template system + python-telegram-bot |
| INST-01 | Plugin installs and runs `/epistract:setup` without repo clone | D-07; marketplace install copies to `~/.claude/plugins/cache`; `setup.sh` uses `${CLAUDE_PLUGIN_ROOT}` |
| INST-02 | Pre-built domains available out of the box | D-08; domains/ already contains drug-discovery and contracts, bundled in plugin package |
| INST-03 | Plugin excludes demo data, test corpora, paper artifacts | D-09..D-11; use `.gitignore` patterns + marketplace source config for exclusion |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.112.0 | Workbench HTTP server | Already in use, async-native |
| python-telegram-bot | 22.7 | Telegram bot reference implementation | Most mature Python Telegram library, async-native, excellent docs |
| PyYAML | 6.0.1 | Template config loading | Already a project dependency |
| Pydantic | 2.11.7 | Template schema validation | Already a project dependency |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| httpx | 0.28.1 | LLM API calls (workbench + bot) | Already used in api_chat.py |
| uvicorn | 0.35.0 | ASGI server | Already used for workbench |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| python-telegram-bot | aiogram | aiogram is also async-native but less documentation; python-telegram-bot has broader community |

**Installation (bot only -- workbench deps already present):**
```bash
uv pip install "python-telegram-bot>=22.0"
```

## Architecture Patterns

### Domain Template Directory Structure
```
domains/
  contracts/
    domain.yaml
    SKILL.md
    epistemic.py
    extract.py
    references/
    workbench/              # NEW: template package
      template.yaml         # Machine-readable template config
  drug-discovery/
    domain.yaml
    SKILL.md
    epistemic.py
    validate_molecules.py
    validation/
    references/
    workbench/              # NEW: template package
      template.yaml
examples/
  workbench/                # Generic shell (currently STA-hardcoded)
    server.py
    system_prompt.py        # Generalized: loads from template
    data_loader.py          # Already generic
    api_chat.py             # Loads persona from template
    api_graph.py            # Already generic
    api_sources.py          # Already generic
    static/
      index.html            # Generalized: dynamic starter questions, entity toggles
      chat.js               # Loading message from template
      graph.js              # Entity colors from API (domain-driven)
      app.js
      style.css
  telegram-bot/             # NEW: reference implementation
    bot.py                  # Main bot entry point
    README.md               # Setup instructions
```

### Pattern 1: Template YAML Schema
**What:** Each domain provides a `workbench/template.yaml` declaring its UI customizations.
**When to use:** When the workbench or Telegram bot needs domain-specific content.
**Example:**
```yaml
# domains/contracts/workbench/template.yaml
title: "Sample Contract Analysis Workbench"
subtitle: "8 contract categories covering 57 documents"
persona: |
  You are the Sample Contract Analyst -- a senior contract analysis
  specialist who has thoroughly reviewed all vendor contracts...
placeholder: "Ask about contracts, costs, deadlines, risks..."
loading_message: "Analyzing contracts"
starter_questions:
  - "What are the top cross-contract conflicts and risks?"
  - "Walk me through every deadline in order"
  - "Build me a budget summary table"
entity_colors:
  PARTY: "#6366f1"
  OBLIGATION: "#f59e0b"
  DEADLINE: "#ef4444"
  COST: "#10b981"
  SERVICE: "#8b5cf6"
  VENUE: "#06b6d4"
  CLAUSE: "#64748b"
  COMMITTEE: "#ec4899"
  PERSON: "#f97316"
  EVENT: "#14b8a6"
  STAGE: "#a855f7"
  ROOM: "#0ea5e9"
dashboard:
  title: "Sample 2026 Contract Portfolio & Key Financial Commitments"
  # Dashboard HTML/content -- either inline or separate file
```

### Pattern 2: Template Discovery via Directory Scan
**What:** The workbench discovers templates by scanning `domains/<name>/workbench/template.yaml`.
**When to use:** At server startup, when the user specifies which domain's graph to explore.
**Example:**
```python
# examples/workbench/template_loader.py
from __future__ import annotations

from pathlib import Path
import yaml

DOMAINS_DIR = Path(__file__).parent.parent.parent / "domains"

# Generic fallback defaults
GENERIC_TEMPLATE = {
    "title": "Knowledge Graph Explorer",
    "subtitle": "Explore entities and relationships",
    "persona": "You are a knowledge graph analyst. Answer questions using the graph data provided.",
    "placeholder": "Ask a question about the knowledge graph...",
    "loading_message": "Analyzing",
    "starter_questions": [],  # auto-generated from entity types
    "entity_colors": {},       # auto-assigned from palette
    "dashboard": None,         # no dashboard for generic
}

def load_template(domain_name: str | None = None) -> dict:
    """Load domain template, falling back to generic defaults."""
    template = dict(GENERIC_TEMPLATE)
    if domain_name:
        tmpl_path = DOMAINS_DIR / domain_name / "workbench" / "template.yaml"
        if tmpl_path.exists():
            domain_tmpl = yaml.safe_load(tmpl_path.read_text())
            template.update({k: v for k, v in domain_tmpl.items() if v is not None})
    return template

def auto_generate_starters(entity_types: list[str]) -> list[str]:
    """Generate starter questions from entity type names."""
    if not entity_types:
        return ["What are the main entities in this knowledge graph?"]
    questions = [
        f"What are all the {t.lower().replace('_', ' ')} entities?",
        f"Show relationships between {entity_types[0].lower().replace('_', ' ')} entities",
        "What conflicts or risks exist in the data?",
    ]
    return questions[:5]
```

### Pattern 3: Workbench API Serves Template Data
**What:** A new `/api/template` endpoint serves template config to the frontend, replacing hardcoded values.
**When to use:** Frontend needs domain-specific labels, colors, starter questions.
**Example:**
```python
# New endpoint in server.py or dedicated api_template.py
@router.get("/api/template")
async def get_template(request: Request):
    """Return domain template for frontend rendering."""
    return request.app.state.template
```

```javascript
// In app.js -- fetch template at init
const template = await fetch('/api/template').then(r => r.json());
document.querySelector('.sidebar-title').textContent = template.title || 'Workbench';
```

### Pattern 4: Telegram Bot Reusing Templates
**What:** Bot loads the same template.yaml for persona and starter questions.
**When to use:** Telegram bot startup.
**Example:**
```python
# examples/telegram-bot/bot.py
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from examples.workbench.data_loader import WorkbenchData
from examples.workbench.template_loader import load_template

async def start(update: Update, context):
    template = context.bot_data["template"]
    starters = template.get("starter_questions", [])
    msg = f"Welcome to {template['title']}!\n\nTry asking:\n"
    for q in starters[:5]:
        msg += f"- {q}\n"
    await update.message.reply_text(msg)
```

### Anti-Patterns to Avoid
- **Hardcoded domain content in HTML/JS:** All domain-specific text must come from template.yaml via API, not be baked into static files.
- **Separate template systems for workbench and bot:** D-06 mandates one template system, two consumers.
- **Large dashboard HTML in YAML:** Keep dashboard as a separate HTML template file or use a simplified data structure in YAML, not raw HTML strings.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Telegram bot framework | Raw HTTP to Bot API | python-telegram-bot 22.7 | Handles updates, webhooks, conversations, rate limiting |
| Template schema validation | Manual dict checking | Pydantic model for template.yaml | Type safety, defaults, clear error messages |
| Entity color auto-assignment | Manual color cycling | Pre-defined palette with modular index | Consistent colors across sessions |
| Plugin file exclusion | Custom packaging script | `.gitignore` patterns (git-based install) | Plugin install uses git clone -- gitignored files are excluded |

**Key insight:** The Claude Code plugin system copies the entire git repo (respecting `.gitignore`) to cache. There is no `.pluginignore` mechanism. File exclusion happens through `.gitignore` or marketplace source configuration.

## Common Pitfalls

### Pitfall 1: Plugin Packaging -- No .pluginignore Exists
**What goes wrong:** D-09 references `.pluginignore` but Claude Code has no such mechanism. Plugin install clones the repo and copies to `~/.claude/plugins/cache`.
**Why it happens:** Assumption that plugin system has npm-style ignore files.
**How to avoid:** Use `.gitignore` to exclude `tests/`, `.planning/`, `docs/` from the git repo itself. Files in `.gitignore` are not cloned. Alternatively, structure the marketplace.json `source` to point to a subdirectory. Since these files are already gitignored or not essential, adding them to `.gitignore` is the correct approach.
**Warning signs:** Plugin package size is unexpectedly large; test files appear in `~/.claude/plugins/cache`.

### Pitfall 2: Template Path Resolution Post-Install
**What goes wrong:** Template loader uses `Path(__file__).parent.parent.parent / "domains"` which breaks when plugin is installed to cache.
**Why it happens:** Plugin install copies files to `~/.claude/plugins/cache/<id>/`, changing the directory tree.
**How to avoid:** Use `${CLAUDE_PLUGIN_ROOT}` environment variable for path resolution. The template loader should resolve paths relative to the plugin root, not relative to the Python file.
**Warning signs:** `FileNotFoundError` when running workbench after marketplace install.

### Pitfall 3: Frontend Hardcoded Entity Types
**What goes wrong:** `index.html` has hardcoded entity toggle buttons and entity type legend for contract domain (PARTY, OBLIGATION, DEADLINE, etc.).
**Why it happens:** V1 built for a single domain.
**How to avoid:** Frontend fetches entity types from `/api/graph/entity-types` (already exists) and template colors from `/api/template`, then dynamically renders toggles and legend.
**Warning signs:** Drug-discovery domain shows contract entity types in sidebar.

### Pitfall 4: Dashboard Content Coupling
**What goes wrong:** The entire dashboard panel in `index.html` (lines 106-201) is a hardcoded STA contract summary with specific vendor data.
**Why it happens:** V1 dashboard was a one-off for the contracts domain.
**How to avoid:** Dashboard content must either come from the template system (domain provides dashboard data/HTML) or be generated dynamically from graph data. Generic fallback: auto-generated summary statistics (entity counts by type, relationship counts).
**Warning signs:** Drug-discovery domain shows STA vendor tables.

### Pitfall 5: Circular Import Between Workbench and Template Loader
**What goes wrong:** Template loader imports from `core/domain_resolver.py` which may not be on PYTHONPATH post-install.
**Why it happens:** Plugin installs don't set up Python package paths.
**How to avoid:** Template loader should be self-contained, only needing PyYAML and Path. It discovers templates by scanning `domains/*/workbench/template.yaml` relative to plugin root, without importing from `core/`.
**Warning signs:** ImportError in template_loader.py when running from plugin cache.

### Pitfall 6: setup.sh Path Assumptions
**What goes wrong:** `scripts/setup.sh` works from repo root but fails from plugin cache directory.
**Why it happens:** Setup script has no awareness of `${CLAUDE_PLUGIN_ROOT}`.
**How to avoid:** The `/epistract:setup` command should use `${CLAUDE_PLUGIN_ROOT}/scripts/setup.sh` path. The setup script itself only installs pip packages (sift-kg, rdkit, biopython) and doesn't reference repo paths, so it should work from any directory.
**Warning signs:** `/epistract:setup` fails with "script not found" after marketplace install.

## Code Examples

### Template YAML Pydantic Model
```python
# examples/workbench/template_schema.py
from __future__ import annotations
from pydantic import BaseModel, Field

class DashboardConfig(BaseModel):
    """Dashboard panel configuration."""
    title: str = "Knowledge Graph Summary"
    subtitle: str = ""
    # Dashboard uses auto-generated stats when no custom content provided

class WorkbenchTemplate(BaseModel):
    """Domain workbench template schema."""
    title: str = "Knowledge Graph Explorer"
    subtitle: str = "Explore entities and relationships"
    persona: str = "You are a knowledge graph analyst. Answer questions using the graph data provided."
    placeholder: str = "Ask a question about the knowledge graph..."
    loading_message: str = "Analyzing"
    starter_questions: list[str] = Field(default_factory=list)
    entity_colors: dict[str, str] = Field(default_factory=dict)
    dashboard: DashboardConfig | None = None
```

### Generic Starter Question Auto-Generation
```python
def auto_generate_starters(entity_types: list[str]) -> list[str]:
    """Generate starter questions from entity type names for generic fallback."""
    if not entity_types:
        return ["What are the main entities in this knowledge graph?"]
    
    type_names = [t.lower().replace("_", " ") for t in entity_types[:3]]
    questions = [
        f"What are all the {type_names[0]} entities and their relationships?",
        "What conflicts or gaps exist in the data?",
        "Show me the most connected entities across all types",
    ]
    if len(type_names) > 1:
        questions.append(
            f"How do {type_names[0]} entities relate to {type_names[1]} entities?"
        )
    return questions
```

### Dynamic Frontend Entity Toggle Rendering
```javascript
// Replace hardcoded entity toggles with API-driven rendering
async function renderEntityToggles(template) {
    const container = document.getElementById('entity-toggles');
    container.innerHTML = '';
    
    // Fetch actual entity types from graph data
    const resp = await fetch('/api/graph/entity-types');
    const data = await resp.json();
    const entityTypes = data.entity_types; // {TYPE: count}
    
    // Default palette for types without explicit colors
    const PALETTE = ['#6366f1','#f59e0b','#ef4444','#10b981','#8b5cf6',
                     '#06b6d4','#64748b','#ec4899','#f97316','#14b8a6'];
    
    let i = 0;
    for (const [type, count] of Object.entries(entityTypes)) {
        const color = template.entity_colors?.[type] || PALETTE[i % PALETTE.length];
        const btn = document.createElement('button');
        btn.className = 'toggle-btn active';
        btn.dataset.type = type;
        btn.style.color = color;
        btn.textContent = type.charAt(0) + type.slice(1).toLowerCase();
        container.appendChild(btn);
        i++;
    }
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hardcoded domain content in HTML | Template system with YAML config | Phase 9 (now) | Enables multi-domain workbench |
| No plugin packaging awareness | Claude Code marketplace install | 2025-2026 | Plugins install via `claude plugin install` |
| python-telegram-bot v13 (sync) | python-telegram-bot v22 (async-native) | v20, 2023 | Must use async patterns (Application, not Updater) |

**Deprecated/outdated:**
- python-telegram-bot `Updater` pattern: replaced by `Application.builder()` in v20+
- `.pluginignore`: Does not exist in Claude Code. Use `.gitignore` instead.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.x |
| Config file | tests/conftest.py |
| Quick run command | `python -m pytest tests/test_workbench.py -x -v` |
| Full suite command | `python -m pytest tests/ -v` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CONS-01 | Workbench loads any domain's template | unit | `python -m pytest tests/test_workbench.py::test_template_loading -x` | Wave 0 |
| CONS-01 | Workbench generic fallback works | unit | `python -m pytest tests/test_workbench.py::test_generic_fallback -x` | Wave 0 |
| CONS-01 | Template API endpoint returns domain config | integration | `python -m pytest tests/test_workbench.py::test_template_api -x` | Wave 0 |
| CONS-02 | Telegram bot loads template and responds | unit | `python -m pytest tests/test_telegram_bot.py::test_bot_template -x` | Wave 0 |
| INST-01 | Setup script runs without errors | smoke | `bash scripts/setup.sh --help` | Existing (setup.sh) |
| INST-02 | Pre-built domains discoverable | unit | `python -m pytest tests/test_unit.py::test_list_domains -x` | Existing |
| INST-03 | Excluded files not in plugin structure | manual | Verify `.gitignore` entries | Manual |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/test_workbench.py -x -v`
- **Per wave merge:** `python -m pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_workbench.py` -- add template loading tests (file exists, needs new test cases)
- [ ] `tests/test_telegram_bot.py` -- new file for bot tests
- [ ] Template loader module must exist before tests can run

## Open Questions

1. **Dashboard generalization strategy**
   - What we know: The dashboard panel (index.html lines 106-201) is entirely STA-specific with vendor tables, financial summaries, and decision cards.
   - What's unclear: Should each domain provide custom dashboard HTML, or should the dashboard auto-generate from graph statistics?
   - Recommendation: Support both -- template.yaml can reference a `dashboard.html` file in the domain's workbench/ directory. Generic fallback generates entity-count tables and top-connected-nodes summary. This keeps the contracts domain's rich dashboard while enabling any domain to have a basic one.

2. **Plugin root path resolution mechanism**
   - What we know: Claude Code sets `${CLAUDE_PLUGIN_ROOT}` env var pointing to plugin cache directory.
   - What's unclear: Whether Python scripts invoked by commands can reliably access this env var, or if commands need to pass it explicitly.
   - Recommendation: Commands in `commands/*.md` should pass `${CLAUDE_PLUGIN_ROOT}` as an argument to Python scripts. Template loader falls back to `Path(__file__).resolve().parent.parent.parent` when env var is not set (repo clone case).

3. **Gitignore-based exclusion vs. source subdirectory**
   - What we know: D-09 wants `.pluginignore` but the mechanism doesn't exist. `.gitignore` excludes files from git clone. The marketplace `source` field can point to a subdirectory.
   - What's unclear: Whether adding `tests/` and `.planning/` to `.gitignore` is acceptable (they're currently tracked), or if a subdirectory approach is needed.
   - Recommendation: Do NOT gitignore tracked directories. Instead, accept that plugin cache includes these files (they're small text files, not a size concern). The important exclusions (`.venv/`, `__pycache__/`, `output/`, `lib/`) are already gitignored. Tests and planning docs in the cache are harmless. If size is a concern later, restructure with a `plugin/` subdirectory as the marketplace source.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Everything | Yes | 3.11+ | -- |
| FastAPI | Workbench | Yes | 0.112.0 | -- |
| uvicorn | Workbench | Yes | 0.35.0 | -- |
| httpx | LLM API calls | Yes | 0.28.1 | -- |
| PyYAML | Template loading | Yes | 6.0.1 | -- |
| Pydantic | Schema validation | Yes | 2.11.7 | -- |
| python-telegram-bot | Telegram bot | No | -- | Install via `uv pip install python-telegram-bot` |
| sse-starlette | Chat streaming | Yes | available | -- |

**Missing dependencies with no fallback:**
- None (all core deps present)

**Missing dependencies with fallback:**
- `python-telegram-bot`: Optional dependency, only needed for Telegram bot example. Install documented in bot README.

## Sources

### Primary (HIGH confidence)
- Claude Code Plugins Reference (https://code.claude.com/docs/en/plugins-reference) -- plugin.json schema, caching behavior, `${CLAUDE_PLUGIN_ROOT}`, directory structure
- Claude Code Discover Plugins (https://code.claude.com/docs/en/discover-plugins) -- marketplace install flow, plugin installation scopes
- Existing codebase analysis -- all workbench files read and analyzed for STA-specific content

### Secondary (MEDIUM confidence)
- python-telegram-bot PyPI -- version 22.7 confirmed via `pip index versions`
- Claude Code GitHub Issues -- confirmed no `.pluginignore` mechanism exists

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already in use or well-established (python-telegram-bot)
- Architecture: HIGH -- template system is a straightforward pattern; all hardcoded content identified precisely
- Pitfalls: HIGH -- plugin caching behavior verified from official docs; path resolution issues documented

**Research date:** 2026-04-03
**Valid until:** 2026-05-03 (stable domain -- plugin system unlikely to change rapidly)
