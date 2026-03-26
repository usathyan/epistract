# Epistract Demo Script — Knowledge Graph Conference

**Duration:** 5-7 minutes
**Scenario:** S6 — GLP-1 Competitive Intelligence (patents + papers)
**Format:** Terminal recording (asciinema) + browser screenshots (Playwright) combined into video

---

## Demo Flow

### Act 1: What is Epistract? (45 seconds)

**Show:** Title card or clean terminal with epistract banner/README header.

**Talking points:**
- "Epistract is a Claude Code plugin for building drug discovery knowledge graphs from scientific literature."
- "Claude Code is Anthropic's agentic coding tool — it runs in the terminal, reads files, writes code, and executes commands. Plugins extend it with domain-specific capabilities."
- "Epistract adds slash commands — `/epistract-ingest`, `/epistract-build`, `/epistract-view`, `/epistract-epistemic` — that orchestrate the full pipeline from raw documents to a queryable knowledge graph."
- "Under the hood, Claude reads each document, understands the biochemistry, and extracts entities and relations into a structured schema — 23 entity types, 46 relation types, calibrated by evidence strength and document type."

**Terminal shows:**
```
$ claude
> /epistract-
```
*Show the autocomplete listing available commands.*

### Act 2: The Corpus (30 seconds)

**Terminal shows:**
```
$ ls tests/corpora/06_glp1_landscape/corpus/
patent_01_novo_nordisk_semaglutide.txt
patent_05_pfizer_oral_glp1.txt
patent_06_hanmi_triple_agonist.txt
...
pmid_35441470.txt
pmid_37192005.txt
pmid_38858523.txt
...
```

**Talking point:** "Here's a competitive intelligence corpus — 10 patent filings from Novo Nordisk, Pfizer, Eli Lilly, Hanmi, and Zealand, plus 15 PubMed papers about GLP-1 receptor agonists. The drug class behind semaglutide and tirzepatide."

### Act 3: Ingest Pipeline (60 seconds)

**Show the command:**
```
/epistract-ingest tests/corpora/06_glp1_landscape/corpus --output tests/corpora/06_glp1_landscape/output
```

**NOTE:** For the demo, we'll show the command being invoked but cut to pre-built output (ingestion takes ~10-15 min). Use a transition like "The pipeline processes each document in parallel..."

**Talking points during transition:**
- "When I run `/epistract-ingest`, Claude Code orchestrates the full pipeline."
- "It reads each document, chunks the text, and dispatches parallel extraction agents — one per document. Each agent uses a drug discovery domain schema with 23 entity types and 46 relation types."
- "Claude understands biochemistry deeply — HGVS variant notation, signaling cascades, patent claim structure. It extracts entities and relations with confidence scores calibrated by document type — a patent prophetic example gets lower confidence than a Phase 3 trial endpoint."
- "After extraction, the pipeline validates molecular identifiers with RDKit, builds the graph with sift-kg, and detects communities with Louvain clustering."

**Terminal output after build:**
```
$ python3 scripts/run_sift.py info tests/corpora/06_glp1_landscape/output
{
  "entity_count": 206,
  "relation_count": 630,
  "entity_type_summary": {"COMPOUND": 45, "PROTEIN": 28, "DISEASE": 22, ...}
}
```

**Talking point:** "206 entities, 630 relations extracted from 25 documents — patents and papers together in one graph."

### Act 4: Interactive Graph Visualization (90 seconds)

**Open the graph in browser:**
```
/epistract-view tests/corpora/06_glp1_landscape/output
```

**Browser shows:** Full-screen interactive graph with colored communities.

**Walk through the graph:**
1. Show the overall topology — clusters of related entities
2. Click on semaglutide node — show its connections (GLP1R, obesity, diabetes, cardiovascular)
3. Click on a patent-sourced relation — show the evidence quote
4. Show the community labels (GLP-1/GIP/Glucagon Triple Agonism, Metabolic Dysfunction-Associated Steatohepatitis, etc.)

**Talking point:** "Communities group entities by topological density — which nodes are heavily interconnected. This tells you *where* in the graph to look. But it doesn't tell you *what kind of knowledge* you're looking at. A patent claim and a Phase 3 trial result sit side by side, indistinguishable."

### Act 5: Epistemic Analysis — The Super Domain Layer (120 seconds)

**This is the main event.**

**Run the command:**
```
/epistract-epistemic tests/corpora/06_glp1_landscape/output
```

**Terminal output:**
```json
{
  "total_relations": 630,
  "base_domain_relations": 604,
  "super_domain_relations": 26,
  "status_breakdown": {
    "asserted": 604,
    "prophetic": 15,
    "contested": 3,
    "hypothesized": 7
  },
  "contradictions": 0,
  "hypotheses": 4,
  "document_types": ["patent", "paper"]
}
```

