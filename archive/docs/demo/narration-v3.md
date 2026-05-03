# Demo Narration + Commands — v3.1 KGC 2026

**Read from phone while recording.** Open Ghostty, `cd ~/code/epistract`, clear. Screen-record terminal + browser.

Target: ~12 minutes, ~1,600 words at 140 wpm. Audience is Knowledge Graph specialists — lead with the graph, use life-sciences as a concrete example, save implementation details for the end.

**Pre-launch workbenches before recording:**
```bash
python scripts/launch_workbench.py tests/corpora/06_glp1_landscape/output-v3 --domain drug-discovery --port 8000 &
python scripts/launch_workbench.py tests/corpora/07_glp1_phase3_trials/output --domain clinicaltrials --port 8001 &
```

---

## Act 1 — The KG problem we're addressing (75s)

*Title card, then a schematic slide.*

**Say:**

> "A knowledge graph has two kinds of content that most toolchains flatten together.
>
> First, there are the **brute facts** — nodes and typed edges grounded to a domain ontology, each edge with a confidence score and a source-document citation. This is what virtually every KG tool produces.
>
> Second, there's the **epistemic content** — *how* each fact was stated. Was it asserted with quantitative evidence? Was it prophetic patent language — 'is expected to,' 'may be prepared by'? Was it hedged research wording — 'suggests,' 'appears to'? Does the same edge appear across sources with conflicting confidence, making it contested? Or do two sources outright contradict each other?
>
> Epistract treats that epistemic content as a first-class Super Domain layer on top of the brute facts KG. Every edge gets tagged. An analyst persona — different for each domain — reads the classified graph and writes a briefing. That's the framework."

---

## Act 2 — A two-layer knowledge graph in action (150s)

*Switch to browser at http://127.0.0.1:8000, Graph panel.*

**Say:** "Here's what that looks like. This is a knowledge graph built from thirty-four documents on a single drug class — we'll come back to the drug-discovery specifics in a minute. For now, focus on the graph structure."

*Pan/zoom the graph.*

**Say:** "Two hundred seventy-eight entities across thirteen types. Eight hundred fifty-five typed relations. Ten Louvain communities. So far, this is a standard labeled property graph — you could reproduce the structure in Neo4j or NetworkX."

*Click a community cluster to highlight it.*

**Say:** "The community structure tells you *where* in the graph to look — which nodes are densely interconnected. Useful for navigation. It tells you nothing about *what kind of knowledge* you're looking at — a patent prophetic claim and a Phase 3 trial result sit in the same community, topologically indistinguishable."

*Switch to terminal.*

**Type:** `cat tests/corpora/06_glp1_landscape/output-v3/claims_layer.json | jq '.summary.epistemic_status_counts'`

**Say:** "This is the Super Domain layer. The same eight hundred fifty-five relations, but now each one is tagged with an epistemic status. Seven categories. Sixty-one prophetic — patent language claiming effects that haven't been demonstrated. Thirty-three contested — same entity pair, same relation type, but different sources give different confidence. Two outright contradictions. The rest cleanly asserted."

**Say:** "This is what the Super Domain adds to the graph. You can now query by epistemic status. You can render contested edges in amber. You can write a policy that says 'never treat a prophetic relation the same as an asserted one.' The graph becomes a reasoning substrate, not just a lookup table."

---

## Act 3 — S6 life-sciences illustration (120s)

*Switch back to browser :8000. Click Chat panel.*

**Say:** "Now let me make this concrete with the corpus we just saw. It's a drug-discovery corpus — thirty-four documents on a class of medications called GLP-1 receptor agonists. You've probably heard of semaglutide, sold as Ozempic and Wegovy, and tirzepatide, sold as Mounjaro and Zepbound. They're used for type-2 diabetes and obesity. The corpus is ten patent filings from Novo Nordisk, Pfizer, and Eli Lilly, plus twenty-four PubMed abstracts about mechanism, safety, and emerging indications."

**Say:** "The chat panel is grounded in the graph data and runs on a senior drug-discovery analyst persona. The persona commits to citing every claim by source document and to using the epistemic-status vocabulary we just saw. Let me ask it the question the research analyst would ask."

*Type into chat:* `Which patents make prophetic claims about new indications, and where are the biggest gaps between prophetic breadth and asserted evidence?`

*Let the response stream. Let the table render.*

**Say:** "This is cross-document synthesis. The chat is grouping prophetic claims by patent family, flagging the ones most likely to be boilerplate, and naming the asserted clinical evidence that would close each gap. Every specific claim cites the source by document ID. This is not retrieval. You couldn't do this with chunk-level RAG because the synthesis is happening at the graph level — the contested edges, the temporal stratification of confidence scores, the cross-patent clustering all live in the claims layer, not in the source text."

---

## Act 4 — The automatic analyst briefing (90s)

*Back to terminal.*

**Type:** `bat tests/corpora/06_glp1_landscape/output-v3/epistemic_narrative.md | head -80`

**Say:** "The chat just answered reactively — I asked, it responded. The same machinery runs proactively. After the epistemic classification writes the claims layer, the pipeline calls the same analyst persona with the full classified graph and asks for a structured briefing. File committed alongside the graph. Regenerated on every run."

