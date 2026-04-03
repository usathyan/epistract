# Phase 4: Cross-Reference Analysis - Research

**Researched:** 2026-03-30
**Domain:** Graph-based cross-contract conflict detection, coverage gap analysis, risk scoring
**Confidence:** HIGH

## Summary

Phase 4 extends the existing epistemic analysis layer (`label_epistemic.py`) to become domain-aware, adding contract-specific cross-reference analysis as the contract domain's Super Domain overlay. The core work is: (1) making `label_epistemic.py` dispatch between biomedical and contract rule sets, (2) adding `conflict_rules` to `domain.yaml`, (3) implementing four conflict detectors (exclusive-use, schedule, term, cost), (4) importing `Sample_Conference_Master.md` as reference-layer nodes for coverage gap analysis, and (5) aggregating findings into severity-scored risk items in `claims_layer.json`.

All code lives within the existing post-build overlay pattern: read `graph_data.json` -> produce analysis -> write to `claims_layer.json` + annotate graph links. No new frameworks or external dependencies required -- this is pure Python logic operating on the existing graph data structures.

**Primary recommendation:** Extend `label_epistemic.py` with a domain-dispatch architecture that loads domain-specific analysis modules. Contract analysis module implements rule-based conflict detection using `conflict_rules` from `domain.yaml`, reference-node gap analysis from Master doc, and severity-scored risk aggregation.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Cross-reference analysis IS the contract domain's epistemic layer. Conflicts = contradictions, coverage gaps = missing claims, risks = epistemic assessments. All findings go into `claims_layer.json` as Super Domain overlays -- NOT a separate output file.
- **D-02:** `label_epistemic.py` must become domain-aware. Biomedical patterns (hedging, prophetic/patent) are one domain's epistemic rules; contracts get their own (conflicts, gaps, risks, implied obligations). The script loads domain-appropriate rules.
- **D-03:** The epistemic layer captures all non-brute-fact knowledge -- tacit knowledge, learned patterns, cross-document contradictions, coverage gaps, experiential insights. This philosophy applies to ALL domains, not just contracts.
- **D-04:** Rule-based detection. Conflict rules defined in `domain.yaml` under a `conflict_rules` section. Domain-portable -- other domains can define their own conflict rules.
- **D-05:** Four conflict types: exclusive-use collisions, schedule contradictions, term contradictions, cost/budget conflicts.
- **D-06:** Conflict rules in `domain.yaml` define patterns: entity type pairs, attribute comparisons, conditions.
- **D-07:** Use `Sample_Conference_Master.md` as baseline for expected coverage. Compare what Master doc expects vs. what contracts cover.
- **D-08:** Master doc imported as reference layer nodes -- separate node type (e.g., PLANNING_ITEM or EXPECTATION) with 'reference' source tag. Visually distinct, non-authoritative.
- **D-09:** Master doc is reference context, not authoritative -- contracts override.
- **D-10:** Three severity categories: CRITICAL, WARNING, INFO.
- **D-11:** Each finding includes a brief suggested action.
- **D-12:** Risk findings aggregate from conflict detection (XREF-02), gap analysis (XREF-03), and external context (XREF-04).

