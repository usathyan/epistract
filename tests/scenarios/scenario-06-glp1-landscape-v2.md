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

## Output Files

- `output-v2/graph_data.json` — 193 nodes, 619 edges
- `output-v2/claims_layer.json` — 595 asserted + 15 prophetic + 5 hypothesized + 4 unclassified + 1 contradiction + 5 hypotheses
- `output-v2/communities.json` — 9 labeled communities
- `output-v2/screenshots/graph_overview.png` — 792KB
- `output-v2/graph.html` — interactive viewer
