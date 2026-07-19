# Epistract Visionary Audit & Roadmap

**Date:** 2026-07-15  
**Auditor posture:** Independent code reviewer + research auditor  
**Branch audited:** `feat/multi-project-cli`  
**Intent:** Critique what Epistract should do but does not yet; map frontier research; propose a product vision worthy of a keynote.

---

## 0. Executive Thesis (one slide)

**Epistract is not “another GraphRAG.”**

It is the **epistemic operating system for a decision** — the system that takes a curated body of documents, extracts *what is claimed*, grades *how much we should believe it*, and returns a graph an analyst can *defend in a review meeting*.

The frontier is not bigger graphs. The frontier is **calibrated knowledge under uncertainty**:

> **Every edge is a claim. Every claim has a warrant. Every warrant has a time of validity. Every contradiction is a first-class citizen. Every gap is an actionable experiment.**

If Microsoft GraphRAG is “find related clusters,” and PaperQA2 is “answer with citations,” Epistract’s destiny is:

> **“Tell me what this corpus asserts, disputes, prophecies, and omits — with molecular truth, regulatory grade, and decision-grade provenance.”**

That is a Jobs-class product idea: *one instrument, one corpus, one decision.*  
That is an Elon-class execution problem: *close the loop from claim → evidence → action → next corpus, relentlessly.*

---

## 1. What Exists Today (honest strengths)

### 1.1 Product positioning (already excellent)

Epistract’s README thesis is correct and rare:

| Audience | Tool they already have | Gap Epistract fills |
|----------|------------------------|---------------------|
| Enterprise KG team | Neo4j / Neptune / Anzo | Too slow, too broad for a 30-paper decision |
| Literature RAG | PaperQA / Perplexity / Elicit | Flat retrieval; no typed science; weak epistemic status |
| GraphRAG clones | Similarity edges | Cannot distinguish inhibits vs activates |
| Ontology platforms | Protégé + committee | Months before first useful graph |

**Design point is right:** small–medium corpora (7–34 docs in validated scenarios), specialist-owned, archive-when-done.

### 1.2 Architecture that already works

| Layer | What ships | Why it matters |
|-------|------------|----------------|
| Domain packages | YAML schema + SKILL + epistemic.py + workbench template | Zero pipeline code for new domains |
| Two-layer KG | Brute facts + epistemic super-domain | Status vocabulary: asserted / hypothesized / prophetic / contested / contradiction / negative / speculative |
| Extraction contract | Pydantic `DocumentExtraction` | Fails loud; honest provenance fields |
| Molecular ground truth | RDKit + Biopython validators | Nodes that are real chemistry/biology, not tokens |
| Multi-agent harness | Claude Code plugin + extractor agents | Parallel docs; no platform team |
| Workbench | Graph + chat + persona-driven narrator | Same graph for briefing and Q&A |
| Quality modules (2026-07) | triple_judge, entity_resolution_v2, hedging, epistemic_temporal, graph_retrieval, index_db, multi-project CLI | Research-backed upgrades already in-tree |

### 1.3 Validated track record

- 6 drug-discovery scenarios + clinicaltrials + FDA labels + contracts scaffold + pharmacovigilance community domain  
- Paper-reported: 111 docs → 783 nodes / 2,230 links; 100% entity type coverage; 93% relation type coverage; 25/25 UATs  
- GLP-1 multi-source (PubMed + patents) is the “hero demo” — prophetic vs asserted is the keynote moment  

### 1.4 Research literacy already above average

Internal survey (`docs/plans/2026-07-04-arxiv-research-notes.md`) adopted:

| Technique | Paper | Module |
|-----------|-------|--------|
| Personalized PageRank retrieval | HippoRAG 2 (2502.14802) | `graph_retrieval.py` |
| Delta indexing | iText2KG (2409.03284) | `index_db.py` (partial) |
| LLM-as-judge triples | GraphJudge / GraphEval | `triple_judge.py` |
| Budgeted ER | ComEM / BoostER | `entity_resolution_v2.py` |
| Bi-temporal invalidation | Zep/Graphiti (2501.13956) | `epistemic_temporal.py` |
| Contradiction cascade | LegalWiz / ContraCrow | `epistemic_temporal.py` (lexical) |
| Graded hedges | UnScientify + hedge-detection | `hedging.py` |

