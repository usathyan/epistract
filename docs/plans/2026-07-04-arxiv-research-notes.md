# arXiv Research Notes — Multi-Project CLI + KG Quality Upgrades

**Research conducted:** 2026-07-04
**Notes reconstructed:** 2026-07-11

## How this research was conducted

A 30+ paper arXiv sweep was run via subagent on 2026-07-04 to inform the multi-project CLI +
KG quality upgrades PR (`feat/multi-project-cli`, now merged). The subagent verified all arXiv
IDs via arxiv.org search/fetch and pulled licenses/stars live from the GitHub API on that date.
The main agent then synthesized the survey into the phased roadmap at
`docs/plans/2026-07-04-multi-project-cli-TODO.md`.

These notes were reconstructed on 2026-07-11 from the archived 2026-07-04 session. Per-paper
rationale is reconstructed from the session extract (the subagent's survey plus the main-agent
synthesis) cross-checked against the roadmap's checkbox status and the citations in the shipped
`core/` modules. Anything not confirmable from those sources is marked `[unverified]`.

Status semantics:

- **Adopted** — implemented in a shipped core module (roadmap checkbox `[x]` and a module cites it).
- **Deferred** — on the roadmap but still unchecked `[ ]`.
- **Rejected** — evaluated in the sweep but neither adopted nor placed on the roadmap. Rejected
  entries appear only in the sweep report (by definition — they never reached the roadmap);
  their rationale is paraphrased from the sweep's own assessment. This bucket includes surveys
  and benchmarks that contributed design evidence but had no adoptable technique.

## Summary

| arXiv ID | Paper | Technique | Status | Maps to |
|----------|-------|-----------|--------|---------|
| 2502.14802 | HippoRAG 2 ("From RAG to Memory") | Personalized PageRank retrieval over phrase+passage graph | Adopted | `core/graph_retrieval.py` (Phases 3–4) |
| 2409.03284 | iText2KG | Incremental construction: delta detection + match-before-insert merge | Adopted (delta detection); graph merge Deferred | `core/index_db.py` (Phase 3); merge still Phase 3 TODO |
| 2411.17388 | GraphJudge | LLM-as-judge triple gate against evidence span | Adopted | `core/triple_judge.py` (Phase 5) |
| 2407.10793 | GraphEval | Triple-level NLI hallucination localization | Adopted | `core/triple_judge.py` (Phase 5) |
| 2405.16884 | ComEM ("Match, Compare, or Select?") | Compound block → shortlist → LLM-select entity resolution | Adopted | `core/entity_resolution_v2.py` (Phase 5) |
| 2401.03426 | BoostER | Budgeted LLM verification of high-uncertainty match candidates | Adopted | `core/entity_resolution_v2.py` (Phase 5) |
| 2501.13956 | Zep / Graphiti | Bi-temporal edges; invalidate-don't-delete on contradiction | Adopted | `core/epistemic_temporal.py` (Phase 6) |
| 2510.03418 | LegalWiz | Similarity filter → NLI → LLM-judge contradiction cascade | Adopted (NLI hookup still TODO) | `core/epistemic_temporal.py` (Phase 6) |
| 2409.13740 | PaperQA2 / ContraCrow | Claim-centric contradiction mining against the corpus | Adopted (NLI hookup still TODO) | Phase 6 contradiction cascade (`core/epistemic_temporal.py`, via roadmap citation) |
| 2405.13319 | "You should probably read this": Hedge Detection in Text | Lexical/POS hedge-cue detection | Adopted | `core/hedging.py` (Phase 6) |
| 2307.14236 | UnScientify | Weakly-supervised scientific-uncertainty detection with span ID | Adopted (cue inventories) | `core/hedging.py` (Phase 6) |
| 2410.05779 | LightRAG | Dual-level query routing; union-merge incremental insertion | Deferred | Phase 4 (routing) + Phase 3 (merge) |
| no arXiv ID | LazyGraphRAG (MSR blog) | Lazy query-time summarization under a token budget | Deferred | Phase 4 |
| 2502.09956 | KGGen | MINE coverage benchmark; LLM-guided cluster-merge | Deferred (MINE); clustering not adopted | Phase 5 |
| 2502.05239 | Hallucination/Omission/Graph-Similarity Metrics | Per-run hallucinated-triple and omitted-fact rates | Deferred | Phase 5 |
| 2505.23628 | AutoSchemaKG | Dynamic schema induction via conceptualization | Deferred | Phase 7 (domain wizard) |
| 2404.03868 | EDC (Extract-Define-Canonicalize) | Definition-embedding relation canonicalization | Deferred | Phase 7 (domain wizard) |
| 2606.15246 `[unverified]` | Provenance-Enhanced Statements in Knowledge Graphs | RDF-star / nanopublication statement-level provenance | Deferred | Phase 6 (nanopub-lite claim record) |
| 2404.16130 | Microsoft GraphRAG | Pre-computed hierarchical community summaries | Rejected | — |
| 2409.13731 | KAG | Mutual chunk↔knowledge indexing + logical-form solver | Rejected | — |
| 2501.06713 | MiniRAG | Heterogeneous chunk+entity graph for small models | Rejected | — |
| 2406.02962 | Docs2KG | MetaKG/LayoutKG/SemanticKG from heterogeneous files | Rejected | — |
| 2510.11297 | "Are LLMs Effective KG Constructors?" | Hierarchical sentence→section→doc extraction | Rejected (evidence only) | — |
| 2506.20963 | EraRAG | LSH-bucketed localized incremental updates | Rejected | — |
| 2508.12393 | MedKGent | Agent-built temporally evolving biomedical KG | Rejected (reference analog) | — |
| 2310.11244 | Peeters & Bizer, Entity Matching using LLMs | Zero/few-shot LLM matching baseline | Rejected (baseline) | — |
| 2409.08185 | Fine-tuning LLMs for Entity Matching | Fine-tune small models for entity matching | Rejected | — |
| 2603.11051 | OpenSanctions Pairs | Multilingual real-world entity-matching benchmark | Rejected (benchmark only) | — |
| 2510.20345 | LLM-empowered KG Construction: A Survey | Field taxonomy; evaluation-metric catalog | Rejected (reference only) | — |
| 2502.11371 | RAG vs GraphRAG Systematic Evaluation | Benchmark: hybrid retrieval dominates | Rejected (design evidence) | — |
| 2604.09666 | "Do We Still Need GraphRAG?" | Benchmark evidence on graph vs vector RAG | Rejected (design evidence) | — |
| 2403.08319 | Knowledge Conflicts for LLMs: A Survey | Conflict taxonomy (context-memory / inter-context / intra-memory) | Rejected (vocabulary reference) | — |
| 2504.00180 | Contradiction Detection in RAG Systems | Typed-contradiction evaluation of LLM context validators | Rejected (design evidence) | — |
| 2601.02627 | Improved Evidence Extraction for Document Inconsistency Detection | Redact-and-retry evidence extraction + evidence-level metrics | Rejected (related work) | — |
| 2502.06472 | KARMA | Nine-agent KG enrichment with verifier/conflict agents | Rejected (reference design) | — |

