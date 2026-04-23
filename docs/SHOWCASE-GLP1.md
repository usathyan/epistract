# Showcase — GLP-1 Competitive Intelligence

A 34-document corpus on the GLP-1 receptor agonist landscape (10 drug patents + 24 PubMed abstracts on semaglutide, tirzepatide, liraglutide, orforglipron, retatrutide, and related peptides), built end-to-end with the v3.0 pipeline. The outputs and the narrator briefing are committed under `tests/corpora/06_glp1_landscape/output-v3/`.

## Try it yourself

```bash
/epistract:dashboard tests/corpora/06_glp1_landscape/output-v3 --domain drug-discovery
```

This launches the interactive workbench on the pre-built graph — no need to re-run ingestion. Ask the chat panel things like:

- *"Which patents make prophetic claims about new indications?"*
- *"Where are the coverage gaps in long-term safety data?"*
- *"Compare semaglutide vs tirzepatide adverse events."*
- *"Map the CNS indication hypothesis chain for semaglutide."*

The chat panel is grounded in the same graph + claims layer that produced the narrative below.

## V3 numbers (vs V2 baseline)

Same 34-document corpus, rebuilt with v3.0 using Sonnet 4.6 for extraction via OpenRouter:

| Metric | V2 (Opus 4.6) | V3 (Sonnet 4.6) | Δ |
|---|---:|---:|---|
| Nodes | 193 | 278 | +44% |
| Edges | 619 | 855 | +38% |
| Communities | 9 | 10 | +1 |
| Prophetic patent claims | 15 | 61 | +307% |
| Contested claims | 5 | 33 | +560% |
| Avg attributes per node | 1.77 | 3.86 | +118% |
| `metadata.domain` in `graph_data.json` | — | `drug-discovery` | new (FIDL-06) |
| `validation_report.json` auto-emitted | — | yes | new (FIDL-07) |
| `epistemic_narrative.md` auto-emitted | — | yes | new (v3) |

**V3 pipeline wins (model-independent):**

- **FIDL-02c**: All 34 extractions passed Pydantic validation at write time (100% pass rate). Zero silent drops during graph build.
- **FIDL-06**: `graph_data.json` carries `metadata.domain: drug-discovery`; the workbench auto-detects it without `--domain` on every call.
- **FIDL-07**: `cmd_build` auto-invoked `domains/drug-discovery/validation/run_validation.py`. Produced `validation_report.json` showing RDKit gracefully skipped (not installed in this env) instead of hard-failing.
- **FIDL-03**: chonkie sentence chunker armed with last-3-sentence overlap. Most S6 docs are short abstracts (avg ~2.3KB) so fit in one chunk, but the infrastructure is in place.
- **v3 narrator**: Automatic analyst briefing in `epistemic_narrative.md`, grounded in the domain persona and the classified graph.

**Caveat:** V2 used Opus 4.6; V3 uses Sonnet 4.6. The extractor-model change is a confound for raw node/edge counts — the 4× prophetic-claims jump is partly Sonnet 4.6's thoroughness on patent forward-looking language plus v3's stricter validation keeping every extraction. The FIDL-06/07/02c wins and the narrator itself are pipeline-level features independent of extractor choice.

## What the graph tells us

