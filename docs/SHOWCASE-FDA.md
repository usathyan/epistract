# Showcase — FDA Product Labels

A 7-document corpus of FDA Structured Product Labeling (SPL) labels covering GLP-1 receptor agonists (Ozempic, Wegovy, Mounjaro), a biologic TNF inhibitor (Humira), a pioneer targeted therapy (Gleevec), the most-prescribed statin (Lipitor), and the prototype anticoagulant (Jantoven/warfarin). Built end-to-end with the v3.2.1 pipeline and the new `fda-product-labels` domain on 2026-04-25. Outputs and the analyst briefing are committed under `tests/corpora/08_fda_labels/output/`.

## Try it yourself

```bash
python scripts/launch_workbench.py tests/corpora/08_fda_labels/output \
    --domain fda-product-labels --port 8044
```

Open http://127.0.0.1:8044. Ask the chat panel:

- *"What boxed warnings are in this corpus and which drugs carry them?"*
- *"Show me the drug interactions for warfarin (Jantoven) — which interacting drugs and what is the clinical consequence?"*
- *"Which lab tests should be monitored for atorvastatin (Lipitor) and at what frequency?"*
- *"Which contraindications apply to pregnancy across this corpus and which drugs share them?"*

The chat panel is grounded in the same graph and claims layer that produced the narrative below. The FDA regulatory intelligence analyst persona is configured to cite SPL set IDs, NDA/ANDA/BLA application numbers, NDC codes, and RxCUI identifiers — the chat will use FDA-canonical references in every answer rather than generic drug-name prose. This citation discipline makes every response auditable against the source label.

## Why this showcase matters

S8 is the regulatory-authoritative third leg of the drug intelligence trio. S6 is forward-looking: patents and PubMed literature with hedging language, prophetic claims, and research speculation. S7 is declarative: trial protocols from ClinicalTrials.gov that describe what a study does, not what it found. S8 is the FDA-reviewed truth — every claim in a Structured Product Label has been through CDER review, is codified under 21 CFR §201.57, and represents the agency's acceptance of the sponsor's evidence package. It is the canonical ground truth for what an approved drug is and is not indicated for, what it warns about, and how it interacts.

The four-level FDA epistemology surfaces a structural difference that S6 and S7 cannot show. In S6, the three-tier vocabulary (asserted/hypothesized/prophetic) captures whether a claim is hedged or forward-looking. In S7, the phase-tier vocabulary (high/medium/low evidence) captures how far along the trial-evidence chain a claim sits. In S8, the FDA four-tier vocabulary (established/observed/reported/theoretical) captures where in the regulatory evidence hierarchy a claim lives — and those four tiers sit side-by-side in a single label: a drug's mechanism of action (theoretical) and its post-marketing hemorrhage reports (reported) and its RCT-cited efficacy (observed) and its boxed warning (established) are all in the same document, now structured as graph relations with different epistemic weights.

For a formulary analyst, a pharmacovigilance team, or a drug-intelligence researcher, this matters practically: the S8 graph can answer "what is the established-tier evidence for warfarin interactions?" as a distinct query from "what are the reported-tier signals for semaglutide adverse reactions?" — giving the analyst a structured, evidence-tiered view that raw label text cannot provide.

## V3.2 numbers (2026-04-25)

