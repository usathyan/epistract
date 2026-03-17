# Design Spec: "Beyond RAG" Technical Report

## Overview

A technical report for arXiv/bioRxiv presenting epistract as a domain-specific agentic architecture for biomedical knowledge graph construction, positioned as an evolution from GraphRAG-based approaches. The central thesis: similarity-based graphs capture co-occurrence; agent-synthesized graphs capture meaning.

## Target

- **Venue:** arXiv (cs.CL or cs.AI) and/or bioRxiv (bioinformatics)
- **Audience:** Bioinformatics data scientists in pharma/biotech
- **Format:** Technical report, ~6-8 pages, structured sections (not IMRAD)
- **Authorship:** Single author (Umesh Bhatt), Claude Code acknowledged as extraction engine in methods
- **Purpose:** Education, promotion, attribution. Working code and reproducible scenarios included.

## Title

**Beyond RAG: Domain-Specific Agentic Architecture for Biomedical Knowledge Graph Construction**

Subtitle: *From GraphRAG to Epistract — evolving latent knowledge graphs for drug discovery*

## Central Thesis

RAG-based knowledge graph construction (GraphRAG) builds relationships from embedding similarity — statistical co-occurrence and vector proximity. This is insufficient for scientific research, where relationships must be typed, directional, evidence-backed, and ontologically grounded. Epistract replaces similarity-based assembly with agent-synthesized comprehension: an LLM reads scientific text with domain understanding, extracts structured entities and relations with confidence scores and evidence passages, and produces knowledge graphs that capture meaning rather than co-occurrence.

## Narrative Arc

1. GraphRAG proved latent knowledge graphs are extractable from scientific literature (prequel)
2. But similarity-based graphs lack the grounding scientists need: typed relations, directionality, evidence traceability, molecular validation
3. Epistract replaces retrieval with comprehension: parallel LLM agents read documents, extract structured knowledge against a domain schema, validate molecular identifiers, and produce scientist-interpretable graphs
4. Validated across 5 drug discovery domains with zero retraining — the schema generalizes, the agents generalize, the pipeline generalizes
5. Open-source, installable in one command, all test artifacts committed for reproducibility

## Paper Structure

### Section 1: Motivation (~1 page)

Open with the problem: knowledge graph construction for drug discovery is expensive, requires domain-specific NER/RE models, and produces graphs that don't generalize across therapeutic areas.

Introduce the GraphRAG experiment (prequel): used GraphRAG + local LLMs to build a latent knowledge graph from 6 drug discovery articles. Results: 3,224 entities, 2,242 relationships, ~167 community reports. Proved the concept — LLMs can extract structured knowledge from literature without task-specific training.

But GraphRAG exposed critical limitations for scientific use:
- Relationships are similarity-based, not semantically typed (an edge between "nivolumab" and "colitis" doesn't say if it's a side effect or treatment)
- No domain schema — entities are generic NER output, not ontologically grounded
- No molecular validation — SMILES strings, sequences, CAS numbers are text, not verified structures
- Community labels are numbered, not semantically meaningful
- No confidence scoring or evidence traceability

These limitations matter because scientists need to trust the graph — they need to know *why* two entities are connected, not just *that* they co-occur.

### Section 2: Architecture (~1.5 pages)

Present the epistract architecture as a response to GraphRAG's limitations. Frame each architectural decision as an evolution:

**2.1 Agent-Based Extraction (not API-based, not RAG-based)**

The key architectural choice: extraction agents run as Claude Code subprocesses, not API calls. Each agent receives a full document, reads it with scientific understanding, and produces structured JSON conforming to the domain schema. For corpora of 4+ documents, agents run in parallel — one per document.

Why agents, not APIs: agents maintain document-level context, can reason about ambiguous passages, and produce evidence-linked extractions. Why agents, not RAG: agents synthesize from comprehension, not similarity. The relationship "sotorasib INHIBITS KRAS G12C" is understood from text, not inferred from embedding proximity.

**2.2 Domain Schema (not generic NER)**

17 entity types, 30 relation types, grounded in 40+ biomedical ontologies (Biolink Model, Gene Ontology, ChEBI, MeSH, MedDRA, HGNC, UniProt, etc.). The schema is designed for the breadth of drug discovery — from gene variants to clinical trials to adverse events.

Schema design rationale: broad enough to cover neurogenetics, oncology, rare disease, immuno-oncology, and cardiovascular/inflammation without modification. Specific enough that every entity type and relation type maps to an established ontology.

**2.3 Molecular Validation Pipeline**

RDKit validates SMILES strings and computes structural properties (InChI, InChIKey, MW, LogP, Lipinski Ro5). Biopython validates nucleotide and amino acid sequences with computed properties. Regex patterns extract NCT numbers, CAS numbers, patent identifiers. This is the "trust layer" — LLMs identify molecular identifiers, deterministic tools validate them.

**2.4 Graph Construction and Community Labeling**

