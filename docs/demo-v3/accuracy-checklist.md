# Accuracy Checklist for the 5-min KGC 2026 Demo

Every factual claim in `demo-script.md` mapped to its source in the codebase. Verify each before recording. If a claim slips, note it here and update both this file and the script.

## Block 1 — Setup

| Claim | Verified against | Status |
|---|---|---|
| "knowledge graph framework called Epistract" | `README.md`, `.claude-plugin/plugin.json` | ✓ |
| "most KG tools stop at extracting entities and typed relations" | General industry observation; defensible in QnA — Neo4j Bloom, GraphDB, Stardog all surface entities + relations as the primary product, not epistemic content | ✓ defensible |
| "thirty-four documents on GLP-1 receptor agonists" | `tests/corpora/06_glp1_landscape/docs/` count = 34 | ✓ |
| "Ten patent filings from Novo Nordisk, Pfizer, Eli Lilly, Hanmi, and Zealand" | `tests/corpora/06_glp1_landscape/docs/patent_*.txt` — 10 files; assignees match | ✓ (corrected — earlier draft omitted Hanmi + Zealand) |
| "Twenty-four PubMed papers" | `tests/corpora/06_glp1_landscape/docs/pmid_*.txt` count = 24 | ✓ |
| "drug class behind semaglutide and tirzepatide, used for type-2 diabetes and obesity" | Public clinical knowledge | ✓ |

## Block 2 — Two-layer architecture

| Claim | Verified against | Status |
|---|---|---|
| "Two hundred seventy-eight entities, eight hundred fifty-five typed relations, ten Louvain communities" | `tests/corpora/06_glp1_landscape/output-v3/graph_data.json` metadata + `communities.json` | ✓ |
| "epistemic status — asserted, prophetic, hypothesized, contested, contradiction, negative, and a few others" | `core/label_epistemic.py` HEDGING_PATTERNS + `claims_layer.summary.epistemic_status_counts`. "A few others" hedge covers `speculative` and `unclassified` | ✓ |
| "regex patterns over evidence text and document-type inference" | `core/label_epistemic.py:HEDGING_PATTERNS`, `infer_doc_type()` | ✓ |
| "senior drug-discovery competitive-intelligence analyst persona" | `domains/drug-discovery/workbench/template.yaml:persona` opens with this exact phrase | ✓ |
| "single string in `domains/drug-discovery/workbench/template.yaml`" | File exists, is one YAML field | ✓ |
| "the same string powers the workbench chat" | `examples/workbench/api_chat.py` reads `template.persona` for system prompt | ✓ |
| "two surfaces" — narrator + workbench chat | Single-source-of-truth pattern documented in `docs/ARCHITECTURE.md` and `docs/ADDING-DOMAINS.md` | ✓ |

## Block 3 — Graph walkthrough

| Claim | Verified against | Status |
|---|---|---|
| "force-directed layout, 278 nodes" | vis.js force-directed; node count from graph_data.json | ✓ |
| Color mapping: compounds indigo, diseases red, clinical trials cyan, mechanisms purple, biomarkers slate | `domains/drug-discovery/workbench/template.yaml:entity_colors` — COMPOUND `#6366f1` (indigo), DISEASE `#ef4444` (red), CLINICAL_TRIAL `#06b6d4` (cyan), MECHANISM `#8b5cf6` (purple), BIOMARKER `#64748b` (slate) | ✓ all match |
| "ten Louvain communities" | `communities.json` shows 10 communities | ✓ |
| "Community structure tells you where to look. It tells you nothing about what kind of knowledge you're looking at" | True statement about Louvain — purely topological algorithm | ✓ |
| "INN names for drugs. HGNC for genes. MeSH for diseases" | `domains/drug-discovery/SKILL.md` Naming Standards section | ✓ |
| "11 to 17 entity types per domain" | drug-discovery 13, contracts 11, clinicaltrials 12, fda-product-labels 17 | ✓ (corrected — earlier draft said "12 to 17") |
| "every edge carries a confidence score and a verbatim source quote" | `DocumentExtraction` Pydantic model — `confidence: float`, `evidence: str` required fields | ✓ |
| "click any edge and you can drill back to the source document" | Workbench `examples/workbench/static/graph.js` has node/edge click handlers | ✓ |
| "`semaglutide INDICATED_FOR obesity` shows up with confidence 0.55 in one source and 0.97 in another" | Verified in `tests/corpora/06_glp1_landscape/output-v3/epistemic_narrative.md` Executive Summary | ✓ |
| "claims layer tags this as `contested`" | Verified — narrator text: "the same relation supported by multiple sources with conflicting confidence" | ✓ |

## Block 4 — Briefing returns

