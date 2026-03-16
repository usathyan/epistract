# Epistract Test Scenarios

Five real-world drug discovery research scenarios, each backed by a curated corpus of PubMed abstracts. Each scenario tests the full epistract pipeline end-to-end: document ingestion → entity extraction → molecular validation → graph building → community detection → visualization.

**Location:** All corpora are in `tests/corpora/` within this repository.

**How to run:** Open Claude Code in the epistract project directory, then use `/epistract-ingest` with the corpus path. Each scenario page includes the exact command.

**For fully automated runs** (no permission prompts):
```bash
claude --dangerously-skip-permissions
```

---

## Scenarios

| # | Scenario | Focus | Documents | Status |
|---|---|---|---|---|
| 1 | [PICALM / Alzheimer's](scenarios/scenario-01-picalm-alzheimers.md) | Genetic target validation | 15 papers | **Completed** |
| 2 | [KRAS G12C Landscape](scenarios/scenario-02-kras-g12c-landscape.md) | Competitive intelligence | 16 papers | **Completed** |
| 3 | [Rare Disease Therapeutics](scenarios/scenario-03-rare-disease.md) | Due diligence | 15 papers | Pending |
| 4 | [Immuno-Oncology Combinations](scenarios/scenario-04-immunooncology.md) | Checkpoint combinations | 15 papers | Pending |
| 5 | [Cardiovascular & Inflammation](scenarios/scenario-05-cardiovascular.md) | Cardiology + inflammation | 14 papers | Pending |

---

## Running All Scenarios

```
/epistract-ingest tests/corpora/01_picalm_alzheimers/docs/ --output tests/corpora/01_picalm_alzheimers/output
/epistract-ingest tests/corpora/02_kras_g12c_landscape/docs/ --output tests/corpora/02_kras_g12c_landscape/output
/epistract-ingest tests/corpora/03_rare_disease/docs/ --output tests/corpora/03_rare_disease/output
/epistract-ingest tests/corpora/04_immunooncology/docs/ --output tests/corpora/04_immunooncology/output
/epistract-ingest tests/corpora/05_cardiovascular/docs/ --output tests/corpora/05_cardiovascular/output
```

After each run, use `/epistract-query` to spot-check entities:
```
/epistract-query "PICALM" --output tests/corpora/01_picalm_alzheimers/output
/epistract-query "sotorasib" --output tests/corpora/02_kras_g12c_landscape/output
/epistract-query "nivolumab" --output tests/corpora/04_immunooncology/output
```

---

## Acceptance Criteria

A scenario **passes** when:

1. All documents in the corpus are processed without errors
2. The knowledge graph contains entities matching the key types for that scenario
3. The key relations from the "Expected Graph Evidence" column are present
4. Communities are detected and auto-labeled with biologically meaningful names
5. The interactive viewer shows meaningful clusters and connections
6. Cross-document entity deduplication works (same entity from multiple papers → one node)
7. Confidence scores are calibrated (primary findings > 0.8, secondary > 0.6)

---

## Corpus Provenance

All documents were retrieved from **PubMed** (National Library of Medicine) via the [NCBI E-utilities API](https://www.ncbi.nlm.nih.gov/books/NBK25501/) on 2026-03-16. PubMed abstracts are publicly available for research use under NLM's terms. No full-text articles, copyrighted figures, or supplementary materials are included — only abstracts and metadata.

The PubMed queries used for each corpus are documented in the individual scenario files. Results were sorted by relevance, deduplicated by PMID, and capped at 15 documents per topic.

---

## Related Documentation

- [TEST_REQUIREMENTS.md](TEST_REQUIREMENTS.md) — Unit tests, functional tests, and user acceptance test specifications with traceability matrix
- [VALIDATION_RESULTS.md](VALIDATION_RESULTS.md) — Manual cross-reference checklists for extraction accuracy review
