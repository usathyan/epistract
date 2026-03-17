# "Beyond RAG" Technical Report — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Write and typeset a 6-8 page technical report for arXiv/bioRxiv presenting epistract's agentic architecture for biomedical knowledge graph construction.

**Architecture:** LaTeX document with 8 sections, 5-7 publication-quality figures, BibTeX references. Written section-by-section using scientific-writing skill, figures generated with scientific-visualization/schematics skills, typeset with arXiv template.

**Tech Stack:** LaTeX (arXiv template), Python (matplotlib/seaborn for figures), beautiful-mermaid (architecture diagrams), BibTeX, tectonic or pdflatex

---

## File Structure

```
paper/
├── main.tex                    # Master LaTeX document
├── references.bib              # BibTeX references
├── sections/
│   ├── 01-motivation.tex       # Section 1: Motivation
│   ├── 02-architecture.tex     # Section 2: Architecture
│   ├── 03-schema.tex           # Section 3: Domain Schema Design
│   ├── 04-evaluation.tex       # Section 4: Evaluation
│   ├── 05-comparison.tex       # Section 5: GraphRAG to Epistract
│   ├── 06-findings.tex         # Section 6: Findings & Lessons
│   ├── 07-availability.tex     # Section 7: Availability & Reproducibility
│   └── 08-conclusion.tex       # Section 8: Conclusion
├── figures/
│   ├── fig1-architecture.pdf       # Pipeline architecture diagram
│   ├── fig2-schema-linkage.pdf     # Molecular biology linkage diagram
│   ├── fig3-scenario-graphs.png    # Multi-panel graph screenshots (5 scenarios)
│   ├── fig4-comparison-table.pdf   # GraphRAG vs Epistract (rendered as figure)
│   ├── fig5-schema-coverage.pdf    # Entity/relation heatmap across scenarios
│   └── fig6-evolution.pdf          # GraphRAG → Epistract evolution infographic
└── Makefile                    # Build targets: pdf, clean, figures
```

---

## Chunk 1: Project Setup + References

### Task 1: Scaffold LaTeX project

**Files:**
- Create: `paper/main.tex`
- Create: `paper/Makefile`
- Create: `paper/references.bib`

- [ ] **Step 1: Create paper directory**

```bash
mkdir -p paper/sections paper/figures
```

- [ ] **Step 2: Create main.tex with arXiv template**

Use `scientific-skills:venue-templates` skill to get arXiv preprint template. Set up:
- Title: "Beyond RAG: Domain-Specific Agentic Architecture for Biomedical Knowledge Graph Construction"
- Author: Umesh Bhatt
- Abstract placeholder
- `\input{}` for each section file
- `\bibliography{references}`

- [ ] **Step 3: Create Makefile**

```makefile
.PHONY: pdf clean figures

pdf: figures
	cd paper && tectonic main.tex

clean:
	cd paper && rm -f *.aux *.bbl *.blg *.log *.pdf

figures:
	python3 paper/scripts/generate_figures.py
```

- [ ] **Step 4: Create references.bib**

Use `scientific-skills:citation-management` skill. Populate with:
- GraphRAG (Microsoft Research, Edge et al. 2024)
- sift-kg (Ceresa 2024)
- Biolink Model (Unni et al. 2022)
- Claude Code / Anthropic documentation
- The prequel article (self-citation — get exact reference from user)
- Key ontologies: ChEBI, Gene Ontology, MeSH, MedDRA, HGNC, UniProt
- Relevant biomedical KG papers: PrimeKG, Hetionet, SPOKE
- LLM extraction papers: GPT-4 for biomedical NER, etc.

- [ ] **Step 5: Verify LaTeX builds**

```bash
cd paper && tectonic main.tex
```

Expected: PDF generates with title page and empty sections.

- [ ] **Step 6: Commit**

```bash
git add paper/
git commit -m "feat: scaffold LaTeX project for Beyond RAG paper"
```

---

## Chunk 2: Figures

### Task 2: Generate architecture diagram (Figure 1)

**Files:**
- Create: `paper/figures/fig1-architecture.pdf`

- [ ] **Step 1: Render architecture mermaid to publication quality**

Use `scientific-skills:scientific-schematics` or `beautiful-mermaid` to render the pipeline diagram from README.md (the `flowchart LR` diagram: Documents → Text Extraction → Claude Extraction → Molecular Validation → Graph Building → Community Labeling → Output). Render as PDF with dark-on-white color scheme suitable for print.

- [ ] **Step 2: Verify figure renders correctly in LaTeX**

- [ ] **Step 3: Commit**

```bash
git add paper/figures/fig1-architecture.pdf
git commit -m "fig: add architecture pipeline diagram"
```

### Task 3: Generate schema linkage diagram (Figure 2)

**Files:**
- Create: `paper/figures/fig2-schema-linkage.pdf`

- [ ] **Step 1: Render molecular biology linkage mermaid**