sift-kg handles deduplication (SemHash, Unicode normalization), Louvain community detection, and interactive visualization. A custom heuristic labeling engine generates descriptive community names from member entity composition — "Alzheimer Disease Risk Loci (30 genes)" instead of "Community 1."

**2.5 Plugin Delivery**

Packaged as a Claude Code plugin — `plugin install` installs it, `/epistract-ingest` runs the full pipeline. This is the delivery innovation: a production KG pipeline that a scientist installs in one command and runs in their terminal, not a notebook or cloud service.

**2.6 Claude Code as Development Environment**

Brief introduction to Claude Code: an agentic coding CLI that orchestrates LLM agents as subprocesses. Key capabilities used by epistract: plugin system (installable tools), skills (domain-specific prompts), parallel agent dispatch (one extractor per document), permission model (user controls what agents can do), bash/file tools (agents read/write extraction JSON, run Python scripts). This section contextualizes epistract within the Claude Code ecosystem for readers unfamiliar with agentic development tools.

### Section 3: Domain Schema Design (~1 page)

The 17 entity types organized by category:
- Drug & Chemistry: COMPOUND, METABOLITE
- Molecular Biology: GENE, PROTEIN, PROTEIN_DOMAIN, SEQUENCE_VARIANT, CELL_OR_TISSUE
- Disease & Phenotype: DISEASE, PHENOTYPE, ADVERSE_EVENT
- Clinical: CLINICAL_TRIAL, BIOMARKER, REGULATORY_ACTION
- Pathways & Mechanisms: PATHWAY, MECHANISM_OF_ACTION
- Context: ORGANIZATION, PUBLICATION

The 30 relation types organized by function:
- Drug-Target, Drug-Disease, Drug-Clinical, Drug-Drug, Molecular Biology, Biomarker, Organizational

Include the molecular biology linkage diagram (GENE → ENCODES → PROTEIN → PARTICIPATES_IN → PATHWAY → IMPLICATED_IN → DISEASE, etc.).

Naming conventions: INN for drugs, HGNC for genes, HGVS for variants, MeSH for diseases, MedDRA for adverse events.

### Section 4: Evaluation (~1.5 pages)

**4.1 Five Scenarios**

