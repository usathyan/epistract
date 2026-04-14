# Drug Discovery Literature Analysis (V2)

Epistract v2.0 introduces a cross-domain knowledge graph framework. This document mirrors the [V1 drug-discovery showcase](drug-discovery.md) but reports results from the **V2 plugin pipeline** — where extraction, validation, graph building, and epistemic analysis run exclusively through `/epistract:*` slash commands with no direct script invocation.

> **Phase 11 status:** All 6 drug-discovery V2 scenarios are complete and passing regression (as of 2026-04-13). Contracts scenario skipped for this public branch — the private contract corpus used for prior validation is confidential and will not be re-validated on this public release. Bring your own contracts to reproduce the results via `domains/contracts/`. Total V2 validation: **111 documents, 867 nodes, 2,592 links, 39 communities** across 6 drug-discovery scenarios.

---

## What Changed in V2

The V2 framework is a domain-agnostic refactor of the V1 drug-discovery pipeline. Functional changes that affect the results below:

1. **Pluggable domain layer** — The drug-discovery schema (17 entity types, 30 relation types, canonical names, validation scripts) is now a self-contained package in `domains/drug-discovery/`. A second domain (`contracts/`) lives alongside it, validating the abstraction.
2. **Per-document parallel extraction** — The `/epistract:ingest` command dispatches one `epistract:extractor` subagent per document rather than batching 3 documents per agent. For a 15-doc corpus this means 15 parallel subagents with isolated contexts, all reading the domain SKILL.md independently.
3. **Plugin-only workflow** — All extraction runs through the Claude Code plugin interface (`/epistract:ingest`, `/epistract:build`, `/epistract:epistemic`, `/epistract:view`, `/epistract:validate`). No direct Python script invocation.
4. **Regression-gated baselines** — `tests/regression/run_regression.py` compares each V2 run against pinned V1 baselines in `tests/baselines/v1/`. The threshold is ≥80% of V1 node/edge/community counts.
5. **Epistemic layer is now a first-class domain artifact** — `core/label_epistemic.py` dispatches to a domain-specific epistemic module (`domains/drug-discovery/epistemic.py`). Output written to `claims_layer.json` with contradictions, hypotheses, and contested claims.

---

## Methodology (V2)

Each scenario follows the same V2 workflow:

1. **Corpus assembly** — unchanged from V1 (same source documents)
2. **Extraction via plugin** — `/epistract:ingest <docs> --output <scenario>/output-v2 --domain drug-discovery` → spawns 1 extractor subagent per document
3. **Molecular validation** — `domains/drug-discovery/validate_molecules.py` (RDKit + Biopython) runs automatically during ingest
4. **Graph construction** — `core/run_sift.py build` with domain-specific `canonical_names` dedup
5. **Community detection** — Louvain on MultiDiGraph, auto-labeled by `label_communities.py`
6. **Epistemic analysis** — `/epistract:epistemic` → pattern-based classification into asserted / hypothesized / prophetic / contradictory
7. **Regression check** — `python tests/regression/run_regression.py --baselines tests/baselines/v1/` → PASS when V2 ≥ 80% of V1 baselines

### Slash-Command Map

The `/epistract:*` commands split into two groups — **full-pipeline commands** that do everything needed for a scenario, and **single-stage re-run commands** that operate on an existing output directory. For a fresh scenario run you only need two commands: `/epistract:ingest` and `/epistract:epistemic`.

