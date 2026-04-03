# Adding New Domains to Epistract

## Executive Summary

Epistract supports pluggable domain configurations. Each domain is a self-contained skill directory under `skills/` that bundles a YAML schema, extraction prompts, and reference documentation. To add a new domain, create a directory following the `skills/drug-discovery-extraction/` reference implementation, define your entity and relation types, write extraction prompts, and pass `--domain <name>` when running the pipeline.

## Technical Summary

A domain package is a directory at `skills/{domain-name}-extraction/` containing three required components:

| File | Purpose | Size Reference |
|------|---------|---------------|
| `domain.yaml` | sift-kg schema — entity types, relation types, system context, extraction hints | ~19 KB (biomedical) |
| `SKILL.md` | Detailed extraction prompt for Claude agents — naming conventions, output format, per-type guidance | ~44 KB (biomedical) |
| `references/` | Quick-reference docs for entity and relation types | 2 files (biomedical) |

Optional: `validation-scripts/` for domain-specific identifier validation (e.g., SMILES for biomedical). The pipeline skips validation if this directory is absent.

The pipeline resolves `--domain contract` to `skills/contract-extraction/domain.yaml`. Default is `drug-discovery` for backward compatibility.

---

## Detailed Guide

### 1. Directory Structure

Create your domain package under `skills/`:

```
skills/{domain-name}-extraction/
├── domain.yaml              # REQUIRED: sift-kg schema
├── SKILL.md                 # REQUIRED: extraction prompt for Claude
├── references/              # REQUIRED: quick-reference docs
│   ├── entity-types.md      #   entity type summary table
│   └── relation-types.md    #   relation type summary table
└── validation-scripts/      # OPTIONAL: domain-specific validators
    └── *.py
```

The naming convention is `{domain-name}-extraction/`. The domain name (the part before `-extraction`) is what users pass to `--domain`. Examples:

- `skills/drug-discovery-extraction/` → `--domain drug-discovery`
- `skills/contract-extraction/` → `--domain contract`
- `skills/regulatory-extraction/` → `--domain regulatory`

### 2. domain.yaml — Schema Definition

This is the sift-kg domain schema. It defines what entities and relations the extraction pipeline recognizes.

**Required top-level fields:**

```yaml
name: "Your Domain Name"          # Human-readable name
version: "1.0.0"                  # Semver for documentation (not enforced)
description: |                    # Multi-line description of the domain
  What documents this domain targets,
  what knowledge it extracts.

system_context: |                 # Prompt context injected into extraction agents
  You are analyzing [domain] documents to build a knowledge graph of [concepts].

  NOMENCLATURE STANDARDS — use canonical names:
  - [Type A]: prefer [standard], e.g. [example]
  - [Type B]: prefer [standard], e.g. [example]

  DISAMBIGUATION RULES — choose the correct entity type:
  - [Type X] vs [Type Y]: [rule]

  CONFIDENCE CALIBRATION — assign confidence scores:
  - 0.9–1.0: Explicitly stated in the text with clear evidence.
  - 0.7–0.89: Strongly supported by context but not directly quoted.
  - 0.5–0.69: Inferred from indirect evidence or background knowledge.
  - Below 0.5: Speculative; flag for review.

fallback_relation: RELATED_TO     # Catch-all relation when no specific type fits

entity_types:
  # ... (see below)

relation_types:
  # ... (see below)
```

**Entity type definition:**

Each entity type is a key under `entity_types:` with these fields:

```yaml
entity_types:
  PARTY:
    description: "Organizations, individuals, or legal entities named in contracts"
    extraction_hints:
      - "Look for named parties in preambles: 'Licensee', 'Licensor', 'Vendor', 'Client'"
      - "Include parent companies and subsidiaries when referenced"
      - "Capture the legal name, not informal references"
```

Required fields per entity type:
- `description` — One sentence explaining what this type represents
- `extraction_hints` — List of 2-4 hints guiding the LLM on where and how to find these entities

**Relation type definition:**

Each relation type is a key under `relation_types:` with these fields:

```yaml
relation_types:
  OBLIGATES:
    description: "A party is obligated to perform an action or provide a service"
    source_types: [PARTY]
    target_types: [OBLIGATION]
    extraction_hints:
      - "Look for 'shall', 'must', 'agrees to', 'is required to', 'will provide'"
      - "The party is the source; the obligation is the target"
```

