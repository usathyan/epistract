---
name: epistract-domain
description: Create a new domain package from sample documents using guided wizard
---

# /epistract:domain

Create a new domain package from sample documents. Analyzes documents via multi-pass
LLM analysis to propose a domain schema, then generates a complete domain package
(domain.yaml, SKILL.md, epistemic.py, references/) ready for the standard pipeline.

## Prerequisites

- Python environment with epistract dependencies installed
- 2-5 sample documents from the target domain (PDF, DOCX, HTML, TXT, or any format Kreuzberg supports)

## Usage

```
/epistract:domain
```

The wizard will prompt for:
1. **Domain name** -- short identifier (e.g., "real-estate", "healthcare-records")
2. **Domain description** -- 1-2 sentences describing the domain (e.g., "Real estate lease agreements between landlords and tenants")
3. **Sample document paths** -- paths to 2-5 representative documents

## Steps

### Step 1: Gather Inputs

Ask the user for:
- **Domain name**: A short, hyphenated identifier. Will become the directory name under `domains/`.
- **Domain description**: 1-2 sentences. This provides context for LLM schema discovery.
- **Sample document paths**: At least 2 documents (recommend 3-5). Accept any file format.

Validate inputs:
- Domain name must be lowercase, alphanumeric with hyphens only
- Check for domain name collision using `core/domain_wizard.py`:
  ```python
  from core.domain_wizard import check_domain_exists
  if check_domain_exists(domain_name):
      # Warn user: domain already exists. Ask to overwrite or pick new name.
  ```
- Verify all document paths exist and are readable files
- Warn if only 1 document provided (minimum 2 required)

**Input validation rules:**
- Domain name regex: `^[a-z][a-z0-9-]*[a-z0-9]$` (start with letter, end with letter/digit, hyphens allowed)
- Reject names shorter than 2 characters
- Reject names containing double hyphens (`--`)
- If a domain name collision is detected (per D-16), present options: overwrite existing or choose a new name

### Step 2: Analyze Documents and Propose Schema

Run the multi-pass LLM analysis pipeline:

```python
from core.domain_wizard import (
    read_sample_documents, build_schema_discovery_prompt,
    build_consolidation_prompt, build_final_schema_prompt
)
```

**Pass 1 -- Per-document entity/relation discovery:**
For each sample document:
1. Read text using `read_sample_documents(doc_paths)`
2. Build the discovery prompt: `build_schema_discovery_prompt(doc["text"], domain_description)`
3. Send prompt to Claude (use the Agent tool or direct LLM call)
4. Parse the JSON response to get candidate entity types and relation types

**Pass 2 -- Cross-document consolidation:**
1. Merge all Pass 1 candidates into a single list
2. Build consolidation prompt: `build_consolidation_prompt(all_candidates, domain_description)`
3. Send to Claude, get deduplicated types with canonical names

**Pass 3 -- Final schema proposal:**
1. Build final prompt: `build_final_schema_prompt(consolidated, domain_description)`
2. Send to Claude, get the final entity_types and relation_types dicts

**Present the proposed schema to the user (per D-14):**

Display a formatted schema summary in chat for review:
```
## Proposed Domain Schema: {domain_name}

### Entity Types ({count})
| Type | Description |
|------|-------------|
| TYPE_NAME | Description... |

### Relation Types ({count})
| Type | Description |
|------|-------------|
| REL_NAME | Description... |

Does this look good? Say "approved" to generate the full package, or suggest changes.
```

Wait for user approval or modifications before proceeding. If the user suggests changes:
- Add/remove/rename entity or relation types as requested
- Re-display the updated schema for confirmation
- Repeat until approved

**Elicit the analyst persona:**

Before generating epistemic parameters, ask the user for a persona paragraph. This text serves BOTH the workbench chat prompt (reactive) AND the automatic narrator that runs after `/epistract:epistemic` (proactive — produces `epistemic_narrative.md`). A good persona names a profession, describes depth of expertise, and commits to the epistemic-status vocabulary (`asserted` / `prophetic` / `hypothesized` / `contested` / `contradictions` / `negative`).

Prompt the user something like:

```
Who should the workbench/narrator behave as for this domain?
- Profession / title (e.g., "senior drug discovery competitive intelligence
  analyst", "procurement contracts analyst", "ESG investment researcher")
- Depth signals (what body of knowledge do they draw on?)
- Formatting preferences (tables? inline citations?)

Paste a paragraph, or type "default" to use the analyst-shaped template.
```

If the user types "default" or provides nothing, pass `persona=None` to
`generate_domain_package()` — the wizard will emit the analyst-shaped
default template that includes epistemic-status vocabulary automatically.

### Step 3: Generate Domain Package

After user approves the schema and persona:

**Generate epistemic parameters:**
1. Collect short text excerpts from each sample document (first ~500 chars each)
2. Build epistemic prompt: `build_epistemic_prompt(entity_types, relation_types, domain_description, sample_excerpts)`
3. Send to Claude to get contradiction_pairs, gap_target_types, confidence_thresholds