From the graph alone, you can see the competitive landscape: three patent families (Novo Nordisk's semaglutide, Eli Lilly's tirzepatide + retatrutide, Pfizer's danuglipron), two delivery platforms (injectable peptide + SNAC-enabled oral), four or five disease clusters (T2DM, obesity, NAFLD, PCOS, CNS indications), and the usual cross-document convergence on `GLP-1 receptor agonism` as the shared mechanism.

From the epistemic layer, you also see **what kind of knowledge the graph contains** — not just which relations exist, but how well-supported each one is.

### Executive summary (from `epistemic_narrative.md`)

> - **GLP-1/GIP dual and triple agonism is the dominant mechanistic theme** across the corpus. `semaglutide`, `tirzepatide`, `orforglipron`, and `retatrutide` are all represented, with asserted clinical evidence strongest for `semaglutide` and `tirzepatide` in Type 2 Diabetes Mellitus and Obesity, and progressively weaker (prophetic → hypothesized) for emerging indications.
> - **61 prophetic claims inflate the apparent indication breadth** of these compounds. Cardiovascular risk reduction, neurodegeneration, and metabolic sub-disorders are largely patent-forward-looking, not empirically established in the graph.
> - **Two confirmed contradictions** exist on `semaglutide` and `tirzepatide` obesity indications, where confidence scores span 0.55–0.97 and 0.65–0.97 respectively — a gap large enough to affect regulatory and commercial forecasting.
> - **Hypothesized CNS and hepatic indications** for `semaglutide` (Alzheimer Disease, Parkinson Disease, Non-Alcoholic Steatohepatitis, Alcohol Use Disorder) are contested across sources with no confirmatory Phase 3 data visible in the graph.
> - **Safety surveillance is materially incomplete**: Nonarteritic Anterior Ischemic Optic Neuropathy as a `semaglutide` adverse event is hypothesized and contested; long-term cardiovascular outcome data for newer agents (`orforglipron`, `retatrutide`) are absent.

### Prophetic claim landscape (excerpt)

The narrator groups the 61 prophetic claims by topic and patent family, and flags each against its gap vs. asserted evidence. Example:

> **Semaglutide Patent Family (`patent_01_us10888605b2_semaglutide`)**
>
> The most prolific source of prophetic claims. Key forward-looking assertions:
>
> | Prophetic Claim | Gap vs. Asserted Evidence |
> |---|---|
> | `semaglutide` INDICATED_FOR `cardiovascular_risk_reduction` | SUSTAIN shows a *trend* toward MACE reduction (asserted trend, not confirmed indication) |
> | `semaglutide` + `sodium_n_8_2_hydroxybenzoyl_amino_caprylate` oral co-formulation | Oral delivery concept is prophetic in this patent; PIONEER trial data exist separately but are marked hypothesized in the graph |
> | `liraglutide` COMBINED_WITH `sodium_n_8_2_hydroxybenzoyl_amino_caprylate` | No empirical combination data in graph; purely compositional patent claim |

### Contested claims — temporal stratification

The narrator doesn't just report contradictions — it reasons about them:

> **`semaglutide` INDICATED_FOR `obesity`** — confidence range 0.55–0.97 across sources including `patent_01_us10888605b2_semaglutide`. The 0.55 instance likely reflects pre-STEP-trial patent language; the 0.97 instance reflects post-approval asserted status. These should be temporally stratified, not treated as equivalent evidence.

### Coverage gaps (excerpt)

> 1. **No long-term safety data for `orforglipron` or `retatrutide`**: The graph contains Phase 3 trial references for `orforglipron` (ACHIEVE program) and Phase 3 initiation for `retatrutide`, but cardiovascular outcome trials (CVOT), renal safety, and oncology signals are entirely absent.
> 2. **No head-to-head comparison data**: The graph asserts `tirzepatide` superiority over "selective GLP-1 receptor agonists" but contains no direct `tirzepatide` vs. `semaglutide` randomized trial node. The SURPASS-2 trial (tirzepatide vs. semaglutide) is not represented.
> 3. **PIONEER oral semaglutide trial integration is incomplete**: The graph marks `semaglutide` EVALUATED_IN `pioneer` as hypothesized — a significant gap given that oral semaglutide (`rybelsus`) is an approved product with published Phase 3 data.

### Recommended follow-ups

> 1. **Temporally stratify the two confirmed contradictions**: Pull filing dates for `patent_01_us10888605b2_semaglutide` and `patent_02_us11357820b2_tirzepatide` and cross-reference against STEP-1 (`NCT03548935`) and SURMOUNT-1 (`NCT04184622`) approval dates. Reclassify pre-approval prophetic instances; upgrade post-approval instances to asserted.
> 2. **Integrate SURPASS-2 trial data**: Add a `clinical_trial:surpass_2` node with direct `tirzepatide` vs. `semaglutide` efficacy and safety relations to close the head-to-head gap. Source: NEJM 2021, Frías et al.
> 3. **Ingest retatrutide Phase 2 data**: Jastreboff et al. NEJM 2023 contains asserted efficacy and safety data for `retatrutide` that would substantially upgrade multiple prophetic nodes.

Full narrative: [`tests/corpora/06_glp1_landscape/output-v3/epistemic_narrative.md`](../tests/corpora/06_glp1_landscape/output-v3/epistemic_narrative.md).

## Artifacts produced

- `tests/corpora/06_glp1_landscape/output-v3/graph_data.json` — 278 nodes, 855 edges, `metadata.domain`
- `tests/corpora/06_glp1_landscape/output-v3/communities.json` — 10 Louvain communities
- `tests/corpora/06_glp1_landscape/output-v3/claims_layer.json` — 758 asserted, 61 prophetic, 31 hypothesized, 2 contradictions, 33 contested, 2 speculative, 1 negative
- `tests/corpora/06_glp1_landscape/output-v3/epistemic_narrative.md` — 1,166-word analyst briefing
- `tests/corpora/06_glp1_landscape/output-v3/validation_report.json` — FIDL-07 auto-validator output (RDKit skipped in this env)
- `tests/corpora/06_glp1_landscape/output-v3/graph.html` — static interactive viewer
- `tests/corpora/06_glp1_landscape/output-v3/s06_delta.json` — structured V2 vs V3 comparison

## Screenshots

See [WORKBENCH.md](WORKBENCH.md) for the full workbench UI tour with all four panels rendered on this corpus.