**This is a real product foundation, not a weekend demo.**

---

## 2. Independent Audit — Gaps (what it should do but does not)

Organized by severity for product destiny, not just code smell.

### 2.1 CRITICAL — Product integrity & scale of ambition

#### G1. The “domain-agnostic” promise leaks domain-specific core

Evidence in `core/`:

- `DEFAULT_DOMAIN = "drug-discovery"` and aliases hardwired  
- `run_sift.py` falls back to drug-discovery when `--domain` missing  
- `label_epistemic.py` defaults domain to drug-discovery  
- `ingest_documents.KNOWN_CATEGORIES` = hotel/pcc/av/catering (contracts event venues)  
- `entity_resolution.PROTECTED_NAMES` includes “pennsylvania convention center authority”  
- Community labeling still carries biomedical/contract branches  

**Impact:** New domains inherit pharmaceutical bias; contracts residue poisons generic core.  
**Jobs test fails:** A tool that claims “any domain” must feel empty until the domain package arrives — not half-drug, half-hotel.

#### G2. Pipeline is still two products glued together

Surfaces today:

1. Claude Code slash commands (`/epistract:ingest`, …) — agent-orchestrated  
2. Standalone CLI (`epistract init/index/search/enhance`) — partial  

**Not fully closed:**

- `epistract index` does not yet drive full extract + build (roadmap Phase 1 unchecked)  
- Graph merge without rebuild is deferred  
- Version skew: plugin 3.2.x vs `pyproject` 3.0.0  
- Packaging: `uv pip install -e .` alone is incomplete (setup.sh owns real deps)

**Impact:** “One command to insight” is aspirational; power users stitch steps.

#### G3. Quality gates default to *lexical* when the brand is *epistemic*

| Module | Default behavior | Full power |
|--------|------------------|------------|
| `triple_judge` | Token overlap of endpoints in evidence | LLM judge via injectable `judge_fn` |
| Contradiction | Antonym relation pairs + negation regex | NLI/LLM `adjudicate_fn` (not wired) |
| Hedging | Weighted cue density | Injectable classifier (not wired) |
| Entity resolve | String/token similarity | Embedding + LLM select (embed path incomplete) |

**Impact:** Keynote demos can look brilliant under LLM extraction; offline/default path is weaker than the paper’s epistemic story. Brand risk: *prophetic claims* look magical; *systematic contradiction mining* is still thin vs PaperQA2’s ContraCrow (~2.3 contradictions/paper with expert validation).

#### G4. No public ontology grounding at link time

Schemas *reference* ontologies (INN, HGNC, MedDRA, etc.) in docs and prompts. Runtime does **not** systematically:

- Resolve drug → RxNorm / ChEMBL / DrugBank ID  
- Resolve gene → HGNC / Ensembl  
- Resolve disease → MONDO / MeSH / ICD  
- Resolve AE → MedDRA PT  
- Resolve compound → InChIKey (partial via RDKit when SMILES present)

**Impact:** Cross-project merge, multi-corpus federation, and regulatory export remain fuzzy-string problems. Competitors in bioinformatics (Open Targets, Hetionet, PrimeKG) win on **stable identifiers**.

#### G5. Scale ceiling is deliberate — but undocumented as a product limit

Design point ~ dozens of documents. Missing:

- Hard performance envelopes (docs, nodes, latency, $ cost)  
- Streaming / map-reduce extract for 1k–10k papers  
- Incremental merge (iText2KG full pattern)  
- Vector index (sqlite-vec deferred)

**Impact:** Users who try “my whole PubMed export” will hate the product without a clear “this is a decision graph, not a warehouse” guardrail + export path.

### 2.2 HIGH — Research-grade knowledge quality

