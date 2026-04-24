#!/bin/bash
# Epistract v3.1 demo — KGC 2026 Tools & Demonstrations Track, 2026-05-08
#
# Run this in a clean Ghostty window. Press Enter to advance between acts.
# Read narration from phone (see docs/demo-v3/narration.md).
# Screen-record terminal + browser. Add voiceover in post if not live.
#
# BEFORE RECORDING:
#   1. Pre-launch both workbenches (in separate terminals):
#        python scripts/launch_workbench.py tests/corpora/06_glp1_landscape/output-v3 --domain drug-discovery --port 8000
#        python scripts/launch_workbench.py tests/corpora/07_glp1_phase3_trials/output --domain clinicaltrials --port 8001
#      Let both load + physics settle before starting.
#   2. Verify ANTHROPIC_API_KEY or OPENROUTER_API_KEY is set (chat will 402 without).
#   3. DnD ON, notifications off, bookmark bar hidden.
#   4. Terminal: 1920x1080, dark theme, Cmd+= 3-4 times for font size.

set -e
cd "$(dirname "$0")/../.."

banner() {
    clear
    echo "=================================================================="
    echo "  $1"
    echo "=================================================================="
    echo ""
}

pause() {
    read -p "  [Press Enter for next act...] "
}

banner "EPISTRACT v3.1.0 - Knowledge Graph Conference 2026"
echo "  github.com/usathyan/epistract"
echo "  Tools & Demonstrations Track, 2026-05-08"
echo ""
echo "  Three pre-built domains. Automatic analyst narrator."
echo "  Turn any document corpus into a knowledge graph that"
echo "  knows what it doesn't know."
echo ""
pause

# Act 2: S6 corpus + build summary
banner "ACT 2 - S6 GLP-1 Competitive Intelligence (drug-discovery)"
echo "$ ls tests/corpora/06_glp1_landscape/docs/ | head -8"
echo ""
ls tests/corpora/06_glp1_landscape/docs/ | head -8
echo ""
echo "# 10 patent filings + 24 PubMed papers = 34 docs"
echo ""
pause

echo "$ # /epistract:ingest tests/corpora/06_glp1_landscape/docs --domain drug-discovery"
echo "$ # (pipeline already ran - output in output-v3/)"
echo ""
echo "$ cat tests/corpora/06_glp1_landscape/output-v3/claims_layer.json | jq '.summary.epistemic_status_counts'"
echo ""
cat tests/corpora/06_glp1_landscape/output-v3/claims_layer.json | jq '.summary.epistemic_status_counts'
echo ""
echo "# 278 nodes, 855 edges; 61 prophetic, 33 contested, 2 contradictions"
pause

# Act 3/4: Workbench chat + narrator
banner "ACT 3+4 - Workbench chat + automatic narrator briefing"
echo "$ # (workbench already running on port 8000)"
echo "$ # Switch to browser - ask: Which patents make prophetic claims?"
echo ""
echo "# After the chat demo, return here and read the narrator briefing:"
echo ""
echo "$ head -80 tests/corpora/06_glp1_landscape/output-v3/epistemic_narrative.md"
echo ""
echo "[Press Enter to show the narrative]"
read
head -80 tests/corpora/06_glp1_landscape/output-v3/epistemic_narrative.md
echo ""
pause

# Act 5: S7 clinicaltrials corpus
banner "ACT 5 - The second lens: clinicaltrials domain"
echo "$ ls domains/"
echo ""
ls domains/ | grep -v __pycache__
echo ""
echo "# drug-discovery, contracts, clinicaltrials (new in v3.1)"
echo ""
echo "$ ls tests/corpora/07_glp1_phase3_trials/docs/"
echo ""
ls tests/corpora/07_glp1_phase3_trials/docs/
echo ""
echo "# 10 GLP-1 Phase 3 protocols from ClinicalTrials.gov v2 API"
pause

echo "$ cat tests/corpora/07_glp1_phase3_trials/output/graph_data.json | jq '.metadata | {nodes: .entity_count, edges: .relation_count, domain: .domain}'"
echo ""
cat tests/corpora/07_glp1_phase3_trials/output/graph_data.json | jq '.metadata | {nodes: .entity_count, edges: .relation_count, domain: .domain}'
echo ""
echo "# 142 nodes, 395 edges, domain: clinicaltrials (FIDL-06 auto-detect)"
pause

# Act 6: Enrichment + phase-tier grading
banner "ACT 6 - CT.gov v2 + PubChem enrichment + phase-tier grading"
echo "$ python domains/clinicaltrials/enrich.py tests/corpora/07_glp1_phase3_trials/output"
echo ""
echo "  (10 trials + 2 compounds, 100% hit rate - pre-computed report)"
cat tests/corpora/07_glp1_phase3_trials/output/extractions/_enrichment_report.json | jq '.'
echo ""
pause

echo "$ head -25 tests/corpora/07_glp1_phase3_trials/output/epistemic_narrative.md"
echo ""
head -25 tests/corpora/07_glp1_phase3_trials/output/epistemic_narrative.md
echo ""
pause

# Act 7: Cross-domain side-by-side
banner "ACT 7 - Same question, two lenses"
echo "  Switch to split-screen browser:"
echo "    LEFT  -> http://127.0.0.1:8000 (S6 drug-discovery)"
echo "    RIGHT -> http://127.0.0.1:8001 (S7 clinicaltrials)"
echo ""
echo "  Type in BOTH chats simultaneously:"
echo "    > What's the evidence for tirzepatide in obesity?"
echo ""
echo "  Let both stream in parallel. Note the citation style + vocabulary"
echo "  differ by persona - patents/papers vs NCT IDs."
pause

# Act 8: Framework mechanics
banner "ACT 8 - A whole domain is 5 files"
echo "$ find domains/clinicaltrials/ -maxdepth 2 | sort"
echo ""
find domains/clinicaltrials/ -maxdepth 2 | sort
echo ""
echo "# domain.yaml, SKILL.md, epistemic.py, enrich.py, workbench/template.yaml"
echo ""
echo "$ # /epistract:domain --input ./my-sample-docs/ --name my-domain"
echo "  -> wizard produces all 5 files from 3-5 sample documents"
pause

# Act 9: Closing
banner "EPISTRACT v3.1.0 - github.com/usathyan/epistract"
echo "  MIT license . Claude Code plugin . automatic analyst narrator"
echo ""
echo "  - docs/SHOWCASE-GLP1.md (S6)"
echo "  - docs/SHOWCASE-CLINICALTRIALS.md (S7)"
echo "  - docs/ADDING-DOMAINS.md (build your own)"
echo ""
echo "  Releases:"
echo "    v3.0.0 - Graph Fidelity & Honest Limits (2026-04-22)"
echo "    v3.1.0 - Clinical Trials domain + enrichment (2026-04-23)"
echo ""
echo "  Thanks for watching. QnA now."
echo ""
