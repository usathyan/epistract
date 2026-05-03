# Epistract v3.2 — Knowledge Graph Conference 2026 Demo Script (5-min cut)

**Conference:** Knowledge Graph Conference 2026 — Tools & Demonstrations Track
**Track date:** 2026-05-08, 10 AM – Noon ET (virtual)
**Video slot:** 5 minutes total + 10–15 min live QnA
**Presenter:** Umesh Bhatt (umesh@8thcross.com)
**Epistract version:** v3.2.2 / 4 pre-built domains (drug-discovery, clinicaltrials, fda-product-labels, contracts) / 8 validated scenarios. S8 fda-product-labels is the README showcase (landed v3.2.1, 2026-04-26); S6 drug-discovery (GLP-1) is the demo corpus — chosen for the richest prophetic-vs-asserted contrast story.
**Prior video:** [v2.0 demo, 2026-03-27, YouTube](https://youtu.be/7mHbdb0nn3Y) — superseded
**Prior 12-min cut:** archived at `archive/docs/demo/narration-v3.md` + `archive/docs/demo/run-demo-v3.sh` for any future longer venue.

---

## Audience profile (carried forward from prior cut)

KGC attendees: domain experts in life sciences, general KG practitioners, ontology experts, computer-science graph theorists. Speak in their vocabulary — Louvain, force-directed layout, ontology grounding, epistemic content, Super Domains. Don't oversimplify; don't lecture either.

---

## Story arc — 5 minutes, one corpus, live demo

| Block | Window | What's on screen | Word budget |
|---|---|---|---:|
| 1. Positioning + GLP-1 scenario | 0:00 – 1:00 | Title → terminal | ~170 |
| 2. Trigger the briefing + name the two layers | 1:00 – 2:00 | Terminal command → workbench loading | ~140 |
| 3. Graph walkthrough while briefing generates | 2:00 – 3:30 | Workbench Graph panel | ~190 |
| 4. Briefing returns — read executive summary | 3:30 – 4:30 | Terminal / VS Code on `epistemic_narrative.md` | ~140 |
| 5. Closing | 4:30 – 5:00 | Title card + GitHub URL | ~70 |

Total narration: ~710 words at 140 wpm = ~5 min. Tight; rehearse twice before recording. Block 1 carries more density (the analyst-inside-a-question framing is what differentiates Epistract from enterprise KG tools — it pays for itself in the QnA), Block 3 trades a tangential schema beat for that air.

---

## Block 1 — Positioning + GLP-1 scenario (60s, 0:00–1:00)

**Surface:** Title card for 5s — full-frame `docs/demo-v3/epistract.png` (1536×1024 schematic: two-layer architecture + persona dual-arrow + four domain pills + scenario thumbnails). Fade to a clean terminal at `~/code/epistract`.

*The schematic doubles as the visual proof of every claim in the narration that follows: Layer 1 (property graph) and Layer 2 (epistemic overlay) are both visible, the persona-as-single-source-of-truth pattern (one arrow to Workbench Chat, one to Epistemic Briefing) is right there, and the four domains + scenario gradient sit along the bottom. A viewer who pauses on the title card can read the architecture before the narration even starts.*

**Fallback ASCII title card** (if the PNG can't be used for any reason):
```
EPISTRACT
A Two-Layer Knowledge Graph Framework
with an Epistemic Super-Domain Layer

github.com/usathyan/epistract · v3.2.2
Paper: paper/v2/main.pdf · Umesh Bhatt · umesh@8thcross.com
```

*The title is the paper's title. Same wording everywhere — the README hero, the paper, the title card — so a viewer who pauses can google it and land on the same artifact every time.*

**Narration:**

> "Hi, I'm Umesh. Epistract is built for the analyst working inside a question — the biomedical researcher screening a thirty-paper landscape for a target decision, the regulatory specialist comparing FDA labels for a class, the CI analyst working through a competitor's patent stack. Their corpus is bounded; the graph they need is built fast, queried hard, archived when the decision is made. A maintained enterprise knowledge graph — Anzo, Neptune, Neo4j — is the wrong tool for that workflow. Too slow to build, too broad to be precise, too costly to retire. Epistract is the right one.
>
> Where it fits in the loop: Claude Code already gives you the deep-research capabilities — web tools, MCP servers for academic search, patents, trials, regulators. You assemble the corpus there. Epistract is what you reach for next — the consolidation layer that turns that body of documents into a structured knowledge graph: typed entities and relations, an epistemic classification on every relation, an analyst briefing, a reactive chat. Most KG tools stop at the brute facts. They tell you what's in a document but not *how* it's stated — asserted, prophetic patent language, hedged hypothesis, or contradiction. Epistract treats that epistemic dimension as a first-class layer on top.
>
> Demo corpus: thirty-four documents on GLP-1 receptor agonists — the drug class behind semaglutide and tirzepatide. Ten patent filings from Novo Nordisk, Pfizer, Eli Lilly, Hanmi, and Zealand. Twenty-four PubMed papers on mechanism, safety, and emerging indications. The graph is already built. I'll trigger the analyst briefing now, and while it runs I'll walk the graph itself."

---

## Block 2 — Trigger briefing + name the two layers (60s, 1:00–2:00)

**Type at terminal (live):**

```bash
.venv/bin/python -m core.label_epistemic \
    tests/corpora/06_glp1_landscape/output-v3 \
    --domain drug-discovery
```

*Hit return. The pipeline starts streaming logs. ~30–60 seconds before `epistemic_narrative.md` is rewritten.*

**Narration (delivered while logs scroll):**

> "While this runs — what's happening here: the brute-facts layer is already extracted. Two hundred seventy-eight entities, eight hundred fifty-five typed relations, ten Louvain communities. The pipeline is now classifying every relation by epistemic status — asserted, prophetic, hypothesized, contested, contradiction, negative, and a few others — using a combination of regex patterns over evidence text and document-type inference. Then it hands the classified graph to a senior drug-discovery competitive-intelligence analyst persona, which produces a structured briefing.
>
> The persona is a single string in the domain config — `domains/drug-discovery/workbench/template.yaml`. The same string powers the workbench chat reactively when users ask questions. One source of truth, two surfaces. Let me show you the graph while the briefing finishes."

*Switch to browser at `http://127.0.0.1:8000` (workbench, pre-loaded with the GLP-1 graph).*

---

## Block 3 — Graph walkthrough while briefing generates (90s, 2:00–3:30)

**Surface:** Workbench Graph panel. Graph already settled.

**Narration:**

> "Here's the graph. Force-directed layout, two hundred seventy-eight nodes, color-coded by entity type — compounds in indigo, diseases in red, clinical trials in cyan, mechanisms of action in purple, biomarkers in slate. Eight hundred fifty-five typed edges. Ten Louvain communities detected at the topology level."

*Pan over a community cluster — for example, the GLP-1 receptor / pharmacology cluster.*

> "Community structure tells you *where* to look — densely interconnected nodes form clusters worth investigating. It tells you nothing about *what kind of knowledge* you're looking at. That's the brute-facts layer being honest about what it knows: structure, but not epistemology."

*Click a `Compound` node — semaglutide or tirzepatide. Show its neighborhood and attributes.*

> "Three things worth pointing out. One: entities are grounded to ontology standards — INN names for drugs, HGNC symbols for genes, MeSH preferred terms for diseases. Two: every edge carries a confidence score and a verbatim source quote. Click any edge —"

*Click an edge, popover shows the evidence quote.*

> "— and you can drill back to the source document. Three, and this is the part where the epistemic layer earns its keep: the same entity pair frequently appears with multiple edges. `semaglutide INDICATED_FOR obesity` shows up with confidence point-five-five in one source and point-nine-seven in another. A flat knowledge graph either loses the variation by averaging, or treats them as conflicting noise. Our claims layer tags this as `contested` and surfaces it to the narrator, which should be done any second now. Let's check."

*Switch back to terminal.*

---

## Block 4 — Briefing returns + executive summary (60s, 3:30–4:30)

**Surface:** Terminal — open `epistemic_narrative.md` in `bat` or VS Code.

```bash
bat tests/corpora/06_glp1_landscape/output-v3/epistemic_narrative.md
```

*Scroll to the Executive Summary section.*

**Narration (read the excerpts verbatim — these are real text from the live graph):**

> "Eleven hundred sixty-six words. Let me read the Executive Summary. This is what the framework just produced — without me writing a single word of it.
>
> 'Sixty-one prophetic claims inflate the apparent indication breadth of these compounds. Cardiovascular risk reduction, neurodegeneration, and metabolic sub-disorders are largely patent-forward-looking, not empirically established.'
>
> 'semaglutide INDICATED_FOR obesity — confidence range zero-point-five-five to zero-point-nine-seven across sources. The point-five-five instance reflects pre-STEP-trial patent language; the point-nine-seven reflects post-approval asserted status. These should be temporally stratified, not treated as equivalent evidence.'
>
> 'Recommend integrating SURPASS-two trial data — direct tirzepatide-versus-semaglutide efficacy relations to close the head-to-head gap. Source: Frías et al, New England Journal of Medicine, 2021.'
>
> Cross-document synthesis. Temporal stratification of confidence. Gap surfacing. Concrete recommended next actions. The narrator persona produced this from the classified graph — it didn't see the source documents directly. Its claims trace back to graph nodes and relations."

---

## Block 5 — Closing (30s, 4:30–5:00)

**Surface:** Brief picture-in-picture of the paper PDF (title page) for ~3 seconds while the closing card loads, then full closing card.

**Narration:**

> "Quick wrap-up. Four pre-built domains today: drug-discovery, contracts, clinicaltrials, FDA product labels. The loop: deep research upstream in Claude Code's broader ecosystem, consolidation through Epistract, follow-up questions against the graph, then back upstream when a gap surfaces. `/epistract:ingest` to fold in new documents, `/epistract:epistemic` to re-grade evidence, workbench chat for reactive questions. Claude Code's memory and MCP ecosystem keep your accumulated context across sessions. Open source, MIT. Paper at `paper/v2/main.pdf` — link's in the README. Code at github.com/usathyan/epistract. Happy to take questions."

**Cut to closing card:**
```
EPISTRACT v3.2.2

Paper:  Epistract — A Two-Layer Knowledge Graph Framework
        with an Epistemic Super-Domain Layer
        github.com/usathyan/epistract/blob/main/paper/v2/main.pdf

Code:   github.com/usathyan/epistract
Author: Umesh Bhatt · umesh@8thcross.com

QnA →
```

*Why the PDF flash on screen: it's a 3-second signal that "this isn't just a demo, there's a paper" — KGC audiences will look up the paper, and seeing the title twice (in narration + on screen) helps it stick. If you don't want screen-time on the PDF, just keep the closing card; the link is still discoverable.*

---

## Production checklist

- [ ] **Title-card asset**: `docs/demo-v3/epistract.png` (1536×1024 schematic) ready as full-frame opener. Subtitle says v3.2.0 — kept as-is; the two-layer architecture hasn't changed across v3.2.x patches.
- [ ] **Pre-built artifacts**: `tests/corpora/06_glp1_landscape/output-v3/{graph_data.json, claims_layer.json, epistemic_narrative.md}` all present and committed
- [ ] **Paper PDF**: `paper/v2/main.pdf` rebuilt against current main and committed (so the GitHub link resolves to the latest version on day-of). Title page open in Preview ahead of time for the Block 5 picture-in-picture.
- [ ] **Workbench pre-launch** before recording: `python scripts/launch_workbench.py tests/corpora/06_glp1_landscape/output-v3 --domain drug-discovery --port 8000` — let physics settle for 30s before hitting record
- [ ] **OpenRouter / Anthropic credits**: enough for the live `/epistract:epistemic` rerun in Block 2 (~$0.05–$0.10 for the narrator call)
- [ ] **Terminal / browser layout**: pre-position so the switch from terminal to browser feels natural; consider a 2-up layout where the terminal stays visible in a corner during graph walkthrough
- [ ] **Recording**: Polycapture (macOS multi-source recorder) — separate sources for terminal and browser, 1920×1080, microphone live with Voice Isolation, app exclusion ON for any window with secrets/notifications, camera bubble small bottom-right or off. Recording each source separately means a stumble on one stream doesn't force a full re-take. Script is paced for live first-person delivery, not TTS post.
- [ ] **Backup plan**: if the live narrator call hangs (rate-limit / SSE error), have a pre-built `epistemic_narrative.md` ready to open at the 3:30 mark — don't dwell on the failure
- [ ] **Rehearsal**: 2 rehearsal passes minimum. The live `/epistract:epistemic` runtime varies (30–90s); know what you'll fill the slack with if it returns early or late

## Phonetic pronunciations for live delivery

| Term | Phonetic |
|---|---|
| epistract | eh-pi-STRACT |
| epistemic | epi-STEM-ick |
| semaglutide | sem-ah-GLUE-tide |
| tirzepatide | teer-ZEH-pa-tide |
| GLP-1 | G-L-P one |
| Louvain | loo-VAN |
| Pydantic | pie-DAN-tik |
| Frías et al | FREE-as et al |
| SURPASS-2 | SUR-pass two |
| HGNC | H-G-N-C |
| MeSH | mesh |

## QnA prep (carried forward, all still valid)

- "How is epistemic status different from a confidence score?" — Categorical, not scalar. Same 0.95 confidence can be `asserted` or `prophetic` depending on source language.
- "How do you decide the epistemic status of an edge?" — Two-stage: rules (regex + doc-type inference + CUSTOM_RULES + cross-source aggregation) → LLM is downstream of classification, only for the narrator briefing.
- "What classifications does the framework ship with, and can I customize them?" — Ships with the seven-status taxonomy (asserted, prophetic, hypothesized, contested, contradiction, negative, speculative) plus per-domain extensions: phase-based grading for clinicaltrials, four-level FDA epistemology (established/observed/reported/theoretical) for fda-product-labels. Customization is one file: edit `domains/<name>/epistemic.py` to add hedging patterns, custom contradiction rules, or new status types. The wizard (`/epistract:domain`) generates a starter `epistemic.py` pre-populated with the shared taxonomy so you edit rather than write from scratch.
- "What's the persona file actually doing?" — One YAML string, used as system prompt in two places (workbench chat + narrator). Per-domain.
- "Does this relate to Eric Little's Super Domain work?" — Yes, vocabulary converged.
- "Can I bring my own LLM?" — Azure AI Foundry → Anthropic direct → OpenRouter, in priority order. All speak Anthropic-native or OpenAI-compat format.
- "Why labeled property graph instead of RDF?" — sift-kg's NetworkX substrate. RDF / GraphML / Turtle exports via `/epistract:export`.
- "Does the framework learn across scenarios?" — Not yet. Refinements are human-mediated. Issue #15 tracks the aspirational compounding mechanism.
- "What corpus size does this handle?" — Designed for small-to-medium corpora that fit a Claude Code session. The seven validated scenarios range from 10 to 34 documents per corpus. The upper bound at which the chat or briefing degrades is undetermined — not yet tested at hundreds or thousands of documents. For scale beyond the workspace, `/epistract:export` dumps to GraphML, CSV, SQLite, or JSON for Neo4j-class persistent stores. MCP-based data-source connectors for on-demand corpus assembly are a future direction.
- "Is there a paper?" — Yes, at `paper/v2/main.pdf` — covers the two-layer architecture, the epistemic super-domain layer, the persona dual-use pattern, the four pre-built domains, and the seven validation scenarios. Linked from the README.
- "How are the paper's claims grounded?" — Every quantitative claim in the paper traces to a committed artifact under `tests/corpora/`. The accuracy checklist (`docs/demo-v3/accuracy-checklist.md`) maps demo claims to their codebase sources too.

---

*Script prepared 2026-04-25. 5-minute cut for the KGC 2026 Tools Track. The longer 12-min cut is in git history at `docs/demo-v3/demo-script.md@2eca1bf` if a future longer venue ever needs it.*
