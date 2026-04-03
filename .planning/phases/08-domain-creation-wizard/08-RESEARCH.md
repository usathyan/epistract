# Phase 8: Domain Creation Wizard - Research

**Researched:** 2026-04-03
**Domain:** LLM-driven schema generation, domain package scaffolding, epistemic rule templating
**Confidence:** HIGH

## Summary

Phase 8 builds an automated domain creation wizard that analyzes sample documents via LLM multi-pass analysis to generate complete domain packages. The codebase already has two working domain packages (drug-discovery, contracts) providing clear templates. The core infrastructure (`domain_resolver.py`, `label_epistemic.py`, `ingest_documents.py`) is stable and well-understood.

The primary technical challenge is twofold: (1) designing effective LLM prompts for multi-pass schema discovery from arbitrary documents, and (2) making the epistemic dispatcher in `label_epistemic.py` generic enough to handle wizard-generated domains without hard-coded domain names. The current dispatcher has hard-coded branches for "contract" and "biomedical" — this must be generalized for generated domains to work end-to-end (WIZD-04).

**Primary recommendation:** Build a `core/domain_wizard.py` module with the multi-pass analysis pipeline, use the contracts domain as the template target (per D-05), and fix the epistemic dispatcher to use a convention-based function lookup (`analyze_<slug>_epistemic`) before generating any domain packages.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** LLM multi-pass analysis — Pass 1 extracts candidate entity/relation types from each doc, Pass 2 consolidates and deduplicates across docs, Pass 3 proposes the final schema
- **D-02:** Minimum 2 sample documents required, recommend 3-5. Wizard warns if only 1 provided
- **D-03:** User provides a 1-2 sentence domain description as required input (e.g., "Real estate lease agreements"). Gives LLM context for schema discovery and naming conventions
- **D-04:** Accept any format Kreuzberg handles (PDF, DOCX, HTML, TXT, etc.) — reuse the existing ingestion pipeline in `core/ingest_documents.py`
- **D-05:** Generated domain.yaml targets contracts-level quality — entity types with descriptions + relation types with descriptions. Not drug-discovery-level (no extraction_hints, disambiguation rules). User can manually enrich later
- **D-06:** Generated SKILL.md uses a template with domain-specific sections: system_context from user's description, entity type extraction guidance derived from sample docs, relation extraction rules, confidence calibration section. Modeled after contracts SKILL.md complexity
- **D-07:** Auto-generate `references/entity-types.md` and `references/relation-types.md` with descriptions and examples from sample documents. Keeps package structure consistent with both existing domains
- **D-08:** No validation scripts generated. Validation (like RDKit for chemistry) is too domain-specific for auto-generation. User adds manually if their domain has validatable identifiers
- **D-09:** Generic template + LLM customization approach. Base template includes all four patterns: contradiction detection, confidence calibration, gap analysis, cross-document linking
- **D-10:** LLM customizes via pattern injection — template has placeholder sections where the LLM injects domain-specific regex patterns, entity type pairs for conflict checking, and gap detection rules
- **D-11:** Generated epistemic.py is a working Python module following the existing pattern — an `analyze_<domain>_epistemic()` function that `core/label_epistemic.py` dispatches to
- **D-12:** Dry-run validation — run generated epistemic.py against a small extraction from sample docs to verify it produces valid output (no crashes, reasonable claim counts). Fix errors before writing final files
- **D-13:** Guided 3-step flow: (1) User provides domain name + description + sample doc paths, (2) Wizard analyzes and presents proposed schema summary in chat, (3) User approves/edits, wizard generates the full package
- **D-14:** Schema review happens in chat — display proposed entity types, relation types, and key epistemic rules as a formatted summary. User says "looks good" or suggests changes
- **D-15:** Write generated package directly to `domains/<name>/` where `domain_resolver.py` discovers it. Immediately usable with the pipeline
- **D-16:** Create only — no update support. If domain already exists, warn and ask to overwrite or pick a new name. Updating existing domains is a manual editing task