Required fields per relation type:
- `description` — One sentence explaining the relationship
- `source_types` — List of valid source entity types (must reference defined `entity_types`)
- `target_types` — List of valid target entity types (must reference defined `entity_types`)

Optional fields:
- `extraction_hints` — List of hints for the LLM
- `symmetric: true` — Relation applies in both directions (e.g., CONFLICTS_WITH)
- `review_required: true` — Flag for human review (safety-critical or ambiguous relations)

**Validation on load:** sift-kg validates the YAML schema when loaded. If `source_types` or `target_types` reference entity types not defined in `entity_types`, the build will fail with a clear error.

### 3. SKILL.md — Extraction Prompt

This is the detailed prompt that guides Claude agents during extraction. It's a markdown file with YAML frontmatter.

**Frontmatter (required):**

```yaml
---
name: {domain-name}-extraction
description: >
  Use when extracting entities and relations from [domain] documents.
  Activates for [document types].
version: 1.0.0
---
```

**Body structure** (follow the biomedical reference at `skills/drug-discovery-extraction/SKILL.md`):

1. **Opening paragraph** — Role description for the extraction agent. What expertise it has, what documents it processes, what output it produces.

2. **Output Format** — JSON schema for `DocumentExtraction`. This is the same across all domains:

   ```json
   {
     "entities": [
       {
         "name": "entity name",
         "entity_type": "TYPE_NAME",
         "attributes": {"key": "value"},
         "confidence": 0.95,
         "context": "exact quote from text"
       }
     ],
     "relations": [
       {
         "relation_type": "RELATION_NAME",
         "source_entity": "entity name",
         "target_entity": "entity name",
         "confidence": 0.95,
         "evidence": "exact quote from text"
       }
     ]
   }
   ```

   **Critical field names:** `entity_type` and `relation_type` — NOT `type`. The `build_extraction.py` script normalizes `type` → `entity_type`/`relation_type` as a safety net, but prompts should use the correct names.

3. **Entity Types section** — For each entity type, provide:
   - Description
   - Naming convention (what canonical form to use)
   - Key attributes to capture (flat dictionary — no nested objects)
   - Extraction hints (domain-specific guidance)

4. **Relation Types section** — For each relation type, provide:
   - Description with directionality (source → target)
   - Examples using your domain entities
   - Edge cases or disambiguation rules

5. **Confidence Calibration** — Domain-specific scoring guidance. Contracts differ from scientific literature — adapt the thresholds to your document type.

6. **Disambiguation Rules** — When two entity types could apply, which to choose and why.

### 4. references/ — Quick-Reference Documentation

Create two markdown files:

**`references/entity-types.md`** — Summary table of all entity types:

```markdown
# Entity Types Quick Reference

N entity types for the [Domain] extraction domain.

| Type | Description | Naming Standard | Key Attributes | Example |
|------|-------------|-----------------|----------------|---------|
| PARTY | Organizations or individuals | Legal name | org_type, role | Pennsylvania Convention Center |
| OBLIGATION | Required actions or deliverables | Action phrase | deadline, penalty | Provide 500 chairs by Aug 1 |
```

Include a **Disambiguation Quick Reference** table at the bottom for entity types that could be confused.

**`references/relation-types.md`** — Summary table of all relation types, grouped by category:

```markdown
# Relation Types Quick Reference

N relation types for the [Domain] extraction domain.

## [Category Name] Relations

| Relation | Source Types | Target Types | Symmetric | Review Required | Example |
|----------|-------------|--------------|-----------|-----------------|---------|
| OBLIGATES | PARTY | OBLIGATION | No | No | Aramark → Provide catering |
```

### 5. validation-scripts/ (Optional)

Domain-specific validation scripts that run post-extraction. The pipeline checks for this directory and skips validation if absent.

**When to include:**
- Your domain has identifiers with verifiable formats (e.g., SMILES strings, CAS numbers, NCT IDs)
- You want to validate extracted values against external databases or format rules

**When to skip:**
- Your domain entities are free-text (names, descriptions, clauses)
- No canonical format exists for your entity identifiers

