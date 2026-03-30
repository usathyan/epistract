# Phase 4: Cross-Reference Analysis - Context

**Gathered:** 2026-03-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Enrich the epistemic layer (Super Domain) with cross-contract analysis — linking entities across contracts, detecting conflicts, identifying coverage gaps against the Master planning document, and flagging risks with severity categories. All findings output into `claims_layer.json` as Super Domain overlays, with corresponding annotations on `graph_data.json`. The analysis script (`label_epistemic.py`) becomes domain-aware so both biomedical and contract domains produce epistemic layers appropriate to their domain.

</domain>

<decisions>
## Implementation Decisions

### Epistemic Layer Architecture
- **D-01:** Cross-reference analysis IS the contract domain's epistemic layer. Conflicts = contradictions, coverage gaps = missing claims, risks = epistemic assessments. All findings go into `claims_layer.json` as Super Domain overlays — NOT a separate output file.
- **D-02:** `label_epistemic.py` must become domain-aware. Biomedical patterns (hedging, prophetic/patent) are one domain's epistemic rules; contracts get their own (conflicts, gaps, risks, implied obligations). The script loads domain-appropriate rules.
- **D-03:** The epistemic layer captures all non-brute-fact knowledge — tacit knowledge, learned patterns, cross-document contradictions, coverage gaps, experiential insights. This philosophy applies to ALL domains, not just contracts. The biomedical implementation was a starting point; contracts expand the concept.

### Conflict Detection
- **D-04:** Rule-based detection. Conflict rules defined in `domain.yaml` under a `conflict_rules` section. Domain-portable — other domains can define their own conflict rules.
- **D-05:** Four conflict types to detect:
  1. **Exclusive-use collisions** — Two contracts claiming exclusive use of the same venue space or time slot
  2. **Schedule contradictions** — Incompatible deadlines or timelines across contracts
  3. **Term contradictions** — Conflicting terms between contracts (e.g., exclusivity vs. assumed access)
  4. **Cost/budget conflicts** — Costs exceeding budget allocations, duplicate charges, contradictory pricing
- **D-06:** Conflict rules in `domain.yaml` define patterns: entity type pairs, attribute comparisons, conditions. This keeps rules transparent, auditable, and domain-portable.

### Coverage Gap Strategy
- **D-07:** Use `Sample_Conference_Master.md` as the baseline for expected coverage. Compare what the Master doc expects vs. what contracts actually cover. Gaps = expectations without matching contract obligations.
- **D-08:** Master doc imported as **reference layer nodes** — separate node type (e.g., PLANNING_ITEM or EXPECTATION) with a 'reference' source tag. Visually distinct and clearly marked as non-authoritative. Linked to matching contract entities.
- **D-09:** Master doc is reference context, not authoritative — contracts override. Gap findings reported as "Master doc expects X, no contract covers it" rather than definitive findings.

### Risk Scoring
- **D-10:** Three severity categories: **CRITICAL** (blocking conflicts, missing essential coverage), **WARNING** (potential issues, budget concerns), **INFO** (minor gaps, nice-to-have coverage). Simple, actionable, filterable in dashboard.
- **D-11:** Each finding includes a brief **suggested action** (e.g., "Review Section 4.2 of Aramark contract against PCC exclusive-use clause"). Actionable guidance for committee chairs.
- **D-12:** Risk findings aggregate from conflict detection (XREF-02), gap analysis (XREF-03), and external context cross-referencing (XREF-04).

### Claude's Discretion
- False positive handling approach for conflict detection (confidence scoring vs. report-all)
- Internal design of domain-aware epistemic analysis (how to dispatch between biomedical and contract rule sets)
- Specific attribute comparison logic for each conflict type
- How to extract/parse planning items from Sample_Conference_Master.md into reference nodes
- Conflict rule schema structure within domain.yaml

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Epistemic Layer (extend this)
- `scripts/label_epistemic.py` — Current epistemic analysis script. Must become domain-aware. Contains biomedical patterns (hedging, prophetic) that serve as reference for contract patterns.
- Eric Little's Super Domain framework — conceptual basis for the epistemic layer

### Domain Schema (add conflict_rules)
- `skills/contract-extraction/domain.yaml` — Contract domain schema. Needs `conflict_rules` section added for Phase 4.
- `skills/contract-extraction/SKILL.md` — Contract extraction prompt. May need enhancement for cross-reference extraction hints.
- `skills/contract-extraction/references/entity-types.md` — Entity type reference. Informs which entities participate in conflicts.
- `skills/contract-extraction/references/relation-types.md` — Relation type reference. CONFLICTS_WITH already defined.

### Graph Data (input to analysis)
- `scripts/run_sift.py` — sift-kg wrapper. `cmd_build()` produces `graph_data.json` that Phase 4 reads.
- `scripts/entity_resolution.py` — Entity resolution pre-processor. Party names already normalized.
- `scripts/extract_contracts.py` — End-to-end orchestrator. Phase 4 analysis runs after this pipeline.

### Coverage Gap Baseline
- External: `Sample_Conference_Master.md` from `akka-2026-dashboard` project — Master planning document with budgets, timelines, risks, committee structures. Source for reference layer nodes.

### Prior Phase Context
- `.planning/phases/03-entity-extraction-and-graph-construction/03-CONTEXT.md` — D-07 (cross-refs as attributes), D-14 (structured typed attributes), D-15 (clause-level provenance)

### Requirements
- `.planning/REQUIREMENTS.md` — XREF-01 through XREF-04 define Phase 4 acceptance criteria

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `scripts/label_epistemic.py` — Epistemic analysis pattern (reads graph_data.json, produces claims_layer.json, updates graph links). Direct extension point for Phase 4.
- `scripts/label_communities.py` — Community labeling pattern (reads graph_data.json, enriches nodes in-place). Shows how to annotate nodes.
- `scripts/entity_resolution.py` — Party name normalization. Cross-contract entity linking builds on resolved names.
- `scripts/domain_resolver.py` — Domain resolution. Epistemic script needs this to load domain-specific rules.
- Structured typed attributes (Phase 3 D-14) — COST.amount, DEADLINE.date, PARTY.aliases already on graph nodes. Analysis can compare these programmatically.

### Established Patterns
- Post-build overlay pattern: `label_epistemic.py` reads graph_data.json → produces overlay JSON → updates graph links
- Domain-aware scripts: `run_sift.py`, `build_extraction.py` already use `domain_resolver.py`
- CLI pattern: `sys.argv` with `--flag value`, no argparse
- Error handling: return error dicts, don't raise

### Integration Points
- `graph_data.json` — Input: built knowledge graph with entities, relations, community labels
- `claims_layer.json` — Output: enriched with cross-reference findings (conflicts, gaps, risks)
- `domain.yaml` — Input: conflict rules, entity type definitions
- `extract_contracts.py` — Orchestrator may need a post-build analysis step added
- Phase 5 dashboard reads `claims_layer.json` for risk/conflict display

</code_context>

<specifics>
## Specific Ideas

- The epistemic layer concept is broader than originally implemented — it captures ALL non-brute-fact knowledge (tacit, learned, cross-document patterns), not just hedging language. Phase 4 realizes this vision for contracts.
- The biomedical epistemic layer should eventually be expanded too (future work), but contract domain proves the expanded concept first.
- Master doc reference nodes must be visually distinct in the graph — committee chairs need to see at a glance what comes from contracts (authoritative) vs. planning docs (reference).

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 04-cross-reference-analysis*
*Context gathered: 2026-03-30*