**Generate all package files:**
```python
from core.domain_wizard import (
    generate_domain_yaml, generate_skill_md, generate_epistemic_py,
    generate_reference_docs, validate_generated_epistemic, write_domain_package
)

# Build system context from domain description
system_context = f"You are analyzing {domain_description}."

# Build extraction guidelines from entity/relation types
extraction_guidelines = (
    f"Extract all {', '.join(entity_types.keys())} entities and "
    f"{', '.join(relation_types.keys())} relations from the text."
)

# Generate each artifact
domain_yaml = generate_domain_yaml(
    domain_name, domain_description, system_context,
    entity_types, relation_types
)
skill_md = generate_skill_md(
    domain_name, system_context, entity_types,
    relation_types, extraction_guidelines
)

domain_slug = domain_name.replace("-", "_")
epistemic_py = generate_epistemic_py(
    domain_slug, entity_types, contradiction_pairs,
    gap_target_types, confidence_thresholds
)

# Validate epistemic.py before writing (per D-12)
validation = validate_generated_epistemic(epistemic_py, domain_slug)
if not validation["valid"]:
    # Report the error and retry with error context
    # Retry up to 2 times, re-generating epistemic_py with error feedback
    for attempt in range(2):
        # Re-generate with error context added to prompt
        epistemic_py = generate_epistemic_py(
            domain_slug, entity_types, contradiction_pairs,
            gap_target_types, confidence_thresholds
        )
        validation = validate_generated_epistemic(epistemic_py, domain_slug)
        if validation["valid"]:
            break
    if not validation["valid"]:
        # Warn user that epistemic validation failed; package will still be created
        # but epistemic.py may need manual fixes
        pass

entity_types_md, relation_types_md = generate_reference_docs(entity_types, relation_types)

# Write the complete package to domains/<name>/
domain_dir = write_domain_package(
    domain_name, domain_yaml, skill_md, epistemic_py,
    entity_types_md, relation_types_md
)
```

**Report success:**
```
Domain package created at: domains/{domain_name}/
Files generated:
- domain.yaml -- {N} entity types, {M} relation types
- SKILL.md -- extraction guidelines for Claude agents
- epistemic.py -- domain-specific epistemic analysis
- references/entity-types.md -- entity type documentation
- references/relation-types.md -- relation type documentation

Your domain is ready! Try it with:
  /epistract:ingest /path/to/documents --domain {domain_name}
```

## Error Handling

- **Document read failures**: Skip unreadable files, warn user, continue if >= 2 readable remain
- **LLM returns invalid JSON**: Retry the prompt once with explicit JSON format instructions
- **Epistemic validation fails**: Retry generation with the error message as context (up to 2 retries)
- **Domain name collision**: Ask user to overwrite or choose new name (per D-16)
- **Fewer than 2 documents**: Error with message "At least 2 sample documents required (3-5 recommended)"

## Schema Bypass (--schema)

For users with an established ontology (e.g., axmp-compliance domains with pre-defined entity/relation types), the wizard supports a deterministic, LLM-free bypass:

```bash
python -m core.domain_wizard --schema my_schema.json --name my-domain
```

This flag skips the 3-pass LLM discovery entirely (see `docs/known-limitations.md §Wizard & CLI Ergonomics (FIDL-08)`) and generates a domain package directly from the user-supplied JSON schema.

### When to use

- You have an established ontology and want reproducible, byte-deterministic domain creation.
- You want to avoid LLM costs and non-determinism during domain setup.
- You are automating domain creation (CI, batch provisioning).

### Schema shape

**Required top-level keys** (both must be non-empty dicts):
- `entity_types`: `{"<TYPE_NAME>": {"description": "..."}}` — map of entity type name to metadata.
- `relation_types`: `{"<REL_NAME>": {"description": "..."}}` — map of relation type name to metadata.

**Optional top-level keys** (sensible defaults applied):
- `description` — domain description for `domain.yaml`; default `""`.
- `system_context` — system prompt for extraction agents; default `"Domain extraction pipeline"`.
- `extraction_guidelines` — extraction instructions; default `"Follow domain schema."`.
- `contradiction_pairs` — epistemic contradiction pairs; default `[]`.
- `gap_target_types` — gap detection targets; default `{}`.
- `confidence_thresholds` — confidence cutoffs; default `{"high": 0.9, "medium": 0.7, "low": 0.5}`.
- `persona` — analyst persona paragraph(s) used by BOTH the workbench chat prompt AND the automatic narrator in `/epistract:epistemic`. When omitted, the wizard emits an analyst-shaped default template with the domain name substituted. For best narrator quality, supply a domain-specific persona that names a profession, describes expertise depth, and commits to the epistemic-status vocabulary (`asserted` / `prophetic` / `hypothesized` / `contested` / `contradictions` / `negative`).

**Required CLI flags:**
- `--schema <file.json>` — path to the JSON schema file.
- `--name <slug>` — domain name (used as directory name under `domains/`). Passed through `generate_slug` for normalization.

### Example

```json
{
  "entity_types": {
    "PARTY": {"description": "A legal entity in the contract."},
    "OBLIGATION": {"description": "A duty one party owes another."}
  },
  "relation_types": {
    "HAS_OBLIGATION": {"description": "Links a PARTY to an OBLIGATION."}
  },
  "description": "Contract obligations domain.",
  "system_context": "You are analyzing vendor contracts.",
  "extraction_guidelines": "Extract all PARTY and OBLIGATION entities.",
  "persona": "You are a senior procurement contracts analyst. When answering questions or producing a briefing, call out epistemic status (asserted / prophetic / hypothesized / contested / contradictions), synthesize across contracts, surface coverage gaps, and cite source contracts inline by ID. Use markdown tables for cross-contract comparisons."
}
```

### No LLM guarantee

When `--schema` is passed, the wizard does NOT import or call LiteLLM at any point. Domain creation is pure Python + filesystem I/O. See `docs/known-limitations.md §Wizard & CLI Ergonomics (FIDL-08)` for the full contract.

## Notes

- Generated packages target contracts-level quality (entity/relation types with descriptions). For richer schemas (extraction_hints, nomenclature rules), manually edit the generated files.
- No validation scripts are generated -- add domain-specific validators manually if needed.
- This command creates only. To update an existing domain, edit its files directly.
- The domain_resolver will auto-discover the generated domain package immediately after creation.