### Claude's Discretion
- False positive handling approach for conflict detection (confidence scoring vs. report-all)
- Internal design of domain-aware epistemic analysis (how to dispatch between biomedical and contract rule sets)
- Specific attribute comparison logic for each conflict type
- How to extract/parse planning items from Sample_Conference_Master.md into reference nodes
- Conflict rule schema structure within domain.yaml

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| XREF-01 | System links entities that appear across multiple contracts (same party, same date, same venue space) | Cross-contract entity linking via source_documents attribute on graph nodes; entity resolution already normalizes party names (Phase 3) |
| XREF-02 | System detects conflicts between contracts (contradictory terms, overlapping exclusive-use claims, incompatible schedules) | Rule-based conflict detection using `conflict_rules` in domain.yaml; four conflict types with attribute comparison logic |
| XREF-03 | System identifies coverage gaps (expected obligations vs. what contracts cover) | Master doc reference nodes compared against contract graph; gap = expectation without matching obligation |
| XREF-04 | System flags risks based on contract terms cross-referenced with dashboard planning data | Risk aggregation from XREF-02 conflicts + XREF-03 gaps + budget/timeline cross-checks; severity scoring (CRITICAL/WARNING/INFO) |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.11+ | Runtime | Project constraint |
| NetworkX | 3.4.2 | Graph traversal for cross-contract queries | Already installed, used by sift-kg |
| PyYAML | 6.0.1 | Load conflict_rules from domain.yaml | Already installed |
| Pydantic | 2.11.7 | Validate conflict rule schemas, finding structures | Already installed |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| re (stdlib) | N/A | Pattern matching for Master doc parsing | Extracting planning items from markdown |
| collections (stdlib) | N/A | defaultdict for aggregation | Grouping findings by severity, entity |
| datetime (stdlib) | N/A | Date parsing for deadline comparisons | Schedule conflict detection |
| json (stdlib) | N/A | Read/write graph_data.json, claims_layer.json | All I/O |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Rule-based conflict detection | LLM-based conflict detection | Rules are auditable, deterministic, domain-portable; LLM adds latency and non-determinism. Rule-based is the locked decision (D-04). |
| Manual date parsing | dateutil | Only needed if date formats are highly variable; stdlib datetime.strptime should suffice for contract dates |

**Installation:** No new packages needed. All dependencies already in the project.

## Architecture Patterns

### Recommended Project Structure
```
scripts/
├── label_epistemic.py          # Extended: domain-aware dispatcher
├── epistemic_biomedical.py     # Extracted: biomedical hedging/patent rules (NEW)
├── epistemic_contract.py       # Contract cross-ref analysis (NEW)
├── domain_resolver.py          # Existing: resolves domain name -> path
├── extract_contracts.py        # Existing: orchestrator (add post-build step)
└── ...
skills/contract-extraction/
├── domain.yaml                 # Extended: add conflict_rules section
└── ...
```

### Pattern 1: Domain-Aware Dispatch
**What:** `label_epistemic.py` detects the domain from graph_data.json metadata (or CLI flag) and dispatches to the appropriate analysis module.
**When to use:** Always -- this is the core architectural change.
**Example:**
```python
# In label_epistemic.py
from domain_resolver import resolve_domain

def analyze_epistemic(output_dir: Path, domain_name: str | None = None) -> dict:
    """Run domain-appropriate epistemic analysis."""
    graph_path = output_dir / "graph_data.json"
    graph_data = json.loads(graph_path.read_text())

    # Detect domain from graph metadata or explicit flag
    if domain_name is None:
        domain_name = graph_data.get("metadata", {}).get("domain", "drug-discovery")

    if domain_name == "contract":
        from epistemic_contract import analyze_contract_epistemic
        return analyze_contract_epistemic(output_dir, graph_data)
    else:
        # Existing biomedical analysis (extract to module or keep inline)
        return _analyze_biomedical(output_dir, graph_data)
```

### Pattern 2: Rule-Based Conflict Detection
**What:** Conflict rules defined in YAML, loaded at runtime, evaluated against graph node attributes.
**When to use:** For XREF-02 conflict detection.
**Example:**
```python
# conflict_rules schema in domain.yaml
# conflict_rules:
#   exclusive_use:
#     description: "Two contracts claiming exclusive use of same space/time"
#     entity_types: [VENUE, SERVICE]
#     match_on: ["entity_type", "attributes.room_or_space"]
#     conflict_condition: "restricts_clause_exists"
#     severity: CRITICAL
#
#   schedule_contradiction:
#     description: "Incompatible deadlines across contracts"
#     entity_types: [DEADLINE]
#     match_on: ["attributes.what_is_due"]
#     conflict_condition: "dates_overlap_or_conflict"
#     severity: WARNING

def evaluate_conflict_rule(rule: dict, node_a: dict, node_b: dict) -> dict | None:
    """Evaluate a single conflict rule against two nodes from different contracts."""
    # Check entity types match rule
    # Compare attributes per match_on fields
    # Apply conflict_condition logic
    # Return finding dict or None
    ...
```

