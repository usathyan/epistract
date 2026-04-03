# Domain Pitfalls

**Domain:** Cross-domain KG extraction (biomedical -> contracts/legal)
**Researched:** 2026-03-29

## Critical Pitfalls

Mistakes that cause rewrites, data corruption, or project failure.

### Pitfall 1: Hardcoded Biomedical Assumptions Throughout Pipeline

**What goes wrong:** The current codebase has biomedical domain logic embedded at multiple layers -- not just in prompts, but in post-processing scripts, community labeling heuristics, validation logic, and output metadata. Attempting to route contract documents through the pipeline without systematically identifying and abstracting every hardcoded assumption produces silently wrong results: contract entities get classified using biomedical heuristics, community labels reference "Disease Risk Loci" for vendor groupings, and extraction metadata stamps "Drug Discovery" on contract outputs.

**Why it happens:** The tool was built for one domain. Single-domain tools accumulate domain assumptions in non-obvious places because there was never a reason to abstract them. The danger is assuming the problem is limited to "swap the prompt" when it is actually distributed across 5+ files.

**Consequences:**
- `build_extraction.py` line 37: `"domain_name": "Drug Discovery"` hardcoded in every extraction JSON
- `label_communities.py` lines 21-25: priority map uses GENE, PROTEIN, PATHWAY, DISEASE -- contract entities (Party, Obligation, Deadline) are missing, so all communities fall through to the generic fallback label
- `scan_patterns.py`: all 8 patterns are molecular/biomedical (InChIKey, SMILES, CAS, DNA/RNA, amino acids) -- none relevant to contracts
- `validate_smiles.py` / `validate_sequences.py`: entire validation layer is biomedical-specific
- Community labeling heuristics (lines 49-105) use percentage thresholds tuned to biomedical entity distributions -- contract entity distributions are completely different

**Prevention:**
1. Audit every Python file in `scripts/` and `skills/` for hardcoded entity types, domain names, or biomedical-specific logic. Create a checklist before writing any new code.
2. Introduce a domain config that provides: entity types, relation types, validation rules, community labeling heuristics, and pattern matchers -- per domain.
3. Make `build_extraction.py` accept `domain_name` as a parameter, not a constant.
4. Make `label_communities.py` load heuristic rules from the domain config rather than hardcoding biomedical priorities.
5. Make validation (scan_patterns, validate_smiles, validate_sequences) conditional: only run biomedical validators when `domain == "drug_discovery"`.

**Detection:** Run a contract document through the existing pipeline unchanged. If output JSON says `"domain_name": "Drug Discovery"` and community labels mention genes/proteins, the abstraction is incomplete.

**Phase:** Must be addressed in Phase 1 (domain config system) before any contract extraction begins.

---

### Pitfall 2: PDF Extraction Failure on Large/Scanned Contracts

**What goes wrong:** The 62 contract PDFs include files from 12-31 MB. Large PDFs can be scanned images (not searchable text), have complex multi-column layouts, embedded tables with merged cells, or mixed text+image pages. Naive text extraction (e.g., `pdfplumber` or `PyMuPDF` with default settings) produces garbled output: columns interleaved, table structure lost, headers repeated as body text, or -- worst case -- empty strings from image-only pages.

**Why it happens:** PDFs are a visual format, not a data format. Contract PDFs from convention centers and hotels are often exported from Word/InDesign with complex layouts, or scanned from physical documents. The extraction tool sees pixels or visual coordinates, not semantic structure.

**Consequences:**
- Entity extraction LLM receives garbage text, producing hallucinated or missing entities
- Table data (room blocks, pricing tiers, capacity charts) extracted as unstructured text loses row/column relationships
- Scanned pages return empty text, silently dropping entire contract sections
- Floor plans and diagrams produce OCR noise that pollutes the extraction