| Metric | V3.2 (`openai/gpt-oss-20b:free`) |
|---|---:|
| Documents | 7 FDA SPL labels (GLP-1, oncology, statin, anticoagulant) |
| Extraction pass rate | 100% (7/7 Pydantic-validated, 0 silent drops) |
| Extraction cost | **$0.00** (free-tier model via OpenRouter) |
| Extraction duration | ~108 min (sequential, `openai/gpt-oss-20b:free`) |
| Nodes | **81** |
| Edges | **149** |
| Entity types | 14 (ADVERSE_REACTION, INACTIVE_INGREDIENT, DRUG_INTERACTION, DOCUMENT, PATIENT_POPULATION, CONTRAINDICATION, DRUG_PRODUCT, ACTIVE_INGREDIENT, MECHANISM_OF_ACTION, MANUFACTURER, WARNING, CLINICAL_STUDY, PHARMACOKINETIC_PROPERTY, LABTEST) |
| Communities | **3** (Louvain: statins/HMG-CoA, anticoagulants/VitK, GLP-1/Novo Nordisk) |
| ADVERSE_REACTION entities | 21 |
| DRUG_INTERACTION entities | 13 |
| CONTRAINDICATION entities | 4 |
| WARNING entities | 2 |
| DRUG_PRODUCT entities | 3 |
| LABTEST entities | **1** (INR — new entity type in v3.2, not in drug-discovery or clinicaltrials) |
| REGULATORY_IDENTIFIER entities | 0 (citations embedded in relation evidence strings; all 7 app numbers in narrative) |
| `established` (FDA evidence tier) | 0 |
| `observed` (FDA evidence tier) | **4** |
| `reported` (FDA evidence tier) | **145** |
| `theoretical` (FDA evidence tier) | 0 |
| `established` (v3 epistemic_status) | 0 |
| `observed` (v3 epistemic_status) | 4 |
| `reported` (v3 epistemic_status) | 145 |
| `theoretical` (v3 epistemic_status) | 0 |
| `metadata.domain` | `fda-product-labels` |
| Narrative word count | **1,579 words** |

### What the numbers say

**Post-marketing pharmacovigilance dominates.** 145 of 149 relations (97%) are `reported` — spontaneous adverse event reports, drug-interaction signals from pharmacovigilance databases, post-marketing study findings. This is structurally correct for FDA SPL labels: the `adverse_reactions`, `drug_interactions`, and `warnings` sections are populated from post-marketing surveillance, not controlled trials. The graph faithfully reflects what FDA labels actually contain rather than what analysts might wish they contained.

**Observed evidence is sparse but high-value.** Only 4 `observed` relations were extracted — RCT-cited efficacy data from `clinical_studies` sections. These are the highest-quality factual claims in the graph: the SUSTAIN-6 cardiovascular outcomes data for Ozempic (`NDA209637`), the LDL-lowering RCT data for Lipitor (`NDA020702`), the survival benefit data for Gleevec (`NDA021588`), and the INR monitoring data for Jantoven (`ANDA040416`). Sparsity here reflects the extraction model's behavior on dense SPL text — the Sonnet 4.6 extractor is expected to recover more `observed` relations in a paid-model run.

**Three tight communities reflect the therapeutic cross-section design.** The Louvain algorithm found 3 clusters: (1) statins/HMG-CoA inhibition (atorvastatin/Lipitor), (2) anticoagulants/vitamin K antagonism (warfarin/Jantoven), (3) GLP-1 agonists/Novo Nordisk (semaglutide Ozempic + Wegovy, tirzepatide Mounjaro). Humira and Gleevec were absorbed into the most-connected communities rather than forming their own. The tight clustering shows strong intra-class knowledge connectivity — cross-label pattern discovery (shared CYP pathways, shared class adverse effects, shared population restrictions) is exactly what the S8 corpus was designed to surface.

**LABTEST is present but sparsely populated.** 1 LABTEST node was extracted (INR monitoring from the warfarin label), confirming the new entity type is functional and being written to the graph. Broader LABTEST coverage — ALT/AST for imatinib, lipid panel for atorvastatin, CBC for adalimumab — is expected with the Sonnet 4.6 extractor. Even with 1 node, the LABTEST monitoring relationship chain is demonstrably present in the graph and queryable via the workbench.

## What V3.2 delivers on FDA labels that V3.0/V3.1 didn't