If included, scripts should follow the pattern in `skills/drug-discovery-extraction/validation-scripts/`:
- Each script is standalone with optional dependency guards
- Returns a dict with validation status, not exceptions
- Sets availability flags at import time (e.g., `HAS_RDKIT = True`)

### 6. Integration Points

These files in the pipeline interact with domain configuration:

| File | Role | What It Does with Domain Config |
|------|------|---------------------------------|
| `scripts/run_sift.py` | Graph builder | Loads `domain.yaml` via sift-kg's `load_domain()`. Accepts `--domain <path>` flag. Defaults to `skills/drug-discovery-extraction/domain.yaml`. |
| `scripts/build_extraction.py` | Extraction writer | Writes `domain_name` field into extraction JSON (currently hardcoded to `"Drug Discovery"` — update for your domain). |
| `agents/extractor.md` | Extraction agent | Currently hardcoded to biomedical entity types and naming standards. Domain-aware agents will read the domain's `SKILL.md` instead. |
| `agents/validator.md` | Validation agent | Runs domain validation scripts if they exist. |

### 7. Testing Your Domain

1. **Validate the YAML loads:**
   ```bash
   python -c "
   from pathlib import Path
   import sys; sys.path.insert(0, 'scripts')
   from run_sift import _import_sift
   load_domain, = _import_sift(['load_domain'])
   d = load_domain(domain_path=Path('skills/{domain-name}-extraction/domain.yaml'))
   print(f'Loaded: {d.name}, {len(d.entity_types)} entity types, {len(d.relation_types)} relation types')
   "
   ```

2. **Run extraction on a test document:**
   ```bash
   # Use /epistract-ingest with --domain flag
   /epistract-ingest --domain {domain-name} --input path/to/test-doc.pdf --output ./test-output/
   ```

3. **Verify extraction output:**
   ```bash
   # Check that extractions use your entity/relation types
   python -c "
   import json
   from pathlib import Path
   for f in Path('./test-output/extractions').glob('*.json'):
       data = json.loads(f.read_text())
       types = {e['entity_type'] for e in data['entities']}
       print(f'{f.name}: {len(data[\"entities\"])} entities, types: {types}')
   "
   ```

4. **Build the graph:**
   ```bash
   python scripts/run_sift.py build ./test-output/ --domain skills/{domain-name}-extraction/domain.yaml
   ```

### 8. Checklist

Before considering a domain package complete:

- [ ] `domain.yaml` loads without error via sift-kg `load_domain()`
- [ ] Every entity type has `description` and `extraction_hints` (2-4 hints each)
- [ ] Every relation type has `description`, `source_types`, `target_types`
- [ ] All `source_types`/`target_types` reference entity types defined in `entity_types`
- [ ] `fallback_relation` is defined for uncategorizable associations
- [ ] `system_context` includes nomenclature standards, disambiguation rules, and confidence calibration
- [ ] `SKILL.md` has frontmatter (`name`, `description`, `version`)
- [ ] `SKILL.md` documents output format with `entity_type`/`relation_type` field names (not `type`)
- [ ] `SKILL.md` covers every entity type with naming convention, key attributes, and extraction hints
- [ ] `SKILL.md` covers every relation type with directionality and examples
- [ ] `references/entity-types.md` has summary table with disambiguation reference
- [ ] `references/relation-types.md` has categorized summary table
- [ ] Test extraction produces entities matching your defined types
- [ ] Graph builds successfully with your domain YAML

---

## Reference Implementation

The biomedical domain at `skills/drug-discovery-extraction/` is the canonical reference:

| Component | File | Size | Content |
|-----------|------|------|---------|
| Schema | `domain.yaml` | 19 KB | 17 entity types, 30 relation types, full system_context |
| Prompt | `SKILL.md` | 44 KB | Per-type naming conventions, attributes, extraction hints, disambiguation |
| Entity ref | `references/entity-types.md` | 3.5 KB | Summary table + disambiguation quick reference |
| Relation ref | `references/relation-types.md` | 3.3 KB | Categorized summary table with examples |
| Validation | `validation-scripts/` | 3 scripts | SMILES (RDKit), sequences (Biopython), pattern scanning (regex) |

When in doubt, read the biomedical implementation and adapt its patterns to your domain.