### Claude's Discretion
- Implementation details of the multi-pass LLM analysis (prompt engineering, chunking strategy for large sample docs)
- Exact template structure for the epistemic.py base template
- Error handling and recovery when LLM produces poor schema proposals
- How to format the schema summary for in-chat review

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| WIZD-01 | `/epistract:domain` analyzes sample docs and proposes domain schema | Multi-pass LLM analysis (D-01..D-04), reuse `ingest_documents.py` for parsing, new `core/domain_wizard.py` for analysis logic |
| WIZD-02 | Wizard generates complete domain package (domain.yaml + SKILL.md + epistemic rules) | Template-based generation from contracts domain reference (D-05..D-08), file writing to `domains/<name>/` (D-15) |
| WIZD-03 | Wizard proposes domain-appropriate epistemic layer rules | Generic template + LLM pattern injection (D-09..D-12), dry-run validation against sample extractions |
| WIZD-04 | Generated domain works with standard pipeline without modification | Requires fixing epistemic dispatcher generalization (critical gap found), domain_resolver already handles auto-discovery |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- Python 3.11+, `uv` for package management
- `ruff` for linting/formatting
- `pytest` for testing
- `pathlib.Path` throughout, no `os.path`
- Snake_case naming, descriptive function names with action verb prefixes
- Type hints with `|` union syntax
- Optional dependencies wrapped in try/except with availability flags
- JSON output with `indent=2`
- Docstrings with Args/Returns sections

## Standard Stack

### Core
| Library | Purpose | Why Standard |
|---------|---------|--------------|
| PyYAML >=6.0 | Generate domain.yaml files | Already used by domain_resolver.py and build_extraction.py |
| Jinja2 (or string templates) | Template SKILL.md and epistemic.py | Standard Python templating; string.Template may suffice given contracts SKILL.md is simple markdown |
| Kreuzberg >=4.0 (via sift-kg) | Parse sample documents | Already used by ingest_documents.py, reuse parse_document() |

### Supporting
| Library | Purpose | When to Use |
|---------|---------|-------------|
| re (stdlib) | Regex pattern generation for epistemic rules | Always — epistemic.py uses compiled regex patterns |
| json (stdlib) | Read/write extraction JSON for dry-run validation | Always |
| ast (stdlib) | Validate generated Python code compiles | Dry-run validation step (D-12) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Jinja2 | string.Template or f-strings | Jinja2 adds a dependency; string.Template is stdlib and sufficient for markdown templates |
| ast.parse | exec() | ast.parse is safer — checks syntax without execution side effects |

**No new dependencies needed.** All required libraries are already in the project. Use `string.Template` or plain f-string formatting for templates to avoid adding Jinja2.

## Architecture Patterns

### Recommended Project Structure
```
core/
  domain_wizard.py        # Main wizard logic: multi-pass analysis, schema generation, package writing
commands/
  domain.md               # /epistract:domain command definition
domains/
  <generated-name>/       # Output: wizard-generated domain package
    domain.yaml
    SKILL.md
    epistemic.py
    references/
      entity-types.md
      relation-types.md
```

### Pattern 1: Multi-Pass LLM Analysis Pipeline
**What:** Three-pass document analysis using Claude as the extraction engine
**When to use:** Always — this is the core wizard logic (D-01)

Pass 1 — Per-document entity/relation discovery:
- For each sample document, parse text via `parse_document()` from `ingest_documents.py`
- If text is large (>10K chars), chunk it using `chunk_document()` from `chunk_document.py`
- Send text to LLM with a schema-discovery prompt asking for candidate entity types and relation types
- Collect raw candidates per document

Pass 2 — Cross-document consolidation:
- Merge candidate types across all documents
- Deduplicate synonyms (e.g., "VENDOR" and "SUPPLIER" become one type)
- LLM reviews merged list, picks canonical names, writes descriptions

Pass 3 — Final schema proposal:
- LLM produces the final entity_types dict and relation_types dict
- Validates: each relation type references valid source/target entity types
- Returns structured JSON matching domain.yaml format

