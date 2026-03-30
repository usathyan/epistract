# Phase 4: Cross-Reference Analysis - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-30
**Phase:** 04-cross-reference-analysis
**Areas discussed:** Analysis output format, Conflict detection rules, Coverage gap strategy, Risk scoring approach

---

## Analysis Output Format

| Option | Description | Selected |
|--------|-------------|----------|
| Analysis layer file | Standalone cross_references.json + graph annotations | |
| Graph-only annotations | Enrich graph_data.json in-place only | |
| Structured report + graph | Markdown report AND JSON overlay | |

**User's choice:** None of the above — user clarified that cross-reference analysis should BE the epistemic layer output (claims_layer.json), not a separate file.

**Follow-up: How should cross-reference analysis relate to the epistemic layer?**

| Option | Description | Selected |
|--------|-------------|----------|
| Contract epistemic layer | Cross-reference IS the contract domain's epistemic layer | |
| Separate analysis layer | Keep epistemic and cross-reference separate | |
| Unified with extensions | Extend claims_layer.json with both | |

**User's choice:** The epistemic layer was always intended to capture ALL non-brute-fact knowledge (tacit, learned, cross-document patterns). Cross-reference analysis fits naturally as the contract domain's epistemic layer. The biomedical implementation was a starting point; this expands the concept. Skills will need to be enhanced to extract and perform cross-document analysis and add findings into this layer as a Super Domain.

---

## Conflict Detection Rules

| Option | Description | Selected |
|--------|-------------|----------|
| Rule-based detection | Explicit conflict rules in domain schema | ✓ |
| LLM-assisted detection | Claude reasons about potential conflicts | |
| Hybrid: rules + LLM review | Rules first, then LLM for edge cases | |

**User's choice:** Rule-based detection (Recommended)

**Follow-up: Conflict types to detect (multi-select)**

| Option | Description | Selected |
|--------|-------------|----------|
| Exclusive-use collisions | Same venue space/time claimed by multiple contracts | ✓ |
| Schedule contradictions | Incompatible deadlines/timelines across contracts | ✓ |
| Term contradictions | Conflicting terms between contracts | ✓ |
| Cost/budget conflicts | Costs exceeding budgets, duplicate charges | ✓ |

**User's choice:** All four conflict types selected.

**Follow-up: How should conflicts be defined in the domain schema?**

| Option | Description | Selected |
|--------|-------------|----------|
| Conflict rules in domain.yaml | Add conflict_rules section to domain.yaml | ✓ |
| Hardcoded in analysis script | Rules in Python script | |
| Separate conflict config | Dedicated conflict_rules.yaml | |

**User's choice:** Conflict rules in domain.yaml

**Follow-up: False positive handling**

| Option | Description | Selected |
|--------|-------------|----------|
| Confidence scoring | 0-1 score per conflict, threshold filtering | |
| Report all, flag uncertain | All reported, uncertain ones flagged | |
| You decide | Claude picks best approach | ✓ |

**User's choice:** You decide

---

## Coverage Gap Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Master doc as baseline | Sample_Conference_Master.md as expected coverage source | ✓ |
| Category-based checklist | Expected coverage per contract category | |
| Contract-only analysis | Only analyze gaps within contracts | |

**User's choice:** Master doc as baseline (Recommended)

**Follow-up: How should Master doc be ingested?**

| Option | Description | Selected |
|--------|-------------|----------|
| Reference layer nodes | Separate node type with 'reference' tag, visually distinct | ✓ |
| Extraction comparison only | Don't add to graph, compare externally | |
| You decide | Claude picks best approach | |

**User's choice:** Reference layer nodes

---

## Risk Scoring Approach

| Option | Description | Selected |
|--------|-------------|----------|
| Severity categories | CRITICAL / WARNING / INFO | ✓ |
| Numeric risk score | Composite 0-100 score | |
| Multi-dimensional | Score across financial, timeline, safety, likelihood | |

**User's choice:** Severity categories (Recommended)

**Follow-up: Should findings include recommended actions?**

| Option | Description | Selected |
|--------|-------------|----------|
| Findings only | Report what was found, no recommendations | |
| Findings + suggestions | Brief suggested action per finding | ✓ |
| You decide | Claude picks | |

**User's choice:** Findings + suggestions

---

## Claude's Discretion

- False positive handling approach for conflict detection
- Internal design of domain-aware epistemic analysis dispatch
- Specific attribute comparison logic per conflict type
- How to parse Sample_Conference_Master.md into reference nodes
- Conflict rule schema structure within domain.yaml

## Deferred Ideas

None — discussion stayed within phase scope.
