# Phase 8: Domain Creation Wizard - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-03
**Phase:** 08-domain-creation-wizard
**Areas discussed:** Document analysis strategy, Schema generation quality, Epistemic rules generation, Wizard interaction flow

---

## Document Analysis Strategy

### Q1: How should the wizard analyze sample documents to discover entity/relation types?

| Option | Description | Selected |
|--------|-------------|----------|
| LLM multi-pass (Recommended) | Analyze 3-5 sample docs with Claude: Pass 1 extracts candidates, Pass 2 consolidates, Pass 3 proposes final schema | ✓ |
| Single-pass extraction | Analyze all docs in one LLM call per doc, then merge | |
| Template + refinement | Start from generic template, refine based on LLM findings | |

**User's choice:** LLM multi-pass
**Notes:** None

### Q2: How many sample documents should the wizard require?

| Option | Description | Selected |
|--------|-------------|----------|
| Minimum 2, recommend 3-5 | At least 2 for cross-document patterns, 3-5 for better coverage | ✓ |
| Exactly 1 is fine | Single doc can bootstrap schema, lower barrier | |
| Minimum 5 | Require enough for statistical coverage | |

**User's choice:** Minimum 2, recommend 3-5
**Notes:** None

### Q3: Should the wizard require a domain description from the user?

| Option | Description | Selected |
|--------|-------------|----------|
| Require brief description (Recommended) | 1-2 sentence description gives LLM context | ✓ |
| Infer from documents | Zero user input beyond file paths | |
| Interactive Q&A | 3-5 clarifying questions before analysis | |

**User's choice:** Require brief description
**Notes:** None

### Q4: What document formats should the wizard accept?

| Option | Description | Selected |
|--------|-------------|----------|
| Reuse existing Kreuzberg pipeline (Recommended) | Accept any format Kreuzberg handles | ✓ |
| PDF only | Simplify to just PDFs | |
| Text/Markdown only | Require pre-extracted text | |

**User's choice:** Reuse existing Kreuzberg pipeline
**Notes:** None

---

## Schema Generation Quality

### Q1: How polished should the generated domain.yaml be?

| Option | Description | Selected |
|--------|-------------|----------|
| Contracts-level (Recommended) | Entity types with descriptions + relation types with descriptions | ✓ |
| Drug-discovery-level | Full extraction_hints, disambiguation rules, nomenclature standards | |
| Minimal skeleton | Just type names with placeholder descriptions | |

**User's choice:** Contracts-level
**Notes:** None

### Q2: How rich should the generated SKILL.md extraction prompt be?

| Option | Description | Selected |
|--------|-------------|----------|
| Template with domain-specific sections (Recommended) | Structured SKILL.md with system_context, entity guidance, relation rules, confidence calibration | ✓ |
| Full expert prompt | Drug-discovery-level with nomenclature standards and ontology references | |
| Minimal template | Basic entity/relation lists with generic instruction | |

**User's choice:** Template with domain-specific sections
**Notes:** None

### Q3: Should the wizard generate reference docs?

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, auto-generate (Recommended) | Generate entity-types.md and relation-types.md with descriptions and examples | ✓ |
| Skip references | Only domain.yaml and SKILL.md | |
| You decide | Claude's discretion | |

**User's choice:** Yes, auto-generate
**Notes:** None

### Q4: Should the wizard generate validation scripts?

| Option | Description | Selected |
|--------|-------------|----------|
| No validation scripts (Recommended) | Too domain-specific for auto-generation | ✓ |
| Placeholder validation | Skeleton validate.py with no-op function | |
| You decide | Claude's discretion | |

**User's choice:** No validation scripts
**Notes:** None

---

## Epistemic Rules Generation

### Q1: How should the wizard generate epistemic.py rules?

| Option | Description | Selected |
|--------|-------------|----------|
| Generic template + LLM customization (Recommended) | Base template with common patterns, LLM customizes | ✓ |
| Fully LLM-generated | LLM writes from scratch | |
| Fixed generic template | Same template for every domain | |

**User's choice:** Generic template + LLM customization
**Notes:** None

### Q2: What epistemic patterns should the generic template include?

| Option | Description | Selected |
|--------|-------------|----------|
| Contradiction detection | Find conflicting entities/claims across documents | ✓ |
| Confidence calibration | Score claims by evidence strength | ✓ |
| Gap analysis | Identify missing expected entities/relations | ✓ |
| Cross-document linking | Link same entities across multiple documents | ✓ |

**User's choice:** All four patterns selected
**Notes:** None

### Q3: Should the generated epistemic.py be a working Python module or config?

| Option | Description | Selected |
|--------|-------------|----------|
| Working Python module (Recommended) | analyze_*_epistemic() function dispatched by label_epistemic.py | ✓ |
| YAML config consumed by generic engine | Declarative rules interpreted by new engine | |
| You decide | Claude's discretion | |

**User's choice:** Working Python module
**Notes:** None

### Q4: How should the LLM customize the epistemic template?

| Option | Description | Selected |
|--------|-------------|----------|
| Pattern injection (Recommended) | Template has placeholder sections for domain-specific patterns | ✓ |
| Full function rewrite | LLM rewrites each template function entirely | |
| Config parameters only | Template parameterized, LLM fills values | |

**User's choice:** Pattern injection
**Notes:** None

### Q5: Should the wizard test generated epistemic.py before finalizing?

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, dry-run validation (Recommended) | Run against small extraction to verify valid output | ✓ |
| No testing | Generate and write, user tests manually | |
| You decide | Claude's discretion | |

**User's choice:** Yes, dry-run validation
**Notes:** None

---

## Wizard Interaction Flow

### Q1: What should the overall wizard flow look like?

| Option | Description | Selected |
|--------|-------------|----------|
| Guided 3-step (Recommended) | Step 1: inputs, Step 2: review proposed schema, Step 3: approve and generate | ✓ |
| Single-shot generation | Generate everything at once | |
| Conversational refinement | Interactive back-and-forth | |

**User's choice:** Guided 3-step
**Notes:** None

### Q2: How should the user review the proposed schema?

| Option | Description | Selected |
|--------|-------------|----------|
| Show schema summary in chat (Recommended) | Formatted summary in conversation, user approves or suggests changes | ✓ |
| Write draft files for review | Write to temp location, user reads files | |
| You decide | Claude's discretion | |

**User's choice:** Show schema summary in chat
**Notes:** None

### Q3: Where should the wizard write the generated domain package?

| Option | Description | Selected |
|--------|-------------|----------|
| domains/<name>/ (Recommended) | Write directly where domain_resolver.py discovers them | ✓ |
| User-specified path | Let user choose location | |
| Output to temp, user moves | Write to temp directory | |

**User's choice:** domains/<name>/
**Notes:** None

### Q4: Should the wizard support updating an existing domain?

| Option | Description | Selected |
|--------|-------------|----------|
| Create only (Recommended) | New domains only, warn if exists | ✓ |
| Create and update | Support both creating and refining | |
| You decide | Claude's discretion | |

**User's choice:** Create only
**Notes:** None

---

## Claude's Discretion

- Multi-pass LLM prompt engineering and chunking strategy
- Exact epistemic.py base template structure
- Error handling for poor schema proposals
- Schema summary formatting for in-chat review

## Deferred Ideas

None — discussion stayed within phase scope