### Pattern 2: Template-Based Package Generation
**What:** Use existing domain packages as structural templates, fill with LLM-generated content
**When to use:** After schema approval (step 3 of D-13)

Template sources (read at generation time, not hard-coded):
- `domains/contracts/domain.yaml` — structure reference
- `domains/contracts/SKILL.md` — complexity target
- `domains/contracts/epistemic.py` — function signature reference
- `domains/contracts/references/*.md` — format reference

### Pattern 3: Generic Epistemic Dispatcher
**What:** Modify `label_epistemic.py` to use convention-based function discovery instead of hard-coded domain names
**When to use:** MUST be done before any generated domain can pass WIZD-04

Current code (hard-coded):
```python
if effective_domain == "contract":
    claims_layer = domain_mod.analyze_contract_epistemic(...)
elif domain_mod is not None and hasattr(domain_mod, "analyze_biomedical_epistemic"):
    claims_layer = domain_mod.analyze_biomedical_epistemic(...)
```

Required change — convention-based lookup:
```python
# Look for analyze_<slug>_epistemic or generic analyze_epistemic
func_name = f"analyze_{effective_domain.replace('-', '_')}_epistemic"
if domain_mod is not None and hasattr(domain_mod, func_name):
    func = getattr(domain_mod, func_name)
    # Check signature for master_doc_path support
    import inspect
    sig = inspect.signature(func)
    if "master_doc_path" in sig.parameters:
        claims_layer = func(output_dir, graph_data, master_doc_path=master_doc_path)
    else:
        claims_layer = func(output_dir, graph_data)
elif domain_mod is not None and hasattr(domain_mod, "analyze_epistemic"):
    claims_layer = domain_mod.analyze_epistemic(output_dir, graph_data)
else:
    claims_layer = _builtin_biomedical_epistemic(output_dir, graph_data)
```

Also update `_load_domain_epistemic()` `dir_map` to not require hard-coded entries — fall back to using domain name directly as directory name (already works since `domain_resolver.py` handles aliases).

### Pattern 4: Epistemic Template with Injection Points
**What:** A base epistemic.py template with placeholder sections for domain-specific patterns
**When to use:** Generating the epistemic module (D-09, D-10)

The template should include:
1. **Contradiction detection** — configurable entity type pairs that can conflict (e.g., VENDOR/COST pairs in contracts)
2. **Confidence calibration** — domain-specific confidence thresholds
3. **Gap analysis** — cross-document coverage checking with configurable target entity types
4. **Cross-document linking** — entity deduplication across source documents

LLM injects into marked sections:
```python
# --- DOMAIN-SPECIFIC CONTRADICTION PAIRS ---
CONTRADICTION_PAIRS = [
    # LLM generates these based on domain analysis
    ("exclusive", "non-exclusive"),
    ("required", "optional"),
]

# --- DOMAIN-SPECIFIC GAP TARGET TYPES ---
GAP_TARGET_TYPES = {
    "budget": ["COST"],
    "timeline": ["DEADLINE"],
}
```

### Anti-Patterns to Avoid
- **Hard-coding domain names in dispatch logic:** Already exists and must be fixed. Use convention-based function lookup
- **Generating code via string concatenation:** Use templates with clearly marked injection points. Raw string building leads to syntax errors
- **Skipping dry-run validation:** Always run `ast.parse()` on generated Python and attempt a dry import before writing final files (D-12)
- **Generating drug-discovery-level complexity:** D-05 explicitly caps at contracts-level quality. Don't generate extraction_hints, disambiguation rules, or nomenclature standards

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Document parsing | Custom PDF/DOCX readers | `core/ingest_documents.py` `parse_document()` | Already handles 75+ formats via Kreuzberg |
| Document chunking | Custom text splitter | `core/chunk_document.py` `chunk_document()` | Clause-aware splitting already built |
| Domain discovery | Manual path resolution | `core/domain_resolver.py` `list_domains()` | Already scans `domains/` for packages |
| YAML serialization | Manual string building | `yaml.safe_dump()` with `default_flow_style=False` | Handles edge cases in YAML formatting |
| Python syntax validation | Try/except exec() | `ast.parse(code)` | Checks syntax without execution side effects |