## Papers

### Adopted

#### HippoRAG 2 — arXiv 2502.14802

- **Title:** "From RAG to Memory: Non-Parametric Continual Learning for LLMs" (Feb 2025; ICML 2025)
- **Technique:** KG with phrase + passage nodes and synonym edges; query-linked seed nodes filtered
  by an LLM "recognition memory" pass, then Personalized PageRank spreads activation to rank
  passages. Beats strong embedding retrievers on associative/multi-hop tasks (+7%).
- **Status:** Adopted.
- **Rationale:** Rated the best quality/effort ratio in the whole survey —
  `networkx.pagerank(G, personalization=seeds)` gives the retrieval pattern for free on the
  existing MultiDiGraph, with no new dependencies.
- **Maps to:** `core/graph_retrieval.py` — personalized-PageRank graph expansion, seeded from
  hybrid search hits, exposed via `epistract search --expand` (roadmap Phases 3–4, shipped).

#### iText2KG — arXiv 2409.03284

- **Title:** iText2KG (Sep 2024; WISE 2024)
- **Technique:** Zero-shot incremental KG construction: each new document's entities/relations are
  matched (embedding cosine + thresholds) against the existing graph before insertion, so the
  graph grows without post-hoc global dedup or rebuilds.
- **Status:** Adopted with caveat — the delta-detection facet is shipped; the match-before-insert
  graph merge is Deferred (roadmap Phase 3, unchecked).
- **Rationale:** Its incremental-growth loop is the reference design for adding documents to an
  existing NetworkX graph without a full rebuild. The shipped piece is the content-hash manifest
  so `epistract index` only re-processes new/changed documents; merging new extractions into the
  existing graph without a rebuild is still on the roadmap.
