# Pre-built Domains

Epistract ships with four domains out of the box. Each is a self-contained package under `domains/<name>/` — a `domain.yaml` schema, a `SKILL.md` extractor instruction file, an `epistemic.py` rules file, and a workbench template (chat persona + narrator persona + entity colors). Adding a new domain takes ~15 minutes via `/epistract:domain` (see [ADDING-DOMAINS.md](ADDING-DOMAINS.md)).

## Domain coverage at a glance

| Domain | Schema | Scenarios validated | Specialty pipeline | Use cases |
|---|---|---|---|---|
| **drug-discovery** | 13 entity / 22 relation types | **6 scenarios** — [S1 PICALM / Alzheimer's](../tests/scenarios/scenario-01-picalm-alzheimers-v2.md) (target validation, 183 nodes / 478 edges) · [S2 KRAS G12C](../tests/scenarios/scenario-02-kras-g12c-landscape-v2.md) (CI, 140 / 432) · [S3 Rare Disease](../tests/scenarios/scenario-03-rare-disease-v2.md) (due diligence, 110 / 278) · [S4 Immuno-oncology](../tests/scenarios/scenario-04-immunooncology-v2.md) (combinations, 151 / 440) · [S5 Cardiovascular](../tests/scenarios/scenario-05-cardiovascular-v2.md) (cardiology, 90 / 245) · **[S6 GLP-1 CI](../tests/scenarios/scenario-06-glp1-landscape-v2.md)** (V3 rebuild, 278 / 855, full narrator briefing — see [SHOWCASE-GLP1](SHOWCASE-GLP1.md)) | RDKit + Biopython molecular validation; prophetic-claim detection from patents; structural-biology doctype short-circuit | Biomedical literature, patents, clinical trial reports — competitive intelligence, target validation, regulatory / adverse-event capture |
| **clinicaltrials** | 12 / 10 | **1 scenario** — **[S7 GLP-1 Phase 3 Trials](../tests/scenarios/scenario-07-clinicaltrials-glp1-phase3.md)** (10 CT.gov protocols, 142 / 395, post-`--enrich` 177 high-evidence relations — see [SHOWCASE-CLINICALTRIALS](SHOWCASE-CLINICALTRIALS.md)) | Phase-based evidence grading (Phase 3 + N≥300 → high; Phase 2 → medium; Phase 1 / observational → low); optional `--enrich` from CT.gov v2 + PubChem PUG REST | ClinicalTrials.gov protocols + IRB submissions + clinical study reports — NCT capture, blinding/enrollment signals, head-to-head comparison framing |
| **fda-product-labels** | 17 / 16 | **1 scenario** — **[S8 FDA Product Labels](../tests/scenarios/scenario-08-fda-product-labels.md)** (7 SPL labels, 81 nodes / 149 edges, 1,579-word narrator briefing — see [SHOWCASE-FDA](SHOWCASE-FDA.md)) | Four-level FDA evidence-tier classifier (`established` / `observed` / `reported` / `theoretical`), in addition to the v3 epistemic vocabulary | FDA Structured Product Labeling (SPL) — drug products, indications, contraindications, boxed warnings, drug interactions, pharmacovigilance, lab-test monitoring |
| **contracts** | 11 / 11 | **0 scenarios** — schema scaffold; [showcase walk-through](showcases/contracts.md) describes the persona; bring your own corpus | Cross-contract conflict detection, obligation gap scoring, risk indicators, SLA / force-majeure reasoning | Event / vendor contract analysis, procurement portfolio review, legal due diligence |

**Reading the table.** *Schema* is the static shape — entity types and relation types declared once. *Scenarios validated* is the track record — how much real-world corpus the domain has actually been run against, and how many narrator briefings have surfaced refinements that contributors folded back into the domain config. A domain with six scenarios has had its persona, epistemic rules, and entity-type coverage exercised against varied source material; one with zero is a schema waiting for its first run. The framework itself doesn't auto-learn across scenarios today — refinements are human-mediated. ([Issue #15](https://github.com/usathyan/epistract/issues/15) tracks an aspirational cross-scenario knowledge persistence layer.)

All four live in `domains/` as self-contained packages — schemas are human-readable YAML; inspect any of `domains/drug-discovery/domain.yaml`, `domains/contracts/domain.yaml`, `domains/clinicaltrials/domain.yaml`, or `domains/fda-product-labels/domain.yaml`. To start a new scenario on an existing domain, just run `/epistract:ingest <your-corpus> --domain <name>` — no schema work needed.

---

## Community-maintained domains

These domains are maintained on community forks and don't ship with the framework yet. Install by checking out the fork.

| Domain | Schema | Source |
|---|---|---|
| **pharmacovigilance** | 10 entity / 11 relation types | [chrisdavidson/epistract `feat/pharmacovigilance-domain`](https://github.com/chrisdavidson/epistract/tree/feat/pharmacovigilance-domain/domains/pharmacovigilance) ([PR #5](https://github.com/chrisdavidson/epistract/pull/5)) — adverse-event reports (FAERS / VAERS / MedWatch) with Bradford-Hill causality vocabulary, MedDRA Preferred Term + WHO ATC nomenclature, reporter-type confidence calibration (HCP > consumer > lawyer), and a `scripts/fetch_faers_corpus.py` for fetching reports from the FDA OpenFDA API. |

---

## Showcase artifacts

### drug-discovery — S6 GLP-1 Competitive Intelligence

34 documents (10 patents + 24 PubMed abstracts) → 278 nodes, 855 edges, 61 prophetic claims, 1,166-word narrator briefing.

- **Showcase doc:** [`SHOWCASE-GLP1.md`](SHOWCASE-GLP1.md)
- **Auto-generated analyst briefing:** [`tests/corpora/06_glp1_landscape/output-v3/epistemic_narrative.md`](../tests/corpora/06_glp1_landscape/output-v3/epistemic_narrative.md)
- **Workbench screenshots:** [dashboard panel](screenshots/workbench-01-dashboard.png) · [chat welcome](screenshots/workbench-02-chat-welcome.png) · [graph panel](screenshots/workbench-03-graph-glp1.png) · [chat on prophetic claims](screenshots/workbench-04-chat-epistemic.png)
- **Interactive graph** (clone + open locally): [`tests/corpora/06_glp1_landscape/output-v3/graph.html`](../tests/corpora/06_glp1_landscape/output-v3/graph.html)
- **Scenario history (V1 → V2 → V3):** [`tests/scenarios/scenario-06-glp1-landscape-v2.md`](../tests/scenarios/scenario-06-glp1-landscape-v2.md)
- **V2 scenario gallery (S1–S5 screenshots from regression validation):** [S1 PICALM](../tests/scenarios/screenshots/scenario-01-graph-v2.png) · [S2 KRAS G12C](../tests/scenarios/screenshots/scenario-02-graph-v2.png) · [S3 Rare Disease](../tests/scenarios/screenshots/scenario-03-graph-v2.png) · [S4 Immuno-oncology](../tests/scenarios/screenshots/scenario-04-graph-v2.png) · [S5 Cardiovascular](../tests/scenarios/screenshots/scenario-05-graph-v2.png) · [S6 GLP-1](../tests/scenarios/screenshots/scenario-06-graph-v2.png)

### clinicaltrials — S7 GLP-1 Phase 3 Landscape

10 CT.gov protocols (SURPASS, SURMOUNT, STEP, PIONEER, SUSTAIN, ACHIEVE) → 142 nodes, 395 edges, 1,197-word narrator briefing.

- **Showcase doc:** [`SHOWCASE-CLINICALTRIALS.md`](SHOWCASE-CLINICALTRIALS.md)
- **Auto-generated analyst briefing:** [`tests/corpora/07_glp1_phase3_trials/output/epistemic_narrative.md`](../tests/corpora/07_glp1_phase3_trials/output/epistemic_narrative.md)
- **Workbench screenshots:** [dashboard panel](screenshots/clinicaltrials-01-dashboard.png) · [chat welcome](screenshots/clinicaltrials-02-chat-welcome.png) · [graph panel](screenshots/clinicaltrials-03-graph.png) · [chat on trial interventions](screenshots/clinicaltrials-04-chat-epistemic.png)
- **Interactive graph** (clone + open locally): [`tests/corpora/07_glp1_phase3_trials/output/graph.html`](../tests/corpora/07_glp1_phase3_trials/output/graph.html)
- **Scenario doc:** [`tests/scenarios/scenario-07-clinicaltrials-glp1-phase3.md`](../tests/scenarios/scenario-07-clinicaltrials-glp1-phase3.md)
- **Raw corpus:** [`tests/corpora/07_glp1_phase3_trials/docs/`](../tests/corpora/07_glp1_phase3_trials/docs/) (10 NCT protocol files)

### fda-product-labels — S8 FDA Product Labels

7 SPL labels (Ozempic, Wegovy, Mounjaro, Humira, Gleevec, Lipitor, Jantoven) → 81 nodes, 149 edges, 1,579-word narrator briefing. Four-level FDA evidence-tier classifier (new in v3.2).

- **Showcase doc:** [`SHOWCASE-FDA.md`](SHOWCASE-FDA.md)
- **Auto-generated analyst briefing:** [`tests/corpora/08_fda_labels/output/epistemic_narrative.md`](../tests/corpora/08_fda_labels/output/epistemic_narrative.md)
- **Workbench screenshots:** [dashboard panel](screenshots/fda-labels-01-dashboard.png) · [chat welcome](screenshots/fda-labels-02-chat-welcome.png) · [graph panel](screenshots/fda-labels-03-graph.png) · [chat on epistemic](screenshots/fda-labels-04-chat-epistemic.png)
- **Interactive graph** (clone + open locally): [`tests/corpora/08_fda_labels/output/graph.html`](../tests/corpora/08_fda_labels/output/graph.html)
- **Scenario doc:** [`tests/scenarios/scenario-08-fda-product-labels.md`](../tests/scenarios/scenario-08-fda-product-labels.md)
- **Raw corpus:** [`tests/corpora/08_fda_labels/docs/`](../tests/corpora/08_fda_labels/docs/) (7 SPL label files)
- **Domain package:** [`domains/fda-product-labels/`](../domains/fda-product-labels/) — 17 entity types, 16 relation types, hand-tailored senior FDA regulatory intelligence analyst persona
- **Four-level FDA evidence-tier classifier:** [`domains/fda-product-labels/epistemic.py`](../domains/fda-product-labels/epistemic.py) — `established` (boxed warnings, contraindications, RCT evidence) / `observed` (clinical-trial efficacy, dosing) / `reported` (post-marketing adverse events, pharmacovigilance signals) / `theoretical` (mechanism, in-vitro predictions). Populated alongside the v3-standard `epistemic_status` field.

### contracts — schema scaffold

No bundled corpus graph in the public repo — the contracts domain is designed for private legal / procurement work.

- **Showcase walk-through:** [`docs/showcases/contracts.md`](showcases/contracts.md)
- **Domain package:** [`domains/contracts/`](../domains/contracts/) — schema, SKILL.md, epistemic.py, workbench template with a worked 57-document persona
- **Run on your own corpus:** `/epistract:ingest <your-contract-corpus> --domain contracts`

> *GitHub renders `.html` files as source, not interactive pages — clone the repo and open the `graph.html` links locally in a browser to interact with the force-directed graphs.*

---

## Adding a new domain

A domain is 11–17 entity types and 10–22 relation types defined in YAML, plus a persona string and an epistemic rules file. No pipeline code changes required.

```bash
/epistract:domain --input ./sample-docs/ --name my-domain
```

The wizard runs a 3-pass LLM schema discovery against your sample documents, proposes entity types and relation types with confidence scores, asks about your analyst persona (the voice the chat panel and narrator will use), and writes a complete domain package to `domains/my-domain/`.

Full walk-through, including manual schema creation and the `--schema` reproducibility path: **[ADDING-DOMAINS.md](ADDING-DOMAINS.md)**.
