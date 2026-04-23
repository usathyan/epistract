# Showcase — Clinical Trials GLP-1 Phase 3 Landscape

A 10-document corpus of ClinicalTrials.gov Phase 3 / pivotal trial protocols for GLP-1 receptor agonists (SURPASS, SURMOUNT, STEP, PIONEER, SUSTAIN, ACHIEVE series). Built end-to-end with the v3.1 pipeline and the new `clinicaltrials` domain on 2026-04-23. Outputs and the narrator briefing are committed under `tests/corpora/07_glp1_phase3_trials/output/`.

## Try it yourself

```bash
python scripts/launch_workbench.py tests/corpora/07_glp1_phase3_trials/output \
    --domain clinicaltrials
```

Open http://127.0.0.1:8000. Ask the chat panel:

- *"Compare the primary endpoints of SURPASS-2 vs SUSTAIN-6."*
- *"Which trials have high-evidence outcomes for `tirzepatide` vs `semaglutide` in obesity?"*
- *"What arms and cohorts does SURMOUNT-1 have, and what's the enrollment per arm?"*
- *"Are there coverage gaps — missing long-term safety data, absent confirmatory trials, incomplete CVOT integration?"*

The chat panel is grounded in the same graph + claims layer that produced the narrative below. The clinicaltrials persona commits to Phase-based evidence grading — `high_evidence` for Phase III randomized double-blind trials with ≥300 enrollment, `medium_evidence` for Phase II, `low_evidence` for Phase I / observational / single-arm / early-termination.

## Why this showcase matters

The S6 GLP-1 narrator flagged specific gaps in the **literature** corpus and recommended follow-ups:

> *"Integrate SURPASS-2 trial data: Add a clinical_trial:surpass_2 node with direct tirzepatide vs semaglutide efficacy and safety relations to close the head-to-head gap."*
>
> *"No long-term safety data for orforglipron or retatrutide: Phase 3 trial references exist but cardiovascular outcome trials (CVOT), renal safety, and oncology signals are entirely absent."*
>
> *"PIONEER oral semaglutide trial integration is incomplete."*

S7 is the answer. Same molecular targets, same companies, but instead of patents + PubMed abstracts (S6), the source is **authoritative trial protocols from ClinicalTrials.gov** — the data that settles the gaps S6 identified.

## V3.1 numbers (2026-04-23)

| Metric | V3.1 (Sonnet 4.6) |
|---|---:|
| Documents | 10 (CT.gov Phase 3 / pivotal protocols) |
| Extraction pass rate | 100% (10 / 10 Pydantic-validated, 0 silent drops) |
| Extraction cost | $0.98 |
| Extraction duration | ~13 min (sequential, Sonnet 4.6 via OpenRouter) |
| Nodes | 142 |
| Edges | 395 |
| Entity types | 11 (Trial, Intervention, Condition, Sponsor, Outcome, Compound, Biomarker, Cohort, Population, TrialPhase, DOCUMENT) |
| Communities | 8 |
| Trials captured | 10 (100% — every NCT anchored) |
| Interventions (drug arms) | 16 |
| Compounds | 2 |
| Outcomes (primary + secondary) | 65 |
| Cohorts | 13 |
| Populations | 10 |
| Biomarkers | 5 |
| `asserted` relations (v3 status) | 394 |
| `unclassified` relations (v3 status) | 1 |
| `high_evidence` relations (phase-tier) | 177 (after `--enrich`) |
| `medium_evidence` relations (phase-tier) | 20 (after `--enrich`) |
| `unclassified` relations (phase-tier) | 198 (not connected to Trial nodes) |
| Enrichment hit rate | 10/10 trials (100%), 2/2 compounds (100%) |
| Contradictions | 0 |
| Contested claims | 0 |
| `metadata.domain` | `clinicaltrials` |
| `epistemic_narrative.md` | 1,197 words |

### What the numbers say

