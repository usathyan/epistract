#!/bin/bash
# Epistract v3.1 demo — KGC 2026 Tools & Demonstrations Track, 2026-05-08
#
# Graph-first arc for KG specialists:
#   Act 1: The KG problem (epistemic content vs. brute facts)
#   Act 2: Two-layer KG in action (Louvain communities + Super Domain)
#   Act 3: S6 life-sciences illustration (GLP-1 corpus)
#   Act 4: Automatic analyst briefing
#   Act 5: Different analysts for different knowledge (S6 vs S7)
#   Act 6: Tech geek internals (domain = 4 files, persona single-source-of-truth)
#   Act 7: Closing
#
# BEFORE RECORDING:
#   1. Pre-launch both workbenches (in separate terminals):
#        python scripts/launch_workbench.py tests/corpora/06_glp1_landscape/output-v3 --domain drug-discovery --port 8000
#        python scripts/launch_workbench.py tests/corpora/07_glp1_phase3_trials/output --domain clinicaltrials --port 8001
#      Let both load + physics settle before starting.
#   2. Verify ANTHROPIC_API_KEY or OPENROUTER_API_KEY is set (chat will 402 without).
#   3. DnD ON, notifications off, bookmark bar hidden.
#   4. Terminal: 1920x1080, dark theme, Cmd+= 3-4 times for font size.
#
# Run: bash docs/demo-v3/run-demo.sh
# Pauses between acts. Press Enter to advance.

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
echo "  Knowledge graphs that know what they don't know."
echo ""
echo "  Two-layer architecture:"
echo "    Layer 1 - brute facts, grounded to domain ontology"
echo "    Layer 2 - Super Domain, epistemic status per edge"
echo ""
pause

# Act 2: Two-layer KG in action
banner "ACT 2 - A two-layer knowledge graph in action"
echo "  Switch to browser at http://127.0.0.1:8000"
echo "  Click the Graph panel."
echo ""
echo "  Observe: 278 entities, 855 relations, 10 Louvain communities"
echo "  Standard labeled property graph - Neo4j/NetworkX-shaped."
echo ""
echo "  Community structure says WHERE to look, not WHAT KIND of knowledge."
pause

echo "$ cat tests/corpora/06_glp1_landscape/output-v3/claims_layer.json | jq '.summary.epistemic_status_counts'"
echo ""
cat tests/corpora/06_glp1_landscape/output-v3/claims_layer.json | jq '.summary.epistemic_status_counts'
echo ""
echo "# Super Domain layer: the same 855 relations, epistemically classified."
echo "# 61 prophetic - patent forward-looking language"
echo "# 33 contested - same edge, conflicting confidence across sources"
echo "#  2 contradictions"
echo "# Rest cleanly asserted."
pause

# Act 3: S6 life-sciences illustration
banner "ACT 3 - S6 life-sciences illustration (GLP-1 corpus)"
echo "  Switch to browser at http://127.0.0.1:8000"
echo "  Click the Chat panel."
echo ""
echo "  Context for the audience:"
echo "    - 34 documents on GLP-1 receptor agonists"
echo "    - semaglutide (Ozempic/Wegovy), tirzepatide (Mounjaro/Zepbound)"
echo "    - 10 patents (Novo Nordisk, Pfizer, Eli Lilly) + 24 PubMed abstracts"
echo ""
echo "  Type into chat:"
echo ""
echo "    Which patents make prophetic claims about new indications,"
echo "    and where are the biggest gaps between prophetic breadth"
echo "    and asserted evidence?"
echo ""
echo "  Let it stream. The answer is a cross-document synthesis - not"
echo "  retrieval - grouped by patent family with inline citations."
pause