#### G6. Claim unit is still the *edge*, not the *atomic scientific claim*

PaperQA2 / ContraCrow extract **atomic claims**, then mine support/contradiction against literature.  
Epistract extracts **typed triples** with evidence spans — stronger structure, weaker claim science.

Missing claim-centric layer:

```
Claim {
  assertion, polarity, quantifiers, population, endpoint,
  study_design, n, effect_size, p_value / CI,
  source_span, doc_id, epistemic_status,
  supports[], contradicts[], supersedes[]
}
```

Without this, “61 prophetic claims” is impressive marketing but not interoperable with nanopublications / PROV-O / clinical evidence standards.

#### G7. No study-design / evidence hierarchy beyond domain heuristics

FDA domain has established/observed/reported/theoretical — excellent.  
Drug-discovery largely relies on hedging + doc_type (patent/paper/structural).

Missing Bradford-Hill style / GRADE / CEBM ladders as first-class:

- RCT > cohort > case report > in vitro > in silico > patent prophecy  
- Sample size and endpoint type should modulate confidence, not just prose hedges  

Pharmacovigilance domain starts this (Bradford-Hill); it should become **core epistemic protocol**, not a fork feature.

#### G8. No coverage / hallucination regression as CI gate

Deferred from KGGen MINE (2502.09956) and hallucination metrics (2502.05239):

- Sample atomic facts per doc at ingest  
- Assert KG entails ≥ X%  
- Report hallucinated triples vs omitted facts  

Without this, schema coverage % is a vanity metric; **truth coverage** is unknown.

#### G9. Temporal & versioning is half-built

`epistemic_temporal` has valid_at / invalid_at / superseded_by.  
Not productized:

- Document publication date → edge validity by default  
- Patent priority date vs grant date vs paper date  
- “What did we believe last Tuesday?” replay  
- PROV-STAR / RDF-star export of statement-level provenance  

### 2.3 HIGH — Experience & agency

#### G10. Acquisition is second-class relative to consolidation thesis

README says Claude Code acquires; Epistract consolidates. Still:

- `/epistract:acquire` + scripts for PubMed/CT.gov/FDA/FAERS exist but are uneven  
- No unified “research brief → corpus plan → fetch → triage” agent loop  
- Paywalled literature still “bring your own PDF” with no institutional connector story  

FutureHouse PaperQA2’s strength is **agentic search + citation traversal**. Epistract’s strength is **schema + epistemology**. The merge is obvious and unimplemented.

#### G11. Workbench is a viewer, not a war room

Ships: graph viz, chat, sources, persona briefing.  
Missing for keynote-grade:

- Claim timeline / epistemic heatmap  
- Contradiction workspace (side-by-side evidence)  
- Gap-driven experiment designer (“three studies to close this”) as interactive objects  
- Human-in-the-loop edge adjudication that writes back to graph  
- Collaborative multi-analyst projects with review states  
- Diff two project snapshots (before/after new papers)

#### G12. No compounding across decisions (Issue #15)

Each project is an island. The aspirational mechanism — **what we learned about the domain schema, entity aliases, and contested edges from prior runs** — is not implemented.  
Without memory of analyst corrections, every project relearns “semaglutide ≈ Ozempic ≈ Wegovy active moiety” from scratch.

### 2.4 MEDIUM — Engineering excellence

| ID | Gap | Detail |
|----|-----|--------|
| E1 | Incomplete packaging | Real install = setup.sh; pyproject under-declares deps |
| E2 | Dual CLI parsers | New argparse CLI vs legacy `sys.argv` scripts |
| E3 | Two-site convention sync | Structural doctype duplicated core ↔ domain |
| E4 | No formal evaluation harness in CI for LLM paths | Baselines exist; LLM judge/NLI not default CI |
| E5 | Cost/latency telemetry | model_used/cost on extractions; no project-level burn dashboard |
| E6 | Security posture | Workbench hardened (v3.2.2); local file graphs still assume trusted environment |
| E7 | Export federation | GraphML/CSV/SQLite/OKF; no Neo4j/RDF-star/nanopub one-click that preserves epistemic attrs |
| E8 | Domain wizard | Good; AutoSchemaKG/EDC-style canonicalize deferred |

