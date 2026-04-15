# Demo Narration + Commands — Run Inside Claude Code

Open a **fresh Ghostty window**, run `claude`, then follow each act.
Read narration from phone. Screen record the Ghostty window only.

---

## Act 1: What is Epistract (45s)

**Type:** `/epistract-` (let autocomplete show, press Escape)

**Say:** "Epistract is a Claude Code plugin for building drug discovery knowledge graphs. Claude Code is Anthropic's agentic coding tool. Epistract adds slash commands that orchestrate the pipeline — from raw documents to a queryable knowledge graph. Under the hood, Claude reads each document, understands the biochemistry, and extracts entities and relations into a 23-type entity schema."

---

## Act 2: The Corpus (30s)

**Type:** `! ls tests/corpora/06_glp1_landscape/output/extractions/`

**Say:** "Here's a competitive intelligence corpus. 10 patent filings from Novo Nordisk, Pfizer, Eli Lilly, Hanmi, and Zealand — plus 24 PubMed papers about GLP-1 receptor agonists. The drug class behind semaglutide and tirzepatide."

---

## Act 3: Graph Info (30s)

**Type:** `! python3 scripts/run_sift.py info tests/corpora/06_glp1_landscape/output`

**Say:** "206 entities, 630 relations extracted from 34 documents. Compounds, proteins, diseases, clinical trials, mechanisms of action — all calibrated by document type."

---

## Act 4: Interactive Graph (90s)

**Type:** `/epistract-view tests/corpora/06_glp1_landscape/output`

**Switch to browser.** Explore the graph — zoom out, click nodes, show communities.

**Say:** "Communities group entities by topological density. This tells you where in the graph to look. But it doesn't tell you what kind of knowledge you're looking at. A patent claim and a Phase 3 trial result sit side by side, indistinguishable."

**Switch back to terminal.**

---

## Act 5: Epistemic Analysis (120s)

**Type:** `/epistract-epistemic tests/corpora/06_glp1_landscape/output`

**Wait for output.** Pause on it.

**Say:** "604 of 630 relations are brute facts — base domain. 26 are epistemic. 15 prophetic patent claims. 7 hypothesized. 3 contested. And 4 named hypotheses emerged — graph-level inference patterns."

**Then type:** `! python3 -c "
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
"`

**Say:** "Patents produce prophetic claims. Papers produce hedged hypotheses. Distinct epistemic categories. In the original graph, indistinguishable."

---

## Act 6: Negative Control (30s)

**Type:** `! python3 scripts/label_epistemic.py tests/corpora/02_kras_g12c_landscape/output`

**Say:** "KRAS G12C — established oncology. 307 relations. Zero epistemic content. The classifier finds signal, not noise."

---

## Act 7: S1 Contradiction (60s)

**Type:** `! python3 scripts/label_epistemic.py tests/corpora/01_picalm_alzheimers/output`

**Say:** "PICALM and Alzheimer's. 1 contradiction — two meta-analyses reporting opposite allele effects, merged to confidence 0.975. Structurally invisible until now."

**Type:** `! open docs/analysis/screenshots/graph-01-hypothesis-highlighted.png`

**Pause 3 seconds.**

**Say:** "The hypothesis crosses two Louvain communities."

**Type:** `! open docs/analysis/screenshots/graph-01-contested-highlighted.png`

**Say:** "Seven contested relations — asserted in some papers, hedged in others."

---

## Act 8: Close (30s)

**Type:** `! echo "https://github.com/usathyan/epistract"`

**Say:** "Communities tell you where to look. Super Domains tell you what kind of knowledge you're looking at. Complementary, not competing."

---

## Before Recording Checklist

- [ ] Fresh Ghostty window → `cd ~/code/epistract` → `claude`
- [ ] Browser: S6 graph tab open (sidebar hidden)
- [ ] Browser: S1 graph tab open (sidebar hidden)
- [ ] DND on
- [ ] This narration on phone
- [ ] Start screen recording (Cmd+Shift+5)