## Common Pitfalls

### Pitfall 1: Epistemic Dispatcher Hard-Coding
**What goes wrong:** Generated domain's epistemic.py exists but `label_epistemic.py` doesn't know how to call it because dispatch is hard-coded for "contract" and "biomedical"
**Why it happens:** Current dispatcher uses `if effective_domain == "contract"` branching instead of convention-based lookup
**How to avoid:** Generalize dispatcher FIRST (before any wizard code), then verify both existing domains still work
**Warning signs:** `analyze_epistemic()` returns the biomedical fallback for a non-biomedical domain

### Pitfall 2: LLM Generating Invalid Python
**What goes wrong:** Generated `epistemic.py` has syntax errors, undefined variables, or missing imports
**Why it happens:** LLM outputs code that looks right but doesn't compile — common with regex patterns containing unescaped special chars
**How to avoid:** `ast.parse()` the generated code. If it fails, retry with error message fed back to LLM. D-12 mandates dry-run validation
**Warning signs:** ImportError or SyntaxError when `label_epistemic.py` tries to load the module

### Pitfall 3: Schema Over-Generation
**What goes wrong:** LLM proposes 30+ entity types and 50+ relation types from a few sample docs
**Why it happens:** LLM tries to be comprehensive, extracts every possible concept as its own type
**How to avoid:** Prompt constraints: "Propose 5-15 entity types and 5-20 relation types. Merge similar concepts." Compare against contracts domain (9 entity types, 9 relation types) as calibration
**Warning signs:** Generated domain.yaml is larger than drug-discovery domain.yaml

### Pitfall 4: Domain Name Collision
**What goes wrong:** Wizard generates a domain into an existing directory, overwriting files
**Why it happens:** User picks a name that matches an existing domain or alias
**How to avoid:** Check `list_domains()` AND `DOMAIN_ALIASES` before proceeding. D-16 says warn and ask to overwrite or rename
**Warning signs:** Existing files in `domains/<name>/` before wizard writes

### Pitfall 5: Epistemic Template Too Generic
**What goes wrong:** Generated epistemic.py is essentially a copy of the biomedical template with different variable names — doesn't actually detect domain-appropriate patterns
**Why it happens:** LLM doesn't have enough context about what "contradiction" means in the new domain
**How to avoid:** Pass the generated entity types + sample document excerpts to the LLM when generating epistemic rules. Ask for specific contradiction patterns, not abstract ones
**Warning signs:** Generated contradiction pairs are the same for every domain

### Pitfall 6: `_load_domain_epistemic()` dir_map Limitation
**What goes wrong:** `_load_domain_epistemic()` has a hard-coded `dir_map = {"drug-discovery": "drug-discovery", "contract": "contracts", "biomedical": "drug-discovery"}` that won't resolve wizard-generated domain names
**Why it happens:** The dir_map was written when only two domains existed
**How to avoid:** Change `_load_domain_epistemic()` to use `domain_resolver.py`'s `_resolve_domain_dir()` or at minimum fall back to using the domain name directly as the directory name
**Warning signs:** `_load_domain_epistemic()` returns None for a valid wizard-generated domain

## Code Examples

### domain.yaml Generation (target format)
```python
# Source: domains/contracts/domain.yaml (verified structure)
import yaml

def generate_domain_yaml(name: str, description: str, system_context: str,
                         entity_types: dict, relation_types: dict) -> str:
    """Generate domain.yaml content matching contracts-level quality."""
    schema = {
        "name": name,
        "version": "1.0.0",
        "description": description,
        "system_context": system_context,
        "entity_types": entity_types,  # {"TYPE_NAME": {"description": "..."}}
        "relation_types": relation_types,  # {"REL_NAME": {"description": "..."}}
    }
    return yaml.safe_dump(schema, default_flow_style=False, sort_keys=False, allow_unicode=True)
```