| Claim | Verified against | Status |
|---|---|---|
| "1,166 words" | `wc -w tests/corpora/06_glp1_landscape/output-v3/epistemic_narrative.md` = 1166 | ✓ |
| Prophetic-claims executive-summary excerpt — verbatim | `epistemic_narrative.md` Executive Summary 2nd bullet | ✓ |
| Temporal stratification excerpt — verbatim | `epistemic_narrative.md` Contested Claims section | ✓ |
| SURPASS-2 recommendation excerpt — verbatim | `epistemic_narrative.md` Recommended Follow-Ups section #2 | ✓ |
| "Frías et al, NEJM 2021" | Real citation: Frías JP et al. NEJM 2021;385:503-515 (SURPASS-2) | ✓ |
| "narrator persona produced this from the classified graph — it didn't see the source documents directly" | `core/label_epistemic.py:_summarize_graph_for_narrator` constructs prompt from claims_layer + graph metadata, NOT from raw text | ✓ |

## Block 5 — Closing

| Claim | Verified against | Status |
|---|---|---|
| "four pre-built domains today" | `ls domains/` = drug-discovery, contracts, clinicaltrials, fda-product-labels | ✓ |
| "Each domain is four required files" | `domain.yaml` + `SKILL.md` + `epistemic.py` + `workbench/template.yaml`. Plus optional helpers like enrich.py, references/, __init__.py | ✓ (corrected to "four required files" + "plus optional helpers") |
| "Open source, MIT license" | `LICENSE` file confirms MIT | ✓ |
| "Runs as a Claude Code plugin" | `.claude-plugin/plugin.json` exists | ✓ |

## QnA-claim audit

Statements that may come up in QnA — make sure each is defensible:

| Statement | Source/defense |
|---|---|
| "v3.2.0 ships four pre-built domains" | CHANGELOG `[3.2.0]` entry |
| "drug-discovery validated across six scenarios" | tests/scenarios/scenario-0{1-6}-*-v2.md all exist with V2 validation status |
| "clinicaltrials launched with one scenario (S7)" | tests/corpora/07_glp1_phase3_trials/ exists, full pipeline output |
| "Phase-based evidence grading in clinicaltrials" | `domains/clinicaltrials/epistemic.py` has the grader |
| "Four-level FDA epistemology classifier in fda-product-labels" | `domains/fda-product-labels/epistemic.py` has `_ESTABLISHED_MARKERS`, `_REPORTED_MARKERS`, `_THEORETICAL_MARKERS` |
| "fda-product-labels has zero scenarios; showcase corpus in flight" | Truthful — Issue #14 tracks it; no `tests/corpora/08_*` exists |
| "framework doesn't auto-learn across scenarios" | True — corrected on 2026-04-25 (commit a8a91db); Issue #15 tracks the aspiration |
| "The narrator briefing is LLM-generated; the claims layer is rule-based" | True — `core/label_epistemic.py` rule engine + LLM call sequence |
| "We use Claude Sonnet for narrator generation" | True at recording time; `core/llm_client.py` supports Azure Foundry → Anthropic → OpenRouter resolution |
| "Validators (RDKit/Biopython) for drug-discovery" | True — `tests/corpora/06_glp1_landscape/output-v3/validation_report.json` is auto-emitted |
| "Optional `--enrich` flag for clinicaltrials only" | True — `commands/ingest.md` Step 5.5 documents this |

## Honesty caveats — say these out loud if asked

- **Auto-learning across scenarios** — does NOT happen. Issue #15 tracks the aspiration. Don't imply otherwise.
- **fda-product-labels has no showcase corpus yet** — Issue #14 in flight with Chris Davidson. Don't display fda-product-labels as if it's at parity with drug-discovery.
- **The narrator briefing is non-deterministic** — `claims_layer.json` is the reproducible artifact; the briefing varies per run. Don't promise byte-identical output.
- **Workbench chat needs an LLM credential** — graph + extraction work without one. Don't promise the chat works in air-gapped settings without configuration.
- **AxMP private use case** — keep out of public talk per user direction.

## Risk: live narrator call hangs / fails during recording

If the live `/epistract:epistemic` call hangs or 402s mid-demo:
- Don't pretend to wait. Acknowledge: "looks like the call is being slow / rate-limited — let me show you the previously committed briefing while it sorts itself out."
- Open `tests/corpora/06_glp1_landscape/output-v3/epistemic_narrative.md` from the last successful run.
- Keep the verbatim quotes the same — they're identical across runs because the persona is deterministic in shape even if word-by-word output varies.

---

*Accuracy checklist prepared 2026-04-25. Re-verify counts and excerpts on the day-of recording in case any underlying file changes between now and then.*
