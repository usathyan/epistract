# Known Limitations

This document records behavioral limits of the epistract pipeline that are deliberate design choices or deferred improvements. Cited by [PIPELINE-CAPACITY.md](PIPELINE-CAPACITY.md) — update here first, then let PIPELINE-CAPACITY.md quote values from this file rather than re-deriving them.

Each section is scoped to a subsystem. Add new sections as limitations are surfaced or deferred.

---

## Domain Wizard sample window (FIDL-05)

**Scope:** `core/domain_wizard.build_schema_discovery_prompt` — the Pass-1 prompt sent to the LLM once per sample document during `/epistract:domain` schema discovery.

**Source:** `.planning/phases/16-wizard-sample-window-beyond-8kb/16-CONTEXT.md` (D-01..D-09). Implemented in Phase 16 Plan 16-01.

### What the wizard sees

For each sample document, the wizard builds Pass-1 prompts using a length-conditional strategy:

- **Documents ≤ 12,000 characters** (`MULTI_EXCERPT_THRESHOLD`) — pass through as full text under the `**Document text:**` header. No truncation, no excerpt markers. This matches the pre-Phase-16 prompt shape for short samples.
- **Documents > 12,000 characters** — three excerpts totalling 12,000 characters:
  - **Head** — first 4,000 characters (`EXCERPT_CHARS`), annotated `[EXCERPT 1/3 — chars 0 to 4000 (head)]`.
  - **Middle** — 4,000-character slice centered on `len(doc) // 2`, annotated `[EXCERPT 2/3 — chars <m0> to <m1> (middle)]`. Explicit midpoint centering (not "second third") so the mid-body anchor lands correctly regardless of head-heavy intros or tail-heavy conclusions.
  - **Tail** — last 4,000 characters, annotated `[EXCERPT 3/3 — chars <t0> to <end> (tail)]`.

  The excerpts are introduced with the preface: "The following are three excerpts from a larger document. Treat them as non-contiguous samples of the same document, not as a single continuous passage." The markers and preface together prevent the LLM from confabulating structural continuity between disjoint slices.

### What the wizard does NOT see

