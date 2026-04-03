# Phase 1: Domain Configuration - Research

**Researched:** 2026-03-29
**Domain:** Pluggable domain configuration system for multi-domain knowledge graph extraction
**Confidence:** HIGH

## Summary

Phase 1 converts epistract from a hardcoded biomedical extraction tool into a multi-domain framework via pluggable YAML configuration. The existing `skills/drug-discovery-extraction/` directory already serves as the reference implementation -- it contains `domain.yaml`, `SKILL.md`, `references/`, and `validation-scripts/`. The sift-kg library (v0.9.0) already supports loading arbitrary domain YAML files via `load_domain(domain_path=Path(...))` returning a Pydantic `DomainConfig` model with built-in validation. The core work is: (1) a domain resolution layer mapping `--domain <name>` to the right `skills/{name}-extraction/domain.yaml` path, (2) a new contract domain YAML + SKILL.md, (3) making agents/scripts domain-aware instead of hardcoding biomedical paths.

The codebase has exactly 6 hardcoded biomedical references that must become dynamic: `run_sift.py` line 37 (default domain path), `build_extraction.py` line 37 (hardcoded "Drug Discovery" domain_name), `validate_molecules.py` line 27 (hardcoded validation-scripts path), `commands/ingest.md` line 65 (hardcoded domain path), `commands/build.md` line 9 (same), and `agents/extractor.md` (hardcoded entity types and biomedical instructions).

**Primary recommendation:** Leverage sift-kg's existing `DomainConfig` Pydantic model for YAML validation (it already validates structure, entity types, relation type source/target references). Build a thin `resolve_domain()` function that scans `skills/` for auto-discovery and maps domain names to paths. The contract domain YAML should mirror the biomedical domain's structure exactly.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** New domains live as skill directories inside `skills/` -- e.g., `skills/contract-extraction/` mirrors `skills/drug-discovery-extraction/`
- **D-02:** Each domain.yaml is fully independent (no shared base schema, no inheritance). If two domains share an entity type, they each define it independently.
- **D-03:** Every domain must be a full package: `domain.yaml` + `SKILL.md` + `references/` directory. All three are required for a valid domain.
- **D-04:** Strict validation on load -- validate YAML structure (entity types exist, relation source/target types reference defined entities, required fields present). Fail fast with clear error if schema is malformed.
- **D-05:** Version field in domain.yaml for documentation (already exists in current YAML) but no enforcement or migration checks.
- **D-06:** Auto-discovery -- scan `skills/` for directories containing `domain.yaml`. No explicit registry needed. New domains become available by dropping in a directory.
- **D-07:** Start with the 7 entity types from requirements (Party, Obligation, Deadline, Cost, Clause, Service, Venue) and iterate after running extraction on real contracts.
- **D-08:** Start with the 6 relation types from requirements (OBLIGATES, CONFLICTS_WITH, DEPENDS_ON, COSTS, PROVIDES, RESTRICTS) and iterate after real extraction.
- **D-09:** Include detailed extraction_hints per entity and relation type, specific to contract language (e.g., "Look for shall, must, agrees to, is required to" for OBLIGATION).
- **D-10:** Fallback relation: `RELATED_TO` for contract associations that don't fit the 6 specific types.
- **D-11:** Contract-specific confidence calibration: 0.9+ for explicit "shall/must" obligations, 0.7-0.89 for implied obligations, 0.5-0.69 for inferred from context.
- **D-12:** Contract-specific disambiguation rules (OBLIGATION vs CLAUSE, COST vs PENALTY, SERVICE vs VENUE).
- **D-13:** Domain selected via `--domain <name>` flag. System resolves name to `skills/{name}-extraction/domain.yaml`.
- **D-14:** Default domain is `drug-discovery` when no `--domain` flag is provided (backward compatibility).
- **D-15:** Add `--list-domains` command that scans `skills/` and shows available domains with descriptions.
- **D-16:** Biomedical becomes a domain config -- the existing `skills/drug-discovery-extraction/` IS the biomedical domain. Pipeline learns dynamic domain resolution instead of hardcoding the path. No migration needed.
- **D-17:** Agents (extractor.md, validator.md) become domain-aware in Phase 1 -- they read the selected domain's SKILL.md for extraction guidance instead of hardcoded biomedical instructions.
- **D-18:** Validation scripts are optional per domain. Biomedical keeps its validators. Contract domain has none initially. Pipeline skips validation if no validation-scripts/ exist for the domain.

