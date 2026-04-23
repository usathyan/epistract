# Scenario 7 (V3): Clinical Trials — GLP-1 Phase 3 Landscape

**Status:** V3 validation in progress
**Run date:** 2026-04-23
**Domain:** `clinicaltrials` (new in v3.1 — 12 entity types, 10 relation types)
**Output:** [`tests/corpora/07_glp1_phase3_trials/output/`](../corpora/07_glp1_phase3_trials/output/)

---

## Purpose

Close the loop on the S6 GLP-1 narrator's recommendation:

> *"**Integrate SURPASS-2 trial data**: Add a `clinical_trial:surpass_2` node with direct `tirzepatide` vs. `semaglutide` efficacy and safety relations to close the head-to-head gap."*
> *"**Ingest retatrutide Phase 2 data**: Jastreboff et al. NEJM 2023 contains asserted efficacy and safety data for `retatrutide` that would substantially upgrade multiple prophetic nodes."*
> *"**No long-term safety data for `orforglipron` or `retatrutide`** … CVOT, renal safety, oncology signals are entirely absent."*

S6 surfaced these as coverage gaps in the **literature** corpus. S7 feeds the same space as **trial protocols** — the authoritative primary source. The new `clinicaltrials` domain extracts Trials, Interventions, Conditions, Sponsors, Outcomes, Compounds, Biomarkers, Cohorts, Populations, Phases, and Sites with Phase-based evidence grading.

## Corpus

10 Phase 3 and pivotal Phase 2/3 protocols fetched from ClinicalTrials.gov v2 API via `scripts/fetch_ct_protocols.py`:

| NCT ID | Trial Acronym | Intervention | Condition | Sponsor |
|---|---|---|---|---|
| NCT03987919 | SURPASS-2 | tirzepatide vs semaglutide | Type 2 Diabetes | Eli Lilly |
| NCT04184622 | SURMOUNT-1 | tirzepatide | Obesity / Overweight | Eli Lilly |
| NCT03548935 | STEP-1 | semaglutide | Obesity | Novo Nordisk |
| NCT03552757 | STEP-2 | semaglutide | T2D + Obesity | Novo Nordisk |
| NCT03611582 | STEP-3 | semaglutide + intensive behavioral therapy | Obesity | Novo Nordisk |
| NCT02906930 | PIONEER-1 | oral semaglutide monotherapy | T2D | Novo Nordisk |
| NCT02692716 | PIONEER-6 | oral semaglutide CV outcomes | T2D w/ CV risk | Novo Nordisk |
| NCT01720446 | SUSTAIN-6 | subcutaneous semaglutide CV outcomes | T2D w/ CV risk | Novo Nordisk |
| NCT05715307 | ACHIEVE-1 | orforglipron | T2D | Eli Lilly |
| NCT05822830 | SURMOUNT-5 | tirzepatide vs semaglutide | Obesity | Eli Lilly |

Total: **~60KB** across 10 trial records, each with structured arms/cohorts, primary/secondary outcomes, eligibility criteria, enrollment counts, and phase designations.

## How to Run

```bash
# 1. Fetch protocols (public CT.gov v2 API; writes to docs/)
python scripts/fetch_ct_protocols.py tests/corpora/07_glp1_phase3_trials

# 2. Ingest + chunk + extract (Sonnet 4.6 via OpenRouter)
python -m core.ingest_documents tests/corpora/07_glp1_phase3_trials/docs \
    --output tests/corpora/07_glp1_phase3_trials/output \
    --domain clinicaltrials
python scripts/extract_corpus.py tests/corpora/07_glp1_phase3_trials/output \
    --domain clinicaltrials --model anthropic/claude-sonnet-4.6

# 3. Normalize + build + epistemic (with narrator)
python -m core.normalize_extractions tests/corpora/07_glp1_phase3_trials/output \
    --domain clinicaltrials
python -m core.run_sift build tests/corpora/07_glp1_phase3_trials/output \
    --domain clinicaltrials
python -m core.label_epistemic tests/corpora/07_glp1_phase3_trials/output \
    --domain clinicaltrials

# 4. (Optional) Enrich via CT.gov v2 + PubChem PUG REST
python domains/clinicaltrials/enrich.py tests/corpora/07_glp1_phase3_trials/output

# 5. Explore
python -m core.run_sift view tests/corpora/07_glp1_phase3_trials/output \
    --domain clinicaltrials
python scripts/launch_workbench.py tests/corpora/07_glp1_phase3_trials/output \
    --domain clinicaltrials
```