**Talking point:** "604 of 630 relations are brute facts — base domain. 26 are epistemic — hypothesized, prophetic, or contested. The epistemic layer separates them."

**Show the patent vs. paper split:**
```
patent: {asserted: 233, prophetic: 17}
paper:  {asserted: 463, hypothesized: 8}
```

**Talking point:** "Patents produce prophetic claims — 'is expected to', 'may be prepared by'. Papers produce hedged hypotheses — 'suggests', 'may offer'. These are distinct epistemic categories. In the original graph, they're indistinguishable."

**Show the hypotheses found:**
```
Hypothesis 1: GLP-1 RAs — chronic pain — diabetic neuropathy — osteoarthritis
  Evidence: "may offer novel analgesia"

Hypothesis 2: Novel small-molecule GLP-1R activation via allosteric mechanisms
  Evidence: "stabilizing an active receptor conformation"
```

**Talking point:** "The epistemic layer groups connected hedged relations into named hypotheses. These are graph-level inference patterns — exactly what Eric Little describes as requiring Super Domain treatment."

### Act 6: Comparison — S2 as Negative Control (30 seconds)

**Quick cut to S2:**
```
$ python3 scripts/label_epistemic.py tests/corpora/02_kras_g12c_landscape/output
{
  "total_relations": 307,
  "base_domain_relations": 307,
  "super_domain_relations": 0,
  "status_breakdown": {"asserted": 307}
}
```

**Talking point:** "KRAS G12C — established oncology. 307 relations, zero epistemic content. The classifier finds signal, not noise. Epistemic density correlates with research maturity and document type."

### Act 7: S1 Annotated Graphs (60 seconds)

**Show the pre-built annotated screenshots:**
- Hypothesis crossing community boundaries (red highlighted)
- Contradiction + contested relations (red + amber highlighted)

**Talking point:** "In Scenario 1 — PICALM and Alzheimer's — the epistemic analysis found a multi-relation hypothesis spanning two Louvain communities. It also found a genuine scientific contradiction: two meta-analyses reporting opposite allele effects for rs541458, merged into one relation at confidence 0.975. The contradiction was structurally invisible. The Super Domain layer makes it explicit."

### Act 8: Closing (30 seconds)

**Terminal shows:**
```
$ ls docs/analysis/
super-domain-epistemic-analysis.md
super-domain-addendum.md
screenshots/
```

**Talking point:** "Communities tell you where to look. Super Domains tell you what kind of knowledge you're looking at. They're complementary, not competing. Full analysis and code on GitHub."

**Show GitHub URL.**

---

## Recording Setup

**Method:** Full screen recording (QuickTime: File → New Screen Recording)
**Resolution:** 1920x1080 or Retina equivalent
**Layout:** Terminal (Claude Code) filling the screen. Browser opens when needed.

### Before You Hit Record

- [ ] Close all apps except Terminal and browser
- [ ] Terminal: increase font size (Cmd+= a few times), dark theme
- [ ] Terminal: `cd ~/code/epistract && clear`
- [ ] Browser: pre-open `tests/corpora/06_glp1_landscape/output/graph.html` in a tab (let physics settle)
- [ ] Browser: pre-open `tests/corpora/01_picalm_alzheimers/output/graph.html` in another tab
- [ ] Hide bookmark bar in browser (Cmd+Shift+B)
- [ ] Do Not Disturb ON (notifications off)
- [ ] Test mic if doing voiceover live (or add voiceover in post)

---

## Command-by-Command Runbook

Copy-paste these in order. Pause between commands for narration.

### Act 1: What is Epistract (45s)

```
# Start Claude Code
claude
```

*Wait for prompt, then type:*
```
/epistract-
```
*Let autocomplete show the available commands. Press Escape — don't run anything yet.*

**Say:** "Epistract is a Claude Code plugin for building drug discovery knowledge graphs from scientific literature. Claude Code is Anthropic's agentic coding tool — it runs in the terminal, reads documents, and understands biochemistry. Epistract adds these slash commands that orchestrate the full pipeline from raw papers and patents to a queryable knowledge graph."

### Act 2: The Corpus (30s)

```
! ls tests/corpora/06_glp1_landscape/output/extractions/
```

**Say:** "Here's a competitive intelligence corpus — 10 patent filings from Novo Nordisk, Pfizer, Eli Lilly, Hanmi, and Zealand, plus 24 PubMed papers about GLP-1 receptor agonists — the drug class behind semaglutide and tirzepatide."

### Act 3: Graph Info (30s)

```
! python3 scripts/run_sift.py info tests/corpora/06_glp1_landscape/output
```

