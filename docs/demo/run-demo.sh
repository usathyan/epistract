#!/bin/bash
# Epistract Demo — Knowledge Graph Conference
# Run this in a clean terminal. Press Enter to advance between acts.
# Add voiceover in post using the talking points in narration.md

cd /Users/umeshbhatt/code/epistract
clear

echo "═══════════════════════════════════════════════════════════════"
echo "  EPISTRACT — Drug Discovery Knowledge Graphs"
echo "  Claude Code Plugin | github.com/usathyan/epistract"
echo "═══════════════════════════════════════════════════════════════"
echo ""
read -p "Press Enter to start..."
clear

# ── Act 1: What is Epistract ──────────────────────────────────────
echo "$ claude"
echo ""
echo "Available epistract commands:"
echo ""
echo "  /epistract-setup      Install dependencies"
echo "  /epistract-ingest     Ingest documents → extract → build → view"
echo "  /epistract-build      Build graph from existing extractions"
echo "  /epistract-validate   Validate molecular identifiers (SMILES, sequences)"
echo "  /epistract-view       Open interactive graph viewer"
echo "  /epistract-epistemic  Analyze epistemic patterns (hypotheses, contradictions)"
echo "  /epistract-query      Search entities in the knowledge graph"
echo "  /epistract-export     Export to GraphML, GEXF, CSV, SQLite, JSON"
echo ""
read -p "Press Enter..."
clear

# ── Act 2: The Corpus ─────────────────────────────────────────────
echo "$ ls tests/corpora/06_glp1_landscape/output/extractions/"
echo ""
ls tests/corpora/06_glp1_landscape/output/extractions/
echo ""
echo "# 10 patents (Novo Nordisk, Pfizer, Eli Lilly, Hanmi, Zealand)"
echo "# 24 PubMed papers about GLP-1 receptor agonists"
echo ""
read -p "Press Enter..."
clear

# ── Act 3: Graph Info ─────────────────────────────────────────────
echo "$ python3 scripts/run_sift.py info tests/corpora/06_glp1_landscape/output"
echo ""
python3 scripts/run_sift.py info tests/corpora/06_glp1_landscape/output
echo ""
echo "# 206 entities, 630 relations from 34 documents"
echo ""
read -p "Press Enter to open interactive graph..."
clear

# ── Act 4: Open Graph Visualization ───────────────────────────────
echo "$ open tests/corpora/06_glp1_landscape/output/graph.html"
echo ""
open tests/corpora/06_glp1_landscape/output/graph.html
echo "# Interactive knowledge graph opened in browser."
echo "# Explore: click nodes, zoom, see community clusters."
echo ""
read -p "Press Enter when done exploring the graph..."
clear

# ── Act 5: Epistemic Analysis ─────────────────────────────────────
echo "$ python3 scripts/label_epistemic.py tests/corpora/06_glp1_landscape/output"
echo ""
python3 scripts/label_epistemic.py tests/corpora/06_glp1_landscape/output
echo ""
read -p "Press Enter for detail..."
echo ""
echo "── Document Type Signatures ──────────────────────────────────"
echo ""
python3 -c "
import json
c = json.load(open('tests/corpora/06_glp1_landscape/output/claims_layer.json'))
print('Document type signatures:')
for dt, counts in c['summary']['document_types'].items():
    print(f'  {dt}: {counts}')
print()
print('Hypotheses found:')
for h in c['super_domain']['hypotheses']:
    print(f'  {h[\"label\"][:70]}')
    print(f'    {h[\"relation_count\"]} relations, {h[\"entity_count\"]} entities')
    print(f'    Evidence: \"{h[\"evidence_summary\"][:80]}\"')
    print()
"
read -p "Press Enter..."
clear

# ── Act 6: Negative Control ───────────────────────────────────────
echo "── Negative Control: KRAS G12C (established oncology) ────────"
echo ""
echo "$ python3 scripts/label_epistemic.py tests/corpora/02_kras_g12c_landscape/output"
echo ""
python3 scripts/label_epistemic.py tests/corpora/02_kras_g12c_landscape/output
echo ""
echo "# 307 relations. Zero epistemic content. 100% brute facts."
echo "# Epistemic density correlates with research maturity."
echo ""
read -p "Press Enter..."
clear

# ── Act 7: S1 Contradiction ──────────────────────────────────────
echo "── PICALM / Alzheimer's Disease ─────────────────────────────"
echo ""
echo "$ python3 scripts/label_epistemic.py tests/corpora/01_picalm_alzheimers/output"
echo ""
python3 scripts/label_epistemic.py tests/corpora/01_picalm_alzheimers/output
echo ""
read -p "Press Enter to see annotated graphs..."
echo ""
echo "# Opening: Hypothesis crossing community boundaries..."
open docs/analysis/screenshots/graph-01-hypothesis-highlighted.png
sleep 3
echo "# Opening: Contradiction + contested relations..."
open docs/analysis/screenshots/graph-01-contested-highlighted.png
echo ""
read -p "Press Enter..."
clear

# ── Act 8: Close ─────────────────────────────────────────────────
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "  Communities tell you WHERE to look."
echo "  Super Domains tell you WHAT KIND OF KNOWLEDGE you're looking at."
echo "  Complementary, not competing."
echo ""
echo "  github.com/usathyan/epistract"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""
