# Demo Narration + Commands — v3.1 KGC 2026

**Read from phone while recording.** Open Ghostty, `cd ~/code/epistract`, clear. Screen-record terminal + browser.

Target: ~12 minutes, ~1,700 words at 140 wpm.

---

## Act 1 — Framework thesis (75s)

*Show title card, then fade to clean terminal.*

**Say:**

> "Most knowledge graph tools stop at 'extract entities and relations.' Epistract keeps going. Every relation in the graph is tagged with its epistemic status — asserted with evidence, prophetic from patent forward-looking language, hypothesized in hedged research wording, contested across conflicting sources, or contradictory outright.
>
> And because every domain needs a different expert reading those classifications, each domain ships with an analyst persona that plays two roles at once: it's the system prompt for the workbench chat when you ask questions, and it's the prompt for an automatic briefing the pipeline writes after every run.
>
> Three pre-built domains today — drug-discovery, contracts, and clinicaltrials — plus a wizard to build your own. Here's what that looks like running."

---

## Act 2 — S6 drug-discovery graph (90s)

**Type:** `ls tests/corpora/06_glp1_landscape/docs/ | head -8`

**Say:** "Our first corpus: thirty-four documents on GLP-1 receptor agonists — the drug class behind semaglutide and tirzepatide. Ten patent filings from Novo Nordisk, Pfizer, Eli Lilly. Twenty-four PubMed papers on mechanism, safety, emerging indications."