**Prevention:**
1. Before building the extraction pipeline, run a triage pass on all 62 documents: classify each as text-native PDF, scanned PDF, or mixed. Use PyMuPDF's `page.get_text()` length as a heuristic -- if a page has <50 characters but visible content, it is likely scanned.
2. Use PyMuPDF (pymupdf4llm) for text-native PDFs -- it is the fastest and handles large files well. For scanned pages, add an OCR fallback (Tesseract or cloud OCR).
3. For tables: use pdfplumber's table extraction mode on pages identified as containing tables, then pass structured table data to the LLM separately from prose text.
4. Set per-page extraction and validate output: if a page yields <20 characters but the PDF shows content, flag it for OCR retry.
5. For the XLS file: use openpyxl directly -- do not convert to PDF first.
6. For the EML file: use Python's `email` stdlib to extract body text and attachments.

**Detection:** After initial extraction, count characters per page per document. Pages with suspiciously low character counts relative to visual content indicate extraction failures.

**Phase:** Phase 2 (document ingestion) -- must be solved before entity extraction can begin.

---

### Pitfall 3: Entity Resolution Across 62 Documents Without Canonical IDs

**What goes wrong:** The same real-world entity appears with different names across contracts. "Pennsylvania Convention Center" vs "PCC" vs "the Venue" vs "the Convention Center". "Aramark" vs "ARAMARK" vs "Aramark Corporation" vs "the Caterer". Without entity resolution, the KG contains dozens of duplicate nodes for the same party, making cross-reference analysis useless.

**Why it happens:** Unlike biomedical entities (which have canonical identifiers like SMILES, InChIKeys, gene symbols), contract entities lack universal IDs. Each contract was written independently by different law firms with different naming conventions. Coreference resolution ("the Venue", "the Center") requires document-level context that LLM extraction prompts often miss.

**Consequences:**
- Cross-contract queries fail: "What are Aramark's obligations?" returns partial results because obligations are split across "Aramark", "ARAMARK", and "the Caterer"
- Graph visualization shows a disconnected cluster of duplicate nodes instead of a hub
- Conflict detection breaks: two obligations that should conflict appear unrelated because they reference different name variants of the same party
- Node count inflates 3-5x, making the graph noisy and unnavigable

**Prevention:**
1. Build a canonical entity registry before extraction: enumerate known parties, venues, and services from the master data (`Sample_Conference_Master.md`). Use this as a seed dictionary.
2. In extraction prompts, instruct the LLM to normalize entity names to canonical forms and provide the registry as context.
3. Post-extraction, run a fuzzy matching pass (e.g., rapidfuzz with token_sort_ratio > 85) to merge near-duplicate entities.
4. For coreference ("the Venue" -> "Pennsylvania Convention Center"), resolve within each document by passing the full document context, not just chunks.
5. Add manual review step: output a candidate merge list for human approval before finalizing the graph.

**Detection:** After graph construction, count distinct Party nodes. If >20 Party nodes exist for an event with ~10-15 vendors, entity resolution is failing.

**Phase:** Phase 3 (entity extraction) and Phase 4 (graph construction) -- extraction prompts handle initial normalization, post-processing handles fuzzy merging.

---

### Pitfall 4: Chunking Destroys Cross-Clause References

**What goes wrong:** Contracts are internally cross-referenced documents. Section 5.2 may say "Subject to the limitations in Section 12.4..." and Section 12.4 may say "Notwithstanding anything in Section 5.2...". If the document is chunked for LLM processing (as epistract does for scientific papers), these references are severed. The LLM sees Section 5.2 without Section 12.4's context, producing an incomplete or misleading obligation extraction.

**Why it happens:** The existing epistract pipeline uses chunk-based extraction (evident from `chunk_size=10000` in `build_extraction.py`). This works for scientific papers where paragraphs are relatively self-contained. Contracts are fundamentally different: clauses reference each other, definitions sections apply globally, and exceptions in one section modify obligations in another.

**Consequences:**
- Obligations extracted without their exceptions/limitations
- Conditional clauses ("if X then Y, subject to Z") lose the Z condition
- Definition terms used throughout the contract are not resolved because the Definitions section is in a different chunk
- Cross-reference relations (DEPENDS_ON, RESTRICTS) between clauses in different chunks are missed entirely

