# Epistract

**A two-layer knowledge graph framework for the analyst working inside a question.**

> 📄 **Paper:** *Epistract: A Two-Layer Knowledge Graph Framework with an Epistemic Super-Domain Layer* — [paper/v2/main.pdf](paper/v2/main.pdf) (April 2026, framework v3.2.x).
>
> 🎥 **Demo (5 min):** [Epistract at Knowledge Graph Conference 2026](https://youtu.be/SRBXZGL42fQ) (May 2026, framework v3.2.2).

I have spent the last decade building enterprise knowledge graphs — Anzo from the Cambridge Semantics era, AWS Neptune / RDF stacks, Neo4j deployments at multiple companies. They worked. They answer the questions executives ask: what do we know across the organization, where do teams' work intersect, what coverage do we have on a topic. They are the right tool for breadth.

The audience this framework is built for is a different one. The biomedical researcher screening a 30-paper landscape for a target-validation decision. The regulatory specialist comparing seven FDA product labels for a class. The CI analyst working through a competitor's patent stack. The contracts reviewer triaging a vendor portfolio. Their questions are bounded by a corpus they have curated for a specific decision, and the graph they need exists for *that* question — built fast, queried hard, archived when the decision is made. Maintaining a permanent enterprise graph is the wrong tool for that workflow: too slow to build, too broad to be precise, too costly to retire.

Epistract is built for that workflow. Point it at a corpus, get a structured graph that answers depth questions about *that* corpus with citations, plus an epistemic layer that distinguishes peer-reviewed claims from patent forward-looking language from hedged hypotheses. The whole loop — corpus → extraction → graph → query → archive — runs end to end in a single specialist's working session, inside [Claude Code](https://claude.ai/claude-code). No platform team. No ontology committee. No maintained mega-graph.

What makes this practical now is the multi-agent AI harness. Claude Code runs the extraction agents in parallel; the workbench chat reads the same graph data the narrator wrote; one persona drives both reactive Q&A and a proactive briefing. Epistract is one tool inside that harness — it does graph construction and epistemic analysis. Claude Code does corpus acquisition, deep research, and archival.

---

## What it looks like

![Workbench Graph — S6 GLP-1](docs/screenshots/workbench-03-graph-glp1.png)

*Epistract running on a 34-document GLP-1 corpus (10 patents + 24 PubMed papers): 278 entities, 855 typed relations, 10 communities, built in ~22 minutes. Each node colored by entity type, each edge a typed relation with a verbatim source quote and confidence score. Pan, zoom, filter, click any node for neighborhood context. The interactive workbench is `/epistract:dashboard`.*

![Workbench Chat — prophetic patent claims](docs/screenshots/workbench-04-chat-epistemic.png)

*The chat panel is grounded in the same graph data the narrator wrote — ask about prophetic claims, contested indications, or coverage gaps and it answers with citations to the originating documents.*

More screenshots: [docs/WORKBENCH.md](docs/WORKBENCH.md).

---

## What Epistract is — and isn't

**Is**

- A consolidation layer for a small-to-medium corpus (7–34 documents in the eight validated scenarios)
- A two-layer graph: brute facts from the corpus + epistemic classification on every relation
- A multi-agent harness that runs end to end inside Claude Code
- Pluggable — four pre-built domains; new domains via a 15-minute wizard from sample documents

**Isn't**

- A persistent enterprise KG store — use `/epistract:export` → Neo4j / Neptune / SQLite for that
- A document acquisition tool — Claude Code's web tools, MCP connectors do that; Epistract starts after acquisition
- A general-purpose answer engine — it answers depth questions about *the corpus you provided*, not the open web
- Self-learning across runs — refinements are human-mediated; [Issue #15](https://github.com/usathyan/epistract/issues/15) tracks the aspirational compounding mechanism

---

## The two layers

**Layer 1 — Brute facts.** Entities and typed relations extracted from the corpus, each with a confidence score and a verbatim source quote. Pydantic-validated at write time — no silent drops.

**Layer 2 — Epistemic super-domain.** Every relation carries a categorical status: `asserted` (stated with quantitative evidence), `prophetic` (patent forward-looking language), `hypothesized` (hedged wording), `contested` (multiple sources with conflicting confidence), `contradiction` (opposing evidence), `negative` (explicit absence), `speculative`. Domains can extend this — the FDA domain ships a four-level evidence-tier classifier (`established` / `observed` / `reported` / `theoretical`) that runs alongside the v3 vocabulary.

**One concrete contrast.** On the GLP-1 corpus (S6, drug-discovery domain), Epistract surfaces **61 prophetic claims** — patent forward-looking language about cardiovascular and neurodegenerative indications — versus **asserted** clinical-trial outcomes for `semaglutide` and `tirzepatide` in T2DM/Obesity. A flat KG would collapse these into a single relation type; the narrator briefing flags the gap explicitly and recommends three follow-up studies to close it.

More: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## Install

Epistract is a [Claude Code](https://claude.ai/claude-code) plugin. Two commands:

```bash
# 1. In Claude Code, add the marketplace and install
/plugin marketplace add usathyan/epistract
/plugin install epistract

# 2. Install Python dependencies
/epistract:setup
```

**Prerequisites:** Python 3.11+, [uv](https://docs.astral.sh/uv/), Claude Code. Optional: RDKit (molecular validation), Biopython (sequence validation), an API key (Azure Foundry, Anthropic, or OpenRouter — for chat/narrator; graph + extraction work without one).

Full install steps, troubleshooting, and Azure Foundry / enterprise gateway config: [docs/WORKBENCH.md](docs/WORKBENCH.md#install).

---

## Showcase — S8: FDA Product Labels

Seven FDA Structured Product Labels — Ozempic, Wegovy, Mounjaro (GLP-1 receptor agonists), Humira (TNF biologic), Gleevec (targeted oncology), Lipitor (statin), Jantoven (warfarin) — fetched from openFDA, ingested, graph built, epistemic layer analyzed, 1,579-word analyst briefing produced.

```bash
# Try it on the bundled S8 corpus (graph is committed in the repo)
/epistract:dashboard tests/corpora/08_fda_labels/output --domain fda-product-labels
```

Open http://127.0.0.1:8000 — interactive graph + dashboard + chat panel with the FDA regulatory intelligence persona. From the auto-generated briefing:

> **Boxed warnings**: *Adalimumab* carries a boxed warning for serious infections and malignancy; *Warfarin* has a boxed warning for major hemorrhage. (Established evidence tier.)
>
> **Drug-drug interactions**: *Warfarin* interactions with CYP2C9 inhibitors, NSAIDs, and antiplatelets; *Semaglutide* interactions with antidiabetic agents and gastric motility drugs. (Reported.)
>
> **Knowledge gaps**: missing pharmacokinetic data for *Semaglutide* in renal impairment; no mechanism-of-action detail for *Imatinib* in the generic label; absent pediatric / geriatric patient-population data for *Tirzepatide*. (Theoretical / Hypothesized.)
>
> **Bottom line**: the corpus contains robust boxed warnings and contraindications but is sparse on pharmacokinetic and patient-population data for newer agents. Formulary decisions should weigh the high-quality safety signals against the gaps in dosing guidance for special populations.

That's the FDA persona reading 7 SPL labels and synthesizing what a regulatory analyst would. The four-level FDA evidence-tier classification surfaces a structural difference flat KGs cannot: a drug's mechanism of action (theoretical), its post-marketing hemorrhage reports (reported), its RCT-cited efficacy (observed), and its boxed warning (established) all live in the same SPL document — and now sit as graph relations with different epistemic weights.

Full briefing, graph, extractions, validation: **[docs/SHOWCASE-FDA.md](docs/SHOWCASE-FDA.md)**.

---

## Pre-built domains

Four domains ship with the framework:

- **drug-discovery** — biomedical literature & patents · 6 scenarios validated (PICALM/Alzheimer's through GLP-1 CI)
- **clinicaltrials** — CT.gov protocols · 1 scenario validated · `--enrich` from CT.gov v2 + PubChem
- **fda-product-labels** — FDA SPL labels · 1 scenario validated · four-level FDA evidence-tier classifier
- **contracts** — event/vendor contract analysis · schema scaffold (bring your own corpus)

Full per-domain schemas, scenario coverage tables, validation history, and showcase artifacts (screenshots, briefings, interactive graphs): **[docs/DOMAINS.md](docs/DOMAINS.md)**.

To create a new domain from sample documents:

```bash
/epistract:domain --input ./sample-docs/ --name my-domain
```

The wizard reads your samples, proposes entity/relation types, asks about your analyst persona, and writes a complete domain package. Walk-through: [docs/ADDING-DOMAINS.md](docs/ADDING-DOMAINS.md).

---

## Commands

| Command | Purpose |
|---|---|
| `/epistract:setup` | Install Python dependencies + optional validation libs |
| `/epistract:acquire` | Fetch documents from PubMed (search + download) |
| `/epistract:ingest` | Extract entities + relations from a corpus, build graph |
| `/epistract:epistemic` | Run epistemic classification + analyst briefing |
| `/epistract:dashboard` | Launch the interactive workbench |
| `/epistract:export` | Dump graph to GraphML / GEXF / CSV / SQLite / JSON |
| `/epistract:domain` | Create a new domain from sample docs (wizard) |
| `/epistract:query` | Search/filter graph by entity name or type |
| `/epistract:ask` | One-shot natural-language Q&A over the graph |

Full reference + flags: [docs/COMMANDS.md](docs/COMMANDS.md).

---

## Documentation

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — pipeline, two-layer design, data formats
- [docs/DOMAINS.md](docs/DOMAINS.md) — per-domain schemas, scenarios, showcase artifacts
- [docs/COMMANDS.md](docs/COMMANDS.md) — full `/epistract:*` reference
- [docs/WORKBENCH.md](docs/WORKBENCH.md) — workbench usage, LLM provider config (Azure / Anthropic / OpenRouter), install troubleshooting
- [docs/ADDING-DOMAINS.md](docs/ADDING-DOMAINS.md) — domain wizard + manual creation
- [docs/PIPELINE-CAPACITY.md](docs/PIPELINE-CAPACITY.md) — formats, limits, what works and what doesn't
- [docs/known-limitations.md](docs/known-limitations.md) — current contracts + known gaps
- [DEVELOPER.md](DEVELOPER.md) — contributing, internals
- [CHANGELOG.md](CHANGELOG.md) — release notes

---

## Name

From Greek **episteme** (ἐπιστήμη) — structured scientific knowledge, the highest form of knowledge in Aristotle's epistemological hierarchy — combined with **extract**. Episteme is not opinion or belief; it is knowledge grounded in evidence, demonstration, and systematic understanding. That is what this tool produces: not a bag of keywords, but a structured representation of how concepts relate to each other, traceable to the source text, honest about what it does and does not know.

---

## License

MIT. See [LICENSE](LICENSE).
