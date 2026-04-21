# Known Limitations

This document records behavioral limits of the epistract pipeline that are deliberate design choices or deferred improvements. It is cited by the Phase 20 README "Pipeline Capacity & Limits" section — update here first, then let Phase 20 quote values from this file rather than re-deriving them.

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

*Last updated: 2026-04-21 — Phase 17 FIDL-06 (Domain Awareness in Consumers) added; Phase 16 FIDL-05 entry preserved.*