**Say:** "The pipeline already ran — 206 entities, 630 relations extracted from 34 documents. 34 compounds, 31 diseases, 19 clinical trials, 11 proteins. Claude handles patent claim language, IUPAC names, hedging — all calibrated by document type."

### Act 4: Interactive Graph (90s)

```
/epistract-view tests/corpora/06_glp1_landscape/output
```

*Switch to browser. The graph should be pre-loaded and settled.*

**Walk through:**
1. **Zoom out** — show the full graph with community clusters
2. **Click on semaglutide** — show its connections radiating out (GLP1R, obesity, diabetes, CV)
3. **Click on a patent-sourced edge** — show the evidence quote in the detail panel
4. **Point out community labels** — "GLP-1/GIP/Glucagon Triple Agonism", "Metabolic Dysfunction-Associated Steatohepatitis", "Danuglipron / Alzheimer Disease / Parkinson Disease"

**Say:** "Communities group entities by topological density — which nodes are heavily interconnected. This tells you where in the graph to look. But it doesn't tell you what kind of knowledge you're looking at. A patent claim and a Phase 3 trial result sit side by side, indistinguishable."

*Switch back to terminal.*

### Act 5: Epistemic Analysis — Main Event (120s)

```
/epistract-epistemic tests/corpora/06_glp1_landscape/output
```

*Wait for output.*

**Say:** "604 of 630 relations are brute facts — base domain. 26 are epistemic. 15 are prophetic patent claims — forward-looking language like 'is expected to' and 'may be prepared by'. 7 are hypothesized — hedged paper findings. 3 are contested — where patents and papers disagree on certainty. And 4 named hypotheses emerged — connected clusters of hedged relations."

**Then show the claims layer detail:**
```
! python3 -c "
import json
c = json.load(open('tests/corpora/06_glp1_landscape/output/claims_layer.json'))
print('Document type signatures:')
for dt, counts in c['summary']['document_types'].items():
    print(f'  {dt}: {counts}')
print()
print('Hypotheses found:')
for h in c['super_domain']['hypotheses']:
    print(f'  {h[\"label\"][:60]}')
    print(f'    {h[\"relation_count\"]} relations, {h[\"entity_count\"]} entities')
"
```

**Say:** "Patents produce prophetic claims. Papers produce hedged hypotheses. These are distinct epistemic categories — in the original graph they're indistinguishable. The epistemic layer groups connected hedged relations into named hypotheses — graph-level inference patterns."

### Act 6: Negative Control (30s)

```
! python3 scripts/label_epistemic.py tests/corpora/02_kras_g12c_landscape/output
```

**Say:** "KRAS G12C — established oncology. 307 relations, zero epistemic content. Every relation is a brute fact. The classifier finds signal, not noise. Epistemic density correlates with research maturity."

### Act 7: S1 Contradiction (60s)

*Switch to browser — show the pre-opened S1 graph tab.*

**Say:** "Scenario 1 — PICALM and Alzheimer's disease."

*Switch back to terminal:*
```
! python3 scripts/label_epistemic.py tests/corpora/01_picalm_alzheimers/output
```

**Say:** "16 epistemic relations, 1 contradiction, 1 hypothesis, 7 contested. The contradiction is real — two meta-analyses reporting opposite allele effects for the same variant, rs541458. One finds it protective, the other finds no association. The graph merged them into one relation at confidence 0.975. The contradiction was structurally invisible. The Super Domain layer makes it explicit."

*Show the annotated screenshots (open in browser or Preview):*
```
! open docs/analysis/screenshots/graph-01-hypothesis-highlighted.png
```
```
! open docs/analysis/screenshots/graph-01-contested-highlighted.png
```

**Say:** "Red — the hypothesis crossing two Louvain communities. Amber — seven contested relations where genes are asserted in some papers but hedged in others. Communities tell you where to look. Super Domains tell you what kind of knowledge you're looking at. Complementary, not competing."

### Act 8: Close (30s)

**Say:** "Epistract is open source. The epistemic analysis runs on any built graph with zero external dependencies. Full analysis, POC code, and annotated graph screenshots are on GitHub."

*Show GitHub URL in terminal:*
```
! echo "https://github.com/usathyan/epistract"
```

---

## Post-Recording

- [ ] Trim dead air / long pauses
- [ ] Add title card at start: "Epistract — Epistemic Super Domains in Drug Discovery Knowledge Graphs"
- [ ] Add GitHub URL card at end
- [ ] Optional: add voiceover if not recorded live
- [ ] Export as MP4, 1080p
- [ ] Tools: iMovie (simple), ffmpeg (CLI), or DaVinci Resolve (free, pro-grade)