**Outcome-heavy, intervention-light.** 65 Outcome nodes vs 16 Intervention nodes. CT.gov protocols are exhaustive about endpoint definitions (primary, secondary, time frames, populations) — the extractor captured this faithfully. The 6.5-to-1 outcome-to-intervention ratio is the biggest feature of the graph.

**Cohort and population stratification is richly captured.** 13 Cohort nodes + 10 Population nodes across 10 trials means the arm-level structure is visible — SURMOUNT-1's 4 active arms (5/10/15mg tirzepatide + placebo) and SURPASS-2's 4 arms (tirzepatide 5/10/15mg + semaglutide 1mg) are there. The clinicaltrials persona's arm/cohort-stratification guidance has structured data to work with.

**All 394 text-classified relations are `asserted`.** CT.gov protocol language is declarative ("participants will receive", "primary endpoint is measured at week 24") — no hedging, no prophetic patent-style forward claims, no contradictions across this corpus (single-source per trial). The v3 classifier correctly reads this as asserted. This is the right answer for trial protocols, and it contrasts cleanly with S6 where 61 prophetic claims surfaced from the same molecular space viewed through patents + literature.

**Phase tagging is a structural gap — resolved via `--enrich`.** Pre-enrichment, only 2 `TrialPhase` entity nodes were extracted for 10 trials (the extractor captured Phase as an attribute rather than a standalone entity). Phase-tier grading defaulted to `medium_evidence` (197) and `unclassified` (198). **After running `domains/clinicaltrials/enrich.py`**, all 10 Trial nodes now carry `ct_phase: PHASE3` from the CT.gov v2 API, plus `ct_enrollment`, `ct_overall_status`, `ct_start_date`, `ct_completion_date`, `ct_brief_title`. `_trial_phase()` reads the new attribute, flipping **177 relations to `high_evidence`** (Phase 3 + enrollment ≥300) — an 89% uplift to the top tier. 198 relations remain `unclassified` because they are document-level or compound-level, not connected to Trial nodes.

**Compound enrichment from PubChem.** Both `Compound` nodes (semaglutide, tirzepatide) now carry `pubchem_cid`, `molecular_formula`, `molecular_weight`, `canonical_smiles`, `inchi`. No new nodes; existing nodes got richer.

## What V3.1 delivers on clinical trials that V3.0 did not

- **Dedicated clinicaltrials domain** — 12 entity types + 10 relation types purpose-built for trial protocol shape (Trials, Interventions, Conditions, Sponsors, Investigators, Outcomes, Compounds, Biomarkers, Cohorts, Populations, TrialPhases, Sites).
- **Phase-based evidence grading** — `domains/clinicaltrials/epistemic.py` grades every Trial-connected relation by trial design (Phase, enrollment, randomization, blinding). The narrator combines this *with* v3's epistemic status vocabulary so a `high_evidence + contested` claim is flagged differently than a `high_evidence + asserted` one.
- **Optional `--enrich` flag** — `/epistract:ingest --enrich` runs `domains/clinicaltrials/enrich.py` after graph build, pulling live metadata:
  - ClinicalTrials.gov v2 API → `ct_overall_status`, `ct_phase`, `ct_enrollment`, `ct_start_date`, `ct_completion_date`, `ct_brief_title`
  - PubChem PUG REST → `pubchem_cid`, `molecular_formula`, `molecular_weight`, `canonical_smiles`, `inchi`
  - Non-blocking: API failures log to `_enrichment_report.json` with per-entity-type hit rates but never abort the pipeline.
- **Clinical trials analyst persona** — shipped in `domains/clinicaltrials/workbench/template.yaml`. Same persona drives both workbench chat (reactive) and automatic narrator (proactive). Commits to NCT citation discipline, arm/cohort stratification, Phase-tier reasoning, and combining phase evidence grading with v3 epistemic status.

## Analyst briefing excerpt

From the auto-generated `epistemic_narrative.md` (full 1,197 words in `tests/corpora/07_glp1_phase3_trials/output/`):