- **Maps to:** `core/index_db.py` (delta detection, shipped); Phase 3 "graph merge without full
  rebuild" (deferred).

#### GraphJudge — arXiv 2411.17388

- **Title:** GraphJudge (Nov 2024; EMNLP'25 main)
- **Technique:** Treats KG quality as a judgment problem — a graph-judgment filter classifies each
  candidate triple correct/incorrect against its evidence (>90% judge accuracy on
  REBEL-Sub/GenWiki, generalizes cross-dataset).
- **Status:** Adopted.
- **Rationale:** Even without fine-tuning, a zero/few-shot "judge each triple against its evidence
  span" pass is a cheap, high-yield quality gate; the extractor LLM is already in the loop, so
  this converts the epistemic layer from regex heuristics to calibrated scores.
- **Maps to:** `core/triple_judge.py` — judges each triple against its evidence span, stores
  verdict/score/gated on the edge; lexical fallback + injectable LLM judge. Exposed via
  `epistract enhance --judge` (roadmap Phase 5, shipped).

#### GraphEval — arXiv 2407.10793

- **Title:** GraphEval (Jul 2024; KiL@KDD)
- **Technique:** Decomposes LLM output into KG triples and NLI-checks each against source context,
  giving triple-level hallucination localization.
- **Status:** Adopted.
- **Rationale:** The sweep proposed running the same machinery in reverse on the pipeline: every
  extracted triple gets an entailment score against its evidence sentence; scores below threshold
  become "hypothesized/unverified" epistemic status.
- **Maps to:** `core/triple_judge.py` (with GraphJudge; roadmap Phase 5, shipped).

#### ComEM ("Match, Compare, or Select?") — arXiv 2405.16884

- **Title:** "Match, Compare, or Select?" (May 2024; COLING 2025)
- **Technique:** Decomposes entity resolution into pairwise matching, comparing, and selecting;
  shows a compound pipeline (cheap model for pairwise, stronger LLM for final selection over
  blocked candidates) improves accuracy while cutting cost dramatically.
- **Status:** Adopted.
- **Rationale:** Exactly the shape of a local pipeline: embed-block → shortlist → single LLM
  "select the coreferent entity or NONE" call per cluster, instead of O(n²) pair prompts.
  Directly reduces graph sparsity/duplication.
- **Maps to:** `core/entity_resolution_v2.py` — type blocking → char/token/embedding similarity →
  borderline-only `verify_fn` hook. Exposed via `epistract enhance --resolve` (roadmap Phase 5,
  shipped).

#### BoostER — arXiv 2401.03426

- **Title:** "On Leveraging LLMs for Enhancing Entity Resolution: a cost-efficient approach" (Jan 2024)
- **Technique:** Treats LLM calls as a budgeted resource — picks which uncertain match candidates
  to send to the LLM by expected reduction in partition uncertainty.
- **Status:** Adopted.
- **Rationale:** Provides the "only ask the LLM about high-entropy pairs" selection math for
  keeping verification cost near zero.
- **Maps to:** `core/entity_resolution_v2.py` (with ComEM; roadmap Phase 5, shipped).

#### Zep / Graphiti — arXiv 2501.13956

- **Title:** "Zep: A Temporal Knowledge Graph Architecture for Agent Memory" (Jan 2025)
- **Technique:** Bi-temporal graph — every edge carries event time (valid_at/invalid_at) and
  ingestion time; a contradicting new fact invalidates (never deletes) the old edge, preserving
  history with full provenance.
- **Status:** Adopted.
- **Rationale:** The invalidate-don't-delete + temporal-validity edge model is precisely an
  epistemic-layer mechanism: "contradicted/superseded" becomes a computed edge state with
  provenance, composing with the existing asserted/hypothesized taxonomy.
- **Maps to:** `core/epistemic_temporal.py` — valid_at/invalid_at/superseded_by; contradicting
  newer edge invalidates the older. Exposed via `epistract enhance --epistemic` (roadmap Phase 6,
  shipped).

#### LegalWiz — arXiv 2510.03418

- **Title:** LegalWiz (Oct 2025)
- **Technique:** Contradiction Mining Agent: semantic-similarity filtering → NLI model → LLM judge,
  for intra- and inter-document conflicts.
- **Status:** Adopted — with the caveat that the NLI model hookup is still TODO; the shipped
  cascade is lexical (antonym-relation + negation-polarity) with an injectable `adjudicate_fn`
  for NLI/LLM adjudication.
- **Rationale:** The filter → NLI → LLM-judge cascade is the right cost structure locally:
  embeddings prune candidate claim pairs, a small NLI model (e.g., DeBERTa-MNLI) scores them,
  and the LLM only adjudicates high-scoring pairs.
- **Maps to:** `core/epistemic_temporal.py` contradiction cascade (roadmap Phase 6, shipped).

#### PaperQA2 / ContraCrow — arXiv 2409.13740

- **Title:** "Language agents achieve superhuman synthesis of scientific knowledge" (Sep 2024,
  FutureHouse)
- **Technique:** ContraCrow pipeline: LLM extracts atomic claims from a paper → for each claim, a
  RAG agent searches the literature with a contradiction-detection prompt (Likert-scored),
  human-expert-validated (~2.3 contradictions found per biology paper).
- **Status:** Adopted — same NLI-hookup caveat as LegalWiz.
- **Rationale:** The claim-centric (not triple-centric) contradiction mining loop is the best
  published design for "what does the rest of the corpus say against this claim" in scientific
  domains.
- **Maps to:** Phase 6 contradiction cascade. Note: the roadmap checkbox credits both LegalWiz and
  ContraCrow/PaperQA2 for the cascade; the `core/epistemic_temporal.py` docstring cites LegalWiz
  only, so this mapping rests on the roadmap citation.

#### Hedge Detection in Text — arXiv 2405.13319

- **Title:** "'You should probably read this': Hedge Detection in Text" (May 2024)
- **Technique:** Joint word + POS hedge-cue model, state of the art on CoNLL-2010.
- **Status:** Adopted.
- **Rationale:** Basis for augmenting the regex `HEDGING_PATTERNS` with a graded cue-based score
  to calibrate "hypothesized" status instead of binary regex hits.
- **Maps to:** `core/hedging.py` — weighted cue density + certainty discount + injectable
  classifier, replacing the binary regex (roadmap Phase 6, shipped).
- **Citation note:** the roadmap line pairs this arXiv ID with the name "UnScientify"; per the
  sweep these are two distinct works (UnScientify is arXiv 2307.14236). Both underlie
  `core/hedging.py`, which cites the 2405.13319 lexical-cue approach and UnScientify's cue
  inventories.

#### UnScientify — arXiv 2307.14236

- **Title:** UnScientify (2023, updated)
- **Technique:** Weakly-supervised pipeline for sentence-level scientific-uncertainty detection
  with span identification (related classic resource: BioScope).
- **Status:** Adopted (cue inventories).
- **Rationale:** Supplies the uncertainty-cue inventories behind the graded hedge score.
- **Maps to:** `core/hedging.py` (roadmap Phase 6, shipped). See citation note under 2405.13319.

### Deferred

#### LightRAG — arXiv 2410.05779

- **Title:** LightRAG (Oct 2024; EMNLP 2025)
- **Technique:** Dual-level retrieval — one cheap LLM call extracts low-level (entity) and
  high-level (topic/concept) keywords from the query, routed to node lookup vs relation/global
  lookup before subgraph assembly. Natively supports incremental union-merge insertion with no
  rebuild.
- **Status:** Deferred (both facets unchecked on the roadmap).
- **Rationale:** Called the single most practical template for local "chat with your KG" —
  dual-level keyword routing + subgraph assembly is ~200 lines on top of an existing NetworkX
  graph + a vector index. Scheduled but not yet implemented.
- **Maps to:** Phase 4 (dual-level query routing) and Phase 3 (union-merge graph insertion).

#### LazyGraphRAG — no arXiv ID (Microsoft Research blog, Nov 2024)

- **Title:** LazyGraphRAG (shipped inside microsoft/graphrag; evaluated via BenchmarkQED, blog
  Jun 2025). No standalone arXiv paper.
- **Technique:** Defers ALL LLM summarization to query time — indexing uses only noun-phrase
  extraction + co-occurrence graph + community detection (≈0.1% of GraphRAG indexing cost);
  query time does relevance-budgeted iterative deepening. Won all 96 BenchmarkQED comparisons.
- **Status:** Deferred.
- **Rationale:** The key architectural lesson for a local tool — don't pre-summarize communities at
  ingest; summarize lazily at query time under a token budget. An order-of-magnitude ingest-cost
  saver.
- **Maps to:** Phase 4 (lazy query-time community/claim summarization).

#### KGGen — arXiv 2502.09956

- **Title:** KGGen (Feb 2025, v2 Nov 2025; NeurIPS'25)
- **Technique:** Two-stage LLM extraction followed by iterative LLM-guided clustering that merges
  near-duplicate entities/relations graph-wide; ships the MINE benchmark (100 articles × 15
  facts, scoring whether a generated KG entails each fact).
- **Status:** Deferred — the MINE-style coverage regression is on the roadmap (Phase 5,
  unchecked); the clustering technique itself was not adopted.
- **Rationale:** MINE is trivially reproducible as a regression test: sample atomic facts per
  document at ingest, assert the built KG entails ≥X% after pipeline changes. Licensing flag from
  the sweep: the stair-lab/kg-gen repo has **no LICENSE file** (GitHub API reports NONE) — treat
  as reference, not a dependency.
- **Maps to:** Phase 5 (MINE-style coverage regression).

#### Hallucination/Omission/Graph-Similarity Metrics — arXiv 2502.05239

- **Title:** "Enhancing KG Construction: Evaluating with Emphasis on Hallucination, Omission, and
  Graph Similarity Metrics" (Feb 2025)
- **Technique:** Extends text→KG evaluation with explicit hallucination and omission rates plus a
  BERTScore-based graph-similarity (node/edge alignment) metric.
- **Status:** Deferred.
- **Rationale:** Defines the three numbers worth reporting per ingest run: hallucinated-triple
  rate, omitted-fact rate, schema conformance.
- **Maps to:** Phase 5 (reported alongside the MINE coverage regression).

#### AutoSchemaKG — arXiv 2505.23628

- **Title:** AutoSchemaKG (May 2025; ACL 2026)
- **Technique:** Fully autonomous KG construction with dynamic schema induction — a
  "conceptualization" phase abstracts instances into semantic types, inducing a schema with zero
  manual work; induced schemas hit 92% semantic alignment with human-crafted schemas. MIT,
  actively maintained.
- **Status:** Deferred.
- **Rationale:** The conceptualization prompt-pattern is the strongest published recipe for a
  domain wizard that proposes a domain.yaml from a sample corpus — evidence-driven rather than
  purely conversational; also validates event-nodes as first-class citizens.
- **Maps to:** Phase 7 (schema-induction bootstrap for the domain wizard).

#### EDC (Extract-Define-Canonicalize) — arXiv 2404.03868

- **Title:** EDC (Apr 2024)
- **Technique:** Open IE → Define (LLM writes natural-language definitions of induced
  relations/types) → Canonicalize (embed definitions, align to a target schema); plus a trained
  schema retriever so large schemas needn't fit in the prompt. MIT (unmaintained since Aug 2024).
- **Status:** Deferred.
- **Rationale:** Definition-embedding canonicalization is the cleanest way to map free-form LLM
  relation strings onto a fixed YAML relation vocabulary without stuffing the entire schema into
  every extraction prompt.
- **Maps to:** Phase 7 (with AutoSchemaKG, domain wizard upgrade).

#### Provenance-Enhanced Statements in Knowledge Graphs — arXiv 2606.15246 `[unverified]`

- **Title:** "Provenance-Enhanced Statements in Knowledge Graphs" (Jun 2026)
- **Technique:** Systematic comparison of reification, named graphs, RDF-star (now in RDF 1.2),
  and nanopublications for statement-level provenance. Related: "Extending Nanopublications with
  Knowledge Provenance" (IRCDL 2025, non-arXiv) adds a fourth graph capturing supporting and
  conflicting bodies of evidence per assertion.
- **Status:** Deferred.
- **Rationale:** A "nanopub-lite" JSON record per claim (assertion triple + provenance + epistemic
  status + supporting/conflicting evidence lists) is a standards-aligned serialization of exactly
  what the asserted/hypothesized/contradicted layer does.
- **Maps to:** Phase 6 (nanopub-lite claim record).
- **Flag:** `[unverified]` — this ID is dated June 2026, only days before the sweep; it appears in
  the sweep's verified-source list and the roadmap, but could not be independently re-confirmed
  during reconstruction.

### Rejected

#### Microsoft GraphRAG — arXiv 2404.16130

- **Technique:** Entity/relation extraction → Leiden community hierarchy → pre-computed
  hierarchical community summaries; global questions answered map-reduce over summaries.
- **Status:** Rejected.
- **Rationale (from the sweep):** the community-summary pattern is proven for theme queries, but
  indexing token cost is notoriously high — mostly superseded for local use by the lazy variant
  (LazyGraphRAG, which was deferred to Phase 4 instead).
- **Maps to:** — (its lazy descendant is on the roadmap).

#### KAG — arXiv 2409.13731

- **Technique:** OpenSPG-based mutual indexing between knowledge and chunks, logical-form-guided
  hybrid solver, knowledge alignment via conceptual reasoning.
- **Status:** Rejected.
- **Rationale (from the sweep):** strongest published results on professional-domain multi-hop QA,
  but "a heavy server-ish stack — mine its mutual chunk↔knowledge indexing idea, don't adopt the
  framework."
- **Maps to:** —

#### MiniRAG — arXiv 2501.06713

- **Technique:** Semantic-aware heterogeneous graph unifying text chunks and named entities in one
  index + topology-enhanced retrieval, designed so small/local models can run RAG well.
- **Status:** Rejected.
- **Rationale (from the sweep):** its applicability was scoped to the case where the chat model is
  small or budget-limited — not epistract's scenario; not pursued.
- **Maps to:** —

#### Docs2KG — arXiv 2406.02962

- **Technique:** Unified MetaKG/LayoutKG/SemanticKG from heterogeneous files (PDF/email/Excel).
- **Status:** Rejected.
- **Rationale (from the sweep):** noted as relevant only "if you want document-structure nodes
  alongside semantic ones"; not pursued.
- **Maps to:** —

#### "Are LLMs Effective KG Constructors?" — arXiv 2510.11297

- **Technique:** Hierarchical (sentence → section → document) extraction; releases an LLM-KG
  dataset.
- **Status:** Rejected (evidence only).
- **Rationale (from the sweep):** useful evidence that sentence-level-only extraction
  under-covers; no technique adopted.
- **Maps to:** —

#### EraRAG — arXiv 2506.20963

- **Technique:** Incremental Graph-RAG — chunks bucketed by hyperplane LSH into a hierarchical
  graph; inserts only re-partition/re-summarize affected buckets (up to an order of magnitude
  less update cost than rebuild-based GraphRAG).
- **Status:** Rejected.
- **Rationale:** the "localize the blast radius of an insert via hashing" idea was noted as
  transferable, but epistract's shipped delta detection uses content-hash manifests (iText2KG
  pattern) instead; not on the roadmap.
- **Maps to:** —

#### MedKGent — arXiv 2508.12393

- **Technique:** LLM agent framework constructing a temporally evolving biomedical KG day-by-day
  over 10M+ PubMed abstracts; sampling-based confidence scores per triple.
- **Status:** Rejected (reference analog).
- **Rationale (from the sweep):** closest published analog to an incremental scientific-literature
  pipeline; noted as reference, no specific technique adopted.
- **Maps to:** —

#### Entity Matching using Large Language Models (Peeters & Bizer) — arXiv 2310.11244

- **Technique:** Establishes that GPT-4-class zero/few-shot matching beats fine-tuned PLM
  baselines, especially on unseen entities; in-context example selection matters more than
  prompt wording.
- **Status:** Rejected (baseline).
- **Rationale:** provided the baseline recipe and prompts for an LLM verify step, but the
  implemented design followed the ComEM compound-pipeline shape instead.
- **Maps to:** —

#### Fine-tuning LLMs for Entity Matching — arXiv 2409.08185

- **Technique:** Fine-tuning helps small models substantially; frontier models gain little.
- **Status:** Rejected.
- **Rationale (from the sweep):** "if you ever want an offline/cheap dedup model, fine-tune small;
  otherwise just prompt the frontier model you already have" — a frontier model is already in the
  loop, so fine-tuning is unnecessary.
- **Maps to:** —

#### OpenSanctions Pairs — arXiv 2603.11051

- **Technique:** Large-scale, multilingual, real-world entity-matching benchmark from sanctions
  data.
- **Status:** Rejected (benchmark only).
- **Rationale (from the sweep):** the most realistic recent ER benchmark "if you want to validate
  a dedup stage"; no validation stage was scheduled.
- **Maps to:** —

#### LLM-empowered KG Construction: A Survey — arXiv 2510.20345

- **Technique:** The current best map of the field (ontology-guided vs open vs hybrid pipelines;
  faithfulness/coverage/consistency metric catalog).
- **Status:** Rejected (reference only).
- **Rationale (from the sweep):** used to position and gap-check the pipeline — it underpins the
  survey's conclusion that a schema-constrained pipeline is already on the higher-precision path
  and the gap to close is canonicalization + judged filtering. No adoptable technique of its own.
- **Maps to:** —

#### RAG vs GraphRAG Systematic Evaluation — arXiv 2502.11371

- **Technique:** Benchmark: vector RAG wins simple factoid queries; graph structure pays off on
  multi-hop and global/sensemaking; hybrid dominates both.
- **Status:** Rejected (design evidence).
- **Rationale:** no technique to adopt, but it (with BenchmarkQED) supplied the evidence for the
  overall retrieval architecture — hybrid seed retrieval (BM25+vector) → PPR graph expansion →
  lazy summarization — that shaped Phases 3–4.
- **Maps to:** —

#### "Do We Still Need GraphRAG?" — arXiv 2604.09666

- **Technique:** Benchmark evidence (Apr 2026) on when graph structure pays off vs vector RAG.
- **Status:** Rejected (design evidence).
- **Rationale:** same role as 2502.11371 — corroborating evidence for the hybrid pattern; no
  adoptable technique.
- **Maps to:** —

#### Knowledge Conflicts for LLMs: A Survey — arXiv 2403.08319

- **Technique:** Canonical conflict taxonomy: context-memory, inter-context (conflicts among
  retrieved documents — epistract's case), intra-memory.
- **Status:** Rejected (vocabulary reference).
- **Rationale (from the sweep):** supplies the vocabulary and failure-mode checklist for the
  epistemic layer; no implementable technique.
- **Maps to:** —

#### Contradiction Detection in RAG Systems — arXiv 2504.00180

- **Technique:** Evaluates LLMs as context validators over retrieved sets with synthetically
  inserted contradictions; finds detection remains hard even for frontier models, conditional
  contradictions hardest.
- **Status:** Rejected (design evidence).
- **Rationale (from the sweep):** "don't rely on a single 'any conflicts here?' prompt — use typed
  contradiction categories and pairwise checks" — evidence that shaped the pairwise cascade
  design, but no technique of its own was adopted.
- **Maps to:** —

#### Improved Evidence Extraction for Document Inconsistency Detection — arXiv 2601.02627

- **Technique:** Redact-and-retry prompting + constrained filtering for evidence extraction, with
  evidence-level metrics and a semi-synthetic dataset.
- **Status:** Rejected (related work).
- **Rationale:** noted in the sweep as related to the contradiction cascade's evidence extraction;
  not adopted and not on the roadmap.
- **Maps to:** —

#### KARMA — arXiv 2502.06472

- **Technique:** Nine-agent KG-enrichment pipeline (reader, extractor, schema aligner, verifier,
  conflict-resolution agents); 83.1% LLM-verified correctness on 1,200 PubMed papers.
- **Status:** Rejected (reference design).
- **Rationale (from the sweep):** a reference design for multi-agent verify + conflict-resolve
  stages that "maps directly onto an extractor/validator agent architecture" epistract already
  has; the framework itself was not adopted.
- **Maps to:** —

## Non-paper tooling evaluated in the sweep

The sweep also surveyed local hybrid-search tooling (not papers; listed here for completeness):

- **SQLite FTS5 (+ sqlite-vec, Reciprocal Rank Fusion)** — the practitioner-consensus zero-server
  pattern. **Partially adopted:** `core/index_db.py` ships FTS5 BM25 + RRF over entities and
  chunks; the sqlite-vec vector column for semantic recall is Deferred (Phases 3 and 5,
  unchecked).
- **LanceDB** — the step-up choice past ~1M vectors. Held as roadmap open decision #3
  (sqlite-vec now vs LanceDB from the start).
- **DuckDB VSS** — rejected: officially experimental; HNSW persistence behind a flag, whole index
  rewritten at every checkpoint.
- **ChromaDB** — rejected: memory-bound at ~1M vectors and no native BM25/FTS, so real hybrid
  search requires bolting on a keyword index anyway.
- **nano-graphrag / fast-graphrag** — flagged as good lightweight reference codebases (MIT), not
  dependencies.
- **BenchmarkQED** (MSR blog) — benchmark used to evaluate LazyGraphRAG; design evidence alongside
  arXiv 2502.11371.
