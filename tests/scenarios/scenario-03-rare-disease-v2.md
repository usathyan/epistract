# Scenario 3 (V2): Rare Disease Therapeutics — Due Diligence

**Status:** V2 validation complete
**V2 run date:** 2026-04-13
**Framework version:** Epistract v2.0
**Output:** [`tests/corpora/03_rare_disease/output-v2/`](../corpora/03_rare_disease/output-v2/)
**V1 reference:** [scenario-03-rare-disease.md](scenario-03-rare-disease.md)

---

## Knowledge Graph (V2)

![Rare Disease V2 Knowledge Graph](screenshots/scenario-03-graph-v2.png)

*110 nodes, 278 links, 5 communities. 15 parallel extractors on 15 PubMed abstracts spanning pegvaliase/PKU, vosoritide/achondroplasia, arimoclomol/Niemann-Pick C, ERT immunogenicity, and AAV gene therapy.*

---

## V1 → V2 Delta

| Metric | V1 Baseline | V2 Run | Δ | Threshold | Result |
|---|---:|---:|---:|---:|:---:|
| Nodes | 94 | **110** | +16 (+17%) | 76 | PASS |
| Edges | 229 | **278** | +49 (+21%) | 184 | PASS |
| Communities | 4 | **5** | +1 | 2 | PASS |
| Documents | 15 | 15 | 0 | — | — |

**Regression verdict:** PASS via `python3 tests/regression/run_regression.py --baselines tests/baselines/v1/ --scenario s03_rare_disease`.

---

## Corpus

Unchanged from V1 — 15 PubMed abstracts in `tests/corpora/03_rare_disease/docs/`. See [V1 scenario doc](scenario-03-rare-disease.md#corpus) for the full provenance list.

---

## Run Statistics

| Metric | Value |
|---|---:|
| Raw entities | 228 |
| Raw relations | 142 |
| Graph nodes | 110 |
| Graph links | 278 |
| Communities | 5 |
| NCT trials detected | 11 |
| SMILES pattern matches (false positives) | 53 |
| Asserted relations | 273 |
| Hypothesized relations | 4 |
| **Contradictions** | **1** |
| **Hypotheses** | **2** |

### Entity Types

| Type | Count |
|---|---:|
| DOCUMENT | 15 |
| BIOMARKER | 13 |
| ADVERSE_EVENT | 13 |
| COMPOUND | 12 |
| CLINICAL_TRIAL | 9 |
| PROTEIN | 8 |
| DISEASE | 8 |
| MECHANISM_OF_ACTION | 7 |
| PHENOTYPE | 5 |
| PATHWAY | 4 |
| REGULATORY_ACTION | 4 |
| GENE | 3 |
| SEQUENCE_VARIANT | 3 |
| METABOLITE | 3 |
| ORGANIZATION | 3 |

Notable: **COMPOUND count (12) is 4× higher than any prior V2 scenario** — rare disease literature is drug-heavy (pegvaliase, sapropterin, vosoritide, arimoclomol, miglustat, valoctocogene roxaparvovec, etc.). GENE count (3) is correspondingly low because the corpus focuses on therapies rather than target discovery.

### Communities

| Community | Members |
|---|---:|
| Prednisone / Valoctocogene Roxaparvovec / Autoimmune Hepatitis | 26 |
| MAPK Pathway | 18 |
| Pegvaliase / Phenylalanine Ammonia Lyase / Type III Hypersensitivity Reaction | 17 |
| Endochondral Ossification / FGFR3 Downstream Signalling Pathway | 17 |
| Hepatocyte Gene Transfer | 9 |

V2 found 5 communities vs V1's 4. The new **Hepatocyte Gene Transfer** cluster is a clean factorization — it captures AAV5-delivered gene therapy biology (valoctocogene roxaparvovec for hemophilia A) that V1 merged into the "PKU Enzyme Replacement / Gene Therapy" cluster.

---

## V2 Insights

1. **Zero permission prompts** — this was the first scenario run fully autonomously without the user approving anything. The Track A settings patch applied before S2 (4 generalized wildcards in `.claude/settings.local.json`) covered every command S3 needed. The entire validate → build → epistemic → view → regression tail ran as one chained Bash invocation.
2. **Raw relation count is 40% lower than S1/S2** (142 vs ~255) — rare disease abstracts are denser on entity mentions than on explicit relational language (lots of `X is a treatment for Y` but few `X INHIBITS Y` mechanistic chains).
3. **Graph edges still expanded 21%** over V1 despite the sparse raw relations. This is because sift-kg's `build_graph` synthesizes `MENTIONED_IN` edges per document-entity pair (164 of 278 edges are `MENTIONED_IN`), which scales with entity count, not relation count.
4. **2 hypotheses flagged** — more than S1 (1) or S2 (0). Investigational rare-disease therapies lean on hedging language ("may provide", "could improve") because many are Phase I/II with limited data.
5. **1 contradiction** — pattern matches S1's SORL1 finding. Likely a drug-indication framing difference between two abstracts; full details in `claims_layer.json`.

---

## Output Files

| File | Description |
|---|---|
| `output-v2/graph_data.json` | 110 nodes, 278 edges |
| `output-v2/communities.json` | 5 community labels |
| `output-v2/graph.html` | Interactive viewer |
| `output-v2/claims_layer.json` | 273 asserted + 4 hypothesized + 1 contradiction + 2 hypotheses |
| `output-v2/screenshots/graph_overview.png` | V2 graph screenshot (486KB) |