### 2.5 What competitors / peers do better

| System | Strength vs Epistract | Epistract counter-strength |
|--------|----------------------|----------------------------|
| **PaperQA2** (FutureHouse) | Superhuman LitQA; agentic search; contradiction mining with expert validation | Typed domain schemas; molecular validation; prophetic patent status; decision-corpus focus |
| **Microsoft GraphRAG / LazyGraphRAG** | Hierarchical community summaries; cheap lazy indexing | Comprehension edges not similarity; epistemic status |
| **LightRAG** | Dual-level routing; incremental union-merge | Richer schema + domain packages |
| **Zep/Graphiti** | Production bi-temporal agent memory | Scientific evidence vocabulary; domain validators |
| **Open Targets / PrimeKG / Hetionet** | Huge multi-omics graphs, stable IDs | Instant project graphs from *your* PDFs; analyst narrative |
| **Neo4j + LLM plugins** | Enterprise scale & ops | No ontology committee; Claude Code harness; epistemic layer |
| **Elicit / Consensus / Scite** | Literature UX at scale | Local corpus sovereignty; exportable KG; patents + labels + trials in one schema |
| **MedKGent / KARMA (papers)** | Multi-agent enrichment architectures | Shipped product + demos + domains |

**White space only Epistract can own:**  
*Decision-scoped, schema-constrained, epistemically graded, chemically validated knowledge graphs built in a working session.*

---

## 3. Frontier Research Map (what to absorb next)

### 3.1 Already internalized (keep deepening)

- HippoRAG 2, GraphJudge, GraphEval, ComEM, BoostER, Graphiti, LegalWiz, PaperQA2/ContraCrow, UnScientify, iText2KG (partial)

### 3.2 Highest-ROI next adoptions

| Priority | Work | Citation / source | Product effect |
|----------|------|-------------------|----------------|
| P0 | Wire NLI adjudicator (DeBERTa-MNLI) into contradiction cascade | LegalWiz 2510.03418 | Real contested/contradiction rates |
| P0 | Default LLM triple judge in `enhance` / post-extract | GraphJudge 2411.17388 | Brand-aligned quality |
| P0 | Atomic claim extraction + ContraCrow-style corpus scan | PaperQA2 2409.13740 | Superhuman synthesis parity on *your* corpus |
| P1 | Dual-level query routing + lazy community summary | LightRAG 2410.05779; LazyGraphRAG | Chat that feels omniscient without $ ingest tax |
| P1 | Match-before-insert graph merge | iText2KG 2409.03284 | Living projects, not rebuilds |
| P1 | MINE-style coverage CI | KGGen 2502.09956 | Honest quality dashboard |
| P1 | Nanopub-lite claim records + RDF-star/PROV export | PROV-STAR; nanopublications; RDF 1.2 star | Regulatory & publishable artifacts |
| P2 | AutoSchemaKG + EDC canonicalize in wizard | 2505.23628; 2404.03868 | Domains in minutes that don’t suck |
| P2 | Ontology linkers (RxNorm, HGNC, MONDO, ChEMBL, MedDRA) | NLM RxNorm; UniProt; ChEMBL | Federated multi-project science |
| P2 | Study-design / GRADE layer | Evidence-based medicine literature | Confidence that pharma reviewers trust |
| P3 | Citation-graph traversal as acquisition tool | PaperQA2 citation tool | Better corpora before extract |
| P3 | Multi-agent enrichment (verifier/conflict agents) | KARMA 2502.06472; MedKGent 2508.12393 | Optional “deep mode” |

### 3.3 bioRxiv / PubMed / patents-specific techniques

