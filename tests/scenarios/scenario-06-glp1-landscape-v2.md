# Scenario 6 (V2): GLP-1 Competitive Intelligence — Multi-Source CI

**Status:** V2 validation complete
**V2 run date:** 2026-04-13
**Output:** [`tests/corpora/06_glp1_landscape/output-v2/`](../corpora/06_glp1_landscape/output-v2/)
**V1 reference:** [scenario-06-glp1-landscape.md](scenario-06-glp1-landscape.md)

---

## Knowledge Graph (V2)

![GLP-1 V2 Knowledge Graph](screenshots/scenario-06-graph-v2.png)

*193 nodes, 619 links, 9 communities. 34 parallel extractors across 24 PubMed abstracts + 10 patents (largest V2 scenario). First V2 scenario with **prophetic epistemic claims** from patent documents.*

---

## V1 → V2 Delta

| Metric | V1 | V2 | Δ | Threshold | Result |
|---|---:|---:|---:|---:|:---:|
| Nodes | 206 | **193** | -6% | 165 | PASS |
| Edges | 630 | **619** | -2% | 504 | PASS |
| Communities | 9 | **9** | 0 | 5 | PASS |

---

## Run Statistics

| Metric | Value |
|---|---:|
| Documents processed | 34 (24 PubMed + 10 patents) |
| Parallel extraction agents | 34 |
| Raw entities | ~457 |
| Raw relations | ~319 |
| Graph nodes | 193 |
| Graph edges | 619 |
| Communities | 9 |
| **NCT trials** | **16** |
| **US patents** | **10** |
| SMILES matches | 131 |
| Amino acid sequences | 4 |
| SEQ_ID_NO markers | 8 |
| InChIKeys | 1 |
| CAS numbers | 1 |
| Validator-enriched entities | 4 |
| Validator-enriched relations | 4 |

### Epistemic Analysis — The Star of S6

| Status | Count |
|---|---:|
| Asserted | 595 |
| **Prophetic** | **15** (patent forward-looking claims) |
| Hypothesized | 5 |
| Unclassified | 4 |
| **Contradictions** | **1** |
| **Hypotheses** | **5** |
| Super-domain relations | 24 |
| Document types | **paper, patent** |

S6 is the **first V2 scenario to surface prophetic claims** from patent documents. The domain-specific `epistemic.py` module distinguishes between:
- **Asserted** — paper-sourced declarative findings ("sotorasib inhibits KRAS G12C")
- **Prophetic** — patent-sourced forward claims ("the compounds of the invention are useful for treating obesity")
- **Hypothesized** — hedged language in either source type

15 prophetic claims correctly identified across the 10 patents. This validates that Chris's earlier work on the epistemic layer correctly reads the domain's doctype signatures and applies different rules per source class.

### Communities

| Community | Members |
|---|---:|
| Hyperglycemia — GLP-1, Pepsin | 30 |
| Substance Use Disorder — GLP-1 Receptor | 20 |
| Gastric Emptying Delay / Central Satiety Signaling | 19 |
| Prediabetes — GIP Receptor / GLP1R / GIPR | 19 |
| MASLD — GIPR / GLP-1R / GCGR | 18 |
| Cilofexor / Denifanstat / Efruxifermin | 13 |
| Triple GLP-1/GIP/Glucagon Receptor Agonism | 10 |
| Liraglutide / Metformin / Dyslipidaemia | 9 |
| CagriSema / Overweight / Phase 3 Trial | 8 |

V2 matches V1's 9 communities exactly — the largest and most complex scenario produced an identical partition count, though the individual community compositions differ slightly. The "Substance Use Disorder" community captures GLP-1's emerging use in alcohol use disorder and opioid addiction, which is a 2024-2025 finding.

---

## V2 Insights (S6)

1. **Prophetic claims work end-to-end** — 15 patent-derived forward-looking claims were correctly classified. This is what the epistemic layer was designed for and S6 is the only V2 scenario that exercises it.
2. **Mixed doctype corpora classify correctly** — The epistemic summary shows `document_types: [patent, paper]`. Patents were routed to prophetic-claim detection, papers to asserted/hypothesized. No misclassification (unlike the `unknown` bug with S2/S4/S5 structural biology docs).
3. **34 parallel extractors succeeded** — previous worry about dispatching >20 agents at once was unfounded. Zero agent failures.
4. **Import-path workaround**: several S6 extractor agents reported needing `python3 -m core.build_extraction` instead of direct `python3 core/build_extraction.py` — suggests running from an unexpected cwd. Non-blocking (extractions still wrote correctly) but worth a fix. Captured in the automation friction log.
5. **V2 tightness pattern continues** — like S5, V2 is slightly below V1 on primary metrics (94% nodes, 98% edges). This is NOT regression: V2 produced the same 9-community partition as V1 and added prophetic-claim classification, so the graph is *more* informative despite having marginally fewer nodes.
6. **Validator enrichment hit 4+4** — patent SMILES and InChIKeys (SNAC, tirzepatide, zealand triple agonist peptides) got RDKit/Biopython-validated and added as canonical entities with computed molecular properties.

---

## V3 Insights (S6)

Same 34-document corpus, rebuilt on 2026-04-22 with Sonnet 4.6 via OpenRouter using the v3.0 pipeline. Output committed under `tests/corpora/06_glp1_landscape/output-v3/`. V2 baseline preserved at `output-v2/` for comparison.

### Headline metrics (V2 → V3)

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
| `epistemic_narrative.md` auto-emitted | — | yes (1,166 words) | new (v3 narrator) |

### What V3 unlocked on the same corpus