> **Executive Summary**
>
> - The knowledge graph is **dominated by `asserted` claims** (394 of 395 relations), with a single unclassified relation — suggesting a highly curated corpus of trial protocols.
> - The graph is **outcome-heavy** (65 Outcome nodes across 10 trials) but **intervention-light** (16 Intervention nodes), indicating that endpoint language is well-captured while the mechanistic and compound-level detail needed for cross-trial comparability may be underrepresented.
> - **Cohort and population stratification** (13 Cohort nodes, 10 Population nodes) is present but not yet linked to divergent outcome signals in the current annotation — a critical gap for any subgroup-level efficacy or safety inference.
> - With only 2 `TrialPhase` nodes recorded against 10 trials, **phase-based evidence grading cannot be applied uniformly** across the corpus; several efficacy claims may be sourced from Phase 1/2 data and should be treated as `low_evidence` or `medium_evidence` until phase attribution is completed.
>
> **Structural tension**: the combination of outcome-heavy annotation with minimal phase tagging means that a Phase 1 signal and a Phase 3 null result for the same compound-condition pair could coexist in the graph as two `asserted` claims with no contradiction flag. This is a material risk for any analyst using the graph to support regulatory or investment decisions.
>
> **Recommended action**: Re-run ingestion with `--enrich` so `ct_phase` is pulled from the CT.gov v2 API as a node attribute. The phase-tier grader already reads this attribute — enriching will convert most `unclassified` tier assignments to `high_evidence` for Phase 3 trials.

The narrator correctly flagged the phase-tagging gap as the highest-priority structural issue and identified the outcome-to-intervention imbalance as the dominant structural feature — both real findings in the generated graph.

## Artifacts produced

- `tests/corpora/07_glp1_phase3_trials/docs/nct*.txt` — 10 trial protocol text files (fetched via `scripts/fetch_ct_protocols.py`)
- `tests/corpora/07_glp1_phase3_trials/output/graph_data.json` — knowledge graph, `metadata.domain: clinicaltrials`
- `tests/corpora/07_glp1_phase3_trials/output/communities.json` — Louvain communities
- `tests/corpora/07_glp1_phase3_trials/output/claims_layer.json` — phase-graded epistemic layer with v3 status vocabulary
- `tests/corpora/07_glp1_phase3_trials/output/epistemic_narrative.md` — clinical trials analyst briefing (new in v3.1, persona-driven)
- `tests/corpora/07_glp1_phase3_trials/output/graph.html` — static interactive viewer
- `tests/corpora/07_glp1_phase3_trials/output/extract_run.json` — per-doc extraction stats

## Cross-scenario narrative

S6 (GLP-1 Competitive Intelligence, literature) → S7 (GLP-1 Phase 3 Trials, protocols) is the intended pair. Run both workbenches side-by-side:

```bash
# Terminal 1 — S6 literature graph
python scripts/launch_workbench.py tests/corpora/06_glp1_landscape/output-v3 \
    --domain drug-discovery --port 8000

# Terminal 2 — S7 trial-protocol graph
python scripts/launch_workbench.py tests/corpora/07_glp1_phase3_trials/output \
    --domain clinicaltrials --port 8001
```

Ask the same question in both — "What's the evidence for tirzepatide in obesity?" — and compare how each domain's persona frames the answer. S6 will cite patents and PubMed abstracts, flag prophetic vs asserted, call out the SURPASS-2 gap. S7 will cite NCT IDs, grade by Phase, and surface arm-level enrollment. Together they are a competitive-intelligence brief that neither alone can produce.

## See also

- [docs/SHOWCASE-GLP1.md](SHOWCASE-GLP1.md) — the S6 drug-discovery literature showcase that motivated this one
- [tests/scenarios/scenario-07-clinicaltrials-glp1-phase3.md](../tests/scenarios/scenario-07-clinicaltrials-glp1-phase3.md) — scenario validation doc
- [docs/ADDING-DOMAINS.md §Domain Enrichment](ADDING-DOMAINS.md) — how the `--enrich` contract works if you want to wire your own domain to an external API