- **Structured abstract / IMRAD-aware chunking** — methods vs results vs claims sections change epistemic prior  
- **ClinicalTrials.gov protocol + results linkage** — already started in clinicaltrials domain; make primary key NCT-centric  
- **SPL / openFDA section-aware extraction** — boxed warning ≠ adverse reactions narrative  
- **Patent claim vs description vs embodiment** — prophetic language is structural to patents, not just hedging regex  
- **FAERS disproportionality signals** — pharmacovigilance domain; promote as first-class signal nodes, not only free text  
- **Figure/table extraction** — forest plots and AE tables are where truth lives; pure text pipelines under-extract  

### 3.4 Explicit non-goals (stay sharp)

Reject becoming:

1. A general web search engine  
2. A permanent enterprise master data platform (export instead)  
3. An untyped embedding soup  
4. A closed SaaS that traps the graph  

---

## 4. Vision: What Epistract Becomes (keynote narrative)

### Act I — The problem (30 seconds)

Science and regulation do not fail from lack of papers.  
They fail from **undifferentiated knowledge**:  
asserted trial results sit next to patent prophecies next to blog-grade hypotheses in the same retrieval blob.

Executives get dashboards.  
Specialists get PDFs.  
Neither gets a **defensible map of belief**.

### Act II — The instrument (60 seconds)

Epistract is the **decision microscope**.

1. Point at a question-bounded corpus.  
2. Extract a **typed molecular graph** (chemistry is real or it doesn’t enter).  
3. Stamp every relation with **epistemic status** and **evidence warrants**.  
4. Invalidate, don’t delete, when the corpus contradicts itself.  
5. Brief the analyst like a colleague who read everything and ranked the fights.

Demo beat (already real on GLP-1):  
*“Sixty-one prophetic patent claims about cardiovascular and neurodegenerative use — against asserted Phase 3 outcomes in diabetes and obesity. Here are the three studies that would close the gap.”*

### Act III — The future product (90 seconds)

**Epistract OS for Knowledge Decisions**

Not a plugin alone — a **protocol**:

```
Corpus → Claims → Graph → Belief State → Decision → Archive → Compounding Memory
```

Five iconic capabilities:

1. **Belief State** — a first-class object: what we currently hold true, contested, prophetic, gap-ridden  
2. **Warrant Cards** — every edge opens to study design, quote, IDs, judge score, temporal validity  
3. **Contradiction Arena** — ContraCrow-class mining *inside your decision corpus* (and optional literature expansion)  
4. **Ontology Spine** — every node wears stable IDs; projects federate without string soup  
5. **Decision Diff** — “What changed in our KRAS graph when the 2026 NEJM paper landed?”

Close line:

> *We did not build a bigger knowledge graph.  
> We built a machine that knows how little it knows — and shows you where to look next.*

---

## 5. Roadmap — Phased to Awesome

Horizon language: **Now / Next / Later / Moonshot**  
Aligned with existing `2026-07-04-multi-project-cli-TODO.md` but extended to product vision.

### Horizon 0 — Finish the foundation (4–6 weeks)

**Theme:** One pipeline, honest defaults, domain purity.

| # | Work | Exit criteria |
|---|------|---------------|
| H0.1 | Domain leakage purge from core (G1) | Contracts hotel categories & PCC names live only in domains/contracts |
| H0.2 | `epistract index` runs extract→normalize→build→optional enhance | One command path documented |
| H0.3 | Version single-source (plugin = pyproject = marketplace) | One version string |
| H0.4 | Full dependency declaration in pyproject / uv lock path | `uv sync && epistract --help` works |
| H0.5 | Wire LLM judge + NLI hooks as default when API keys present | Lexical only when offline; logged mode |
| H0.6 | Domain-specific antonym maps from domain.yaml | No hardwired INCREASES/DECREASES only |
| H0.7 | Fix workbench “edges” vs “links” and remaining hardcodes (Phase 2 TODO) | Persona always from template |

### Horizon 1 — Decision Graph 1.0 (1–2 quarters)

**Theme:** Claims, coverage, living projects.