1. **Automatic analyst narrative.** The epistemic layer now produces a structured briefing on every run — executive summary, prophetic claim landscape grouped by patent family, contested-claims analysis with source IDs, coverage gaps, recommended follow-ups. V2 stopped at counts; V3 writes the analyst synthesis a human would. Full output: `tests/corpora/06_glp1_landscape/output-v3/epistemic_narrative.md`.

2. **4× prophetic claim detection (15 → 61).** Sonnet 4.6's thoroughness on patent forward-looking language ("is expected to", "may be prepared by", "could be formulated as") combined with v3's stricter Pydantic validation keeping every extraction rather than silently dropping malformed ones.

3. **Temporal contradiction reasoning.** V2 surfaced 1 contradiction as a fact; V3's narrator now reasons about why it exists. For `semaglutide INDICATED_FOR obesity` with confidence range 0.55–0.97, the narrator correctly identifies the 0.55 instance as pre-STEP-trial patent language and the 0.97 instance as post-approval asserted status — two *temporally* separated instances that look like a contradiction but aren't. Same pattern detected for tirzepatide vs SURMOUNT-1.

4. **Per-node richness doubled.** Average 3.86 structured attributes per node in V3 vs 1.77 in V2 (+118%). V3 entities carry drug_class, compound_code, route_of_administration, mesh_term, development_stage, etc. — not just a type label. The graph is *denser in facts per node*, not just wider.

5. **New epistemic status tiers.** V3 surfaces `speculative` (2 instances) and `negative` (1 instance) in addition to V2's 4 tiers, plus `contested_claims` grew from 5 to 33 — finer gradation of certainty matters for clinical and regulatory decisions.

6. **Domain metadata auto-propagation (FIDL-06).** `graph_data.json.metadata.domain: drug-discovery` is populated automatically. `/epistract:dashboard tests/corpora/06_glp1_landscape/output-v3` (no `--domain` flag) correctly loads the drug-discovery persona, entity colors, and starter questions. V2 graphs required explicit `--domain` every time.

7. **Auto-validator fired cleanly (FIDL-07).** `cmd_build` auto-invoked `domains/drug-discovery/validation/run_validation.py` and produced `validation_report.json` with `status: skipped, reason: RDKit not installed` — graceful degrade. V2 had no auto-validator invocation; validator failure would have crashed the build.

8. **Single-source-of-truth persona.** The upgraded drug-discovery persona in `domains/drug-discovery/workbench/template.yaml` now drives BOTH the reactive workbench chat (when users ask questions) AND the proactive narrator (when `/epistract:epistemic` runs). Upgrade the persona once; both surfaces improve together.

9. **Zero extraction drops (FIDL-02c).** All 34 extractions passed Pydantic validation at write time. 100% pass rate through `normalize_extractions`. V2 had the reliability floor at ≥95% on a 24-file Bug-4 reproducer; V3 confirmed it holds at 34 docs with a real corpus.

10. **Smoke-test of plugin path.** A separate 3-document subset (`tests/corpora/smoke_glp1/`) ran through the full `epistract:extractor` subagent dispatch path to validate the real-user plugin flow end-to-end. Produced 25 nodes / 56 edges / validation_report.json — confirms the subagent plumbing works identically to the direct-call script used for the full rebuild.

### Known caveats for V3-on-S6

- **Model confound.** V2 used Opus 4.6; V3 uses Sonnet 4.6. The raw node/edge growth is partly extractor-model change, partly pipeline improvement. The FIDL-06/07/02c wins and the narrator are pipeline-level features independent of extractor choice.
- **Single-chunk corpus.** S6 documents are short abstracts and patent excerpts (avg ~2.3KB). Most fit in one chunk, so FIDL-03 sentence-aware overlap did not exercise meaningfully. Will show on larger-document corpora.
- **RDKit gated off.** The validator infrastructure fired but RDKit was not installed in the rebuild env. Molecular property enrichment (V2's 4+4 SMILES/InChIKey entries) is pending an RDKit-enabled rerun.

For the full V3 narrative briefing, see [`output-v3/epistemic_narrative.md`](../corpora/06_glp1_landscape/output-v3/epistemic_narrative.md). For the public-facing showcase, see [`docs/SHOWCASE-GLP1.md`](../../docs/SHOWCASE-GLP1.md).

---

## Output Files

### V2 (2026-04-13)

- `output-v2/graph_data.json` — 193 nodes, 619 edges
- `output-v2/claims_layer.json` — 595 asserted + 15 prophetic + 5 hypothesized + 4 unclassified + 1 contradiction + 5 hypotheses
- `output-v2/communities.json` — 9 labeled communities
- `output-v2/screenshots/graph_overview.png` — 792KB
- `output-v2/graph.html` — interactive viewer

### V3 (2026-04-22)

- `output-v3/graph_data.json` — 278 nodes, 855 edges, `metadata.domain: drug-discovery`
- `output-v3/claims_layer.json` — 758 asserted + 61 prophetic + 31 hypothesized + 2 speculative + 1 negative + 2 unclassified + 2 contradictions + 33 contested claims
- `output-v3/communities.json` — 10 labeled communities
- `output-v3/epistemic_narrative.md` — 1,166-word analyst briefing (new in v3)
- `output-v3/validation_report.json` — auto-validator output (RDKit skipped cleanly)
- `output-v3/graph.html` — interactive viewer (with FIDL-06 domain-aware title)
- `output-v3/extract_run.json` — per-doc extraction stats ($3.20 total, 544,296 tokens)
- `output-v3/s06_delta.json` — machine-readable V2 vs V3 delta