### SKILL.md Generation (target format)
```python
# Source: domains/contracts/SKILL.md (verified structure)
SKILL_TEMPLATE = """# {domain_name}

{system_context}

## Entity Types

| Type | Description |
|------|-------------|
{entity_type_rows}

## Relation Types

| Type | Description |
|------|-------------|
{relation_type_rows}

## Extraction Guidelines

{extraction_guidelines}
"""
```

### Epistemic Function Signature (required interface)
```python
# Source: domains/contracts/epistemic.py line 758, domains/drug-discovery/epistemic.py line 271
# Both follow: analyze_<slug>_epistemic(output_dir: Path, graph_data: dict) -> dict
# Contract variant adds optional master_doc_path parameter

def analyze_{slug}_epistemic(
    output_dir: Path,
    graph_data: dict,
) -> dict:
    """Run domain-specific epistemic analysis.
    
    Returns:
        claims_layer dict with keys: metadata, summary, base_domain, super_domain
    """
    nodes = graph_data.get("nodes", [])
    links = graph_data.get("links", [])
    # ... domain-specific analysis ...
    return {
        "metadata": {"domain": "{slug}", "description": "..."},
        "summary": {"epistemic_status_counts": {...}, ...},
        "base_domain": {"description": "...", "relation_count": N},
        "super_domain": {"description": "...", ...},
    }
```

### Dry-Run Validation Pattern
```python
import ast
import importlib.util
from pathlib import Path

def validate_generated_epistemic(code: str, module_path: Path, func_name: str) -> dict:
    """Validate generated epistemic.py compiles and has correct interface."""
    # Step 1: Syntax check
    try:
        ast.parse(code)
    except SyntaxError as e:
        return {"valid": False, "error": f"SyntaxError: {e}"}
    
    # Step 2: Write temp file and try import
    module_path.write_text(code)
    try:
        spec = importlib.util.spec_from_file_location("test_epistemic", module_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    except Exception as e:
        return {"valid": False, "error": f"ImportError: {e}"}
    
    # Step 3: Check function exists
    if not hasattr(mod, func_name):
        return {"valid": False, "error": f"Missing function: {func_name}"}
    
    # Step 4: Dry run with minimal data
    func = getattr(mod, func_name)
    try:
        result = func(module_path.parent, {"nodes": [], "links": []})
        if not isinstance(result, dict):
            return {"valid": False, "error": "Function must return dict"}
        for key in ("metadata", "summary", "base_domain", "super_domain"):
            if key not in result:
                return {"valid": False, "error": f"Missing key: {key}"}
    except Exception as e:
        return {"valid": False, "error": f"Runtime error: {e}"}
    
    return {"valid": True}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hard-coded domain dispatch | Must become convention-based | Phase 8 (this phase) | Enables unlimited wizard-generated domains |
| 2 domains (drug-discovery, contracts) | N domains via wizard | Phase 8 (this phase) | Core value proposition of framework |

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest |
| Config file | none (uses defaults via conftest.py) |
| Quick run command | `python -m pytest tests/test_unit.py -x -v` |
| Full suite command | `python -m pytest tests/ -v` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| WIZD-01 | Wizard analyzes sample docs and proposes schema | unit | `python -m pytest tests/test_unit.py::test_wizard_schema_proposal -x` | No — Wave 0 |
| WIZD-02 | Wizard generates complete domain package | unit | `python -m pytest tests/test_unit.py::test_wizard_generates_package -x` | No — Wave 0 |
| WIZD-03 | Wizard proposes domain-appropriate epistemic rules | unit | `python -m pytest tests/test_unit.py::test_wizard_epistemic_generation -x` | No — Wave 0 |
| WIZD-04 | Generated domain works with standard pipeline | integration | `python -m pytest tests/test_integration.py::test_wizard_domain_pipeline -x` | No — Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/test_unit.py -x -v`
- **Per wave merge:** `python -m pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_unit.py::test_wizard_*` — unit tests for wizard schema generation, package generation, epistemic generation
- [ ] `tests/test_integration.py::test_wizard_domain_pipeline` — end-to-end test that generated domain works with pipeline
- [ ] `tests/fixtures/wizard/` — sample documents for wizard testing (2-3 small text files from a non-biomedical, non-contract domain)
- [ ] Test for epistemic dispatcher generalization — verify both existing domains still work after refactor