**Type (don't run):** `/epistract:ingest tests/corpora/06_glp1_landscape/docs --output tests/corpora/06_glp1_landscape/output-v3 --domain drug-discovery`

**Say:** "One slash command does the whole thing — read, chunk, extract, validate, build, render. Each document goes through a drug-discovery schema with thirteen entity types and twenty-two relation types. Molecular validators check every SMILES string with RDKit. Write-time Pydantic validation means no extraction silently drops. Two hundred seventy-eight entities, eight hundred fifty-five relations out of thirty-four documents."

**Type:** `cat tests/corpora/06_glp1_landscape/output-v3/claims_layer.json | jq '.summary.epistemic_status_counts'`

**Shows:** `{"asserted": 758, "prophetic": 61, "hypothesized": 31, "contested": 33, "contradictions": 2, "speculative": 2, "negative": 1}`

**Say:** "And the epistemic layer has split those eight hundred fifty-five relations into seven status buckets. Sixty-one prophetic claims — patent forward-looking language. Thirty-three contested claims. Two outright contradictions. That's the base layer."

---

## Act 3 — Workbench chat (120s)

**Type:** `python scripts/launch_workbench.py tests/corpora/06_glp1_landscape/output-v3 --domain drug-discovery`

**Switch to browser** (http://127.0.0.1:8000, pre-loaded, settled).

**Say:** "This is the workbench. Three panels — dashboard summary, interactive graph, chat. Title auto-detected from graph metadata. No `--domain` flag on this command."

**Click Graph panel.** *Pan the graph.*

**Say:** "Two hundred seventy-eight nodes colored by entity type. Ten Louvain communities. Compounds in indigo, diseases in red, clinical trials in cyan."

**Click Chat panel.** *Scroll starter questions into view.*

**Say:** "But the chat panel is where the design shows up. System prompt is a senior drug-discovery CI analyst. It commits to citation discipline — every claim references source documents. And it commits to the epistemic-status vocabulary. Let me ask it the research question."

**Type into chat:** `Which patents make prophetic claims about new indications, and where are the biggest gaps between prophetic breadth and asserted evidence?`

*Wait for stream. Let the table render.*

**Say:** "This is not retrieval. It's synthesis. The chat is reasoning about which prophetic claims are clinically plausible, which look like patent boilerplate, which trial data would resolve the gap. Every claim cites source documents by ID."

---

## Act 4 — Automatic narrator briefing (90s)

**Back to terminal.**

**Type:** `bat tests/corpora/06_glp1_landscape/output-v3/epistemic_narrative.md | head -80`

**Say:** "The workbench chat answered reactively — I asked, it answered. But `/epistract:epistemic` does the same reasoning proactively. After the rule engine writes the claims layer, the pipeline calls the same analyst persona with the full classified graph and asks for a structured briefing. File committed alongside the graph."

**Read verbatim from the narrative (scroll to show each excerpt as you read):**

> "Sixty-one prophetic claims inflate the apparent indication breadth of these compounds. Cardiovascular risk reduction, neurodegeneration, and metabolic sub-disorders are largely patent-forward-looking, not empirically established."

> "semaglutide INDICATED_FOR obesity — confidence range 0.55 to 0.97 across sources. The 0.55 instance likely reflects pre-STEP-trial patent language; the 0.97 instance reflects post-approval asserted status. These should be temporally stratified, not treated as equivalent evidence."

> "Integrate SURPASS-2 trial data — add a clinical_trial:surpass_2 node with direct tirzepatide-vs-semaglutide efficacy relations. Source: NEJM 2021, Frías et al."

**Say:** "This isn't a post-hoc summary. This is an analyst reading the graph and telling you what it's missing. And the persona that wrote it is the same string that powered the chat. Upgrade the persona once, both surfaces improve."

---

## Act 5 — The second lens: clinicaltrials (75s)

**Type:** `ls domains/`

*Shows drug-discovery, contracts, clinicaltrials.*

**Say:** "Three pre-built domains. Clinicaltrials is new in version three-point-one. It reads ClinicalTrials.gov protocols, IRB submissions, clinical study reports. Twelve entity types — Trial, Intervention, Cohort, TrialPhase, Outcome. Ten relation types. Phase-based evidence-tier grading built in."

**Type:** `ls tests/corpora/07_glp1_phase3_trials/docs/`

**Say:** "Scenario 7. Same molecular space. But instead of patents and papers, here's the authoritative source — ten Phase 3 trial protocols from ClinicalTrials.gov. SURPASS-2, SURMOUNT-1, all three STEP trials, both PIONEER cardiovascular studies, SUSTAIN-6, ACHIEVE-1. The exact trials the drug-discovery narrator just told us were missing."

**Type (don't run):** `python scripts/fetch_ct_protocols.py tests/corpora/07_glp1_phase3_trials`

**Say:** "One script call — CT.gov v2 API, stdlib urllib, ten protocols fetched. Then the standard pipeline with `--domain clinicaltrials`."

**Type:** `cat tests/corpora/07_glp1_phase3_trials/output/graph_data.json | jq '.metadata | {nodes: .entity_count, edges: .relation_count}'`

**Shows:** `{"nodes": 142, "edges": 395}`

**Say:** "One hundred forty-two entities, three hundred ninety-five relations. Different domain, same pipeline."

---

## Act 6 — Enrichment + phase-tier grading (90s)

**Type:** `python domains/clinicaltrials/enrich.py tests/corpora/07_glp1_phase3_trials/output`

*Real execution — takes ~5 seconds.*

**Shows report:** 10/10 trials, 2/2 compounds, 100% hit rate.

**Say:** "The clinicaltrials domain ships with an enrichment layer. One command hits ClinicalTrials.gov v2 for every trial node — phase, enrollment, dates, status — and PubChem PUG REST for every compound — canonical SMILES, formula, InChI. Hundred percent hit rate. Non-blocking: network failures log counts but never abort."

**Type:** `python -m core.label_epistemic tests/corpora/07_glp1_phase3_trials/output --domain clinicaltrials 2>&1 | tail -6`

**Say:** "And now the phase-tier grader has data. A hundred seventy-seven relations marked high_evidence — Phase 3, randomized, enrollment over three hundred. Twenty medium. The remaining unclassified aren't failures — they're relations not connected to a trial node, which the grader correctly skips."

**Type:** `bat tests/corpora/07_glp1_phase3_trials/output/epistemic_narrative.md | head -25`

**Say:** "New briefing, same pattern. This narrator is tuned differently — it reasons about arm-level enrollment, endpoint multiplicity, phase-tier coverage. Different persona, same framework."

---

## Act 7 — Cross-domain side-by-side (90s)

**Have both workbenches already launched.**
```bash
# Prep before recording:
python scripts/launch_workbench.py tests/corpora/06_glp1_landscape/output-v3 --domain drug-discovery --port 8000 &
python scripts/launch_workbench.py tests/corpora/07_glp1_phase3_trials/output --domain clinicaltrials --port 8001 &
```

**Switch to split screen.** Left = :8000 (drug-discovery). Right = :8001 (clinicaltrials).

**Say:** "The competitive-intelligence move. Same question in both. Same molecular space. Different source material, different domain persona, different knowledge graph."

**Type into BOTH chats simultaneously:** `What's the evidence for tirzepatide in obesity?`

*Let both stream in parallel.*

**Say:** "Left side — drug-discovery persona reading the literature graph. It talks about patent claims, hedged research wording, what the trials should show. Right side — clinicaltrials persona reading the protocol graph. NCT numbers, enrollment counts, primary endpoints, phase-tier evidence grades."

**Say:** "Neither alone is a CI brief. Together they are. Same pipeline. Same epistemic machinery. Same persona-dual-use pattern. Two domains, one integrated understanding."

---

## Act 8 — Framework mechanics (60s)

**Back to terminal.**

**Type:** `tree domains/clinicaltrials/ -L 2`

*Shows:* `domain.yaml`, `SKILL.md`, `epistemic.py`, `enrich.py`, `workbench/template.yaml`.

**Say:** "A whole domain is five files. Schema in YAML. Extraction prompt in Markdown. Epistemic rules and optional enrichment in Python. Workbench config in YAML. No core-code changes. That's the whole contract."

**Type (don't execute):** `/epistract:domain --input ./my-sample-docs/ --name my-domain`

**Say:** "And if you don't want to hand-write any of it, the domain wizard runs multi-pass LLM analysis on three to five sample documents, proposes a schema, and generates all five files."

---

## Act 9 — Closing (40s)

**Switch to:** https://github.com/usathyan/epistract/releases

**Say:** "Epistract runs as a Claude Code plugin. Version three-point-one shipped April twenty-third. Open source, MIT license.
>
> The thesis again: communities tell you where in the graph to look. Super Domains tell you what kind of knowledge you're looking at. An analyst persona tells you what to do with it. That's the framework.
>
> Happy to answer questions. Thanks for watching."

**Cut to title card.**

---

## Phonetic pronunciations for TTS voiceover

| Term | Phonetic |
|---|---|
| epistract | "eh-pi-stract" (short i, stress on "stract") |
| epistemic | "epi-STEM-ick" |
| semaglutide | "sem-ah-GLUE-tide" |
| tirzepatide | "teer-ZEH-pa-tide" |
| orforglipron | "or-for-GLI-pron" |
| retatrutide | "reh-ta-TROO-tide" |
| danuglipron | "dan-you-GLI-pron" |
| GLP-1 | "G-L-P one" (three letters, then "one") |
| NCT04184622 | "N-C-T zero-four, one-eight-four, six-two-two" |
| PIONEER | "PIE-oh-neer" |
| SURPASS | "SUR-pass" |
| SURMOUNT | "SUR-mount" |
| SUSTAIN | "sus-TAIN" |
| ACHIEVE | "uh-CHEEV" |
| clinicaltrials | "clinical trials" (space between the two words for the voice) |
| Pydantic | "pie-DAN-tick" |
| Louvain | "loo-VAN" |
| PubMed | "pub-med" |
| ClinicalTrials.gov v2 | "Clinical Trials dot gov version two" |
| Claude | "clawed" |