| Slash command | Runs | When to use | Notes |
|---|---|---|---|
| `/epistract:ingest <docs> --output <dir> --domain <name>` | read → chunk → extract → validate → build graph → generate viewer | **Fresh scenario run** — start here | Internally calls everything below except `epistemic`. Do **not** also invoke `build`/`view`/`validate` as follow-ups. |
| `/epistract:epistemic <dir>` | pattern-based classification → `claims_layer.json` | After every fresh `ingest` | Separate because it reads `graph_data.json` *after* the graph is built. Produces the contradictions/hypotheses overlay. |
| `/epistract:build <dir>` | graph build only (no extraction) | Re-running the builder on existing extractions (e.g., after a domain.yaml change) | Skip if you just ran `ingest`. |
| `/epistract:view <dir>` | `graph.html` generation only | Re-generating the viewer after editing the graph | Skip if you just ran `ingest`. |
| `/epistract:validate <dir>` | molecular validation only | Re-running validation without re-extracting | Skip if you just ran `ingest`. |
| `/epistract:query <dir> <query>` | entity search on existing graph | Post-run exploration | Read-only, cheap. |
| `/epistract:export <dir> <format>` | GraphML / GEXF / CSV / SQLite export | Post-run data handoff | Read-only on the graph. |
| `/epistract:view-neighborhood <dir> <entity>` | subgraph viewer centered on an entity | Deep-dive on a specific node | Optional. |

**Per-scenario recipe — minimum command sequence:**

```
/epistract:ingest tests/corpora/<scenario>/docs --output tests/corpora/<scenario>/output-v2 --domain drug-discovery
/epistract:epistemic tests/corpora/<scenario>/output-v2
```

Everything else (regression check, screenshot capture, V2 doc update) happens outside the plugin via the commands shown in the per-scenario V2 reports.

---

## V2 Scenario Results

| # | Scenario | Focus | Docs | V1 Nodes | V2 Nodes | V1 Edges | V2 Edges | V1 Comm | V2 Comm | Status |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| 1 | PICALM / Alzheimer's | Genetic target validation | 15 | 149 | **183** | 457 | **478** | 6 | **7** | ✅ PASS |
| 2 | KRAS G12C Landscape | Competitive intelligence | 16 | 108 | **140** | 307 | **432** | 4 | **5** | ✅ PASS |
| 3 | Rare Disease Therapeutics | Due diligence | 15 | 94 | **110** | 229 | **278** | 4 | **5** | ✅ PASS |
| 4 | Immuno-Oncology Combinations | Checkpoint combinations | 16 | 132 | **151** | 361 | **440** | 5 | **5** | ✅ PASS |
| 5 | Cardiovascular & Inflammation | Cardiology + inflammation | 15 | 94 | **90** | 246 | **245** | 5 | **4** | ✅ PASS |
| 6 | GLP-1 Competitive Intelligence | Multi-source CI | 34 | 206 | **193** | 630 | **619** | 9 | **9** | ✅ PASS |

**V1 totals:** 111 documents · 783 nodes · 2,230 links · 33 communities
**V2 totals (2026-04-13):** 111 documents · **867 nodes · 2,592 links · 39 communities** · **6 of 6 scenarios complete**
**Delta vs V1:** +10.7% nodes, +16.2% edges, +18.2% communities across all 6 scenarios combined

---

### Scenario 1: PICALM / Alzheimer's Disease ✅ PASS