*Read verbatim from the narrative — scroll to each section as you read:*

> "Sixty-one prophetic claims inflate the apparent indication breadth of these compounds. Cardiovascular risk reduction, neurodegeneration, and metabolic sub-disorders are largely patent-forward-looking, not empirically established."

> "semaglutide INDICATED_FOR obesity — confidence range 0.55 to 0.97 across sources. The 0.55 instance likely reflects pre-STEP-trial patent language; the 0.97 instance reflects post-approval asserted status. These should be temporally stratified, not treated as equivalent evidence."

> "Integrate SURPASS-2 trial data — add a clinical_trial:surpass_2 node with direct tirzepatide-vs-semaglutide efficacy relations to close the head-to-head gap. Source: NEJM 2021, Frías et al."

**Say:** "This is an analyst reading the graph and telling you what it's missing. The persona that produced this briefing is the same string that powered the chat you just saw — one YAML field used as the system prompt in two places. Upgrade the persona, both surfaces improve together. That's the domain's expert voice, stored exactly once."

---

## Act 5 — Different analysts for different kinds of knowledge (120s)

*Switch to split-screen: browser :8000 on the left, browser :8001 on the right.*

**Say:** "Up to this point we've looked at one graph. But the framework claim is that the same pipeline works for any domain — the only thing that changes is the domain config. Let me show that as a graph-level claim."

**Say:** "On the right is a completely different knowledge graph. Same molecular space — GLP-1 agonists — but the source is ten ClinicalTrials.gov trial protocols. SURPASS-2, SURMOUNT-1, STEP-1 through three, the PIONEER cardiovascular trials, SUSTAIN-6, ACHIEVE-1. And the domain here is `clinicaltrials`, not `drug-discovery`. Twelve entity types including Trial, Intervention, Cohort, TrialPhase, Outcome. Ten relation types. Phase-based evidence grading baked into the epistemic layer."

*Point at the right-side graph.*

**Say:** "One hundred forty-two entities, three hundred ninety-five relations, eight communities. Different graph from a different domain, built by the same core pipeline."

**Say:** "Now the test. Same question, both chats."

*Type into BOTH chats simultaneously:* `What's the evidence for tirzepatide in obesity?`

*Let both stream in parallel.*

**Say:** "Left side — the drug-discovery analyst persona reading the literature graph. Cites patents and PubMed abstracts. Talks about prophetic claims, hedged research wording, what the trials should show. Right side — the clinical trials analyst persona reading the protocol graph. Cites NCT identifiers. Names enrollment counts, primary endpoints, phase-tier evidence grades."

**Say:** "Neither graph alone is a competitive-intelligence brief. Together they are. And this is the graph-level claim: same epistemic machinery, same persona-dual-use pattern, different ontology commitments, produces two knowledge graphs that are complementary by construction."

---

## Act 6 — For the tech geeks — how it's built (120s)

*Back to terminal.*

**Say:** "For the implementers in the room. A quick look under the hood."

**Type:** `tree domains/clinicaltrials/ -L 2`

**Say:** "A whole domain is four required files. Schema in YAML. Extraction prompt in Markdown. Epistemic rules in Python. Workbench config — including the analyst persona — in YAML. No core-code changes. The clinicaltrials package also ships an optional helper module to pull live metadata from its natural authoritative source, ClinicalTrials.gov. That's a package-level convenience, not a framework feature — any domain with a canonical external data source can include its own helper the same way."

**Type:** `cat domains/clinicaltrials/workbench/template.yaml | grep -A 3 "^persona"`

**Say:** "This is the single string that drives both the reactive workbench chat and the proactive narrator. One source of truth per domain. Change it once, both surfaces pick up the change."

**Type:** `ls core/`

**Say:** "The core pipeline is domain-agnostic — no clinicaltrials or drug-discovery code anywhere in it. It resolves a domain package at runtime, applies the schema, runs the epistemic classifier, calls the narrator. LLM credential priority is Azure AI Foundry first, then Anthropic direct, then OpenRouter — your choice. Claude Sonnet at the time of this recording."

**Type (don't execute):** `/epistract:domain --input ./my-sample-docs/ --name my-domain`

**Say:** "And if you don't want to hand-write any of it, the domain wizard runs multi-pass LLM analysis on three to five sample documents, proposes a schema, and emits all four required files. You have a working custom domain in about fifteen minutes. Open source, MIT license, runs as a Claude Code plugin."

---

## Act 7 — Closing (45s)

*Switch to https://github.com/usathyan/epistract/releases.*

**Say:** "Epistract version three-point-one shipped last week. Three pre-built domains — drug discovery, contracts, clinical trials — each demonstrating the two-layer architecture. Each with an analyst persona in the domain package. Each producing an auto-generated epistemic narrative on every run.
>
> The framework's one-line summary: communities tell you where in the graph to look. Super Domains tell you what kind of knowledge you're looking at. Analyst personas tell you what to do with it.
>
> Happy to take questions now. Thank you."

*Cut to title card.*

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
| ClinicalTrials.gov | "Clinical Trials dot gov" |
| Claude | "clawed" |
| Novo Nordisk | "NOH-voh NOR-disk" |
| Eli Lilly | "EE-lie LILL-ee" |
