# Roadmap — FDA Product Labels Domain

**Project:** Epistract FDA Product Labels Domain
**Phases:** 4 | **Requirements:** 9 | **All v1 requirements covered** ✓

## Overview

| # | Phase | Goal | Requirements |
|---|-------|------|--------------|
| 1 | Domain Schema & Extraction | Define entity/relation schema and extraction prompt for FDA label knowledge | FDA-01, FDA-02, FDA-03, FDA-04 |
| 2 | API Integration & Enrichment | Wire open.fda.gov API for corpus acquisition and post-build enrichment | FDA-05, FDA-06, FDA-07 |
| 3 | Validation & End-to-End Testing | Ingest real FDA labels, build graph, verify coverage and quality | FDA-08 |
| 4 | Domain-Aware Community Labeling | Make community label generation configurable per domain via domain.yaml anchors | FDA-09 |

---

## Phase 1: Domain Schema & Extraction

**Goal:** A working `domains/fda-labels/` domain package — domain.yaml schema, SKILL.md extraction prompt, and epistemic.py analysis module — that can be loaded by Epistract's domain resolver and used to extract entities and relations from FDA product label text.

**Requirements:** FDA-01, FDA-02, FDA-03, FDA-04

**Success Criteria:**
1. `domain_resolver.py resolve_domain("fda-labels")` returns valid metadata without errors
2. `domain.yaml` defines ≥8 entity types and ≥5 relation types with descriptions
3. `SKILL.md` references FDA label section conventions (indications_and_usage, warnings, adverse_reactions, drug_interactions) and INN naming standards
4. `epistemic.py` exports `annotate_relations(graph, ...)` function with ≥3 epistemology levels
5. Domain listed in output of `domain_resolver.list_domains()`

---

## Phase 2: API Integration & Enrichment

**Goal:** A working `enrich.py` that queries open.fda.gov `/drug/label` post-build to annotate Drug nodes with label metadata, plus corpus acquisition support so users can fetch FDA label data before ingestion.

**Requirements:** FDA-05, FDA-06, FDA-07

**Success Criteria:**
1. `domains/fda-labels/enrich.py` runs without error on a graph built from FDA label extractions
2. Enrich script enriches ≥1 Drug node with open.fda.gov metadata (application_number or manufacturer name)
3. Corpus acquisition: running the acquire command with `--domain fda-labels` fetches ≥1 FDA label JSON document from open.fda.gov
4. `workbench/template.yaml` exists and defines entity_type_colors for Drug, Indication, Warning
5. `_enrichment_report.json` written to output_dir after enrichment run

---

## Phase 3: Validation & End-to-End Testing

**Goal:** Full end-to-end pipeline verified — ingest sample FDA label documents, build graph, run enrichment, confirm entity/relation coverage meets expectations.

**Requirements:** FDA-08

**Success Criteria:**
1. Pipeline runs end-to-end: `/epistract:ingest --domain fda-labels` on 3+ sample documents without errors
2. Built graph contains ≥5 Drug entities with at least 1 relation each
3. At least 1 Drug entity linked to ≥1 Indication entity and ≥1 Warning entity
4. Enrichment step completes and adds metadata to ≥1 Drug node
5. `domain_resolver.py` alias `fda_labels` and `fda` resolve to `fda-labels`

---

## Phase 4: Domain-Aware Community Labeling

**Goal:** Make community label generation configurable per domain by reading a `community_label_anchors` list from each domain's `domain.yaml`. Update `core/label_communities.py` to use anchors instead of hardcoded biomedical/contracts logic. Update `core/domain_wizard.py` to emit `community_label_anchors` for all generated domains. Re-label the fda-product-labels smoke-test graph to verify readable output.

**Requirements:** FDA-09

**Plans:** 2 plans

Plans:
- [ ] 04-01-PLAN.md — Add anchors to fda-product-labels domain.yaml, refactor label_communities.py with anchor path + backward-compat fallback, update domain_wizard.py to emit anchors
- [ ] 04-02-PLAN.md — Re-run labeler on fda-smoke-test graph and human-verify readable output

**Success Criteria:**
1. `domains/fda-product-labels/domain.yaml` contains `community_label_anchors: [DRUG_PRODUCT, ACTIVE_INGREDIENT, INDICATION, MANUFACTURER]`
2. `core/label_communities.py` reads `community_label_anchors` from domain.yaml when present; falls back to existing logic when absent
3. Community labels for fda-product-labels graph use drug/ingredient names as anchors (e.g. "Fluconazole", "Risperidone") rather than mechanism descriptions
4. `core/domain_wizard.py` generates `community_label_anchors` in domain.yaml output for all new domains
5. Existing domains (drug-discovery, contracts, clinicaltrials) produce unchanged or improved labels after the refactor

---

*Roadmap created: 2026-04-23*