## Critical Integration Gap: Epistemic Dispatcher

**This is the most important finding of this research.** The current `label_epistemic.py` has TWO hard-coding issues that block WIZD-04:

1. **`_load_domain_epistemic()` line 45:** `dir_map` is hard-coded with only 3 entries. Any wizard-generated domain name not in this map will fail to load its epistemic module, even if the file exists at the correct path.

2. **`analyze_epistemic()` lines 401-414:** Dispatch logic is branched by domain name strings ("contract", "biomedical"). A wizard-generated domain will fall through to the biomedical fallback, ignoring its custom epistemic.py entirely.

**Fix required before wizard can satisfy WIZD-04:**
- Make `_load_domain_epistemic()` fall back to `domains/<name>/epistemic.py` when `dir_map` has no entry
- Make `analyze_epistemic()` use convention-based function lookup: `analyze_<slug>_epistemic()`
- Both existing domains must continue to work after refactor

## Open Questions

1. **LLM Prompt Engineering for Schema Discovery**
   - What we know: Multi-pass analysis is decided (D-01). Contracts domain has 9 entity types, 9 relation types as calibration reference.
   - What's unclear: Optimal prompt wording to get consistent, well-scoped schemas from diverse document types. This is Claude's discretion area.
   - Recommendation: Start with a conservative prompt that asks for 5-15 entity types. Include the contracts schema as a few-shot example of appropriate granularity.

2. **Epistemic Template Completeness**
   - What we know: Must include contradiction detection, confidence calibration, gap analysis, cross-document linking (D-09).
   - What's unclear: How much of the contract epistemic.py's complexity (760 lines) should be in the template vs. generated.
   - Recommendation: Template should be ~100-150 lines covering the four patterns with simple implementations. The contracts epistemic.py is domain-specific; don't try to replicate its full complexity.

3. **Wizard as Command vs. Module**
   - What we know: Entry point is `/epistract:domain` command (WIZD-01). Wizard is interactive (D-13, D-14).
   - What's unclear: Since this is a Claude Code command (markdown file in `commands/`), the wizard logic runs as instructions to Claude, not as a standalone Python script.
   - Recommendation: `commands/domain.md` defines the interactive flow. `core/domain_wizard.py` provides the Python utilities (file generation, validation, dry-run). The command orchestrates, the module provides tools.

## Sources

### Primary (HIGH confidence)
- `domains/contracts/domain.yaml` — verified target structure (9 entity types, 9 relation types, descriptions only)
- `domains/contracts/SKILL.md` — verified target complexity (40 lines, entity/relation tables + guidelines)
- `domains/contracts/epistemic.py` — verified function signature: `analyze_contract_epistemic(output_dir, graph_data, master_doc_path=None) -> dict`
- `domains/drug-discovery/epistemic.py` — verified function signature: `analyze_biomedical_epistemic(output_dir, graph_data) -> dict`
- `core/domain_resolver.py` — verified auto-discovery: scans `domains/` for dirs with `domain.yaml`
- `core/label_epistemic.py` — verified hard-coded dispatch (lines 37-55 dir_map, lines 401-414 branching)
- `core/ingest_documents.py` — verified `parse_document()` API for reuse
- `core/chunk_document.py` — verified `chunk_document()` API for large doc handling
- `domains/contracts/references/entity-types.md` — verified reference doc format
- `domains/contracts/references/relation-types.md` — verified reference doc format

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new dependencies needed, all patterns from existing codebase
- Architecture: HIGH — clear template from two existing domains, well-defined interfaces
- Pitfalls: HIGH — critical dispatcher issue identified from source code analysis
- Epistemic template design: MEDIUM — template structure is Claude's discretion, contracts epistemic.py provides reference but is very domain-specific

**Research date:** 2026-04-03
**Valid until:** 2026-05-03 (stable — internal project patterns, no external API changes expected)
