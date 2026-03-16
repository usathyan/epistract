# Epistract Test Scenarios

## Testing Philosophy

Epistract is a tool for scientists building knowledge from primary literature. Its output informs drug discovery decisions — target selection, competitive positioning, safety signal detection. This demands a level of testing rigor normally associated with pharmaceutical software validation: **traceability, reproducibility, cross-domain generalization, and defense in depth**.

Each test scenario is not just a functional test. It is a complete end-to-end scientific evaluation: a curated corpus of real PubMed abstracts, processed through the full pipeline, with the resulting knowledge graph evaluated against domain-expert expectations. Every scenario exercises different parts of the domain schema to ensure the system generalizes rather than overfits to a single therapeutic area.

The testing process is itself a form of engineering — each run surfaces bugs, architectural insights, and design decisions that feed back into the codebase. All findings are documented with root cause analysis, fixes, and verification. See [FINDINGS.md](FINDINGS.md) for the complete engineering findings log.

---

## Test Quality Standards

| Standard | How It Is Applied |
|---|---|
| **Traceability** | Every entity/relation type traced from ontology spec → `domain.yaml` → extraction → graph → UAT. Findings traced from discovery → root cause → fix → verification. |
| **Reproducibility** | All inputs (PubMed abstracts), outputs (extractions, graphs), and evidence (screenshots) committed to the repository. Any reviewer can re-run and compare. |
| **Defense in depth** | Critical fixes employ two-layer defenses: primary (root cause) + secondary (defensive runtime normalization). No single point of failure. |
| **Cross-domain validation** | Same pipeline tested across 5 fundamentally different drug discovery domains. Validates generalization, not overfitting. |
| **Scientist-facing documentation** | Each result includes a scientific narrative evaluable by domain experts. Community labels validated against biological expectations. |
| **Living test artifacts** | Output files are committed and versioned. Regressions are detectable by comparing current output against committed baselines. |

---

## Scenarios

Five real-world drug discovery research scenarios, each backed by a curated corpus of PubMed abstracts:

| # | Scenario | Focus | Documents | Status | Nodes | Links | Communities |
|---|---|---|---|---|---|---|---|
| 1 | [PICALM / Alzheimer's](scenarios/scenario-01-picalm-alzheimers.md) | Genetic target validation | 15 | **Completed** | 149 | 457 | 6 |
| 2 | [KRAS G12C Landscape](scenarios/scenario-02-kras-g12c-landscape.md) | Competitive intelligence | 16 | **Completed** | 108 | 307 | 4 |
| 3 | [Rare Disease Therapeutics](scenarios/scenario-03-rare-disease.md) | Due diligence | 15 | Pending | — | — | — |
| 4 | [Immuno-Oncology Combinations](scenarios/scenario-04-immunooncology.md) | Checkpoint combinations | 15 | Pending | — | — | — |
| 5 | [Cardiovascular & Inflammation](scenarios/scenario-05-cardiovascular.md) | Cardiology + inflammation | 14 | Pending | — | — | — |

### Why These Five Scenarios

Each scenario is chosen to exercise a different slice of the drug discovery schema and a different scientific use case:

| Scenario | Primary Entity Types Tested | Primary Relation Types Tested | Scientific Workflow |
|---|---|---|---|
| 1. PICALM / AD | GENE, PROTEIN, PATHWAY, PHENOTYPE | IMPLICATED_IN, PARTICIPATES_IN, ENCODES | Target validation: gene → biology → disease |
| 2. KRAS G12C | COMPOUND, CLINICAL_TRIAL, SEQUENCE_VARIANT, ADVERSE_EVENT | CONFERS_RESISTANCE_TO, INHIBITS, COMBINED_WITH, EVALUATED_IN | Competitive intelligence: drugs → trials → resistance |
| 3. Rare Disease | COMPOUND, DISEASE, MECHANISM_OF_ACTION, ORGANIZATION | INDICATED_FOR, HAS_MECHANISM, DEVELOPED_BY | Due diligence: program → mechanism → indication |
| 4. Immuno-Oncology | COMPOUND, BIOMARKER, ADVERSE_EVENT, CLINICAL_TRIAL | COMBINED_WITH, CAUSES, PREDICTS_RESPONSE_TO | Combination strategy: drugs → biomarkers → safety |
| 5. Cardiovascular | COMPOUND, PROTEIN, DISEASE, REGULATORY_ACTION | TARGETS, INHIBITS, GRANTS_APPROVAL_FOR | Pipeline assessment: target → trial → approval |

Together, the five scenarios are designed to exercise all 17 entity types and all 30 relation types in the domain schema.

---

## Cumulative Results

| Metric | Scenario 1 | Scenario 2 | Combined | Target |
|---|---|---|---|---|
| Documents processed | 15 | 16 | 31 | 75+ |
| Raw entities extracted | 297 | 231 | 528 | — |
| Graph nodes (deduplicated) | 149 | 108 | 257 | — |
| Graph links | 457 | 307 | 764 | — |
| Communities detected | 6 | 4 | 10 | — |
| Entity types exercised | 10/17 (59%) | 16/17 (94%) | 17/17 (100%) | 17/17 |
| Relation types exercised | 14/30 (47%) | 17/30 (57%) | 20/30 (67%) | 30/30 |
| UATs passed | 4/4 | 5/5 | 9/9 | 18/18 |
| Critical bugs found & fixed | 2 | 1 | 3 | 0 remaining |

---

## Running Scenarios

```
/epistract-ingest tests/corpora/01_picalm_alzheimers/docs/ --output tests/corpora/01_picalm_alzheimers/output
/epistract-ingest tests/corpora/02_kras_g12c_landscape/docs/ --output tests/corpora/02_kras_g12c_landscape/output
/epistract-ingest tests/corpora/03_rare_disease/docs/ --output tests/corpora/03_rare_disease/output
/epistract-ingest tests/corpora/04_immunooncology/docs/ --output tests/corpora/04_immunooncology/output
/epistract-ingest tests/corpora/05_cardiovascular/docs/ --output tests/corpora/05_cardiovascular/output
```

For fully automated runs (no permission prompts):
```bash
claude --dangerously-skip-permissions
```

---

## Acceptance Criteria

A scenario **passes** when:

1. All documents in the corpus are processed without pipeline errors
2. The knowledge graph contains entities matching the key types for that scenario
3. The key relations from the "Expected Graph Evidence" column are present
4. Communities are detected and auto-labeled with biologically meaningful names
5. The interactive viewer shows meaningful clusters and connections
6. Cross-document entity deduplication works (same entity from multiple papers → one node)
7. Confidence scores are calibrated (primary findings > 0.8, secondary > 0.6)
8. No `entity_type`/`relation_type` field naming errors (regression check for F-001)
9. All version references are consistent (regression check for F-003)

---

## Corpus Provenance

All documents were retrieved from **PubMed** (National Library of Medicine) via the [NCBI E-utilities API](https://www.ncbi.nlm.nih.gov/books/NBK25501/) on 2026-03-16. PubMed abstracts are publicly available for research use under NLM's terms. No full-text articles, copyrighted figures, or supplementary materials are included — only abstracts and metadata.

The PubMed queries used for each corpus are documented in the individual scenario files. Results were sorted by relevance, deduplicated by PMID, and capped at 15 documents per topic.

---

## Related Documentation

- [FINDINGS.md](FINDINGS.md) — Engineering findings, bugs, root cause analysis, and systemic lessons
- [TEST_REQUIREMENTS.md](TEST_REQUIREMENTS.md) — Unit tests, functional tests, and user acceptance test specifications with traceability matrix
- [VALIDATION_RESULTS.md](VALIDATION_RESULTS.md) — Manual cross-reference checklists for extraction accuracy review