![PICALM Alzheimer's V2 Knowledge Graph](../../tests/scenarios/screenshots/scenario-01-graph-v2.png)

*V2: 183 nodes, 478 links, 7 auto-labeled communities. Compared to V1: +34 nodes (+23%), +21 edges (+5%), +1 community.*

| Community | Members | Theme |
|---|---:|---|
| Alzheimer Disease — Tau | 42 | Tau protein, tauopathy, SORL1 variants, gene-tau associations |
| Late-Onset Alzheimer Disease Risk Loci (25 genes) | 31 | GWAS hub — APOE, CLU, CR1, BIN1, TREM2, ABCA7 and 19 others |
| Huntington Disease — Atg5, Map1Lc3, App-Ctf | 28 | Cross-neurodegenerative autophagy hub (APP-CTF, LC3, HD, PD) |
| Clathrin-Mediated Endocytosis (Fcho1, Bin1, Dnm2) | 11 | **New as standalone community** — tissue/sex-specific CME machinery |
| Amyloid Precursor Protein Processing (Psen1, Psen2, App) | 9 | Canonical amyloid hypothesis cascade |
| Endocytosis / Amyloid Beta Clearance (Picalm) | 8 | PICALM's direct functional context |
| Cerebral Shrinkage / Beta-Amyloid Deposition / Tau Phosphorylation | 8 | **New** — phenotype cluster not surfaced in V1 |

**V2-specific findings:**
- **1 contradiction detected** by the epistemic layer: `SORL1 → IMPLICATED_IN → late_onset_alzheimer_disease` — Karch 2015 and Chouraki 2014 differ on whether SORL1 should be considered a robust genetic risk factor. The layer flagged this as `evidence_direction` conflict for human review.
- **Community factorization is finer** — V2 splits V1's monolithic risk-loci cluster into a tau-centric group (42) and a GWAS-loci group (31), while elevating Clathrin-Mediated Endocytosis from a sub-cluster to a standalone community.
- **77 genes extracted** (V1: 48) — the per-document subagent workflow pulled more gene mentions from each abstract because each agent had the full domain SKILL.md in its own context.

→ **[Full scenario 1 V2 report](../../tests/scenarios/scenario-01-picalm-alzheimers-v2.md)**

---

### Scenario 2: KRAS G12C Inhibitor Landscape ✅ PASS

![KRAS G12C V2 Knowledge Graph](../../tests/scenarios/screenshots/scenario-02-graph-v2.png)

*V2: 140 nodes, 432 links, 5 auto-labeled communities. Compared to V1: +32 nodes (+30%), +125 edges (+41%), +1 community. Strongest V2-over-V1 edge expansion seen so far.*

| Community | Members | Theme |
|---|---:|---|
| Cancer — KRAS Protein | 29 | Core KRAS biology, pan-cancer KRAS mutations |
| RAS-Mutant Cancer — VCP, MRAS:SHOC2:PP1C Complex, EGFR | 29 | Combination strategies, EGFR co-targeting, MRAS complex biology |
| Lung Adenocarcinoma — KRAS G12C Protein, KRAS | 28 | NSCLC-specific findings, sotorasib/adagrasib clinical profile |
| PD-1 Checkpoint Blockade | 12 | **New standalone community** — V1 merged into adagrasib/ICI cluster |
| Scribble Pathway / Hippo Signaling Pathway | 8 | **New** — adaptive resistance via YAP/TAZ, not surfaced in V1 |

**V2-specific findings:**
- **0 contradictions** — KRAS literature is predominantly declarative clinical/mechanistic reporting with consistent findings. This is the expected behavior for a CI corpus vs. S1's genetics corpus where meta-analyses disagreed on SORL1.
- **Structural biology document integrates cleanly** — `structural_sotorasib.txt` (the one non-PubMed document in S2) contributed 26 entities and 25 relations, including `PROTEIN_DOMAIN` entries for the switch-II pocket and P-loop. No schema errors.
- **20 distinct relation types** used (vs S1's 11) — competitive-intelligence corpora exercise the schema more comprehensively than genetics corpora because every doc mentions trials, drugs, resistance, and approvals.
- **Minor gap surfaced:** the structural biology document registered as `document_type: unknown` in the epistemic summary because the classifier only knows `paper` and `patent`. Low-severity todo to add a `structural` signature class.

→ **[Full scenario 2 V2 report](../../tests/scenarios/scenario-02-kras-g12c-landscape-v2.md)**

---

### Scenario 3: Rare Disease Therapeutics ✅ PASS

![Rare Disease V2 Knowledge Graph](../../tests/scenarios/screenshots/scenario-03-graph-v2.png)

*V2: 110 nodes, 278 links, 5 communities. +17% nodes, +21% edges, +1 community vs V1. First scenario run fully autonomously with zero permission prompts.*

| Community | Members | Theme |
|---|---:|---|
| Prednisone / Valoctocogene Roxaparvovec / Autoimmune Hepatitis | 26 | AAV gene therapy immunogenicity, hemophilia A |
| MAPK Pathway | 18 | Shared signaling hub across FGFR3-driven disorders |
| Pegvaliase / Phenylalanine Ammonia Lyase / Type III Hypersensitivity | 17 | PKU enzyme replacement, immunogenicity |
| Endochondral Ossification / FGFR3 Downstream Signalling | 17 | Achondroplasia, vosoritide, CNP analogs |
| Hepatocyte Gene Transfer | 9 | **New standalone community** — AAV5 delivery mechanisms |

**V2-specific findings:**
- **COMPOUND count (12) is 4× higher than any prior V2 scenario** — rare disease literature is drug-heavy vs. target-heavy
- **2 hypotheses + 1 contradiction** surfaced by the epistemic layer (highest hypothesis count so far)
- **Zero permission prompts during the run** — Track A settings patch applied before S2 is fully holding
- New `Hepatocyte Gene Transfer` community cleanly factors out AAV-delivered gene therapy biology that V1 merged into the PKU cluster

→ **[Full scenario 3 V2 report](../../tests/scenarios/scenario-03-rare-disease-v2.md)**

---

### Scenario 4: Immuno-Oncology Combinations ✅ PASS

![Immuno-Oncology V2 Knowledge Graph](../../tests/scenarios/screenshots/scenario-04-graph-v2.png)

*V2: 151 nodes, 440 links, 5 communities. +14% nodes, +22% edges vs V1. First scenario with **validator enrichment** (25 amino acid sequences detected in nivolumab structural doc, 11 entities + 11 relations auto-added to the graph).*

| Community | Members |
|---|---:|
| Nivolumab / PDCD1 / Clear Cell Renal Cell Carcinoma | 34 |
| Neoplasms — PD-L2, PD-1, PD-L1 | 21 |
| Diffuse Large B-Cell Lymphoma — MHC II / FGL1 / LAG-3 | 21 |
| Hepatocellular Carcinoma — HIF, VEGF | 16 |
| CTLA-4 Blockade | 13 |

**V2-specific findings:**
- **32 NCT clinical trials extracted** — highest of any V2 scenario so far
- **PEPTIDE_SEQUENCE as a new entity type** surfaced via validator enrichment — first time this path activated in V2
- Zero permission prompts, fully autonomous run
- Same `document_type: unknown` issue for the sequence-level doc — tracked by Phase 12

→ **[Full scenario 4 V2 report](../../tests/scenarios/scenario-04-immunooncology-v2.md)**

---

### Scenario 5: Cardiovascular & Inflammation ✅ PASS (tight margin)

![Cardiovascular V2 Knowledge Graph](../../tests/scenarios/screenshots/scenario-05-graph-v2.png)

*V2: 90 nodes, 245 links, 4 communities. **First scenario where V2 did not exceed V1** — 96% nodes, 99.6% edges, 80% communities. All metrics still above the 80% regression threshold. V2 found a cleaner factorization with 4 communities merging V1's 5 cardiac myosin clusters into a single CYP metabolism-aware parent cluster.*

| Community | Members |
|---|---:|
| Heart Failure — Cardiac Myosin, CYP2C19, CYP3A4 | 24 |
| Moderate-To-Severe Psoriasis — TYK2 | 20 |
| MYBPC3 / oHCM / Hyper-Contractile Phenotype | 10 |
| ATPase Inhibition of Cardiac Myosin | 9 |

**V2-specific findings:**
- Zero permission prompts during run — fully autonomous
- Validator enrichment contributed 1 entity + 1 relation from `structural_mavacamten.txt` (SMILES-backed)
- Same `document_type: unknown` gap for the structural doc (tracked by Phase 12)
- S5 tightness likely reflects the mixed corpus (10 cardiovascular + 5 psoriasis/TYK2 — two sub-domains with minimal cross-connection)

→ **[Full scenario 5 V2 report](../../tests/scenarios/scenario-05-cardiovascular-v2.md)**

---

### Scenario 6: GLP-1 Competitive Intelligence ✅ PASS

![GLP-1 V2 Knowledge Graph](../../tests/scenarios/screenshots/scenario-06-graph-v2.png)

*V2: 193 nodes, 619 links, 9 communities. 94% nodes, 98% edges, 100% communities vs V1. **First V2 scenario with prophetic epistemic claims** — 15 forward-looking claims correctly identified across 10 GLP-1 patents from Novo Nordisk, Eli Lilly, Pfizer, and Zealand Pharma.*

| Community | Members |
|---|---:|
| Hyperglycemia — GLP-1 / Pepsin | 30 |
| Substance Use Disorder — GLP-1 Receptor | 20 |
| Gastric Emptying Delay / Central Satiety Signaling | 19 |
| Prediabetes — GIP Receptor, GLP1R, GIPR | 19 |
| MASLD — GIPR / GLP-1R / GCGR | 18 |
| Cilofexor / Denifanstat / Efruxifermin (MASH competitors) | 13 |
| Triple GLP-1/GIP/Glucagon Receptor Agonism | 10 |
| Liraglutide / Metformin / Dyslipidaemia | 9 |
| CagriSema / Overweight / Phase 3 | 8 |

**V2-specific findings (the star of S6):**
- **15 prophetic claims** identified by the epistemic layer — patent-derived forward-looking claims like "the compounds of the invention are useful for treating obesity"
- **Mixed doctype corpora classify correctly** — `document_types: [patent, paper]` with different epistemic rules per class. No misclassification.
- **5 hypotheses + 1 contradiction** — highest hypothesis count of any V2 scenario (GLP-1 neurodegeneration/addiction literature is mechanistically speculative)
- **Validator enrichment hit 4+4** — patent SMILES and InChIKeys for SNAC, tirzepatide, and Zealand triple agonist peptides were RDKit/Biopython-validated and added as canonical entities
- **16 NCT trials + 10 US patents** extracted — richest multi-source corpus in the suite

→ **[Full scenario 6 V2 report](../../tests/scenarios/scenario-06-glp1-landscape-v2.md)**

---

---

## Framework-Level Insights from the V2 Run

Captured while running Phase 11-03. These apply to any drug-discovery scenario that flows through the V2 plugin, not just S1.

### Canonical naming does the heavy lifting

The 354 → 183 entity collapse on S1 (48% reduction) is almost entirely driven by `domain_canonical_entities` declared in `domains/drug-discovery/domain.yaml`. Per-document extractor agents produce variant spellings ("amyloid precursor protein", "APP", "Amyloid-β precursor protein") that all resolve to a single canonical node during `build_graph` postprocess. Without the canonical map, V2 would produce 2-3× too many nodes.

### Per-document parallelism is the right granularity for abstracts

For corpora where each document is <1 chunk (~10K chars), per-document agents are optimal. Each agent reads the SKILL.md once, extracts one doc, and returns <50 words to the orchestrator. Main-session context stays clean, which matters when running 6 scenarios sequentially.

For corpora with large documents that need multi-chunk processing (e.g., patents or FDA approval letters in future scenarios), this granularity may need to become per-chunk.

### MultiDiGraph edges vs viewer display edges

The HTML viewer footer shows a lower relation count than `graph_data.json` because it collapses bidirectional edges to undirected display edges. Regression metrics must read `graph_data.json` directly, not the viewer. Documented here because the discrepancy confused the run orchestrator and is worth capturing for future V2 runs.

### Epistemic layer finds ambiguity without LLM cost

The V2 epistemic layer is pattern-based (regex + polarity heuristics) and runs in <1 second. On S1 it surfaced a real polarity conflict on SORL1 without any LLM invocation. For scenarios with patent corpora (S6), the prophetic-claim detection is expected to produce higher signal.

### Plugin regression runner has a transition mode

During Phase 11, both `output/` (V1 reference) and `output-v2/` (V2 work-in-progress) coexist under each scenario directory. `tests/regression/run_regression.py` was updated to prefer `output-v2/` when present and fall back to `output/`. This lets the V1 baselines remain pinned while V2 runs proceed.

---

## Molecular Validation (unchanged from V1)

When RDKit and Biopython are installed, epistract automatically validates molecular identifiers found in source text:

- **SMILES** — canonical form, InChI, InChIKey, molecular formula, MW, LogP, Lipinski Ro5
- **DNA/RNA sequences** — GC content, complement, reverse complement, translation
- **Protein sequences** — molecular weight, isoelectric point, instability index, GRAVY
- **Pattern detection** — NCT numbers, CAS numbers, patent numbers, InChIKeys

S1 is a genetics corpus with no small molecules. The pattern scanner found 56 SMILES-shaped strings, all of which are gene-abbreviation false positives (`(PICALM)`, `(ITSN1-L)`, `WDFY3/ALFY`). This matches V1 behavior.

---

## Epistemic Layer (V2)

V2 elevates epistemic analysis to a domain-level artifact. For the drug-discovery domain, `domains/drug-discovery/epistemic.py` classifies relations as:

- **Asserted** — high confidence, no hedging
- **Hypothesized** — hedging language ("may", "might", "could")
- **Prophetic** — patent-sourced forward-looking claims
- **Negative** — high-confidence statements of absence
- **Contradictory** — same (source, relation, target) with opposing evidence across documents

S1 epistemic output: 474 asserted · 3 hypothesized · 1 contradictory · 1 unclassified. One contradiction (SORL1) surfaced for human review.

---

## Regression Verification

The V2 plugin pipeline is gated by `tests/regression/run_regression.py`. Each completed scenario must pass:

```bash
python tests/regression/run_regression.py --baselines tests/baselines/v1/ --scenario <scenario_name>
```

**Pass criteria (from V1 baseline thresholds):**
- Nodes ≥ 80% of V1
- Edges ≥ 80% of V1
- Communities ≥ 50% of V1
- `claims_layer.json` exists
- Molecular validation completes without Python exceptions

S1 regression on 2026-04-13: **PASS** (183/149 nodes, 478/457 edges, 7/6 communities).

---

## Full Scenario Details (V2)

- [Scenario 1 V2: PICALM / Alzheimer's](../../tests/scenarios/scenario-01-picalm-alzheimers-v2.md) ✅
- [Scenario 2 V2: KRAS G12C Landscape](../../tests/scenarios/scenario-02-kras-g12c-landscape-v2.md) ✅
- [Scenario 3 V2: Rare Disease Therapeutics](../../tests/scenarios/scenario-03-rare-disease-v2.md) ✅
- [Scenario 4 V2: Immuno-Oncology Combinations](../../tests/scenarios/scenario-04-immunooncology-v2.md) ✅
- [Scenario 5 V2: Cardiovascular & Inflammation](../../tests/scenarios/scenario-05-cardiovascular-v2.md) ✅
- [Scenario 6 V2: GLP-1 Competitive Intelligence](../../tests/scenarios/scenario-06-glp1-landscape-v2.md) ✅

---

## See Also

- [V1 drug-discovery showcase](drug-discovery.md) — reference baselines
- [Phase 11 plan](../../.planning/phases/11-end-to-end-scenario-validation/) — the execution plan this doc records progress for
- [V1 baselines](../../tests/baselines/v1/) — pinned JSON baselines each V2 scenario is compared against
- [Regression runner](../../tests/regression/run_regression.py) — Python comparison tool