# Act 4: Automatic analyst briefing
banner "ACT 4 - The automatic analyst briefing"
echo "$ bat tests/corpora/06_glp1_landscape/output-v3/epistemic_narrative.md | head -80"
echo ""
echo "  [Press Enter to display]"
read
head -80 tests/corpora/06_glp1_landscape/output-v3/epistemic_narrative.md
echo ""
echo "  Key excerpts to read verbatim (scroll + quote):"
echo "    - Executive Summary opening (61 prophetic claims...)"
echo "    - Contested claim with temporal stratification"
echo "    - Recommended follow-up (integrate SURPASS-2)"
echo ""
echo "  Key point: the persona that wrote this briefing is the same"
echo "  string that powered the chat in Act 3. One YAML field. Two surfaces."
pause

# Act 5: Different analysts for different knowledge
banner "ACT 5 - Different analysts for different kinds of knowledge"
echo "  Switch to split-screen browser:"
echo "    LEFT  -> http://127.0.0.1:8000 (S6 drug-discovery)"
echo "    RIGHT -> http://127.0.0.1:8001 (S7 clinicaltrials)"
echo ""
echo "  Context for the audience:"
echo "    - Same molecular space (GLP-1 agonists)"
echo "    - Different source material - 10 CT.gov trial protocols"
echo "    - Different domain - clinicaltrials (12 entity types, 10 relations)"
echo "    - Different persona - senior CT analyst, phase-tier grading"
echo ""
echo "  Type in BOTH chats simultaneously:"
echo ""
echo "    What's the evidence for tirzepatide in obesity?"
echo ""
echo "  Let both stream. Observe citation style + vocabulary differ:"
echo "    LEFT  - patents + PubMed, epistemic status vocabulary"
echo "    RIGHT - NCT IDs, enrollment counts, phase-tier grades"
echo ""
echo "  Neither alone is a CI brief. Together they are."
pause

# Act 6: For the tech geeks
banner "ACT 6 - For the tech geeks - how it's built"
echo "$ tree domains/clinicaltrials/ -L 2"
echo ""
tree domains/clinicaltrials/ -L 2 2>/dev/null || find domains/clinicaltrials/ -maxdepth 2 | sort
echo ""
echo "# 4 required files: domain.yaml, SKILL.md, epistemic.py, workbench/template.yaml"
echo "# enrich.py is an optional package-level helper (domain-specific)"
echo ""
pause

echo "$ cat domains/clinicaltrials/workbench/template.yaml | grep -A 3 '^persona'"
echo ""
grep -A 3 "^persona" domains/clinicaltrials/workbench/template.yaml
echo ""
echo "# One string. Drives reactive chat AND proactive narrator."
echo "# Single source of truth per domain."
pause

echo "$ ls core/"
echo ""
ls core/ | grep -v __pycache__ | grep -v "^_"
echo ""
echo "# Core is domain-agnostic. No drug-discovery or clinicaltrials"
echo "# code anywhere in core/. Domain package is resolved at runtime."
echo ""
echo "# LLM priority: Azure AI Foundry > Anthropic > OpenRouter"
echo "# Claude Sonnet at recording time."
pause

echo "$ # /epistract:domain --input ./my-sample-docs/ --name my-domain"
echo ""
echo "# Wizard runs 3-pass LLM analysis on 3-5 sample docs"
echo "# Produces a working domain package in ~15 minutes"
pause

# Act 7: Closing
banner "EPISTRACT v3.1.0 - github.com/usathyan/epistract"
echo "  MIT license . Claude Code plugin . v3.1.0 shipped 2026-04-23"
echo ""
echo "  Three pre-built domains:"
echo "    - drug-discovery    (S6 showcase)"
echo "    - contracts         (schema scaffold)"
echo "    - clinicaltrials    (S7 showcase)"
echo ""
echo "  Docs:"
echo "    - docs/SHOWCASE-GLP1.md"
echo "    - docs/SHOWCASE-CLINICALTRIALS.md"
echo "    - docs/ADDING-DOMAINS.md (build your own)"
echo ""
echo "  The framework in one line:"
echo "    Communities tell you where in the graph to look."
echo "    Super Domains tell you what kind of knowledge you're looking at."
echo "    Analyst personas tell you what to do with it."
echo ""
echo "  QnA now. Thanks for watching."
echo ""