- **Shoulder regions** — for very long documents, the chars between ~4,000 and the start of the middle slice (e.g., chars 4000..len//2-2000), and between the end of the middle slice and the start of the tail (e.g., chars len//2+2000..len-4000), are NEVER sent in a Pass-1 call. An entity type that appears only in a "shoulder region" of a single document will not be proposed from that document. Mitigation: Pass-2 consolidation across multiple documents often surfaces shoulder-region vocabulary from at least one other sample with overlapping coverage.
- **Very long tails beyond 4KB** — the last 4,000 characters are the full tail budget. A 200KB patent's claims section at chars 190,000..200,000 is captured; a 600KB legal compendium's chars 500,000..596,000 region is not.
- **Summarization** — no summarizer pass; excerpts are raw character slices. Deferred — see `16-CONTEXT.md` §deferred item 1.

### Why no sliding-window or summarize-then-analyze

- **Sliding-window (N calls/doc)** — rejected for Phase 16. N× the token cost for a marginal per-doc coverage gain that Pass-2 cross-document dedupe already supplies. See `16-CONTEXT.md` §specifics "Multi-excerpt over sliding-window…".
- **Summarize-then-analyze** — deferred. Adds a summarizer pass and opens the "what is a good summary for schema discovery" question; revisit in v3.x if multi-excerpt proves insufficient for specific corpora.

### Token cost (measured 2026-04-21)

- **Input tokens per Pass-1 call (measured on the `long_contract.txt` fixture, 60,200 chars, 2026-04-21):** 2631 input tokens. Method: tiktoken cl100k_base. Soft budget 24,000 tokens → headroom ≈ 9× the measured cost.
- **Soft budget:** ~24,000 input tokens per call. Headroom: ~9× the measured value (2631 tokens measured 2026-04-21). No runtime enforcement — the wizard is user-invoked and cost escalations are user-visible.
- **Rationale for no enforcement:** `16-CONTEXT.md` §deferred item 3 (runtime budget would require injecting tiktoken into the critical path; out of scope for v3.0).

### Pass-2 / Pass-3 impact

None. Pass-2 (consolidation, `build_consolidation_prompt`) and Pass-3 (final schema, `build_final_schema_prompt`) are byte-identical to the pre-Phase-16 implementation. They consume the richer Pass-1 candidate lists without format changes. See `16-CONTEXT.md` D-07.

### Acceptance gate

Phase 16's acceptance is prompt-level, not LLM-level: for the synthetic fixture `tests/fixtures/wizard_sample_window/long_contract.txt` (~60,000 chars with three sentinel phrases placed in head / middle / tail), the prompt built by `build_schema_discovery_prompt` contains all three sentinels verbatim (`PARTY_SENTINEL_HEAD`, `OBLIGATION_SENTINEL_MIDDLE`, `TERMINATION_SENTINEL_TAIL`) plus all three `[EXCERPT N/3 — ...]` markers. See `tests/TEST_REQUIREMENTS.md` UT-043 and FT-016.

### Related

- `core/domain_wizard.EXCERPT_CHARS` — 4,000.
- `core/domain_wizard.MULTI_EXCERPT_THRESHOLD` — 12,000.
- `core/domain_wizard._build_excerpts` — pure slice helper.
- Phase 20 README "Pipeline Capacity & Limits" section consumes the values in this section.

---

## Domain awareness propagation (FIDL-06)

**Scope:** How the domain selected at build time (`/epistract:ingest --domain <name>`) propagates to every downstream consumer — workbench server, chat system prompt, standalone `graph.html` viewer, `/epistract:dashboard` skill — so that a contracts graph shows contracts branding and a drug-discovery graph shows drug-discovery branding, without the user passing `--domain` again at each consumer.

**Source:** `.planning/phases/17-domain-awareness-in-consumers/17-CONTEXT.md` (D-01..D-16). Implemented in Phase 17 Plans 17-01 + 17-02.

### Single source of truth

`graph_data.json.metadata.domain: str | None` — written by `core.run_sift.cmd_build` after sift-kg's `run_build` emits the file. This is the ONE place the domain name is persisted post-build. Every consumer reads from here.

- `null` value: user built without `--domain` flag (generic build). Consumers fall back to their generic defaults.
- Missing key entirely: legacy graph (built before Phase 17). Consumers fall back with a one-shot stderr warning pointing to `/epistract:ingest --domain <name>`.

### Precedence rule

Consumers resolve the effective domain via `examples.workbench.template_loader.resolve_domain(output_dir, explicit_domain)`:

1. **Explicit arg wins** — if the caller passes `--domain <name>`, that value is used regardless of metadata. Rationale: experimenting with a contracts graph under the drug-discovery template should be possible without rebuilding.
2. **Metadata fallback** — when no explicit arg, read `graph_data.json.metadata.domain`.
3. **Generic fallback** — when neither present, fall through to `template_loader.GENERIC_TEMPLATE` and emit a one-shot warning.

The `resolve_domain` helper returns a `(resolved_domain: str | None, source: str)` tuple; `source` is `"explicit" | "metadata" | "fallback"` for debugging and banner display.

### Propagation points

- **Workbench server (`examples/workbench/server.py::create_app`)** — calls `resolve_domain` then `load_template`; `GET /api/template` returns the resolved template.
- **Launcher (`scripts/launch_workbench.py`)** — calls `resolve_domain` for the console banner (so users can see which source won); passes the raw `--domain` into `create_app` (which re-resolves — the helper is idempotent).
- **Standalone graph viewer (`core/run_sift.py::cmd_view`)** — post-processes `graph.html` to replace the empty `<h1></h1>` with `<h1>{domain title}</h1>` and append a `<script>` block that overlays `template.yaml:entity_colors` onto vis.js nodes on DOMContentLoaded.
- **Chat system prompt (`examples/workbench/system_prompt.py::build_system_prompt`)** — reads `template.analysis_patterns.cross_references_heading` (and `appears_in_phrase`) to customize the cross-references section for the domain. Contracts uses "CROSS-CONTRACT REFERENCES"; drug-discovery uses "CROSS-STUDY REFERENCES".

### Legacy-graph behavior (D-08)

Graphs built before Phase 17 have no `metadata.domain` key. When such a graph is opened:
- Workbench: falls back to the generic `Knowledge Graph Explorer` template with a one-shot stderr warning.
- `graph.html`: gets `<h1>Knowledge Graph</h1>` (generic) and keeps sift-kg's default entity palette (no overlay).
- Chat system prompt: keeps the hardcoded "CROSS-CONTRACT REFERENCES" (the pre-Phase-17 behavior) with a one-shot stderr warning.

No migration script is provided — users rebuild their graphs to get the new metadata. Rebuilds are fast enough (typically < 1 minute for a 60-doc corpus) that a migration script would cost more than it saves.

### What propagation does NOT do

- **No live chat re-parse** — if `template.yaml:analysis_patterns` changes, users must restart the workbench to pick it up. The template is loaded once at `create_app` time.
- **No browser-side fetch of metadata** — `graph.html` reads nothing from the network; the `<h1>` and color overlay are baked into the HTML at `cmd_view` time.
- **No per-user overrides** — the template is per-domain, not per-user. Future scope.
- **No DomainContext object** — explicitly rejected in 17-CONTEXT.md §deferred item 1. The metadata-field approach is simpler and covers the current consumer set; revisit if a second cross-cutting field (e.g., `ocr_mode`, `extensions`) needs the same propagation.

### Acceptance gate

- UT-044 (cmd_build writes metadata.domain)
- UT-045 (resolve_domain precedence — explicit > metadata > fallback, 4 branches)
- UT-046 (build_system_prompt reads analysis_patterns with fallback + warning)
- FT-018 (end-to-end: stub contracts graph + stub drug-discovery graph → GET /api/template returns the right template; D-09 explicit-beats-metadata; D-08 legacy fallback)

### Related

- `core/run_sift.cmd_build` — persists metadata.domain.
- `core/run_sift.cmd_view` — post-processes graph.html with domain title + entity colors.
- `examples/workbench/template_loader.resolve_domain` — precedence resolver.
- `examples/workbench/template_schema.AnalysisPatterns` — Pydantic model for domain-specific chat vocabulary.
- `domains/contracts/workbench/template.yaml:analysis_patterns` — "CROSS-CONTRACT REFERENCES".
- `domains/drug-discovery/workbench/template.yaml:analysis_patterns` — "CROSS-STUDY REFERENCES".
- Phase 20 README "Pipeline Capacity & Limits" section cites this doc for the domain-awareness propagation contract.

---

## Per-Domain Extensibility (FIDL-07)

**Scope:** Two opt-in extension points let domains ship richer analysis without touching core: (1) custom epistemic rules as `CUSTOM_RULES: list[callable]` in each domain's `epistemic.py`, and (2) optional post-extraction validators as `domains/<name>/validation/run_validation.py`. Also: the drug-discovery domain's `epistemic.py` recognizes a `"structural"` doc type for crystallography / cryo-EM / X-ray papers.

**Source:** `.planning/phases/18-per-domain-epistemic-and-validator-extensibility/18-CONTEXT.md` (D-01..D-19). Implemented in Phase 18 Plans 18-01 (infrastructure + UT-047/UT-048/UT-050) and 18-02 (structural doctype + wizard stub + UT-049/FT-019).

### CUSTOM_RULES contract

Each rule is a module-level callable in `domains/<name>/epistemic.py`:

```python
def my_rule(nodes: list[dict], links: list[dict], context: dict) -> list[dict]:
    """Return a list of finding dicts."""
    return [{"rule_name": "my_rule", "type": "example",
             "severity": "INFO", "description": "x", "evidence": {}}]

CUSTOM_RULES: list = [my_rule]
```

- **Context dict keys:** `output_dir: Path`, `graph_data: dict`, `domain_name: str`.
- **Finding shape:** at minimum `{rule_name, type, severity, description, evidence}`. The `rule_name` is the key under which findings merge into `claims_layer["super_domain"]["custom_findings"]`.
- **Execution order = list order.** No dependency graph. Rules that need ordering must assemble themselves in the list.
- **Rule-failure isolation:** each rule is wrapped in `try/except Exception`. A raising rule does NOT abort the phase; instead its slot records `[{rule_name, status: "error", error: str(e)}]` and iteration continues. One bad rule cannot break the layer.
- **Backward-compat:** domains without a `CUSTOM_RULES` attribute produce byte-identical `claims_layer.json` — the `custom_findings` key is omitted entirely, not set to an empty dict (D-07). Legacy contracts and drug-discovery graphs are untouched.

### validation_dir discovery

`core.domain_resolver.get_validation_dir(domain_name) -> Path | None` locates a domain's validator directory. It returns the path iff:
1. `domains/<name>/validation/` exists as a directory, AND
2. `domains/<name>/validation/run_validation.py` exists inside it.

Missing either condition → `None`. Missing-is-silent: no warning is logged when a domain has no validator (absence is not a warning condition — D-08).

### validation_report.json semantics

`core.run_sift.cmd_build`, after community labeling, checks `resolve_domain(domain_name)["validation_dir"]`. If non-None, it dynamically loads `run_validation.py` via `importlib.util.spec_from_file_location`, calls `run_validation(output_dir) -> dict`, and writes the dict to `<output_dir>/validation_report.json`.

- **Failure is non-fatal (D-04):** any exception during load or call writes `{"status": "error", "error": str(e), "domain": <name>}` and `cmd_build` continues. Build health > validator health.
- **Skip semantics:** when optional validator deps are missing (e.g., RDKit for drug-discovery), the validator can return `{"status": "skipped", "reason": "..."}` — both `"ok"` and `"skipped"` are normal outcomes.
- **Absent validator:** no `validation_report.json` is written; no warning.

### Structural doctype (drug-discovery only for v3.0)

`domains/drug-discovery/epistemic.py:infer_doc_type` and its sibling in `core/label_epistemic.py` both recognize a `"structural"` doc type. Signals:

- **Document ID prefix:** `PDB_PATTERN = re.compile(r"^pdb[_-]", re.I)` — matches `pdb_1abc`, `pdb-7XYZ`, etc. Checked FIRST in `infer_doc_type` so a hypothetical ambiguous ID like `pdb_pmid_*` classifies as structural.
- **Content keywords** (first 800 chars of evidence, lowercased): `"crystal structure"`, `"x-ray crystallograph"`, `"cryo-em"`, `"electron microscop"`.
- **Resolution regex:** `\b\d+(?:\.\d+)?\s*(?:Å|angstrom)\b` (case-insensitive) — matches `2.1 Å`, `3 angstrom`, etc.

The content-signal helper `_detect_structural_content(evidence)` is exposed at module level for rule authors who want to short-circuit doctype classification when the document ID is generic (e.g., a PMID paper whose body is a crystal-structure report). It is NOT called in the main dispatch path; rule authors opt in by importing.

### High-confidence structural short-circuit

`classify_epistemic_status(evidence, confidence, doc_type)` treats structural papers as evidence-grade: when `doc_type == "structural"` AND `confidence >= 0.9`, the function returns `"asserted"` BEFORE the hedging pattern scan (D-06). Crystallography reports literal coordinates, not hypotheses — hedging-regex false positives like "hypothesized structure" should not downgrade a high-confidence structural claim. Below 0.9, structural claims fall through to normal hedging detection.

### Two-site convention sync

The `PDB_PATTERN`, `STRUCTURAL_CONTENT_RE`, `_detect_structural_content` helper, `infer_doc_type` branch, and `classify_epistemic_status` short-circuit live in TWO modules: `domains/drug-discovery/epistemic.py` and `core/label_epistemic.py`. These are convention-synchronized siblings — **no shared import** (D-05). Each future structural signal must be added to BOTH sites. UT-049 asserts identical behavior across both modules so any drift is caught.

### Wizard default

`core/domain_wizard.generate_epistemic_py` now emits a no-op `CUSTOM_RULES: list = []` stub + 6-line example comment (D-10). New domains opt in by uncommenting and implementing. Wizard does NOT create a `validation/` directory by default (D-11 — too opinionated; domain authors decide).

### What extensibility does NOT do

- **No remote/dynamic rule loading** — `CUSTOM_RULES` is a plain Python list in `epistemic.py`, not a URL/plugin registry. Deferred indefinitely.
- **No YAML-driven rule DSL** — Python callables are strictly more powerful; revisit only if non-engineers author rules.
- **No rule dependency graph** — execution order = list order. Cross-rule dependencies deferred.
- **No validator schema enforcement** — `validation_report.json` is a loose dict contract; formalize if/when Phase 20 needs structured parsing.
- **No workbench UI for custom findings** — deferred to Phase 20 or later.
- **Structural doctype is drug-discovery-only for v3.0** — contracts and wizard-generated domains get the hook points (CUSTOM_RULES + validator discovery) but not the structural signals. Adding structural-doctype to another domain requires mirroring PDB_PATTERN + content helpers + short-circuit into that domain's `epistemic.py`.

### Acceptance gate

- UT-047 (CUSTOM_RULES dispatch merges findings — Plan 18-01)
- UT-048 (get_validation_dir returns Path for drug-discovery, None otherwise — Plan 18-01)
- UT-049 (structural doctype detection in both modules — Plan 18-02)
- UT-050 (rule-failure isolation — Plan 18-01)
- FT-019 (end-to-end: baseline invariance + structural propagation + validator report — Plan 18-02)

### Related

- `core/domain_resolver.get_validation_dir` — validator discovery.
- `core/label_epistemic.analyze_epistemic` — CUSTOM_RULES iteration.
- `core/run_sift.cmd_build` — post-build validator dispatch.
- `domains/drug-discovery/validation/run_validation.py` — convention entry example.
- `domains/drug-discovery/epistemic.py:PDB_PATTERN` — structural signal.
- `core/label_epistemic.py:PDB_PATTERN` — two-site sync sibling.
- `core/domain_wizard.generate_epistemic_py` — emits CUSTOM_RULES stub for new domains.
- Phase 20 README "Pipeline Capacity & Limits" section cites this doc.

## Wizard & CLI Ergonomics (FIDL-08)

**Scope:** Four bundled polish fixes surfaced during the axmp-compliance build that share a "ergonomics-of-authoring" root cause: (1) safe slugification for wizard-generated domain directory names; (2) wizard auto-emission of `workbench/template.yaml` for new domains; (3) `run_sift.py build --domain` accepting either a name OR a path to `domains/<name>/domain.yaml`; (4) `/epistract:domain --schema <file.json> --name <slug>` flag bypassing the 3-pass LLM discovery entirely.

**Source:** `.planning/phases/19-wizard-and-cli-ergonomics/19-CONTEXT.md` (D-01..D-22). Implemented in Phase 19 Plans 19-01 (slug helper + workbench template emission + UT-051/UT-052) and 19-02 (`--domain` path shim + `--schema` bypass + UT-053/UT-054/FT-020).

### generate_slug rules

`core.domain_wizard.generate_slug(name: str) -> str` normalizes a human-readable domain name into a safe filesystem directory name. Pipeline:

1. **NFKD normalize + ASCII strip**: `unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")` — removes accents and non-Latin characters without transliteration.
2. **Lowercase.**
3. **Collapse non-alphanumeric runs**: every run of characters outside `[a-z0-9]` becomes a single `-` via `re.sub(r"[^a-z0-9]+", "-", value)`.
4. **Strip leading/trailing `-`.**
5. **Collapse residual `--+`** (belt-and-suspenders defensive pass).
6. **Reject empty or malformed** results: `ValueError(f"Cannot derive slug from: {name!r}")`.

**Examples:**
- `generate_slug("Q&A Analysis (v2)")` → `"q-a-analysis-v2"`
- `generate_slug("  Hello World  ")` → `"hello-world"`
- `generate_slug("drug-discovery")` → `"drug-discovery"` (byte-identity for existing clean inputs)
- `generate_slug("contracts")` → `"contracts"` (byte-identity)
- `generate_slug("中文 Analysis")` → `"analysis"` (CJK stripped, Latin preserved)
- `generate_slug("")` → `ValueError`
- `generate_slug("中文")` → `ValueError` (pure non-Latin input yields empty after stripping)

### Deterministic palette rotation for entity_colors

`core.domain_wizard.generate_workbench_template(domain_slug, entity_types)` emits `workbench/template.yaml` with one palette color per entity type. Assignment is deterministic:

1. Sort entity type names alphabetically.
2. Assign `DEFAULT_ENTITY_COLORS[i % len(DEFAULT_ENTITY_COLORS)]` for `i = 0..N-1`.

The palette (12 vis.js-friendly colors):
```python
DEFAULT_ENTITY_COLORS = [
    "#97c2fc", "#ffa07a", "#90ee90", "#f1c40f",
    "#e74c3c", "#9b59b6", "#1abc9c", "#e67e22",
    "#34495e", "#fd79a8", "#636e72", "#00b894",
]
```

The emitted YAML is a complete override of the Phase 17 `WorkbenchTemplate` Pydantic model (every field populated), so downstream consumers never fall back to defaults.

### --domain path shim

`core.run_sift.resolve_domain_arg(value)` accepts either a bare domain name OR a path to a `domains/<name>/domain.yaml` file. Rules:

- **Bare name** (no `/`, no `.yaml`) → passthrough unchanged. The filesystem is never touched (D-08 explicit non-ambiguity — domain names ending in `.yaml` are unsupported by this rule).
- **Path inside `DOMAINS_DIR`** matching `<DOMAINS_DIR>/<name>/domain.yaml` → extracts and returns `<name>`.
- **Path outside `DOMAINS_DIR`** → stderr error `Error: --domain expects a name registered under domains/, not an arbitrary path. Try --domain <inferred_name> after registering the domain.` followed by `sys.exit(1)`.

The explicit error (rather than silent path inference) teaches the user the name-not-path contract.

### --schema bypass flag

`python -m core.domain_wizard --schema <file.json> --name <slug>` skips the 3-pass LLM discovery entirely and calls `generate_domain_package` directly.

- **Required CLI flags:** `--schema <file>` and `--name <slug>`. Missing `--name` → error and exit non-zero (no sample corpus to derive a name from).
- **Required schema keys:** `entity_types` (dict) and `relation_types` (dict). Missing or wrong type → error and exit non-zero with the key listed.
- **Optional schema keys:** `description`, `system_context`, `extraction_guidelines`, `contradiction_pairs`, `gap_target_types`, `confidence_thresholds`. All default to sensible stubs.
- **No LLM guarantee:** the bypass does NOT import LiteLLM. UT-054 asserts this by monkeypatching `sys.modules["litellm"] = None` — if the bypass accidentally takes the 3-pass path, the test fails.

### Non-Latin input handling

Domain names containing non-Latin characters (CJK, Cyrillic, Arabic, etc.) are handled by NFKD + ASCII-ignore: accents stripped, base Latin letters preserved. Pure non-Latin input (e.g., `中文` with no Latin letters) yields an empty slug and raises `ValueError` — no transliteration is performed (pinyin/romaji/etc. are deferred).

Mixed Latin + non-Latin (`"中文 Analysis"`) yields just the Latin portion (`"analysis"`).

### What FIDL-08 does NOT do

- **Non-Latin transliteration** (CJK → pinyin, Cyrillic → Latin) — library dependency not justified for v3.0. Deferred.
- **Interactive slug conflict resolver** (e.g., "slug 'foo' exists; use 'foo-2'?") — out of scope. Domain name collisions error out; user re-runs with a different name.
- **`--schema` hybrid mode** (partial schema + LLM consolidation of missing pieces) — no clear use case. Bypass is all-or-nothing.
- **Workbench theming beyond entity_colors + analysis_patterns** (fonts, logos, custom CSS) — Phase 20 or later.
- **CLI redesign** (replace ad-hoc `sys.argv` parsing with argparse/click) — existing parsing works; out of scope.

### Acceptance gate

- UT-051 (`generate_slug` edge cases — Plan 19-01)
- UT-052 (`generate_workbench_template` WorkbenchTemplate-valid YAML — Plan 19-01)
- UT-053 (`resolve_domain_arg` path shim — Plan 19-02)
- UT-054 (`--schema` bypass, LLM-free — Plan 19-02)
- FT-020 (end-to-end wizard `--schema` → valid domain package — Plan 19-02)

### Related

- `core.domain_wizard.generate_slug` — slugifier primitive.
- `core.domain_wizard.generate_workbench_template` — workbench/template.yaml emitter.
- `core.domain_wizard.main` — `--schema` bypass entry point.
- `core.run_sift.resolve_domain_arg` — `--domain` path shim.
- `examples.workbench.template_schema.WorkbenchTemplate` — Pydantic contract validated by UT-052 and FT-020.
- `commands/domain.md §Schema Bypass` — user-facing docs for the `--schema` flag.
- Phase 20 README "Pipeline Capacity & Limits" section will cite this doc.

---

*Last updated: 2026-04-22 — FIDL-08 Phase 19 complete (Wizard & CLI Ergonomics); FIDL-07, FIDL-06, FIDL-05 entries preserved.*
