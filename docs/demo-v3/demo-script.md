# Epistract v3.1 — Knowledge Graph Conference 2026 Demo Script

**Conference:** Knowledge Graph Conference 2026 — Tools & Demonstrations Track
**Track date:** 2026-05-08, 10 AM – Noon ET (virtual)
**Video slot:** 10–15 minutes + 10–15 min live QnA
**Host:** Umesh Bhatt (umesh@8thcross.com)
**Epistract version:** v3.1.0 (shipped 2026-04-23)
**Prior video:** [v2.0 demo, 2026-03-27, YouTube](https://youtu.be/7mHbdb0nn3Y) — superseded by this one

---

## What changed since the v2.0 video

| Aspect | v2.0 video (Mar 2026) | v3.1 video (this one) |
|---|---|---|
| Domains | drug-discovery only | drug-discovery + contracts + clinicaltrials |
| Epistemic layer | Rule-based classification only | Rules + automatic LLM analyst narrator |
| Workbench persona | Generic "knowledge graph analyst" | Domain-specific senior-analyst persona, dual-use for chat + narrator |
| External enrichment | None | CT.gov v2 + PubChem PUG REST via `--enrich` |
| Showcases | S1 PICALM + S6 GLP-1 literature | S6 GLP-1 literature + S7 GLP-1 Phase 3 trials (paired) |
| Scenarios | 6 | 7 |
| Narrator output | none | auto-generated `epistemic_narrative.md` per run |
| Fidelity story | "we extract entities" | "we tell you what the graph doesn't know" |

---

## Story arc

**Three beats:**

1. **Framework thesis.** *Most KG tools stop at "extract entities and relations." Epistract keeps going: every relation is tagged with its epistemic status — asserted, prophetic, hypothesized, contested. A per-domain analyst persona reads the classified graph and writes a structured briefing. Three pre-built domains demonstrate the framework.*

2. **One molecular space, two lenses.** Same GLP-1 receptor agonist landscape (semaglutide, tirzepatide, orforglipron, retatrutide) seen through **literature** (S6: patents + PubMed, drug-discovery domain) and through **trial protocols** (S7: ClinicalTrials.gov, clinicaltrials domain). Each produces a different knowledge graph. The narrator synthesizes each one differently — and the two together constitute a competitive-intelligence briefing that neither alone can produce.

3. **The epistemic layer is the differentiator.** Show the narrator output cold. Let it speak. Quote it.

---

## Target duration: ~12 minutes

Fits comfortably in the 10–15 min window; leaves headroom for inevitable slippage. Narration is ~1700 words at 140 wpm.

| # | Act | Duration | Main surface |
|---|---|---:|---|
| 1 | Framework intro + epistemic thesis | 75s | Slide / README |
| 2 | S6 — build a drug-discovery graph | 90s | Terminal (pre-built output) |
| 3 | S6 workbench — domain-aware chat, prophetic claims | 120s | Browser :8000 |
| 4 | S6 narrator — auto-generated briefing | 90s | VS Code / terminal |
| 5 | S7 — clinicaltrials domain, the second lens | 75s | Terminal |
| 6 | S7 narrator + enrichment — phase-tier grading | 90s | Terminal + VS Code |
| 7 | Cross-domain comparison — same question, two lenses | 90s | Side-by-side browsers :8000 + :8001 |
| 8 | Framework mechanics — 3 files per domain | 60s | `domains/` tree + `ADDING-DOMAINS.md` |
| 9 | Closing — tags, releases, QnA prompt | 40s | GitHub releases page |

---

## Act 1 — Framework intro + epistemic thesis (75s)

**Show:** Clean title card with the one-liner tagline, then fade to README header.

**Title card:**
```
EPISTRACT
Turn any document corpus into a knowledge graph
that knows what it doesn't know.
v3.1.0 — github.com/usathyan/epistract
```

**Narration:**

> "Most knowledge graph tools stop at 'extract entities and relations.' Epistract keeps going. Every relation in the graph is tagged with its epistemic status — asserted with evidence, prophetic from patent forward-looking language, hypothesized in hedged research wording, contested across conflicting sources, or contradictory outright.
>
> And because every domain needs a different expert reading those classifications, each domain ships with an analyst persona that plays two roles at once: it's the system prompt for the workbench chat when you ask questions, and it's the prompt for an automatic briefing the pipeline writes after every run.
>
> Three pre-built domains today — drug discovery literature, event contracts, and clinical trial protocols — plus a wizard to build your own from sample documents. The framework is domain-agnostic; each domain is a config package of about five files.
>
> Here's what that looks like running."

---

## Act 2 — S6 drug-discovery graph (90s)

**Surface:** Terminal (pre-built output, we're not waiting for extraction).

**Commands to type (real, on-camera):**

```bash
cd ~/code/epistract
ls tests/corpora/06_glp1_landscape/docs/ | head -8
```

> "Our first corpus: thirty-four documents on GLP-1 receptor agonists — the drug class behind semaglutide and tirzepatide. Ten patent filings from Novo Nordisk, Pfizer, Eli Lilly. Twenty-four PubMed papers on mechanism, safety, and emerging indications."

```bash
ls tests/corpora/06_glp1_landscape/output-v3/ingested/ | wc -l
ls tests/corpora/06_glp1_landscape/output-v3/extractions/ | head -5
```

> "The pipeline already ran. I'll show you the command anyway."

```
/epistract:ingest tests/corpora/06_glp1_landscape/docs --output tests/corpora/06_glp1_landscape/output-v3 --domain drug-discovery
```

*Don't execute — cut to pre-built output.*

> "One slash command does the whole thing — read, chunk, extract, validate, build the graph, render the viewer. Each document goes through a drug-discovery domain schema with thirteen entity types and twenty-two relation types. Molecular validators check every SMILES string with RDKit, every peptide sequence with Biopython. Write-time Pydantic validation means no extraction silently drops. Two hundred seventy-eight entities, eight hundred fifty-five relations out of thirty-four documents."

**Cut to:** `cat tests/corpora/06_glp1_landscape/output-v3/claims_layer.json | jq '.summary.epistemic_status_counts'` OR screenshot from SHOWCASE-GLP1.md.

**Shows:**
```
{"asserted": 758, "prophetic": 61, "hypothesized": 31, "contested": 33, "contradictions": 2, "speculative": 2, "negative": 1}
```

> "And the epistemic layer has split those eight hundred fifty-five relations into seven status buckets. Sixty-one prophetic claims — patent forward-looking language. Thirty-three contested claims — same relation, different sources, different confidence. Two outright contradictions. That's the base layer. Now for the interesting part."

---

## Act 3 — Workbench chat, the domain-aware analyst (120s)

**Surface:** Browser at `http://127.0.0.1:8000` — launch workbench on S6 pre-built output.

```bash
python scripts/launch_workbench.py tests/corpora/06_glp1_landscape/output-v3 --domain drug-discovery
```

*Switch to browser. Show the loaded workbench — Dashboard / Chat / Graph panels.*

> "This is the workbench. Three panels: an auto-generated dashboard summary, an interactive force-directed graph, and a chat panel grounded in the graph data. Look at the title — it says 'Drug Discovery Knowledge Graph Explorer,' auto-detected because the graph's metadata carries the domain name. No `--domain` flag on this command."

**Click Graph panel:** *Show the 278 nodes colored by entity type, 10 communities visible.*

> "Here's the graph. Entity-type filter pills at the top — compounds in indigo, diseases in red, clinical trials in cyan. The Louvain community structure shows how entities cluster topologically."

**Click Chat panel.** *Show the welcome screen with starter questions.*

> "But the chat panel is where the framework's design really shows up. The system prompt is a senior drug-discovery competitive-intelligence analyst. It commits to citation discipline — every claim must reference source documents. It commits to the epistemic-status vocabulary. Let me ask it the question the research analyst would ask."

**Type into chat:**
```
Which patents make prophetic claims about new indications, and where are the biggest gaps between prophetic breadth and asserted evidence?
```

*Wait for response to stream. It will cite NCT IDs and patent numbers in backticks, structure the answer in a table grouped by patent family, identify specific contested indications, and recommend trials to ingest.*

> "This is not retrieval. It's synthesis. The chat is reasoning about which prophetic claims are clinically plausible, which look like patent boilerplate, and which concrete trial data would resolve the gap. Every claim cites source documents by ID."

---

## Act 4 — Automatic narrator, the proactive briefing (90s)

**Surface:** Cut back to terminal, open `epistemic_narrative.md` in VS Code or `bat`.

```bash
bat tests/corpora/06_glp1_landscape/output-v3/epistemic_narrative.md | head -80
```

> "The workbench chat answered a question reactively — I asked, it responded. But `/epistract:epistemic` does the same reasoning proactively. After the rule engine writes the claims layer, the pipeline calls the same analyst persona with the full classified graph and asks for a structured briefing. That file is committed alongside the graph."

**Walk the narrative on-screen.** Read these excerpts verbatim (the narrator actually wrote these — they're not made up):

> *Executive summary excerpt:* "Sixty-one prophetic claims inflate the apparent indication breadth of these compounds. Cardiovascular risk reduction, neurodegeneration, and metabolic sub-disorders are largely patent-forward-looking, not empirically established."

> *Contested claims excerpt:* "semaglutide INDICATED_FOR obesity — confidence range 0.55 to 0.97 across sources. The 0.55 instance likely reflects pre-STEP-trial patent language; the 0.97 instance reflects post-approval asserted status. These should be temporally stratified, not treated as equivalent evidence."

> *Recommended follow-up excerpt:* "Integrate SURPASS-2 trial data — add a clinical_trial:surpass_2 node with direct tirzepatide-vs-semaglutide efficacy relations to close the head-to-head gap. Source: NEJM 2021, Frías et al."

> "This isn't a post-hoc summary. This is an analyst reading the graph and telling you what it's missing. And the persona that wrote it is the same string that powered the chat you just saw. Upgrade the persona once, both surfaces improve. Single source of truth for the domain's expert voice."

---

## Act 5 — The second lens: clinicaltrials domain (75s)

**Surface:** Terminal.

```bash
ls domains/
```

*Show three dirs: `drug-discovery/`, `contracts/`, `clinicaltrials/`.*

> "Three pre-built domains. Drug-discovery is the one we just used. Clinicaltrials is new in version three-point-one — it reads ClinicalTrials.gov protocols, IRB submissions, and clinical study reports. Twelve entity types including Trial, Intervention, Cohort, TrialPhase, Outcome. Ten relation types. Phase-based evidence-tier grading built in."

```bash
ls tests/corpora/07_glp1_phase3_trials/docs/
```

> "Scenario 7. Same molecular space as our literature graph. But instead of patents and papers, here's the authoritative source — ten Phase 3 trial protocols from ClinicalTrials.gov. SURPASS-2, SURMOUNT-1, all three STEP trials, both PIONEER cardiovascular studies, SUSTAIN-6, ACHIEVE-1 for orforglipron. These are the exact trials the drug-discovery narrator told us were missing."

```bash
python scripts/fetch_ct_protocols.py tests/corpora/07_glp1_phase3_trials
```

*Don't execute — quick cut, or show the file that was already produced.*

> "One script call — ClinicalTrials.gov v2 API, stdlib urllib, ten protocols fetched. Then the standard pipeline, but with `--domain clinicaltrials`."

```bash
ls tests/corpora/07_glp1_phase3_trials/output/
```

> "One hundred forty-two entities, three hundred ninety-five relations, eight communities. Different domain, same pipeline."

---

## Act 6 — Phase-tier grading + external enrichment (90s)

**Surface:** Terminal.

```bash
python domains/clinicaltrials/enrich.py tests/corpora/07_glp1_phase3_trials/output
```

*Execute — takes ~5 seconds. Shows:*

```
{"trials": {"total": 10, "enriched": 10, "hit_rate": 1.0},
 "compounds": {"total": 2, "enriched": 2, "hit_rate": 1.0}}
```

> "The clinicaltrials domain ships with an enrichment layer. One command hits ClinicalTrials.gov v2 for every trial node — pulls back official phase, enrollment count, start and completion dates, overall status — and PubChem PUG REST for every compound — canonical SMILES, molecular formula, InChI. Hundred percent hit rate here. Non-blocking by contract: network failures log counts but never abort the pipeline."

```bash
python -m core.label_epistemic tests/corpora/07_glp1_phase3_trials/output --domain clinicaltrials | tail -5
```

> "And after enrichment, the phase-tier grader has data to work with. A hundred seventy-seven relations now marked high_evidence — Phase 3, randomized, enrollment over three hundred. Twenty medium. The remaining unclassified aren't failures — they're relations not connected to a trial node, which the grader correctly skips."

```bash
bat tests/corpora/07_glp1_phase3_trials/output/epistemic_narrative.md | head -30
```

> "New briefing, same pattern. This narrator is tuned differently — it reasons about arm-level enrollment, endpoint multiplicity, phase-tier coverage. Different persona, same framework."

---

## Act 7 — Cross-domain comparison (90s)

**Surface:** Split screen or two browser windows side by side.

```bash
# Terminal A (keep running from Act 3)
python scripts/launch_workbench.py tests/corpora/06_glp1_landscape/output-v3 --domain drug-discovery --port 8000 &
# Terminal B
python scripts/launch_workbench.py tests/corpora/07_glp1_phase3_trials/output --domain clinicaltrials --port 8001
```

*Both browsers open. Window on the left is S6 drug-discovery. Window on the right is S7 clinicaltrials.*

> "Now the competitive-intelligence move. Same question in both. Same molecular space. Different source material, different domain persona, different knowledge graph."

**Type into BOTH chats:**
```
What's the evidence for tirzepatide in obesity?
```

*Let both stream simultaneously. S6 will cite patents + PubMed abstracts, mention SURMOUNT-1 but note it as missing detail, reason about prophetic patent claims, flag the temporally-stratified contradiction. S7 will cite NCT04184622 directly with 2,539 enrollment, four-arm design, phase-tier grading, exact primary endpoints.*

> "Left side — drug-discovery persona reading the literature graph. It talks about patent claims, hedged research wording, what the trials should show. Right side — clinicaltrials persona reading the protocol graph. It cites NCT numbers, enrollment counts, primary endpoints, phase-tier evidence grades. Neither one alone is a CI brief. Together they are."

> "And this is the framework claim. Same pipeline. Same epistemic machinery. Same persona-dual-use pattern. Two domains, two views, one integrated understanding."

---

## Act 8 — Framework mechanics (60s)

**Surface:** Terminal.

```bash
tree domains/clinicaltrials/ -L 2
```

```
domains/clinicaltrials/
├── domain.yaml           # 12 entity types, 10 relation types
├── SKILL.md              # 529-line extraction prompt
├── epistemic.py          # phase-based evidence grading
├── enrich.py             # CT.gov + PubChem enrichment
└── workbench/
    └── template.yaml     # persona + entity colors + starters
```

> "A whole domain is five files. Schema in YAML, extraction prompt in Markdown, epistemic rules and optional enrichment in Python, workbench config in YAML. That's the whole contract. No core-code changes."

```
/epistract:domain --input ./my-sample-docs/ --name my-domain
```

> "And if you don't want to hand-write any of it, the domain wizard analyzes three to five sample documents, proposes a schema via multi-pass LLM analysis, and generates all five files. Now you have a custom domain."

> "All three pre-built domains and the wizard are in the repo. The drug-discovery and clinicaltrials showcases with full narratives and workbench screenshots are in docs/SHOWCASE-GLP1.md and docs/SHOWCASE-CLINICALTRIALS.md."

---

## Act 9 — Closing (40s)

**Surface:** GitHub releases page `github.com/usathyan/epistract/releases`.

> "Epistract runs as a Claude Code plugin. Version three-point-one shipped April twenty-third. Open source, MIT license, installable with two commands in Claude Code.
>
> The thesis again: communities tell you where in the graph to look. Super Domains tell you what kind of knowledge you're looking at. An analyst persona tells you what to do with it. That's the framework.
>
> Happy to answer questions. Thanks for watching."

**Cut to title card:**
```
EPISTRACT v3.1.0
github.com/usathyan/epistract
umesh@8thcross.com
```

---

## Production checklist

- [ ] **Recording environment**: Ghostty terminal (1920×1080, dark theme, 16pt font). Browser: Safari or Chrome, bookmark bar hidden, DnD on.
- [ ] **Pre-built output**: `tests/corpora/06_glp1_landscape/output-v3/` and `tests/corpora/07_glp1_phase3_trials/output/` both present on disk and committed.
- [ ] **Enrichment artifacts**: verify `_enrichment_report.json` exists under `output/extractions/`.
- [ ] **Workbench pre-launch**: launch both (`--port 8000` S6, `--port 8001` S7) in separate terminals before record to let physics settle.
- [ ] **Workbench credentials**: verify `ANTHROPIC_API_KEY` or `OPENROUTER_API_KEY` is set (otherwise chat will 402). Top up credits if running low.
- [ ] **Terminal state**: `cd ~/code/epistract && clear` between cuts.
- [ ] **Capture method**: QuickTime File → New Screen Recording (or OBS with mic track disabled; add voiceover in post). Separate record per act — cleaner editing.
- [ ] **Voiceover**: Either record live or do in post with ElevenLabs (Roger voice, eleven_multilingual_v2 model per the v2.0 pipeline). Phonetic spellings for TTS: sem-ah-glue-tide, teer-zeh-pa-tide, or-for-GLI-pron, GLP-one, epi-stem-ick.
- [ ] **Narration length check**: script is ~1,700 words; at 140 wpm that's ~12 minutes. Pad video by ~5% with buffer shots to match the longer voiceover cadence.
- [ ] **Post-production**: ffmpeg merge, EBU R128 loudness normalization (same pipeline as v2.0 video), crossfade between acts.

## Act runbook for Day-of QnA prep

Likely audience questions + answers:

- **"How is the epistemic layer different from a confidence score?"** — A confidence score tells you how strongly a single extraction is supported. Epistemic status tells you *what kind* of support exists — asserted evidence vs. patent forward-looking language vs. hedged research suggestion vs. disputed across sources. It's categorical, not scalar. Same 0.95 confidence can be asserted or prophetic depending on the source language.
- **"What's the persona file actually doing?"** — It's one string used as the system prompt in two places: the workbench chat request, and the `/epistract:epistemic` narrator LLM call. Both see the same "You are a senior drug discovery analyst…" preamble. Upgrade once, both improve. Per-domain because a contracts analyst doesn't reason the way a CT analyst does.
- **"Can I bring my own LLM?"** — Credential resolver priority is Azure AI Foundry → Anthropic direct → OpenRouter. All three speak the Anthropic-native message format (or the OpenAI-compat format on OpenRouter). Works with Claude Sonnet 4.5 or 4.6; bring-your-own-model is a config change, not a code change.
- **"How do you handle the cold-start problem for a brand new domain?"** — `/epistract:domain --input ./samples/` runs a three-pass LLM analysis on three to five sample documents. Produces a full domain package. Wizard limits schemas to 15 entity types and 20 relation types by default to keep extraction tight.
- **"What about hallucinations in the narrator?"** — The narrator's input is the classified graph (JSON) plus the persona. It doesn't see the source documents directly. Its claims must reference graph nodes and relations. When it does speculate (we've seen cases where it infers patent-like language from a non-patent corpus), the mitigation is source-type hinting in the prompt — candidate v3.2 fix.
- **"Is this just RAG?"** — No. RAG retrieves chunks at query time. Epistract extracts a structured graph once, then the workbench chat answers questions grounded in that graph. The epistemic layer and narrator are graph-level, not chunk-level. This gives you cross-document synthesis, contradiction detection, and named hypotheses — which retrieval alone can't surface.

---

*Script prepared 2026-04-23 for the KGC 2026 Tools & Demonstrations track, 2026-05-08. Superseded prior v2.0 script at `archive/docs/demo/demo-script.md`.*