### Pattern 3: Reference Node Overlay
**What:** Master doc planning items imported as PLANNING_ITEM nodes with `source: "reference"` tag. Linked to matching contract entities for gap analysis.
**When to use:** For XREF-03 coverage gap analysis.
**Example:**
```python
def import_master_doc(master_path: Path, graph_data: dict) -> tuple[list[dict], list[dict]]:
    """Parse Master doc into reference layer nodes.

    Returns:
        Tuple of (reference_nodes, reference_links) to merge into graph.
    """
    text = master_path.read_text()
    items = parse_planning_items(text)  # Extract budgets, timelines, requirements

    ref_nodes = []
    for item in items:
        ref_nodes.append({
            "id": f"ref:{item['id']}",
            "name": item["description"],
            "entity_type": "PLANNING_ITEM",
            "source": "reference",
            "source_document": "Sample_Conference_Master",
            "attributes": item["attributes"],
            "confidence": 0.5,  # Non-authoritative
        })

    return ref_nodes, match_to_contract_entities(ref_nodes, graph_data["nodes"])
```

### Pattern 4: Post-Build Overlay (Existing Pattern)
**What:** Analysis reads graph_data.json, produces overlay, writes claims_layer.json, updates graph links.
**When to use:** This is the existing pattern from `label_epistemic.py` -- Phase 4 extends it.
**Example:**
```python
# Output structure for claims_layer.json (contract domain)
{
    "metadata": { ... },
    "summary": {
        "conflicts_found": 12,
        "gaps_found": 5,
        "risks": {"CRITICAL": 3, "WARNING": 7, "INFO": 5},
    },
    "base_domain": {
        "description": "Contractual facts -- asserted obligations, costs, deadlines",
        "relation_count": 200,
    },
    "super_domain": {
        "description": "Cross-contract epistemic layer -- conflicts, gaps, risks",
        "conflicts": [ ... ],
        "coverage_gaps": [ ... ],
        "risks": [ ... ],
    },
}
```

### Anti-Patterns to Avoid
- **Modifying biomedical behavior:** The existing biomedical epistemic analysis must continue to work unchanged. Extract it cleanly or keep it as the default path.
- **Hardcoding STA-specific logic:** Master doc parsing should be generic enough for other reference documents; STA-specific structure parsing is implementation detail in the parser, not in the framework.
- **Creating CONFLICTS_WITH relations during analysis:** The graph already has CONFLICTS_WITH as a relation type from extraction. Phase 4 analysis *detects additional conflicts* that extraction missed by comparing attributes across contracts -- these go into claims_layer.json, not as new graph edges (to preserve the graph as extraction output).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Date comparison | Custom date parser | `datetime.strptime` with known formats | Contract dates follow standard formats; parsing edge cases are minimal |
| Graph traversal | Manual adjacency lists | `NetworkX` queries on the existing MultiDiGraph | Already the graph backend; supports multi-hop queries, node attribute filtering |
| YAML conflict rule loading | Custom config parser | `PyYAML` + `Pydantic` model validation | Consistent with existing domain.yaml loading pattern |
| Entity dedup across contracts | New dedup system | Existing `source_documents` attribute on merged nodes | Phase 3 entity resolution already links cross-contract entities; nodes carry `source_documents` list |

**Key insight:** The graph already contains cross-contract entity links from Phase 3's entity resolution. Phase 4 *analyzes* these links rather than creating them from scratch. The `source_documents` attribute on merged nodes tells you which contracts reference the same entity.

## Common Pitfalls

### Pitfall 1: Breaking Biomedical Epistemic Analysis
**What goes wrong:** Refactoring `label_epistemic.py` introduces regressions in the biomedical hedging/patent analysis.
**Why it happens:** The existing code has tightly coupled biomedical patterns (HEDGING_PATTERNS, PATENT_PATTERN, etc.) with the analysis pipeline.
**How to avoid:** Extract biomedical logic to `epistemic_biomedical.py` first, verify existing tests pass, then add contract dispatch. Keep the existing `analyze_epistemic()` signature backward-compatible.
**Warning signs:** Tests UT-001 through UT-014 (biomedical) fail after refactoring.