The `flowchart TB` from README: GENE → ENCODES → PROTEIN → PARTICIPATES_IN → PATHWAY, etc. Render as PDF, print-friendly.

- [ ] **Step 2: Commit**

```bash
git add paper/figures/fig2-schema-linkage.pdf
git commit -m "fig: add domain schema linkage diagram"
```

### Task 4: Create multi-panel scenario graph figure (Figure 3)

**Files:**
- Create: `paper/scripts/generate_figures.py`
- Create: `paper/figures/fig3-scenario-graphs.png`

- [ ] **Step 1: Write figure generation script**

Use `scientific-skills:scientific-visualization` and `scientific-skills:matplotlib`. Create a 5-panel figure (1 row × 5, or 2 rows) combining the 5 scenario screenshots from `tests/scenarios/screenshots/scenario-0N-graph.png`. Add panel labels (a-e), scenario names, and node/link counts as subtitles.

- [ ] **Step 2: Generate figure**

```bash
python3 paper/scripts/generate_figures.py
```

- [ ] **Step 3: Commit**

```bash
git add paper/scripts/ paper/figures/fig3-scenario-graphs.png
git commit -m "fig: add multi-panel scenario graph screenshots"
```

### Task 5: Generate schema coverage heatmap (Figure 5)

**Files:**
- Modify: `paper/scripts/generate_figures.py`
- Create: `paper/figures/fig5-schema-coverage.pdf`

- [ ] **Step 1: Add heatmap generation to script**

Use `scientific-skills:seaborn` or `scientific-skills:matplotlib`. Create a heatmap showing which entity types and relation types are exercised in each scenario. Data source: `tests/FINDINGS.md` cumulative metrics and F-007 schema generalization table.

Rows: 17 entity types + 30 relation types
Columns: 5 scenarios
Cells: present/absent (binary) or count

- [ ] **Step 2: Generate and verify**

- [ ] **Step 3: Commit**

```bash
git add paper/scripts/ paper/figures/fig5-schema-coverage.pdf
git commit -m "fig: add schema coverage heatmap"
```

### Task 6: Create GraphRAG → Epistract evolution infographic (Figure 6)

**Files:**
- Create: `paper/figures/fig6-evolution.pdf`

- [ ] **Step 1: Generate evolution infographic**

Use `scientific-skills:infographics` or `scientific-skills:scientific-schematics`. Visual showing the two-stage evolution:
- Left: GraphRAG approach (embedding similarity, generic NER, numbered communities)
- Right: Epistract approach (agent comprehension, domain schema, semantic communities)
- Center: arrow showing the evolution with key differentiators labeled

- [ ] **Step 2: Commit**

```bash
git add paper/figures/fig6-evolution.pdf
git commit -m "fig: add GraphRAG to Epistract evolution infographic"
```

---

## Chunk 3: Write Sections 1-3

### Task 7: Write Section 1 — Motivation

**Files:**
- Create: `paper/sections/01-motivation.tex`

- [ ] **Step 1: Write motivation section**

Use `scientific-skills:scientific-writing` skill. ~1 page. Content per spec:
- Problem statement: KG construction for drug discovery is expensive and domain-specific
- GraphRAG prequel: 6 articles, 3224 entities, 2242 relationships, ~167 communities
- Limitations exposed: untyped relations, no schema, no validation, numbered communities, no evidence
- The gap: scientists need typed, directional, evidence-backed, ontologically grounded relationships
- Thesis statement: agent-synthesized comprehension vs similarity-based assembly

Reference: prequel article, GraphRAG paper, relevant biomedical KG work.

- [ ] **Step 2: Verify compiles**

```bash
cd paper && tectonic main.tex
```

- [ ] **Step 3: Commit**

```bash
git add paper/sections/01-motivation.tex
git commit -m "paper: write Section 1 — Motivation"
```

### Task 8: Write Section 2 — Architecture

**Files:**
- Create: `paper/sections/02-architecture.tex`

- [ ] **Step 1: Write architecture section**

Use `scientific-skills:scientific-writing`. ~1.5 pages. Five subsections per spec:
- 2.1 Agent-Based Extraction — why agents not APIs, why agents not RAG
- 2.2 Domain Schema — 17 types, 30 relations, 40+ ontologies
- 2.3 Molecular Validation — RDKit, Biopython, regex patterns
- 2.4 Graph Construction — sift-kg, dedup, community detection, labeling
- 2.5 Plugin Delivery — one-command install

Reference Figure 1 (architecture diagram). Frame each decision as GraphRAG → Epistract evolution.

- [ ] **Step 2: Verify compiles**

- [ ] **Step 3: Commit**

```bash
git add paper/sections/02-architecture.tex
git commit -m "paper: write Section 2 — Architecture"
```

### Task 9: Write Section 3 — Domain Schema Design

**Files:**
- Create: `paper/sections/03-schema.tex`

- [ ] **Step 1: Write schema section**