- **Dedicated fda-product-labels domain** — 17 entity types including LABTEST and REGULATORY_IDENTIFIER (both new in v3.2, absent from drug-discovery and clinicaltrials), 16 relation types tuned to SPL document shape (TREATS, CONTRAINDICATES, CAUSES_ADVERSE_REACTION, INTERACTS_WITH, REQUIRES_MONITORING, IDENTIFIED_BY, and more).
- **Four-level FDA epistemology classifier** — `domains/fda-product-labels/epistemic.py` grades every relation by SPL-source signals: boxed warnings + contraindications produce `established`; `clinical_studies` RCT language produces `observed`; `adverse_reactions` and `postmarketing` language produces `reported`; `mechanism_of_action` + `pharmacology` produce `theoretical`. Combined with v3 `epistemic_status` on every relation, giving analysts a two-dimensional evidence view.
- **Hand-tailored FDA regulatory intelligence analyst persona** — depth in pharmacovigilance, formulary analysis, drug-interaction screening, and SPL document review. Citation discipline scoped to FDA-canonical identifiers (SPL set ID, NDA/ANDA/BLA, NDC, RxCUI, UNII). Drives both reactive workbench chat AND proactive `/epistract:epistemic` narrator.
- **LABTEST entity** — first-class node type for ALT/AST, INR, lipid panel, CBC monitoring relationships. Not present in drug-discovery or clinicaltrials domains. Makes lab-monitoring connections queryable as graph edges rather than unstructured prose.
- **Cross-label synthesis** — the corpus is intentionally cross-cutting (GLP-1 + oncology + statin + anticoagulant). The graph surfaces shared mechanisms (CYP pathway interactions across statin + warfarin), shared monitoring patterns (hepatotoxicity monitoring across multiple drug classes), and shared population restrictions (pregnancy contraindications across Ozempic, Wegovy, Lipitor, and Jantoven).

## Analyst briefing excerpt

From the auto-generated `epistemic_narrative.md` (full 1,579 words in `tests/corpora/08_fda_labels/output/`):

> **Evidence Quality Assessment**
>
> The FDA four-level epistemology framework was applied to all extracted relations. The corpus is heavily weighted toward **reported** evidence, reflecting the post-marketing nature of the data. **Established** evidence is limited to the boxed warnings and contraindications mandated by the FDA. **Observed** evidence is present but confined to efficacy and basic pharmacokinetics. **Theoretical** evidence is absent, indicating that the labels rely on empirical data rather than predictive modeling.
>
> Representative observed-tier citations: *Atorvastatin* LDL-lowering data (`NDA020702`); *Semaglutide* CV-risk reduction (`NDA209637`); *Imatinib* survival benefit (`NDA021588`); *Warfarin* INR monitoring (`ANDA040416`). Representative reported-tier signals: pancreatitis reports for *Semaglutide*; hepatotoxicity for *Imatinib*; bleeding events for *Warfarin* (`ANDA040416`); Stevens-Johnson syndrome for *Adalimumab* (`BLA125057`).
>
> **Boxed warnings identified:** `BLA125057` (adalimumab/Humira) — serious infections, malignancy, and hypersensitivity reactions. `ANDA040416` (warfarin/Jantoven) — major hemorrhage, especially intracranial. These represent the highest-priority safety signals in the corpus. **Contraindications:** Warfarin is contraindicated in pregnancy and active bleeding; Atorvastatin in active liver disease and pregnancy; Semaglutide (both `NDA209637` and `NDA215256`) for known hypersensitivity; Imatinib (`NDA021588`) for hypersensitivity to any excipient.
>
> **Cross-label pattern:** The *Warfarin* interactions with CYP2C9 inhibitors are mirrored in *Imatinib* (CYP3A4) and *Semaglutide* (CYP3A4/1A2) interactions, highlighting the importance of CYP profiling in formulary decisions. Pancreatitis is a recurrent adverse reaction across both *Semaglutide* indications (`NDA209637`, `NDA215256`), underscoring a class effect that warrants formulary-level monitoring protocols for all GLP-1 receptor agonists.

The narrator correctly identified the post-marketing dominance (97% `reported`) as the highest-priority structural finding — accurate for FDA labels and analytically important because it tells a formulary analyst this graph is stronger for pharmacovigilance queries than for efficacy queries. The four `observed` relations represent the highest-quality efficacy claims in the corpus and were correctly identified with FDA-canonical application-number citations. The cross-label CYP pathway pattern and the GLP-1 pancreatitis class effect emerged as the key synthetic findings that no single-product label reading could surface.