| # | Domain | Documents | Nodes | Links | Communities | UATs |
|---|---|---|---|---|---|---|
| 1 | Neurogenetics (PICALM/Alzheimer's) | 15 | 149 | 457 | 6 | 4/4 |
| 2 | Oncology (KRAS G12C) | 16 | 108 | 307 | 4 | 5/5 |
| 3 | Rare Disease | 15 | 94 | 229 | 4 | 3/3 |
| 4 | Immuno-Oncology | 16 | 132 | 361 | 5 | 4/4 |
| 5 | Cardiovascular/Inflammation | 15 | 94 | 246 | 5 | 3/3 |
| **Total** | **5 domains** | **77** | **577** | **1,600** | **24** | **19/19** |

**4.2 Cross-Domain Schema Coverage**

- Entity types exercised: 17/17 (100%) across all 5 scenarios
- Relation types exercised: 27/30 (90%)
- Each domain naturally exercises different schema facets — neurogenetics is gene-heavy, oncology is compound-heavy, rare disease is clinical-heavy, immuno-oncology is protein-heavy, cardiovascular is mechanism-heavy
- The schema is neither over-specified nor under-specified

**4.3 Community Detection Quality**

24 communities across 5 scenarios, all with biologically meaningful auto-generated labels. Representative examples per domain. Scenario 5 validated separation of unrelated therapeutic areas (cardiology vs dermatology) within a single corpus.

### Section 5: GraphRAG to Epistract Comparison (~1 page)

The evolution table:

| Dimension | GraphRAG (Prequel) | Epistract (Current) |
|---|---|---|
| Relationship basis | Embedding similarity | LLM comprehension |
| Schema | Generic NER | 17 entity types, 30 relations, 40+ ontologies |
| Relation typing | Untyped edges | Typed, directional (INHIBITS, CAUSES, etc.) |
| Evidence | None | Source passage + confidence score |
| Validation | None | RDKit, Biopython, NCT/CAS patterns |
| Development tool | Cursor + Gemini 2.5 Pro | Claude Code |
| Delivery | Scripts, manual setup | One-command plugin install |
| Scale tested | 6 articles | 77 articles across 5 domains |
| Cross-domain | Single domain | 5 domains, zero retraining |
| Community labels | Numbered | Semantic heuristic labeling |
| Reproducibility | Code on GitHub | Plugin + committed test artifacts |

Discussion of what each column means for a scientist using the graph:
- Typed relations mean you can ask "what inhibits KRAS?" not just "what's near KRAS?"
- Evidence traceability means you can verify any edge back to the source text
- Molecular validation means SMILES in the graph are verified structures, not LLM approximations

### Section 6: Human-AI Collaboration Process (~1 page)

This section describes how epistract was actually built — not as autonomous AI generation, but as an interactive power session with continuous human-AI collaboration.

**6.1 Session Structure**

The entire system — plugin architecture, domain schema, 5 test scenarios, extraction pipeline, documentation, and this paper — was built in collaborative Claude Code sessions. The human drove scientific and strategic decisions; Claude Code drove implementation, parallelization, and documentation.

**6.2 Course Corrections**

Document specific instances where human judgment redirected the process:
- Branding: user proposed the "latent knowledge graphs" framing and title direction
- Tooling: user redirected from Chrome DevTools Protocol to Playwright for screenshots
- Documentation completeness: user caught that scenario results weren't pushed, that README still showed "Pending," that the status column was redundant after all scenarios completed
- Disclaimer wording: multiple iterations to find the right tone ("explores how AI-assisted tooling can accelerate...")
- Paper framing: user sharpened "Beyond RAG" from an architecture claim to an epistemological one (comprehension vs similarity)

**6.3 What the Human Decided vs What the AI Decided**

Human decisions: scenario topics, UAT criteria, branding, paper framing, target audience, what to include/exclude. AI decisions: extraction JSON schema, parallel agent dispatch, defensive normalization, community labeling heuristics, documentation structure.

**6.4 Engineering Findings**

Brief: 3 bugs found through live testing (F-001 schema naming, F-002 unlabeled communities, F-003 version cascade). Two-layer defense pattern. Reference FINDINGS.md for details.

### Section 7: Availability & Reproducibility (~0.5 page)

- Open source: GitHub repository with MIT license
- One-command install: `plugin install epistract@epistract`
- All test inputs (77 PubMed abstracts), outputs (extraction JSONs, graph data), and evidence (screenshots) committed to repository
- Any reviewer can re-run any scenario and compare against committed baseline
- Dependencies: Claude Code, Python 3.11+, sift-kg (auto-installed), optional RDKit/Biopython

### Section 8: Conclusion (~0.5 page)

Close the arc: what began as a GraphRAG experiment with 6 articles evolved into a domain-specific agentic pipeline validated across 5 drug discovery domains. The central finding: for scientific knowledge graphs, comprehension-based extraction produces fundamentally more useful graphs than similarity-based assembly. The contribution is both the method (agentic extraction with domain schemas) and the tool (an open-source, installable pipeline that works today).

Future directions: Neo4j export, vector embeddings for combined graph+vector retrieval, external enrichment from PubChem/ChEMBL/UniProt APIs.

## Figures

1. **Architecture diagram** — the epistract pipeline (mermaid, already in README)
2. **Domain schema linkage** — GENE → PROTEIN → PATHWAY → DISEASE chain (mermaid, already in README)
3. **Graph screenshots** — one representative per scenario (already captured)
4. **Comparison table** — GraphRAG vs Epistract (Section 5)
5. **Schema coverage heatmap** — entity/relation types exercised per scenario

## References

- GraphRAG (Microsoft Research, 2024)
- sift-kg (Ceresa, 2024)
- Biolink Model
- Claude Code documentation
- The prequel article (self-citation)
- Key biomedical ontologies (ChEBI, GO, MeSH, etc.)

## Output Format

- LaTeX with bioRxiv/arXiv template
- PDF generated via `pdflatex` or `tectonic`
- Figures as PNG (screenshots) and PDF (mermaid renders)
- BibTeX for references

## Writing Approach

- Use `elements-of-style:writing-clearly-and-concisely` principles
- Active voice, concrete language, no hedging
- Every claim backed by data from the 5 scenarios
- Code snippets only where they illustrate architectural decisions
- Prefer tables and figures over prose for comparative data

## Skills & Tools for Production

The following scientific skills will be used during writing:

- **`scientific-skills:scientific-writing`** — IMRAD-adjacent structure, flowing prose, citation management
- **`scientific-skills:scientific-visualization`** — Publication-ready figures (multi-panel layouts, colorblind-safe palettes)
- **`scientific-skills:scientific-schematics`** — Architecture diagrams, pipeline schematics
- **`scientific-skills:matplotlib`** / **`scientific-skills:seaborn`** — Schema coverage heatmaps, entity distribution charts
- **`scientific-skills:latex-posters`** or **`scientific-skills:venue-templates`** — arXiv/bioRxiv LaTeX formatting
- **`scientific-skills:citation-management`** — BibTeX generation, reference validation
- **`scientific-skills:generate-image`** — Custom figures where programmatic generation falls short
- **`scientific-skills:infographics`** — The GraphRAG → Epistract evolution visual
- **`scientific-skills:markdown-mermaid-writing`** — Architecture and pipeline diagrams rendered to publication quality via `beautiful-mermaid`

## Non-Goals

- This is not a benchmarking paper — we don't compare against BioBERT, PubMedBERT, etc.
- This is not a survey — we don't review all biomedical KG methods
- This is not a product announcement — the tone is scientific, not promotional
- We don't claim state-of-the-art on any NLP benchmark