## V3.1 Results (2026-04-23)

| Metric | Value |
|---|---:|
| Documents processed | 10 (100% Pydantic pass rate — 0 silent drops) |
| Graph nodes | **142** across **11 entity types** |
| Graph edges | **395** |
| Communities | **8** |
| Extraction cost | **$0.98** (119,658 tokens, Sonnet 4.6 via OpenRouter) |
| Extraction duration | ~13 min (10 docs, sequential) |
| `epistemic_narrative.md` | **1,197 words** |

### Entity type distribution

| Entity type | Count |
|---|---:|
| Outcome | 65 |
| Intervention | 16 |
| Cohort | 13 |
| DOCUMENT | 10 |
| Trial | 10 |
| Population | 10 |
| Condition | 6 |
| Biomarker | 5 |
| Sponsor | 3 |
| TrialPhase | 2 |
| Compound | 2 |

### Epistemic layer

| Metric | Value |
|---|---:|
| Total relations | 395 |
| `asserted` (v3 status) | 394 |
| `unclassified` (v3 status) | 1 |
| `high_evidence` (phase-tier, after `--enrich`) | **177** |
| `medium_evidence` (phase-tier, after `--enrich`) | 20 |
| `unclassified` (phase-tier, non-trial-linked) | 198 |
| Enrichment hit rate | 10/10 trials (100%), 2/2 compounds (100%) |
| Contradictions | 0 |
| Contested claims | 0 |

**Why all `asserted`, no `prophetic`?** CT.gov protocol language is largely declarative ("participants will receive X", "primary endpoint is HbA1c reduction at week 24"). Unlike patents and academic papers, trial protocols don't hedge or make forward-looking claims — they describe what the study *does*. The v3 classifier correctly reads this language as asserted.

**Why most relations are `unclassified` in the phase tier?** The graph surfaces only 2 `TrialPhase` entity nodes — Phase is captured as a *trial attribute*, not as an explicit entity connection in most cases. The narrator flags this as the highest-priority structural gap. With `--enrich`, Chris Davidson's `enrich.py` pulls `ct_phase` as a node attribute on Trial nodes, which the `_trial_phase()` helper reads — so an enriched run should move many `unclassified` to `medium_evidence` / `high_evidence`.

### How this compares to S6

| Aspect | S6 (drug-discovery literature) | S7 (clinicaltrials protocols) |
|---|---|---|
| Corpus | 34 docs (10 patents + 24 PubMed abstracts) | 10 CT.gov Phase 3 protocols |
| Nodes / Edges | 278 / 855 | 142 / 395 |
| Communities | 10 | 8 |
| Prophetic claims | 61 | 0 (correctly — protocols don't hedge) |
| Contested claims | 33 | 0 (single source per trial; no cross-protocol dissent) |
| Narrator focus | Where the claims are hedged, which patents are forward-looking, what clinical data would resolve contradictions | Entity distribution, structural gaps (phase tagging, head-to-head absence), coverage gaps in CVOT / biomarker / post-market data |

Both run through the exact same v3 pipeline with different domain personas driving both the reactive workbench chat and the proactive narrator.

See [`docs/SHOWCASE-CLINICALTRIALS.md`](../../docs/SHOWCASE-CLINICALTRIALS.md) for the full V3.1 narrative briefing and the cross-scenario narrative with S6.

## Notes

- **Persona-driven narrator.** The clinicaltrials domain ships with a workbench `template.yaml` persona that commits to Phase-based evidence grading (Phase III → high_evidence, Phase II → medium, Phase I/observational → low), NCT ID citation discipline, arm/cohort stratification, and combining phase tier with v3 epistemic status (`asserted` / `prophetic` / `contested` / etc.). Same persona drives both reactive workbench chat AND proactive `/epistract:epistemic` narrative.
- **FIDL-07 validator dispatch.** No `domains/clinicaltrials/validation/run_validation.py` ships with v3.1 — the validator hook is available if we later want to validate NCT ID shapes or PubChem CID structures.
- **FIDL-06 domain metadata.** `graph_data.json.metadata.domain = "clinicaltrials"` auto-populated by graph build; downstream consumers (workbench, graph.html) auto-detect.