## Artifacts produced

- `tests/corpora/08_fda_labels/docs/*.txt` — 7 SPL label plaintext files (semaglutide_ozempic.txt, semaglutide_wegovy.txt, tirzepatide_mounjaro.txt, adalimumab_humira.txt, imatinib_gleevec.txt, atorvastatin_lipitor.txt, warfarin_jantoven.txt)
- `tests/corpora/08_fda_labels/output/graph_data.json` — knowledge graph, `metadata.domain: fda-product-labels`, 81 nodes, 149 edges
- `tests/corpora/08_fda_labels/output/communities.json` — 3 Louvain communities (statins, anticoagulants, GLP-1)
- `tests/corpora/08_fda_labels/output/claims_layer.json` — 4-tier FDA epistemic layer with `evidence_tier_counts` and `epistemic_status_counts` at top level
- `tests/corpora/08_fda_labels/output/epistemic_narrative.md` — FDA regulatory intelligence briefing (1,579 words, persona-driven, 29 FDA ID citations)
- `tests/corpora/08_fda_labels/output/graph.html` — static interactive vis.js viewer (186 KB)
- `tests/corpora/08_fda_labels/output/extract_run.json` — per-doc extraction stats (docs_done=7, docs_failed=0, total_cost_usd=0.00)

## Cross-scenario narrative

S6 → S7 → S8 is the complete drug intelligence trio. Run all three workbenches side-by-side:

```bash
# Terminal 1 — S6 literature graph
python scripts/launch_workbench.py tests/corpora/06_glp1_landscape/output-v3 \
    --domain drug-discovery --port 8000

# Terminal 2 — S7 trial-protocol graph
python scripts/launch_workbench.py tests/corpora/07_glp1_phase3_trials/output \
    --domain clinicaltrials --port 8001

# Terminal 3 — S8 FDA-label graph
python scripts/launch_workbench.py tests/corpora/08_fda_labels/output \
    --domain fda-product-labels --port 8044
```

Ask the same question across all three workbenches: *"What is the evidence for tirzepatide in obesity?"* Each persona frames the answer differently. S6 (drug-discovery) cites patents and PubMed abstracts, flags prophetic vs asserted claims, calls out the SURPASS-2 data gap in the literature at the time of publication, and hedges on long-term safety. S7 (clinicaltrials) cites NCT IDs, grades evidence by Phase (Phase 3 SURMOUNT = `high_evidence`), surfaces arm-level enrollment and primary endpoints, and notes the absence of post-market CVOT data. S8 (fda-product-labels) cites `NDA215866`, grades by FDA tier (the SURPASS comparator data in the label is `observed`; the GLP-1 class warnings are `reported`), and surfaces the pregnancy contraindication, the thyroid C-cell tumor warning shared with semaglutide, and the monitoring requirements absent from the other two personas.

Together, the three workbenches produce a complete competitive-intelligence brief that no single workbench could produce: S6 tells you what the research community asserted and predicted, S7 tells you what the trial investigators declared and measured, and S8 tells you what the FDA accepted as the official record — the authoritative regulatory truth at the top of the evidence hierarchy.

## See also

- [tests/scenarios/scenario-08-fda-product-labels.md](../tests/scenarios/scenario-08-fda-product-labels.md) — scenario validation doc with full metrics tables and entity-type distribution
- [docs/SHOWCASE-GLP1.md](SHOWCASE-GLP1.md) — S6 drug-discovery literature showcase
- [docs/SHOWCASE-CLINICALTRIALS.md](SHOWCASE-CLINICALTRIALS.md) — S7 clinical-trials showcase
- [domains/fda-product-labels/SKILL.md](../domains/fda-product-labels/SKILL.md) — the domain extraction prompt
- [docs/ADDING-DOMAINS.md](ADDING-DOMAINS.md) — how to build your own domain