| # | Work | Research anchor |
|---|------|-----------------|
| H1.1 | Atomic **Claim** layer above triples | PaperQA2 / nanopubs |
| H1.2 | ContraCrow-in-corpus + optional expand-to-literature | 2409.13740 |
| H1.3 | Graph merge without full rebuild | iText2KG / LightRAG |
| H1.4 | sqlite-vec + embeddings for search & ER | HippoRAG + ComEM |
| H1.5 | Dual-level routing + lazy community summary in `/ask` | LightRAG / LazyGraphRAG |
| H1.6 | MINE-style coverage + hallucination report per project | KGGen |
| H1.7 | Ontology linkers v1 (RxNorm, HGNC, MONDO, ChEMBL, InChIKey) | NLM / ChEMBL APIs |
| H1.8 | Study-design / evidence-grade core protocol | GRADE + FDA tier generalization |
| H1.9 | Belief State API + workbench Contradiction Arena | Product UX |
| H1.10 | Cost/latency dashboard per project | Ops excellence |

**Keynote demo at end of H1:**  
Import 40 papers + 10 patents → open Belief State → click contested edge → see NLI+LLM adjudication → export nanopub-lite pack for the review board.

### Horizon 2 — Knowledge OS (2–4 quarters)

**Theme:** Compounding, federation, multi-agent depth.

