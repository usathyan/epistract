# Epistract v3.2 — Knowledge Graph Conference 2026 Demo Script (5-min cut)

**Conference:** Knowledge Graph Conference 2026 — Tools & Demonstrations Track
**Track date:** 2026-05-08, 10 AM – Noon ET (virtual)
**Video slot:** 5 minutes total + 10–15 min live QnA
**Presenter:** Umesh Bhatt (umesh@8thcross.com)
**Epistract version:** v3.2.0 / 4 pre-built domains, S7 clinicaltrials shipped, S6 drug-discovery validated across 6 sub-scenarios
**Prior video:** [v2.0 demo, 2026-03-27, YouTube](https://youtu.be/7mHbdb0nn3Y) — superseded
**Prior 12-min script:** retained in git history at `docs/demo-v3/demo-script.md@2eca1bf` if a longer cut is ever needed

---

## Audience profile (carried forward from prior cut)

KGC attendees: domain experts in life sciences, general KG practitioners, ontology experts, computer-science graph theorists. Speak in their vocabulary — Louvain, force-directed layout, ontology grounding, epistemic content, Super Domains. Don't oversimplify; don't lecture either.

---

## Story arc — 5 minutes, one corpus, live demo

| Block | Window | What's on screen | Word budget |
|---|---|---|---:|
| 1. Setup + GLP-1 scenario context | 0:00 – 1:00 | Title → terminal | ~140 |
| 2. Trigger the briefing + name the two layers | 1:00 – 2:00 | Terminal command → workbench loading | ~140 |
| 3. Graph walkthrough while briefing generates | 2:00 – 3:30 | Workbench Graph panel | ~210 |
| 4. Briefing returns — read executive summary | 3:30 – 4:30 | Terminal / VS Code on `epistemic_narrative.md` | ~140 |
| 5. Closing | 4:30 – 5:00 | Title card + GitHub URL | ~70 |

Total narration: ~700 words at 140 wpm = ~5 min. Tight; rehearse twice before recording.

---

## Block 1 — Setup + GLP-1 scenario (60s, 0:00–1:00)

**Surface:** Title card for 5s, fade to a clean terminal at `~/code/epistract`.

**Title card:**
```
EPISTRACT
A two-layer knowledge graph framework
github.com/usathyan/epistract · v3.2.0
```

**Narration:**

> "Hi, I'm Umesh. I want to show you a knowledge graph framework called Epistract. The motivating problem: most KG tools stop at extracting entities and typed relations. They tell you what's in a document but not *how* that something was stated — was it asserted with quantitative evidence? Was it patent forward-looking language? Was it hedged research wording? Does it contradict another source? Epistract treats that epistemic dimension as a first-class layer on top of the brute facts.
>
> To show you what that means concretely: I've already ingested thirty-four documents on GLP-1 receptor agonists — the drug class behind semaglutide and tirzepatide, used for type-2 diabetes and obesity. Ten patent filings from Novo Nordisk, Pfizer, Eli Lilly, Hanmi, and Zealand. Twenty-four PubMed papers on mechanism, safety, and emerging indications. The graph is already built. I'll trigger the analyst briefing now, and while it runs I'll walk through the graph itself."

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

> "Three things worth pointing out. One: entities are grounded to ontology standards. INN names for drugs. HGNC symbols for genes. MeSH preferred terms for diseases. The schema is in YAML, eleven to seventeen entity types per domain across our four pre-built domains. Two: every edge carries a confidence score and a verbatim source quote. Click any edge —"

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

**Surface:** Title card with GitHub URL + version + 4-domain summary.

**Narration:**

> "Quick wrap-up. The framework is domain-agnostic — four pre-built domains today: drug-discovery, contracts, clinicaltrials, FDA product labels. Each domain is four required files — schema in YAML, extraction prompt in Markdown, epistemic rules in Python, analyst persona in YAML — plus optional helpers like an external-API enrichment module. Open source, MIT license. Runs as a Claude Code plugin. Code at github.com/usathyan/epistract. Happy to take questions."

**Cut to title card:**
```
EPISTRACT v3.2.0
github.com/usathyan/epistract
umesh@8thcross.com
QnA →
```

---

## Production checklist

- [ ] **Pre-built artifacts**: `tests/corpora/06_glp1_landscape/output-v3/{graph_data.json, claims_layer.json, epistemic_narrative.md}` all present and committed
- [ ] **Workbench pre-launch** before recording: `python scripts/launch_workbench.py tests/corpora/06_glp1_landscape/output-v3 --domain drug-discovery --port 8000` — let physics settle for 30s before hitting record
- [ ] **OpenRouter / Anthropic credits**: enough for the live `/epistract:epistemic` rerun in Block 2 (~$0.05–$0.10 for the narrator call)
- [ ] **Terminal / browser layout**: pre-position so the switch from terminal to browser feels natural; consider a 2-up layout where the terminal stays visible in a corner during graph walkthrough
- [ ] **Recording**: QuickTime screen recording, 1920×1080, microphone live (this script is paced for live first-person delivery, not TTS post)
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
- "What's the persona file actually doing?" — One YAML string, used as system prompt in two places (workbench chat + narrator). Per-domain.
- "Does this relate to Eric Little's Super Domain work?" — Yes, vocabulary converged.
- "Can I bring my own LLM?" — Azure AI Foundry → Anthropic direct → OpenRouter, in priority order. All speak Anthropic-native or OpenAI-compat format.
- "Why labeled property graph instead of RDF?" — sift-kg's NetworkX substrate. RDF / GraphML / Turtle exports via `/epistract:export`.
- "Does the framework learn across scenarios?" — Not yet. Refinements are human-mediated. Issue #15 tracks the aspirational compounding mechanism.

---

*Script prepared 2026-04-25. 5-minute cut for the KGC 2026 Tools Track. The longer 12-min cut is in git history at `docs/demo-v3/demo-script.md@2eca1bf` if a future longer venue ever needs it.*