### Pitfall 2: False Positive Conflicts
**What goes wrong:** Conflict detection reports too many false positives (e.g., two contracts mention "Hall A" but in non-conflicting contexts).
**Why it happens:** Naive entity-name matching without considering the relationship context (one contract provides Hall A, another restricts it -- that's different from two claiming exclusive use).
**How to avoid:** Conflict rules must check not just entity matches but the *relation context* (RESTRICTS clauses, exclusivity attributes, overlapping time windows). Use confidence scoring: HIGH confidence for explicit contradictions, MEDIUM for potential conflicts, LOW for informational.
**Warning signs:** More than 50% of flagged conflicts are not actionable.

### Pitfall 3: Master Doc Parsing Fragility
**What goes wrong:** `Sample_Conference_Master.md` has a specific markdown structure that changes, breaking the parser.
**Why it happens:** Hard-coupling to specific heading levels, table formats, or section names.
**How to avoid:** Parse conservatively -- extract high-level planning items (budgets, timelines, committee responsibilities) with clear section markers. Log what was/wasn't parsed. Make the parser configurable.
**Warning signs:** Parser extracts 0 items from a structurally valid document.

### Pitfall 4: claims_layer.json Schema Incompatibility
**What goes wrong:** Contract domain's claims_layer.json has a different structure than biomedical, breaking downstream consumers (Phase 5 dashboard).
**Why it happens:** Each domain adds domain-specific fields without maintaining a common schema.
**How to avoid:** Keep the top-level structure consistent across domains (`metadata`, `summary`, `base_domain`, `super_domain`). Domain-specific content goes *inside* `super_domain` with clear type discrimination (`super_domain.domain: "contract"` vs `"drug-discovery"`).
**Warning signs:** Dashboard code has to special-case every domain.

### Pitfall 5: Modifying graph_data.json Beyond Annotations
**What goes wrong:** Adding reference nodes directly to graph_data.json pollutes the extraction graph with non-contract data.
**Why it happens:** Treating reference nodes the same as extracted nodes.
**How to avoid:** Reference nodes must be clearly tagged (`source: "reference"`) and potentially stored in a separate section of graph_data.json or in claims_layer.json. The planner should decide whether reference nodes live in the graph or in the claims layer only.
**Warning signs:** Graph queries return reference data mixed with contract data without clear distinction.

## Code Examples

### Cross-Contract Entity Identification (XREF-01)
```python
# Nodes already carry source_documents from Phase 3 entity resolution
def find_cross_contract_entities(nodes: list[dict]) -> list[dict]:
    """Find entities appearing in multiple contracts."""
    cross_refs = []
    for node in nodes:
        sources = node.get("source_documents", [])
        if len(sources) > 1:
            cross_refs.append({
                "entity_id": node["id"],
                "entity_name": node.get("name", ""),
                "entity_type": node.get("entity_type", ""),
                "contracts": sources,
                "contract_count": len(sources),
            })
    return sorted(cross_refs, key=lambda x: x["contract_count"], reverse=True)
```

### Conflict Rule YAML Schema
```yaml
# Addition to skills/contract-extraction/domain.yaml
conflict_rules:
  exclusive_use:
    description: "Two contracts claiming exclusive use of same venue space"
    source_entity_type: CLAUSE
    source_attribute: "clause_type"
    source_value: "exclusivity"
    target_entity_type: VENUE
    match_attribute: "room_or_space"
    severity: CRITICAL
    suggested_action_template: "Review {source_entity} against {conflicting_entity} for exclusive-use overlap"

  schedule_conflict:
    description: "Overlapping or contradictory deadlines for same deliverable"
    entity_type: DEADLINE
    match_attribute: "what_is_due"
    compare_attribute: "date"
    conflict_condition: "dates_conflict"
    severity: WARNING
    suggested_action_template: "Reconcile deadline {entity_a} with {entity_b} -- dates conflict"

  cost_budget_mismatch:
    description: "Contract costs exceeding budget allocations"
    source_entity_type: COST
    compare_against: "reference"  # Compare with Master doc budget items
    severity: WARNING
    suggested_action_template: "Verify {cost_entity} against budget allocation in Master doc"

  term_contradiction:
    description: "Conflicting terms between contracts"
    entity_type: OBLIGATION
    match_attribute: "action"
    conflict_condition: "terms_contradict"
    severity: CRITICAL
    suggested_action_template: "Review {entity_a} vs {entity_b} for contradictory terms"
```

### Risk Finding Structure
```python
# Each finding in claims_layer.json
{
    "id": "conflict:exclusive_use:001",
    "type": "exclusive_use",
    "severity": "CRITICAL",
    "description": "Aramark exclusivity clause conflicts with outside dessert vendor agreement",
    "entities_involved": ["clause:aramark_exclusivity", "obligation:dessert_vendor_service"],
    "contracts_involved": ["aramark_catering_agreement", "sweet_treats_vendor_agreement"],
    "evidence": {
        "source_a": {"contract": "aramark_catering_agreement", "section": "Article IV, Section 4.2"},
        "source_b": {"contract": "sweet_treats_vendor_agreement", "section": "Scope of Services"},
    },
    "suggested_action": "Review Article IV, Section 4.2 of Aramark contract against Sweet Treats vendor scope",
    "confidence": 0.9,
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Monolithic epistemic analysis | Domain-dispatched analysis | Phase 4 | Enables contract domain to have its own epistemic rules |
| Biomedical-only hedging patterns | Domain-appropriate patterns per domain | Phase 4 | Contracts use conflict/gap/risk patterns instead of hedging |
| claims_layer with biomedical schema | Domain-tagged claims_layer with common structure | Phase 4 | Dashboard can render any domain's epistemic layer |

## Open Questions

1. **Master Doc Location**
   - What we know: `Sample_Conference_Master.md` lives in the separate `akka-2026-dashboard` project (per CONTEXT.md canonical refs).
   - What's unclear: Should Phase 4 copy/symlink it, or accept it as a CLI argument path?
   - Recommendation: Accept as CLI argument `--master-doc <path>`. Do not hard-code location or create cross-project dependencies.

2. **Reference Nodes in Graph vs. Claims Layer**
   - What we know: D-08 says reference nodes should be visually distinct with 'reference' source tag.
   - What's unclear: Should reference nodes be added to `graph_data.json` (for visualization) or only to `claims_layer.json` (for analysis)?
   - Recommendation: Add to `graph_data.json` with `source: "reference"` tag so they appear in visualization. Dashboard (Phase 5) can filter/style them differently.

3. **Attribute Completeness from Phase 3**
   - What we know: Phase 3 D-14 specified structured typed attributes (COST.amount, DEADLINE.date, etc.).
   - What's unclear: How consistently extraction agents populate these attributes in practice. Missing attributes degrade conflict detection quality.
   - Recommendation: Conflict detectors should gracefully handle missing attributes -- skip comparison, log as INFO-level finding ("Insufficient data for conflict check on entity X").

4. **Integration with extract_contracts.py Pipeline**
   - What we know: `extract_contracts.py` chains chunking -> merge -> resolution -> build. Epistemic analysis runs after.
   - What's unclear: Should the orchestrator call the new analysis, or keep it as a separate manual step?
   - Recommendation: Add as Step 5 in `extract_contracts.py` (after graph build, before exit). Also keep callable standalone.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.2.1 |
| Config file | none -- tests run directly |
| Quick run command | `python3 -m pytest tests/test_unit.py -x -v` |
| Full suite command | `python3 -m pytest tests/test_unit.py -v` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| XREF-01 | Cross-contract entity linking identified | unit | `python3 -m pytest tests/test_unit.py::test_ut040_cross_contract_entities -x` | Wave 0 |
| XREF-02 | Conflict detection (4 types) | unit | `python3 -m pytest tests/test_unit.py::test_ut041_conflict_detection -x` | Wave 0 |
| XREF-02 | Conflict rules load from domain.yaml | unit | `python3 -m pytest tests/test_unit.py::test_ut042_conflict_rules_yaml -x` | Wave 0 |
| XREF-03 | Coverage gap identification | unit | `python3 -m pytest tests/test_unit.py::test_ut043_coverage_gaps -x` | Wave 0 |
| XREF-04 | Risk flagging with severity | unit | `python3 -m pytest tests/test_unit.py::test_ut044_risk_scoring -x` | Wave 0 |
| ALL | Domain-aware dispatch (biomedical unchanged) | unit | `python3 -m pytest tests/test_unit.py::test_ut045_domain_dispatch -x` | Wave 0 |
| ALL | claims_layer.json contract schema | unit | `python3 -m pytest tests/test_unit.py::test_ut046_claims_layer_schema -x` | Wave 0 |
| ALL | Backward compat: biomedical tests still pass | regression | `python3 -m pytest tests/test_unit.py -x -v` | Existing |

### Sampling Rate
- **Per task commit:** `python3 -m pytest tests/test_unit.py -x -v`
- **Per wave merge:** `python3 -m pytest tests/test_unit.py -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_unit.py::test_ut040_cross_contract_entities` -- covers XREF-01
- [ ] `tests/test_unit.py::test_ut041_conflict_detection` -- covers XREF-02 (exclusive-use, schedule, term, cost)
- [ ] `tests/test_unit.py::test_ut042_conflict_rules_yaml` -- covers XREF-02 rule loading
- [ ] `tests/test_unit.py::test_ut043_coverage_gaps` -- covers XREF-03
- [ ] `tests/test_unit.py::test_ut044_risk_scoring` -- covers XREF-04
- [ ] `tests/test_unit.py::test_ut045_domain_dispatch` -- covers domain-aware dispatch
- [ ] `tests/test_unit.py::test_ut046_claims_layer_schema` -- covers output format

## Project Constraints (from CLAUDE.md)

- **Package management:** `uv` (not pip directly)
- **Linting:** `ruff check`
- **Formatting:** `ruff format`
- **Testing:** `pytest`
- **Python:** 3.11+
- **Naming:** snake_case functions, SCREAMING_SNAKE_CASE constants, descriptive variable names
- **Path handling:** `pathlib.Path` throughout, avoid os.path
- **Error handling:** Return error dicts, don't raise; optional imports with availability flags
- **JSON:** `indent=2` for all output
- **CLI pattern:** `sys.argv` with `--flag value`, no argparse
- **Imports:** Wrap optional dependencies in try/except at module level
- **Type hints:** Use `|` for Union, type hints on all function signatures

## Sources

### Primary (HIGH confidence)
- `scripts/label_epistemic.py` -- existing epistemic analysis pattern, direct extension point
- `scripts/entity_resolution.py` -- party name normalization, source_documents tracking
- `scripts/extract_contracts.py` -- pipeline orchestrator, integration point
- `scripts/domain_resolver.py` -- domain dispatch infrastructure
- `skills/contract-extraction/domain.yaml` -- existing schema, needs conflict_rules addition
- `skills/contract-extraction/references/entity-types.md` -- attribute schemas for comparison logic
- `skills/contract-extraction/references/relation-types.md` -- CONFLICTS_WITH already defined
- `tests/test_unit.py` -- test patterns (38 existing tests, UT numbering, fixture patterns)

### Secondary (MEDIUM confidence)
- `.planning/phases/03-entity-extraction-and-graph-construction/03-CONTEXT.md` -- D-07 (cross-refs as attributes), D-14 (structured typed attributes), D-15 (clause-level provenance)

### Tertiary (LOW confidence)
- None -- all findings are from direct codebase inspection

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - no new dependencies, all existing libraries
- Architecture: HIGH - extends well-understood existing patterns (label_epistemic.py, domain_resolver.py)
- Pitfalls: HIGH - based on direct code inspection of existing patterns and data structures

**Research date:** 2026-03-30
**Valid until:** 2026-04-30 (stable -- no external dependency changes expected)