Use `scientific-skills:scientific-writing`. ~1 page. Content:
- Entity type taxonomy table (6 categories, 17 types)
- Relation type taxonomy (7 categories, 30 types)
- Molecular biology linkage diagram (reference Figure 2)
- Naming conventions (INN, HGNC, HGVS, MeSH, MedDRA)
- Ontology grounding table

- [ ] **Step 2: Verify compiles**

- [ ] **Step 3: Commit**

```bash
git add paper/sections/03-schema.tex
git commit -m "paper: write Section 3 — Domain Schema Design"
```

---

## Chunk 4: Write Sections 4-5

### Task 10: Write Section 4 — Evaluation

**Files:**
- Create: `paper/sections/04-evaluation.tex`

- [ ] **Step 1: Write evaluation section**

Use `scientific-skills:scientific-writing`. ~1.5 pages. Three subsections:
- 4.1 Five Scenarios — summary table (77 docs, 577 nodes, 1600 links, 19/19 UATs)
- 4.2 Cross-Domain Schema Coverage — 100% entity, 90% relation coverage. Reference Figure 5 (heatmap). Each domain exercises different facets.
- 4.3 Community Detection Quality — 24 communities, all semantically labeled. Representative examples. Scenario 5 cross-domain separation validation.

Reference Figure 3 (multi-panel screenshots).

- [ ] **Step 2: Verify compiles**

- [ ] **Step 3: Commit**

```bash
git add paper/sections/04-evaluation.tex
git commit -m "paper: write Section 4 — Evaluation"
```

### Task 11: Write Section 5 — GraphRAG to Epistract Comparison

**Files:**
- Create: `paper/sections/05-comparison.tex`

- [ ] **Step 1: Write comparison section**

Use `scientific-skills:scientific-writing`. ~1 page. Content:
- Full comparison table (11 dimensions from spec)
- Discussion of what typed relations, evidence traceability, and molecular validation mean for scientists
- Reference Figure 6 (evolution infographic)

- [ ] **Step 2: Verify compiles**

- [ ] **Step 3: Commit**

```bash
git add paper/sections/05-comparison.tex
git commit -m "paper: write Section 5 — GraphRAG to Epistract Comparison"
```

---

## Chunk 5: Write Sections 6-8 + Abstract + Final Assembly

### Task 12: Write Section 6 — Findings & Lessons Learned

**Files:**
- Create: `paper/sections/06-findings.tex`

- [ ] **Step 1: Write findings section**

~0.5 page. Brief: 3 bugs found and fixed (F-001 schema field naming, F-002 unlabeled communities, F-003 version propagation). Core design principles for LLM-in-the-loop systems. Reference FINDINGS.md for details.

- [ ] **Step 2: Commit**

```bash
git add paper/sections/06-findings.tex
git commit -m "paper: write Section 6 — Findings"
```

### Task 13: Write Section 7 — Availability & Reproducibility

**Files:**
- Create: `paper/sections/07-availability.tex`

- [ ] **Step 1: Write availability section**

~0.5 page. Open source (MIT), one-command install, all artifacts committed, dependencies listed.

- [ ] **Step 2: Commit**

```bash
git add paper/sections/07-availability.tex
git commit -m "paper: write Section 7 — Availability"
```

### Task 14: Write Section 8 — Conclusion

**Files:**
- Create: `paper/sections/08-conclusion.tex`

- [ ] **Step 1: Write conclusion**

~0.5 page. Close the GraphRAG → Epistract arc. Central finding: comprehension > similarity for scientific KGs. Future directions: Neo4j, vector embeddings, external enrichment APIs.

- [ ] **Step 2: Commit**

```bash
git add paper/sections/08-conclusion.tex
git commit -m "paper: write Section 8 — Conclusion"
```

### Task 15: Write Abstract

**Files:**
- Modify: `paper/main.tex`

- [ ] **Step 1: Write abstract**

~200 words. Must contain: problem, approach (agentic vs RAG), key result (5 domains, 77 docs, 577 nodes, 19/19 UATs, zero retraining), availability (open-source plugin).

- [ ] **Step 2: Commit**

```bash
git add paper/main.tex
git commit -m "paper: write abstract"
```

### Task 16: Final assembly and PDF build

**Files:**
- Modify: `paper/main.tex`

- [ ] **Step 1: Verify all sections compile together**

```bash
cd paper && tectonic main.tex
```

- [ ] **Step 2: Check page count (target: 6-8 pages)**

If over, tighten prose. If under, add detail to evaluation or comparison sections.

- [ ] **Step 3: Verify all figures render**

Check all 5-6 figures appear in the PDF at appropriate sizes.

- [ ] **Step 4: Verify all references resolve**

No `[?]` citations in the PDF.

- [ ] **Step 5: Final commit**

```bash
git add paper/
git commit -m "paper: complete Beyond RAG technical report v1"
```

- [ ] **Step 6: Generate final PDF and push**

```bash
git push
```