**Prevention:**
1. For contracts under ~50 pages (most of these), pass the full document text to the LLM rather than chunking. Modern context windows (200K+ tokens) can handle 50-page contracts.
2. For contracts exceeding context limits: extract the Definitions section first and prepend it to every chunk as context.
3. Use a two-pass extraction strategy: Pass 1 extracts entities and within-section relations; Pass 2 specifically targets cross-references by providing the full document outline with section headers.
4. Include cross-reference detection in the extraction prompt: "Identify any references to other sections (e.g., 'per Section X.Y') and create REFERENCES relation types."
5. Validate by counting REFERENCES/DEPENDS_ON relations -- if a 30-page contract with obvious cross-references produces zero such relations, the chunking is destroying them.

**Detection:** Manual spot-check: open 3 contracts, find explicit cross-references ("per Section X"), verify they appear as relations in the extracted graph.

**Phase:** Phase 2 (document ingestion) for chunking strategy, Phase 3 (extraction) for prompt design.

---

## Moderate Pitfalls

### Pitfall 5: Over-Engineering the Domain Config System

**What goes wrong:** Building an elaborate plugin/registry system with YAML schemas, validator registries, ontology inheritance, and dynamic loading -- when there are currently only 2 domains (biomedical and contracts) and a vague third (regulatory). The config system becomes more complex than the extraction logic itself.

**Why it happens:** "Future-proofing" instinct. The PROJECT.md mentions the config system should support future domains, which tempts building for 20 domains when 2-3 are realistic.

**Consequences:**
- Weeks spent on config infrastructure instead of contract extraction
- Config system has its own bugs, edge cases, and testing burden
- Contributors must learn the config DSL before contributing a new domain
- YAGNI violation: features built for hypothetical domains that never materialize

**Prevention:**
1. Start with the simplest possible config: a Python dictionary per domain with keys for `entity_types`, `relation_types`, `validation_rules`, `community_heuristics`. No YAML, no plugin loading, no registry pattern.
2. Two concrete configs: `BIOMEDICAL_CONFIG` and `CONTRACT_CONFIG` as Python dicts in a single `domain_configs.py` file.
3. Only add abstraction when the third domain arrives and you see what actually varies.
4. Rule of three: do not abstract until you have 3 concrete instances.

**Detection:** If the domain config PR has more lines of config infrastructure than lines of actual contract entity/relation definitions, it is over-engineered.

**Phase:** Phase 1 (domain config system) -- constrain scope deliberately.

---

### Pitfall 6: Treating Contract KG Like a Literature KG (Wrong Epistemic Model)

**What goes wrong:** Applying the biomedical epistemic analysis (hypotheses, contradictions, confidence levels for scientific claims) to contracts. Contracts do not contain hypotheses -- they contain obligations. The epistemic status of a contract clause is not "supported/contradicted/hypothesized" -- it is "binding/conditional/expired/superseded".

**Why it happens:** `label_epistemic.py` is a powerful feature of epistract. The temptation is to reuse it for contracts. But the epistemology of contracts is fundamentally different from scientific literature.

**Consequences:**
- Contract obligations misclassified as "hypotheses" because they use conditional language ("if the event is cancelled...")
- Hedging language detection flags normal contract language as uncertain ("may", "shall endeavor to", "reasonable efforts")
- Contradiction detection fires on complementary clauses (vendor provides X, organizer provides Y) that are not actually contradictory
- Users lose trust in the analysis because it clearly misunderstands legal language

**Prevention:**
1. Do NOT run `label_epistemic.py` on contract extractions. It is biomedical-specific.
2. Instead, build a contract-specific analysis layer: obligation status (active/conditional/expired), conflict detection (same resource/time claimed by two vendors), coverage gaps (services needed but no vendor assigned).
3. Map the contract analysis to appropriate concepts: "conflict" instead of "contradiction", "obligation" instead of "hypothesis", "coverage gap" instead of "missing evidence".
4. Keep epistemic analysis available for biomedical scenarios only.

**Detection:** If contract analysis output contains terms like "hypothesis", "evidence strength", or "hedging language" -- the wrong analysis layer is being applied.