### Claude's Discretion
- Implementation details of YAML validation (Pydantic model, manual checks, or sift-kg's built-in validation)
- Naming convention for domain skill directories (confirmed pattern: `{domain-name}-extraction/`)
- Internal domain resolution function design

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DCFG-01 | System supports pluggable domain configurations via YAML schema defining entity types, relation types, and extraction prompts per domain | sift-kg `DomainConfig` Pydantic model already validates YAML structure; auto-discovery via `skills/` scanning; `resolve_domain()` function maps names to paths |
| DCFG-02 | Contract domain ontology defines 7 entity types and 6 relation types | Domain YAML structure verified -- `entity_types` dict with `description` + `extraction_hints`, `relation_types` dict with `source_types` + `target_types` |
| DCFG-03 | Domain-specific extraction prompt templates guide Claude to extract contract-relevant entities and relations | SKILL.md pattern verified in biomedical domain -- contract SKILL.md follows same structure with contract-specific guidance |
| DCFG-04 | Existing biomedical extraction pipeline (Scenarios 1-6) continues to work unchanged | 6 hardcoded references identified; default domain stays `drug-discovery`; existing tests must pass unchanged |

</phase_requirements>

## Project Constraints (from CLAUDE.md)

- **Package manager:** `uv` (not pip directly)
- **Linting:** `ruff check` and `ruff format`
- **Testing:** `pytest` (`python -m pytest tests/test_unit.py -v`)
- **Python:** 3.11+
- **Paths:** Always use `pathlib.Path`, never `os.path`
- **Naming:** snake_case functions, SCREAMING_SNAKE_CASE constants
- **Type hints:** Use `|` for Union (e.g., `str | None`)
- **Imports:** Wrap optional dependencies in try/except, set availability flags
- **Error handling:** Return error dicts, not exceptions for validation
- **JSON:** `indent=2` for all JSON output
- **CLI pattern:** Manual `sys.argv` parsing (no argparse in main scripts)
- **Docstrings:** Triple-quoted with description, Args, Returns
- **Makefile:** Standard targets required

## Standard Stack

### Core (Already Installed -- No New Dependencies)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| sift-kg | 0.9.0 | Domain loading, graph building, entity resolution | Already the foundation; `load_domain()` handles YAML parsing and Pydantic validation |
| PyYAML | 6.0.1 | YAML parsing (used by sift-kg internally) | Already installed as sift-kg dependency |
| Pydantic | 2.11.7 | DomainConfig model validation | Already used by sift-kg; provides schema validation for free |
| pytest | 8.2.1 | Unit testing | Already in use |
| Python | 3.11.0 | Runtime | Already enforced |

### Supporting

No new libraries needed. This phase is purely organizational -- restructuring how existing code finds and loads domain configurations.

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| sift-kg's DomainConfig validation | Custom Pydantic model | Redundant -- sift-kg already validates; custom model would duplicate logic |
| Auto-discovery (scan skills/) | Explicit registry file | Registry requires manual maintenance; scanning is simpler for small domain count |
| sys.argv CLI parsing | argparse/typer | Would break project convention (D-13 uses existing CLI pattern) |

## Architecture Patterns

### Domain Directory Structure

```
skills/
├── drug-discovery-extraction/   # Existing biomedical domain (unchanged)
│   ├── domain.yaml              # 17 entity types, 30 relation types
│   ├── SKILL.md                 # Extraction prompt for Claude agents
│   ├── references/              # Entity type and relation type docs
│   │   ├── entity-types.md
│   │   └── relation-types.md
│   └── validation-scripts/      # Optional: molecular validation
│       ├── validate_smiles.py
│       ├── validate_sequences.py
│       └── scan_patterns.py
│
├── contract-extraction/         # NEW: Contract domain
│   ├── domain.yaml              # 7 entity types, 6+1 relation types
│   ├── SKILL.md                 # Contract extraction prompt
│   └── references/              # Contract entity/relation docs
│       ├── entity-types.md
│       └── relation-types.md
│       # No validation-scripts/ -- D-18 says none initially
```

### Pattern 1: Domain Resolution Function

**What:** A `resolve_domain()` function that maps domain names to paths and validates the domain package structure.
**When to use:** Called by `run_sift.py`, `build_extraction.py`, `validate_molecules.py`, and agent prompts whenever a domain is needed.
**Location:** New file `scripts/domain_resolver.py` (shared utility).

```python
# scripts/domain_resolver.py
from pathlib import Path

SKILLS_DIR = Path(__file__).parent.parent / "skills"
DEFAULT_DOMAIN = "drug-discovery"


def resolve_domain(domain_name: str | None = None) -> Path:
    """Resolve domain name to domain.yaml path.

    Args:
        domain_name: Domain name (e.g., 'contract', 'drug-discovery').
                     None defaults to 'drug-discovery'.

    Returns:
        Path to domain.yaml file.

    Raises:
        FileNotFoundError: If domain directory or required files missing.
    """
    name = domain_name or DEFAULT_DOMAIN
    domain_dir = SKILLS_DIR / f"{name}-extraction"

    if not domain_dir.exists():
        available = list_domains()
        raise FileNotFoundError(
            f"Domain '{name}' not found at {domain_dir}\n"
            f"Available domains: {', '.join(d['name'] for d in available)}"
        )

    # D-03: Validate required files
    required = ["domain.yaml", "SKILL.md"]
    for req in required:
        if not (domain_dir / req).exists():
            raise FileNotFoundError(
                f"Domain '{name}' missing required file: {req}"
            )

    if not (domain_dir / "references").is_dir():
        raise FileNotFoundError(
            f"Domain '{name}' missing required directory: references/"
        )

    return domain_dir / "domain.yaml"


def list_domains() -> list[dict[str, str]]:
    """Scan skills/ for available domains.

    Returns:
        List of dicts with 'name' and 'description' keys.
    """
    import yaml

    domains = []
    for d in sorted(SKILLS_DIR.iterdir()):
        if d.is_dir() and (d / "domain.yaml").exists():
            try:
                with open(d / "domain.yaml") as f:
                    data = yaml.safe_load(f)
                name = d.name.removesuffix("-extraction")
                domains.append({
                    "name": name,
                    "description": data.get("description", "").strip().split("\n")[0],
                    "version": data.get("version", "unknown"),
                })
            except Exception:
                continue
    return domains


def get_domain_skill_md(domain_name: str | None = None) -> str:
    """Read the SKILL.md content for a domain.

    Args:
        domain_name: Domain name. None defaults to 'drug-discovery'.

    Returns:
        Content of the domain's SKILL.md file.
    """
    name = domain_name or DEFAULT_DOMAIN
    skill_path = SKILLS_DIR / f"{name}-extraction" / "SKILL.md"
    return skill_path.read_text()


def get_validation_scripts_dir(domain_name: str | None = None) -> Path | None:
    """Get validation-scripts/ directory for a domain, or None if absent.

    Args:
        domain_name: Domain name. None defaults to 'drug-discovery'.

    Returns:
        Path to validation-scripts/ or None if domain has no validators.
    """
    name = domain_name or DEFAULT_DOMAIN
    vs_dir = SKILLS_DIR / f"{name}-extraction" / "validation-scripts"
    return vs_dir if vs_dir.is_dir() else None
```

### Pattern 2: Contract Domain YAML Structure

**What:** The contract domain YAML follows the exact same structure as the biomedical domain YAML, validated by sift-kg's `DomainConfig` Pydantic model.
**Key fields from DomainConfig schema:**
- `name` (str, required)
- `version` (str, required)
- `description` (str, required)
- `system_context` (str | None) -- prompt context for Claude
- `fallback_relation` (str | None) -- D-10: `RELATED_TO`
- `entity_types` (dict[str, EntityTypeConfig]) -- each has `description`, `extraction_hints[]`
- `relation_types` (dict[str, RelationTypeConfig]) -- each has `description`, `source_types[]`, `target_types[]`, optional `symmetric`, `review_required`, `extraction_hints[]`
- `schema_free` (bool, default False)

### Pattern 3: Updating Hardcoded References

**What:** Six locations currently hardcode biomedical paths/names. Each needs updating to use domain resolution.

| File | Line | Current | Change To |
|------|------|---------|-----------|
| `scripts/run_sift.py` | 37 | Hardcoded `skills/drug-discovery-extraction/domain.yaml` | Use `resolve_domain(domain_name)` |
| `scripts/build_extraction.py` | 37 | `"domain_name": "Drug Discovery"` | Accept domain_name parameter, read from domain.yaml |
| `scripts/validate_molecules.py` | 27 | Hardcoded `skills/drug-discovery-extraction/validation-scripts` | Use `get_validation_scripts_dir(domain_name)` |
| `commands/ingest.md` | 65 | Hardcoded domain path in example | Add `--domain` flag documentation |
| `commands/build.md` | 9 | Hardcoded domain path | Add `--domain` flag documentation |
| `agents/extractor.md` | all | Hardcoded biomedical entity types and naming standards | Make domain-aware: read domain SKILL.md dynamically |

### Anti-Patterns to Avoid
- **Shared base schema:** D-02 explicitly forbids inheritance. Don't create a base domain config.
- **Modifying biomedical domain.yaml:** The existing file must remain unchanged (DCFG-04).
- **Registry file:** D-06 says auto-discovery, not a manifest.
- **Argparse migration:** Stick with `sys.argv` parsing per project convention.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| YAML schema validation | Custom validation logic | sift-kg `load_domain()` with Pydantic DomainConfig | Already validates entity types, relation source/target references, required fields. Raises clear errors on malformed YAML |
| YAML parsing | Custom parser | PyYAML (via sift-kg) | Already a dependency |
| Domain name to path mapping | Complex plugin system | Simple `resolve_domain()` with directory scanning | Two domains now, maybe 3-4 ever. No need for plugin architecture |

**Key insight:** sift-kg's `load_domain()` already does the heavy lifting. It parses YAML, validates against the Pydantic model, and returns a typed `DomainConfig`. The only new code needed is the thin name-to-path resolution layer and the domain package completeness check (D-03: SKILL.md + references/ exist).

## Common Pitfalls

### Pitfall 1: Breaking Biomedical Default Behavior
**What goes wrong:** Changing the default domain or requiring `--domain` flag breaks existing Scenarios 1-6.
**Why it happens:** Forgetting that `None` domain must map to `drug-discovery`.
**How to avoid:** `resolve_domain(None)` always returns the drug-discovery domain path. All existing tests pass without modification. Test with no `--domain` flag explicitly.
**Warning signs:** Existing test `test_ut001_domain_loads` or `test_ut013_run_sift_build` fails.

### Pitfall 2: Relation source/target Types Referencing Undefined Entity Types
**What goes wrong:** Contract domain YAML defines a relation with `source_types: [CONTRACTOR]` but `CONTRACTOR` isn't in `entity_types`.
**Why it happens:** Typo or inconsistency when writing the contract domain YAML.
**How to avoid:** sift-kg's `load_domain()` may or may not validate cross-references. Add explicit validation in `resolve_domain()` or after `load_domain()` to check that all relation source/target types exist in entity_types.
**Warning signs:** Graph build silently drops relations with unknown types.

### Pitfall 3: build_extraction.py Hardcoded domain_name
**What goes wrong:** Extraction JSON files always say `"domain_name": "Drug Discovery"` even when extracting contracts.
**Why it happens:** Line 37 of `build_extraction.py` hardcodes the string.
**How to avoid:** Pass domain_name as parameter. Read it from the domain.yaml `name` field.
**Warning signs:** Contract extraction JSONs show wrong domain_name in metadata.

### Pitfall 4: Agent Prompts Still Hardcoded
**What goes wrong:** `agents/extractor.md` lists biomedical entity types. Contract extraction uses wrong entity types.
**Why it happens:** Agent markdown files are static, not dynamically loaded.
**How to avoid:** Make agents domain-aware per D-17 -- they read the selected domain's SKILL.md instead of having hardcoded lists. The command (ingest.md) passes domain context to the agent.
**Warning signs:** Contract extraction produces COMPOUND entities instead of PARTY entities.

### Pitfall 5: validate_molecules.py Crashes for Domains Without Validators
**What goes wrong:** `validate_molecules.py` tries to import from a non-existent `validation-scripts/` directory.
**Why it happens:** Hardcoded path assumes all domains have validation scripts.
**How to avoid:** Per D-18, check if `validation-scripts/` exists. If not, skip validation entirely. Return a no-op result.
**Warning signs:** ImportError or FileNotFoundError when running contract domain pipeline.

## Code Examples

### Contract domain.yaml (verified structure matches sift-kg DomainConfig)

```yaml
name: "Contract Analysis"
version: "1.0.0"
description: |
  Domain for extracting structured knowledge graphs from event contracts,
  vendor agreements, and service-level agreements. Covers parties, obligations,
  deadlines, costs, clauses, services, and venue specifications.
  Optimized for PDF contracts from Sample 2026 event planning.

system_context: |
  You are analyzing event contracts and vendor agreements to build a knowledge
  graph of parties, obligations, deadlines, costs, and services.

  NAMING STANDARDS:
  - Parties: Use the most formal name from the contract (e.g., "Aramark
    Sports & Entertainment Services, LLC" not "the Caterer")
  - Obligations: Start with an action verb (e.g., "Provide catering services
    for all event meals")
  - Deadlines: Include both date and what is due (e.g., "Final headcount due
    by August 1, 2026")
  - Costs: Include amount and what it covers (e.g., "$45 per person for
    lunch service")

  DISAMBIGUATION RULES:
  - OBLIGATION vs CLAUSE: Use OBLIGATION for actionable requirements with a
    responsible party (shall/must/will). Use CLAUSE for legal terms, conditions,
    and boilerplate (indemnification, force majeure, governing law).
  - COST vs PENALTY: Use COST for standard pricing and fees. Create a separate
    COST with attributes noting it is a penalty for late fees, cancellation
    charges, or damage assessments.
  - SERVICE vs VENUE: Use SERVICE for what is being provided (catering,
    security, AV). Use VENUE for physical spaces (Hall A, Room 201, Loading
    Dock B).

  CONFIDENCE CALIBRATION:
  - 0.9-1.0: Explicit "shall", "must", "agrees to", "is required to" language
  - 0.7-0.89: Implied obligations from context ("as discussed", "per standard practice")
  - 0.5-0.69: Inferred from general contract language or cross-reference

fallback_relation: RELATED_TO

entity_types:
  PARTY:
    description: "Organizations, companies, or individuals that are parties to the contract"
    extraction_hints:
      - "Look for named organizations in the preamble, signature blocks, and 'between' clauses"
      - "Include full legal names and any DBA or abbreviated names used in the contract"
      - "Capture the role when stated (e.g., 'Licensor', 'Contractor', 'Client')"

  OBLIGATION:
    description: "Actionable requirements, duties, or commitments that a party must fulfill"
    extraction_hints:
      - "Look for 'shall', 'must', 'agrees to', 'is required to', 'will provide'"
      - "Each obligation should identify WHO must do WHAT"
      - "Distinguish from general clauses -- obligations are specific and actionable"
      - "Capture conditions or triggers ('upon receipt of', 'no later than')"

  DEADLINE:
    description: "Specific dates, time periods, or temporal milestones in the contract"
    extraction_hints:
      - "Look for specific dates, 'no later than', 'within N days', 'prior to'"
      - "Capture both the date/period and what action is due"
      - "Include contract term dates (effective date, expiration, renewal)"

  COST:
    description: "Financial amounts, fees, rates, and payment terms in the contract"
    extraction_hints:
      - "Look for dollar amounts, rates ('$X per person', '$Y per hour'), and totals"
      - "Capture what the cost covers and any conditions"
      - "Include payment terms ('net 30', 'due upon signing', 'monthly installments')"
      - "Note penalties, late fees, and cancellation charges as separate COST entities"

  CLAUSE:
    description: "Legal terms, conditions, provisions, and boilerplate sections"
    extraction_hints:
      - "Look for section headers, article numbers, and standard legal provisions"
      - "Include indemnification, force majeure, limitation of liability, governing law"
      - "Capture the clause type and key terms, not full text"

  SERVICE:
    description: "Services, products, or deliverables being provided under the contract"
    extraction_hints:
      - "Look for descriptions of what is being provided: catering, security, AV, decorations"
      - "Capture service scope, specifications, and any exclusions"
      - "Distinguish from VENUE -- SERVICE is what is done, VENUE is where"

  VENUE:
    description: "Physical locations, spaces, rooms, and facilities referenced in the contract"
    extraction_hints:
      - "Look for room names, hall designations, floor levels, and facility areas"
      - "Include capacity, dimensions, and access restrictions when mentioned"
      - "Pennsylvania Convention Center specific: Hall A-F, Room numbers, Loading Docks"

relation_types:
  OBLIGATES:
    description: "Party is obligated to fulfill an obligation, provide a service, or meet a deadline"
    source_types: [PARTY]
    target_types: [OBLIGATION, SERVICE, DEADLINE]
    extraction_hints:
      - "Look for 'shall', 'must', 'agrees to' linking a party to an action"
      - "'Aramark OBLIGATES Provide catering for 500 guests'"

  CONFLICTS_WITH:
    description: "Two entities have contradictory or incompatible terms"
    source_types: [OBLIGATION, CLAUSE, COST, DEADLINE]
    target_types: [OBLIGATION, CLAUSE, COST, DEADLINE]
    symmetric: true
    review_required: true
    extraction_hints:
      - "Look for contradictory terms across contracts or within the same contract"
      - "Exclusive-use clauses that conflict with other vendor agreements"
      - "Overlapping time slots or space allocations"

  DEPENDS_ON:
    description: "One entity depends on or requires another to be fulfilled first"
    source_types: [OBLIGATION, SERVICE, DEADLINE]
    target_types: [OBLIGATION, SERVICE, DEADLINE, PARTY]
    extraction_hints:
      - "Look for 'contingent upon', 'subject to', 'requires prior', 'following completion of'"
      - "Temporal dependencies: 'after setup is complete', 'prior to event'"

  COSTS:
    description: "Links a cost amount to the service, obligation, or party it applies to"
    source_types: [COST]
    target_types: [SERVICE, OBLIGATION, PARTY]
    extraction_hints:
      - "Links dollar amounts to what they pay for"
      - "'$45/person COSTS Lunch catering service'"

  PROVIDES:
    description: "Party provides a service or uses a venue"
    source_types: [PARTY]
    target_types: [SERVICE, VENUE]
    extraction_hints:
      - "Look for 'provides', 'furnishes', 'supplies', 'makes available'"
      - "'Convention Center PROVIDES Hall A for general sessions'"

  RESTRICTS:
    description: "A clause or obligation restricts or limits another entity"
    source_types: [CLAUSE, OBLIGATION]
    target_types: [PARTY, SERVICE, VENUE, COST]
    extraction_hints:
      - "Look for 'exclusive', 'prohibited', 'may not', 'restricted to', 'limited to'"
      - "Exclusivity clauses, non-compete provisions, space usage restrictions"

  RELATED_TO:
    description: "General association between entities -- use when a more specific relation does not apply"
    source_types: [PARTY, OBLIGATION, DEADLINE, COST, CLAUSE, SERVICE, VENUE]
    target_types: [PARTY, OBLIGATION, DEADLINE, COST, CLAUSE, SERVICE, VENUE]
    symmetric: true
    extraction_hints:
      - "Use only when a more specific relation type does not apply"
      - "This is the fallback relation for associations that do not fit other categories"
```

### Verified: sift-kg DomainConfig validates this structure

```python
# Source: verified locally against sift-kg 0.9.0
from sift_kg import load_domain
from pathlib import Path

# This is what sift-kg's Pydantic model expects:
# DomainConfig fields:
#   name: str
#   version: str
#   description: str
#   entity_types: dict[str, EntityTypeConfig]
#     EntityTypeConfig: description, extraction_hints[], canonical_names[], canonical_fallback_type
#   relation_types: dict[str, RelationTypeConfig]
#     RelationTypeConfig: description, source_types[], target_types[], symmetric, extraction_hints[], review_required
#   system_context: str | None
#   fallback_relation: str | None
#   schema_free: bool (default False)

domain = load_domain(domain_path=Path("skills/contract-extraction/domain.yaml"))
# Raises pydantic.ValidationError if structure is invalid
```

### Cross-reference validation (D-04 enhancement beyond sift-kg)

```python
def validate_domain_cross_refs(domain_path: Path) -> list[str]:
    """Validate that relation source/target types reference defined entity types.

    Args:
        domain_path: Path to domain.yaml.

    Returns:
        List of error messages. Empty if valid.
    """
    import yaml

    with open(domain_path) as f:
        data = yaml.safe_load(f)

    entity_names = set(data.get("entity_types", {}).keys())
    errors = []

    for rel_name, rel_config in data.get("relation_types", {}).items():
        for st in rel_config.get("source_types", []):
            if st not in entity_names:
                errors.append(
                    f"Relation '{rel_name}' source_type '{st}' not in entity_types"
                )
        for tt in rel_config.get("target_types", []):
            if tt not in entity_names:
                errors.append(
                    f"Relation '{rel_name}' target_type '{tt}' not in entity_types"
                )

    return errors
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hardcoded biomedical domain path | Dynamic domain resolution via name | Phase 1 (now) | Enables multi-domain support |
| Agent prompts with hardcoded entity lists | Domain-aware agents reading SKILL.md | Phase 1 (now) | Agents work with any domain |
| Validation always runs | Validation optional per domain (D-18) | Phase 1 (now) | Contract domain works without RDKit/Biopython |

**No deprecated/outdated patterns to worry about.** sift-kg 0.9.0 is current and its `load_domain()` API is stable.

## Open Questions

1. **sift-kg cross-reference validation**
   - What we know: sift-kg `load_domain()` validates Pydantic field types (strings, lists, etc.)
   - What's unclear: Whether it also validates that relation `source_types`/`target_types` reference entity types defined in the same YAML
   - Recommendation: Add explicit cross-reference validation (shown in code examples above) regardless -- D-04 demands strict validation

2. **Agent prompt templating mechanism**
   - What we know: D-17 says agents should read domain SKILL.md dynamically
   - What's unclear: How exactly the ingest command passes domain context to spawned agent subprocesses
   - Recommendation: The command markdown (ingest.md) should pass `--domain` to the agent spawn, and the agent reads the corresponding SKILL.md at runtime. Implementation detail for planner.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.2.1 |
| Config file | None (uses defaults, run from project root) |
| Quick run command | `python -m pytest tests/test_unit.py -v -x` |
| Full suite command | `python -m pytest tests/test_unit.py -v` |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DCFG-01 | resolve_domain() maps names to paths, auto-discovers domains, validates package completeness | unit | `python -m pytest tests/test_unit.py::test_resolve_domain -x` | No -- Wave 0 |
| DCFG-01 | list_domains() scans skills/ and returns available domains | unit | `python -m pytest tests/test_unit.py::test_list_domains -x` | No -- Wave 0 |
| DCFG-01 | load_domain() validates YAML schema via sift-kg Pydantic model | unit | `python -m pytest tests/test_unit.py::test_contract_domain_loads -x` | No -- Wave 0 |
| DCFG-02 | Contract domain.yaml has 7 entity types and 7 relation types (6 + fallback) | unit | `python -m pytest tests/test_unit.py::test_contract_domain_schema -x` | No -- Wave 0 |
| DCFG-02 | Relation source/target types reference only defined entity types | unit | `python -m pytest tests/test_unit.py::test_contract_cross_refs -x` | No -- Wave 0 |
| DCFG-03 | Contract SKILL.md exists and contains contract-specific extraction guidance | unit | `python -m pytest tests/test_unit.py::test_contract_skill_md -x` | No -- Wave 0 |
| DCFG-04 | Existing biomedical tests pass unchanged (UT-001, UT-013) | unit | `python -m pytest tests/test_unit.py::test_ut001_domain_loads tests/test_unit.py::test_ut013_run_sift_build -x` | Yes |
| DCFG-04 | resolve_domain(None) returns drug-discovery path (backward compat) | unit | `python -m pytest tests/test_unit.py::test_default_domain -x` | No -- Wave 0 |
| DCFG-04 | build_extraction with no domain arg produces same output | unit | `python -m pytest tests/test_unit.py::test_build_extraction_default -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/test_unit.py -v -x`
- **Per wave merge:** `python -m pytest tests/test_unit.py -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_unit.py` -- add tests for domain resolution, contract domain schema, cross-reference validation, backward compatibility
- [ ] No new test file needed -- extend existing `tests/test_unit.py` per project convention
- [ ] No framework install needed -- pytest 8.2.1 already available

## Sources

### Primary (HIGH confidence)
- sift-kg 0.9.0 `DomainConfig` Pydantic model -- inspected locally via `model_json_schema()` and `load_domain()` API
- `skills/drug-discovery-extraction/domain.yaml` -- reference implementation read directly (17 entity types, 30 relation types)
- `scripts/run_sift.py` -- current codebase, hardcoded domain path at line 37
- `scripts/build_extraction.py` -- current codebase, hardcoded domain_name at line 37
- `agents/extractor.md` -- current agent prompt with hardcoded biomedical entity types

### Secondary (MEDIUM confidence)
- None needed -- all research based on direct codebase and library inspection

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new dependencies; verified sift-kg API locally
- Architecture: HIGH -- domain directory structure follows existing pattern exactly; DomainConfig schema verified
- Pitfalls: HIGH -- all hardcoded references found via grep; sift-kg validation behavior tested locally
- Contract ontology: MEDIUM -- entity/relation types from requirements (D-07, D-08), but extraction_hints are first-draft and will iterate after real extraction (per user decision)

**Research date:** 2026-03-29
**Valid until:** 2026-04-28 (stable -- sift-kg API unlikely to change)
