# Phase 1: Domain Configuration - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-29
**Phase:** 01-domain-configuration
**Areas discussed:** Domain config structure, Contract ontology design, Domain selection mechanism, Biomedical compatibility

---

## Domain Config Structure

### Where should new domain configs live?

| Option | Description | Selected |
|--------|-------------|----------|
| Inside skills/ | Each domain is a skill directory: skills/contract-extraction/, etc. Reuses existing plugin layout. | ✓ |
| Separate domains/ directory | Top-level domains/ directory with just YAML configs. Splits domain knowledge across directories. | |
| Registry pattern | A domain-registry.yaml at project root that maps domain names to config paths. | |

**User's choice:** Inside skills/
**Notes:** None

### Should there be a shared base schema?

| Option | Description | Selected |
|--------|-------------|----------|
| Fully independent | Each domain.yaml is self-contained. No inheritance. | ✓ |
| Shared base + extensions | A base-schema.yaml defines common types. Domain YAMLs extend it. | |
| You decide | Claude picks. | |

**User's choice:** Fully independent
**Notes:** None

### Minimum required files for a new domain?

| Option | Description | Selected |
|--------|-------------|----------|
| domain.yaml only | Just YAML required. SKILL.md and validation optional. | |
| domain.yaml + SKILL.md | Both schema and prompt template required. | |
| Full package always | domain.yaml + SKILL.md + references/ — every domain must be complete. | ✓ |

**User's choice:** Full package always
**Notes:** None

### Schema validation on load?

| Option | Description | Selected |
|--------|-------------|----------|
| Strict validation | Validate YAML structure on load. Fail fast with clear error. | ✓ |
| Permissive loading | Load whatever is in YAML. Let sift-kg handle issues downstream. | |
| You decide | Claude picks. | |

**User's choice:** Strict validation
**Notes:** None

### Versioning support?

| Option | Description | Selected |
|--------|-------------|----------|
| Version field, no enforcement | Include version field for documentation. No compatibility checks. | ✓ |
| Skip versioning for v1 | Don't worry about it now. | |
| Version with migration | Version + migration path. | |

**User's choice:** Version field, no enforcement
**Notes:** None

### Domain discovery mechanism?

| Option | Description | Selected |
|--------|-------------|----------|
| Auto-discover | Scan skills/ for directories containing domain.yaml. | ✓ |
| Explicit registry | Config file lists known domains. | |
| You decide | Claude picks. | |

**User's choice:** Auto-discover
**Notes:** None

---

## Contract Ontology Design

### Entity types — 7 from requirements or refine?

| Option | Description | Selected |
|--------|-------------|----------|
| Start with 7, iterate | Use Party, Obligation, Deadline, Cost, Clause, Service, Venue. Refine after real extraction. | ✓ |
| Expand now | Add more types before extraction begins. | |
| Let me specify | User has specific list. | |

**User's choice:** Start with 7, iterate
**Notes:** None

### Relation types — 6 from requirements or refine?

| Option | Description | Selected |
|--------|-------------|----------|
| Start with 6, iterate | Use OBLIGATES, CONFLICTS_WITH, DEPENDS_ON, COSTS, PROVIDES, RESTRICTS. | ✓ |
| Expand now | Add more relations before extraction. | |
| Let me specify | User has specific list. | |

**User's choice:** Start with 6, iterate
**Notes:** None

### Extraction hints in domain.yaml?

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, detailed hints | Each entity/relation type gets extraction_hints specific to contract language. | ✓ |
| Minimal hints | Brief descriptions only. | |
| You decide | Claude structures it. | |

**User's choice:** Yes, detailed hints
**Notes:** None

### Fallback relation?

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, RELATED_TO | Generic fallback for contract associations. | ✓ |
| No fallback | Force all relations into 6 types. | |
| You decide | Claude picks. | |

**User's choice:** Yes, RELATED_TO
**Notes:** None

### Confidence calibration?

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, contract-specific | Calibrate for contract language (shall/must = 0.9+, implied = 0.7-0.89). | ✓ |
| Reuse biomedical calibration | Same thresholds, different descriptions. | |
| You decide | Claude designs calibration. | |

**User's choice:** Yes, contract-specific
**Notes:** None

### Disambiguation rules?

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, contract-specific | OBLIGATION vs CLAUSE, COST vs PENALTY, SERVICE vs VENUE. | ✓ |
| Skip for v1 | Contracts less ambiguous than biomedical. | |
| You decide | Claude adds where needed. | |

**User's choice:** Yes, contract-specific
**Notes:** None

---

## Domain Selection Mechanism

### How should users specify domain?

| Option | Description | Selected |
|--------|-------------|----------|
| Domain name flag | --domain contract. System resolves name to YAML path. | ✓ |
| Project config file | .epistract.yaml in working directory sets default domain. | |
| Both name flag + project config | Project config sets default, flag overrides. | |

**User's choice:** Domain name flag
**Notes:** None

### Default domain when no flag?

| Option | Description | Selected |
|--------|-------------|----------|
| drug-discovery | Preserve backward compatibility. | ✓ |
| No default, require flag | Always require --domain. | |
| You decide | Claude picks. | |

**User's choice:** drug-discovery
**Notes:** None

### --list-domains command?

| Option | Description | Selected |
|--------|-------------|----------|
| Yes | Scan skills/ and show available domains. | ✓ |
| No, just document it | Documentation is sufficient. | |

**User's choice:** Yes
**Notes:** None

---

## Biomedical Compatibility

### How should biomedical compatibility be handled?

| Option | Description | Selected |
|--------|-------------|----------|
| Biomedical becomes a domain config | Existing drug-discovery-extraction/ IS the biomedical domain. Pipeline learns dynamic resolution. | ✓ |
| Parallel code path | Leave biomedical untouched. Domain config is a new code path. | |
| Thin wrapper only | Add domain resolution to run_sift.py only. Don't touch agents or commands. | |

**User's choice:** Biomedical becomes a domain config
**Notes:** None

### Agents domain-aware in Phase 1?

| Option | Description | Selected |
|--------|-------------|----------|
| Domain-aware in Phase 1 | Agents read domain SKILL.md for extraction guidance. | ✓ |
| Defer to Phase 3 | Keep agents biomedical-specific until needed. | |
| You decide | Claude assesses fit. | |

**User's choice:** Domain-aware in Phase 1
**Notes:** None

### Validation scripts handling?

| Option | Description | Selected |
|--------|-------------|----------|
| Optional per domain | Validation scripts optional. Pipeline skips if none exist. | ✓ |
| Stub contract validators | Create placeholder validation scripts for contracts. | |
| Defer validation entirely | Validation stays biomedical-only. | |

**User's choice:** Optional per domain
**Notes:** None

---

## Claude's Discretion

- Implementation details of YAML validation
- Domain skill directory naming convention
- Internal domain resolution function design

## Deferred Ideas

None — discussion stayed within phase scope.