| # | Work |
|---|------|
| H2.1 | Cross-project **compounding memory** (Issue #15): alias tables, schema refinements, adjudicated edges |
| H2.2 | Multi-agent “deep enhance”: extractor / verifier / conflict / gap agents (KARMA-inspired) |
| H2.3 | Agentic acquisition: research plan → fetch → triage → human approve → index |
| H2.4 | Citation traversal + institutional PDF dropbox connectors |
| H2.5 | RDF-star / PROV-STAR / Neo4j export with full epistemic attrs |
| H2.6 | Collaborative projects: review queues, signed adjudications, audit log |
| H2.7 | Domain marketplace (signed packages; pharmacovigilance-class community domains) |
| H2.8 | Evaluation suite: LitQA-style questions *on scenario corpora* with frozen gold |
| H2.9 | Multimodal: table/figure extraction for AE tables, forest plots, patent Markush (scoped) |
| H2.10 | Policy packs: HIPAA/GxP modes (local-only models, sealed export) |

### Horizon 3 — Moonshots (visionary, Elon-scale)

| Moonshot | Description |
|----------|-------------|
| **M1. World Model of a Franchise** | Continuously updated belief state for a drug franchise (e.g., GLP-1) from open literature + labels + trials + FAERS — with human gate on every status promotion |
| **M2. Experiment Co-pilot** | Gaps auto-compile into protocol sketches + power calculations + competing claim map |
| **M3. Regulatory Submission Twin** | FDA-label / CTD-aligned graph that diffs sponsor claims vs public evidence |
| **M4. Cross-domain Transfer** | Same epistemic OS for climate policy, semiconductor supply chain, case law — without rewriting core |
| **M5. Self-auditing Science** | Continuous ContraCrow across open full-text; publish contradiction feeds as public good |
| **M6. Edge Runtime** | Fully air-gapped biomedical decision graph on-prem with local LLMs + local ontology mirrors |

---

## 6. Design Principles (constitution)

Write these on the wall; reject features that violate them.

1. **Comprehension over proximity** — edges mean science, not cosine.  
2. **Every edge is a claim with a warrant** — no free-floating structure.  
3. **Invalidate, don’t delete** — history is epistemic gold.  
4. **Chemistry/biology must be real** — validators are not optional chrome.  
5. **Domain packages own meaning; core owns mechanism** — zero leakage.  
6. **Decision-scoped by default** — warehouse scale is export, not ego.  
7. **Offline-capable, online-excellent** — lexical floors; LLM ceilings.  
8. **Analyst is sovereign** — HITL adjudication writes truth; models propose.  
9. **Measure truth coverage, not just schema coverage.**  
10. **Archive is a feature** — finish the decision; compound the learning.

---

## 7. Success Metrics (what “awesome” means numerically)

| Metric | Today (approx) | Awesome target |
|--------|----------------|----------------|
| Time corpus → first Belief State | ~20–40 min / 30 docs | <10 min interactive; <60 min for 200 docs |
| Triple support rate (LLM judge) | Unknown / lexical only default | ≥90% supported or explicitly partial |
| Contradiction precision (human spot-check) | Heuristic | ≥70% expert-validated (PaperQA2 bar ~70%) |
| Ontology link rate (drugs/genes) | Low / prompt-only | ≥85% of named drugs/genes |
| MINE coverage on scenario corpora | Not measured | ≥80% atomic facts entailed |
| Domain creation time | ~15 min wizard | <10 min + canonicalized types |
| Zero-leak domain switch test | Fails (core defaults DD) | Pass contracts↔FDA↔drugs with same core binary |
| Analyst correction reuse | None | ≥50% of aliases reused on next project in domain |
| Export fidelity | Structure yes; epistemic partial | Round-trip epistemic attrs to Neo4j/RDF-star |

---

## 8. Recommended Immediate Priority Stack

If only **five** things happen after this audit:

1. **Purge domain leakage from core** — restore the product’s integrity.  
2. **Claim layer + wired LLM/NLI quality path** — make epistemology real by default.  
3. **Close the CLI loop** (`index` = full pipeline; merge deltas).  
4. **Ontology IDs on nodes** — future-proof federation.  
5. **Contradiction Arena in workbench** — the keynote UI.

Everything else is amplification.

---

## 9. Closing auditor note

Epistract already has something most open-source KG tools lack: **a clear user**, **a sharp non-goal list**, **a two-layer epistemic story**, and **research-aware engineering**.

What separates a clever plugin from a generational tool is not another entity type. It is the courage to:

- measure honesty (coverage, hallucination, contradiction precision),  
- ground symbols in the real world (ontologies, molecules),  
- and ship a **Belief State** people will stake a career decision on.

That is the plan.  
That is the product.  
That is worth a keynote.

---

## Appendix A — Codebase map (audit snapshot)

| Area | Path | LOC (order) | Health |
|------|------|-------------|--------|
| Core pipeline | `core/` | ~8–9k | Strong; leakage + dual surfaces |
| Domains | `domains/*` | 5 packages | drug-discovery mature; others uneven |
| Workbench | `examples/workbench/` | ~1.5k | Good UX; not yet war room |
| CLI | `core/cli.py` | ~500 | New multi-project; not full pipeline |
| Tests | `tests/` | broad unit/integration/e2e | Strong structure; LLM paths optional |
| Paper | `paper/` | submission-ready narrative | Align roadmap to v4 claims carefully |
| Research notes | `docs/plans/2026-07-04-arxiv-research-notes.md` | excellent | Execute deferred rows |

## Appendix B — Primary external references

- PaperQA2 — arXiv:2409.13740; github.com/Future-House/paper-qa  
- HippoRAG 2 — arXiv:2502.14802  
- GraphJudge — arXiv:2411.17388; GraphEval — arXiv:2407.10793  
- LightRAG — arXiv:2410.05779; LazyGraphRAG (MSR)  
- iText2KG — arXiv:2409.03284  
- Zep/Graphiti — arXiv:2501.13956  
- LegalWiz — arXiv:2510.03418  
- KGGen / MINE — arXiv:2502.09956  
- AutoSchemaKG — arXiv:2505.23628; EDC — arXiv:2404.03868  
- MedKGent — arXiv:2508.12393; KARMA — arXiv:2502.06472  
- PROV-STAR / RDF-star provenance literature; nanopublications + PROV-K  
- RxNorm (NLM), ChEMBL, Open Targets, UniProt, MONDO, MedDRA  

## Appendix C — Alignment with in-repo TODOs

This vision **extends** rather than replaces `docs/plans/2026-07-04-multi-project-cli-TODO.md`:

- Phases 1–2 unchecked items → Horizon 0  
- Phases 3–6 deferred quality → Horizon 1  
- Phase 7 wizard + Issue #15 compounding → Horizon 2  
- Moonshots are new and intentionally beyond current roadmap  

---

*End of report.*