**Phase:** Phase 5 (cross-reference analysis / risk detection) -- design contract-specific analysis from scratch.

---

### Pitfall 7: Telegram Bot Timeouts on KG Queries

**What goes wrong:** The Telegram Bot API has strict timeout constraints. Long-running KG queries (multi-hop graph traversals, cross-contract aggregations) exceed the response window. The bot appears unresponsive, or worse, sends partial results without indicating they are incomplete.

**Why it happens:** Telegram's `getUpdates` long polling has a ~50s timeout. If a KG query takes 30+ seconds (large graph traversal, LLM reasoning over results), the bot may timeout before responding. Webhook mode has similar constraints -- Telegram will retry the webhook if no response comes quickly, potentially causing duplicate processing.

**Consequences:**
- User sends query, gets no response, sends again -- causing duplicate processing
- Partial results returned without warning, leading to incorrect decisions
- Bot process crashes on timeout, requires manual restart
- Query results returned after user has moved on, confusing the conversation flow

**Prevention:**
1. Implement async query pattern: bot immediately acknowledges the query ("Searching across 62 contracts..."), then sends results when ready.
2. Set hard timeout on KG queries (15 seconds). If exceeded, return top partial results with "Showing 5 of ~20 results. Query still processing..."
3. Pre-compute common aggregations (total costs by vendor, all deadlines sorted by date, obligation counts per party) and cache them.
4. Use Telegram's `editMessage` for progress updates on long queries rather than sending multiple messages.
5. Test with the actual graph size (62 documents, estimated 500-2000 nodes) to establish realistic query latencies before deploying.

**Detection:** During development, time every query type. Any query consistently >10s needs optimization or pre-computation.

**Phase:** Phase 7 (Telegram integration) -- but query performance testing should start in Phase 5 (analysis layer).

---

### Pitfall 8: Backward Compatibility Breakage in Biomedical Scenarios

**What goes wrong:** Refactoring shared code (build_extraction.py, run_sift.py, label_communities.py) to support domain configs inadvertently breaks the existing biomedical pipeline. Scenarios 1-6 produce different results, validation checksums change, and the published paper's reproducibility is compromised.

**Why it happens:** The refactoring seems safe ("just adding a parameter"), but biomedical scenarios depend on exact output formats, community label strings, and graph structures. Even changing a default parameter value can alter outputs.

**Consequences:**
- Published results no longer reproducible with current code
- Validation results change, requiring re-review of all 6 scenarios
- Demo video shows outputs that no longer match current code
- Paper figures become stale

**Prevention:**
1. Before any refactoring, snapshot all 6 scenarios' outputs as regression baselines: `graph_data.json`, `communities.json`, `claims_layer.json` checksums.
2. Run all biomedical scenarios after every shared-code change. Diff outputs against baselines.
3. All domain config changes must default to biomedical behavior when no domain is specified. The biomedical path must work identically whether the domain config system exists or not.
4. Add a CI test: "run scenario 1 extraction, diff against baseline, fail if changed."
5. Use feature flags, not rewrites: add `domain` parameter to functions, default to `"drug_discovery"`, existing callers unchanged.

**Detection:** After any shared code change, run `diff` on scenario 1's `graph_data.json` against the committed baseline. Any difference means backward compatibility is broken.

**Phase:** Every phase that touches shared code -- but especially Phase 1 (domain config) and Phase 4 (graph construction).

---

## Minor Pitfalls

### Pitfall 9: Graph Visualization Scaling With Contract Entities

**What goes wrong:** Contract KGs may produce more nodes than biomedical scenarios. 62 documents x ~20 entities each = 1,200+ entities. The existing vis.js visualization becomes unusable above ~300 nodes (documented in CONCERNS.md).

**Prevention:**
1. Plan for clustered/filtered views from the start. The interactive web report should default to showing aggregated views (by vendor, by category) not individual entities.
2. Use the dashboard as the primary interface, not the raw graph visualization.
3. Implement filtering: show only one vendor's subgraph, only obligations, only deadlines.

**Phase:** Phase 6 (web report / dashboard).

---

### Pitfall 10: LLM Extraction Prompt Drift Between Domains

**What goes wrong:** The contract extraction prompt is iteratively refined until it works well, but without versioning, the prompt drifts and earlier extractions use different prompts than later ones. Results become inconsistent across the 62 documents.

**Prevention:**
1. Version extraction prompts in the domain config. Each extraction run records which prompt version was used.
2. Re-extract all documents when the prompt changes materially, not just new ones.
3. Store the prompt hash in extraction JSON metadata for reproducibility.

**Phase:** Phase 3 (entity extraction).

---

### Pitfall 11: Master Data Reference Layer Treated as Ground Truth

**What goes wrong:** `Sample_Conference_Master.md` is imported as contextual nodes, but users start treating dashboard-derived data as authoritative instead of the actual contract terms. When Master.md says the budget is $805K but the contracts sum to $900K, which is correct?

**Prevention:**
1. PROJECT.md already states "contracts override" -- enforce this in the schema. Master data nodes should have a `source: "reference"` flag, contract nodes `source: "contract"`.
2. In the web report, visually distinguish reference data from contract-sourced data (e.g., gray vs. bold).
3. When conflicts exist between master data and contracts, surface them explicitly as findings, not silently merge them.

**Phase:** Phase 4 (graph construction) -- when importing master data.

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Domain config system | Over-engineering (P5) | Simple Python dicts, rule of three |
| Document ingestion | PDF extraction failures (P2), chunking kills cross-refs (P4) | Triage docs first, full-doc extraction where possible |
| Entity extraction | Entity resolution (P3), prompt drift (P10) | Seed registry from master data, version prompts |
| Graph construction | Hardcoded biomedical logic (P1), backward compat (P8) | Audit all shared code, regression baselines |
| Cross-reference analysis | Wrong epistemic model (P6) | Build contract-specific analysis, not reuse biomedical |
| Web report | Graph scaling (P9) | Clustered/filtered views, not raw graph |
| Telegram integration | Query timeouts (P7) | Async pattern, pre-computed aggregations |
| All shared-code phases | Backward compat (P8) | CI regression tests against scenario baselines |

## Sources

- [Neo4j: Agentic GraphRAG for Commercial Contracts](https://neo4j.com/blog/developer/agentic-graphrag-for-commercial-contracts/) -- contract KG entity design, evaluation dataset importance
- [Frontiers: KG + LLM Fusion Challenges](https://www.frontiersin.org/journals/computer-science/articles/10.3389/fcomp.2025.1590632/full) -- 40% cross-domain performance degradation
- [Springer: KG Extraction Error Downstream Effects](https://link.springer.com/article/10.1007/s41109-025-00749-0) -- entity resolution errors compound in graph analysis
- [Explosion: From PDFs to AI-ready Structured Data](https://explosion.ai/blog/pdfs-nlp-structured-data) -- PDF extraction pitfalls
- [Unstract: Contract OCR Guide](https://unstract.com/blog/contract-ocr-guide-to-extracting-data-from-contracts/) -- scanned contract challenges
- [EmergentMind: Contract Knowledge Graphs Overview](https://www.emergentmind.com/topics/contract-knowledge-graphs) -- CONTRADICTS relations, cross-reference modeling
- [GRAPH-GRPO-LEX: Contract Graph Modeling](https://arxiv.org/pdf/2511.06618) -- contract-as-graph structure
- [python-telegram-bot Timeout Discussions](https://github.com/python-telegram-bot/python-telegram-bot/discussions/2876) -- Telegram bot timeout patterns
- [Procycons: PDF Extraction Benchmark 2025](https://procycons.com/en/blogs/pdf-data-extraction-benchmark/) -- PyMuPDF vs pdfplumber performance
- Epistract codebase: `scripts/build_extraction.py`, `scripts/label_communities.py`, `scripts/label_epistemic.py`, `skills/drug-discovery-extraction/validation-scripts/scan_patterns.py` -- hardcoded biomedical assumptions identified by direct code inspection (HIGH confidence)
