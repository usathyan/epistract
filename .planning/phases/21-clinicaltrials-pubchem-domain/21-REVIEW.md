---
phase: 21-clinicaltrials-pubchem-domain
reviewed: 2026-04-18T12:00:00Z
depth: standard
files_reviewed: 12
files_reviewed_list:
  - commands/ingest.md
  - commands/acquire.md
  - commands/build.md
  - commands/validate.md
  - commands/ask.md
  - commands/query.md
  - commands/export.md
  - commands/view.md
  - commands/setup.md
  - commands/domain.md
  - commands/epistemic.md
  - commands/dashboard.md
findings:
  critical: 0
  warning: 4
  info: 4
  total: 8
status: issues_found
---

# Phase 21: Code Review Report — Command Usage Guard Audit

**Reviewed:** 2026-04-18T12:00:00Z
**Depth:** standard
**Files Reviewed:** 12
**Status:** issues_found

## Summary

This review focuses on the `## Usage Guard` sections added (or updated) across all 12
`commands/*.md` files in Phase 21, with attention to:

1. Whether each command uses the correct guard variant — **guard-and-stop** (for commands
   that require at least one argument) vs **orientation-only** (for commands that are valid
   with no arguments).
2. Accuracy and completeness of documented flags and defaults.
3. Whether `--enrich` is documented in `ingest.md`.
4. Cross-file consistency of pattern, tone, and wording.

**Guard variant classification (correct vs not):**

| File | Guard Variant | Correct? |
|---|---|---|
| ingest.md | guard-and-stop (no args or --help) | Yes |
| acquire.md | guard-and-stop (no args or --help) | Yes |
| build.md | guard-and-stop (no args or --help) | Yes |
| validate.md | guard-and-stop (no args or --help) | Yes |
| ask.md | guard-and-stop (no args or --help) | Yes |
| query.md | guard-and-stop (no args or --help) | Yes |
| export.md | guard-and-stop (**no format argument** or --help) | **Warning — non-standard wording** |
| view.md | orientation-only (--help only) | Yes — no args is valid |
| setup.md | orientation-only (no stop instruction) | Yes — no args is valid |
| domain.md | orientation-only (--help only, otherwise start wizard) | Yes — no args is valid |
| epistemic.md | guard-and-stop (no args or --help) | Yes |
| dashboard.md | guard-and-stop (no args or --help) | Yes |

Overall, the guard variant choices are correct. Four issues were found: a non-standard
trigger phrase in `export.md`, a missing `--enrich` entry in `ingest.md`'s `## Arguments`
section, a persona/examples mismatch in `ask.md`, and a `<output-dir>` positional that
appears under `Options:` in `query.md`.

---

## Warnings

### WR-01: `export.md` guard trigger says "no format argument" instead of "no arguments" — diverges from all other commands

**File:** `commands/export.md:10`

**Issue:** The Usage Guard reads: "If invoked with no format argument or with `--help`".
Every other guard-and-stop command uses "no arguments or with `--help`". The phrase "no
format argument" is semantically correct (the format is the required positional), but it is
inconsistent with the uniform pattern used across all 11 other files. It also subtly implies
the guard fires only when the `<format>` positional is absent, which is true but may confuse
an agent into showing help when format is present but output-dir is absent — when in fact the
command runs fine without output-dir.

**Fix:** Standardize the trigger phrase to match every other guard-and-stop command:
```
**If invoked with no arguments or with `--help`:** Display the following usage block verbatim and stop — do not run any pipeline steps.
```

---

### WR-02: `ingest.md` `## Arguments` section does not document `--enrich`

**File:** `commands/ingest.md:36–41`

**Issue:** The `## Usage Guard` block correctly lists `--enrich` with a full description
(lines 26–27). However, the `## Arguments` section (lines 36–41) lists only five flags
(`path`, `--output`, `--domain`, `--validate`, `--view`, `--fail-threshold`) and omits
`--enrich` entirely. A Claude agent parsing the Arguments section for dispatch logic will
not find `--enrich` there, creating a documentation inconsistency that could cause the
flag to be silently dropped if the agent uses Arguments as the authoritative flag list.

**Fix:** Add the missing entry after `--fail-threshold`:
```
- `--enrich` (optional): Enrich graph via external APIs after build — clinicaltrials domain only.
  Triggers ClinicalTrials.gov v2 lookup for Trial nodes and PubChem PUG REST lookup for
  Compound nodes. No-op for other domains.
```

---

### WR-03: `ask.md` Usage Guard examples reference clinical-trials entities but the embedded persona is hardcoded to contracts

**File:** `commands/ask.md:22–24` and `commands/ask.md:55–79`

**Issue:** The Usage Guard examples are:
```
/epistract:ask "What trials involve remdesivir?"
/epistract:ask "Summarize key findings" --output-dir ./my-output
/epistract:ask "Which compounds target KRAS G12C?" --output-dir ./drug-output
```
These are clinical-trials and drug-discovery queries. However, `## Step 3` (lines 55–79)
hardcodes the "Sample Contract Analyst" persona that explicitly references the
"Pennsylvania Convention Center" 2026 event and analyzes "vendor contracts". The description
frontmatter also reads "answers with citations, cost breakdowns, and risk analysis" — which
is contracts-domain language.

The command as written is a contracts-only tool masquerading as a domain-agnostic one. The
Usage Guard examples suggesting it works for clinical trials ("What trials involve
remdesivir?") and drug discovery ("Which compounds target KRAS G12C?") are incorrect — those
questions will be answered through the contracts lens, producing misleading results. This is
a documentation correctness bug: either the examples should be scoped to contracts, or the
persona in Step 3 should be made domain-aware and the Usage Guard examples updated to match.

**Fix (minimal — align examples to actual behavior):**
```
Examples:
  /epistract:ask "What are the total catering costs?"
  /epistract:ask "Summarize key obligations" --output-dir ./my-output
  /epistract:ask "Which vendors have exclusivity clauses?" --output-dir ./contracts-output
```

Or (fuller fix): Make the persona selection dynamic based on the domain detected from
`graph_data.json` metadata, and update the examples to span domains with a note that the
persona adapts automatically.

---

### WR-04: `query.md` lists `<output-dir>` as a positional under `Options:` — structurally misleading

**File:** `commands/query.md:18–21`

**Issue:** The Usage Guard block shows:
```
Options:
  --type <entity-type>    Filter results by entity type
                          (Trial, Compound, ...)
  <output-dir>            Path to extraction output directory  (default: ./epistract-output)
```
`<output-dir>` is a positional argument with a default, not an option flag. It does not use
`--` prefix syntax. Listing it under `Options:` alongside `--type` creates an ambiguity:
an agent may attempt to pass `--output-dir ./epistract-output` as a flag (which `run_sift.py
search` does not accept), rather than passing it as a bare positional. All other commands
with an optional positional (e.g., `export.md`) keep positionals out of the `Options:`
block.

**Fix:**
```
Required:
  <search-term>    Entity name or keyword to search for

Optional:
  <output-dir>     Path to extraction output directory  (default: ./epistract-output)

Options:
  --type <entity-type>    Filter results by entity type
                          (Trial, Compound, Condition, Sponsor, Endpoint, Arm, Biomarker,
                           Gene, Protein, Drug, Disease, Party, Obligation, etc.)
```

---

## Info

### IN-01: `view.md` guard condition correctly uses `--help` only, but omits explicit note that no-args is valid

**File:** `commands/view.md:10`

**Issue:** The guard reads: "If invoked with `--help`: Display the following usage block
verbatim and stop. Otherwise proceed with existing logic." This is the correct
orientation-only variant — `view` is valid with no arguments and should not stop. However,
the Usage Guard block itself says "All arguments are optional — running with no arguments
opens the default output directory." This self-documents the intent well. No code change
needed, but the `## Usage Guard` trigger line could add a brief rationale to make the
deviation from the standard guard-and-stop pattern explicit, reducing the risk of a future
editor "correcting" it to guard-and-stop:
```
**If invoked with `--help`:** Display the following usage block verbatim and stop. No-arg
invocation is intentionally valid — it opens the default output directory.
```

---

### IN-02: `setup.md` guard block does not include a "stop" or "proceed" instruction — no trigger condition stated

**File:** `commands/setup.md:6–17`

**Issue:** The other orientation-only commands (`view.md`, `domain.md`) explicitly state
their trigger condition ("If invoked with `--help`"). `setup.md`'s guard block has no
trigger condition at all — it shows the usage block as a bare display block with no
conditional instruction. This means there is no guidance on when to show help vs when to
proceed with execution. For `setup`, which takes no flags, the implicit intent is "always
show a brief reminder then proceed", but an agent reading the other guards may expect an
explicit trigger sentence.

**Fix:** Add a one-line trigger before the usage block:
```
**Always display this usage summary, then proceed with setup:**
```
Or, to match `view.md` and `domain.md` style:
```
**If invoked with `--help`:** Display this block and stop. Otherwise proceed with setup.
```

---

### IN-03: `build.md` `## Arguments` section documents `--list-domains` flag that does not appear in the Usage Guard or pipeline steps

**File:** `commands/build.md:29`

**Issue:** The Arguments section reads: `"--domain` (optional): Domain name (default:
drug-discovery). Use `--list-domains` to see available domains."` The `--list-domains` flag
does not appear in the Usage Guard block and is not mentioned in the pipeline steps. There
is no corresponding handling in `run_sift.py build` based on the project architecture
described in CLAUDE.md. This looks like a stale reference — the flag was either planned and
never implemented, or it belongs to a different subcommand.

**Fix:** Remove the `--list-domains` reference from the Arguments section, or add it
to the Usage Guard options block and to the pipeline steps with the corresponding
`run_sift.py` invocation if the flag is actually supported.

---

### IN-04: `epistemic.md` and `ask.md` reference old command syntax with hyphens (`/epistract-query`, `/epistract-build`) instead of colon syntax

**File:** `commands/epistemic.md:61–64`, `commands/ask.md` (implicit in `## Step 2` path references)

**Issue:** `epistemic.md` Step 3 (lines 61–65) reads:
```
- Use `/epistract-query` to search within the claims layer
- Export with `/epistract-export`
```
The canonical command syntax used throughout the codebase and in all Usage Guard blocks is
`/epistract:query` and `/epistract:export` (colon separator). The hyphen-separated form
`/epistract-query` is the old pre-plugin syntax. Using the wrong separator in the "next
steps" suggestions will cause users to invoke commands that do not exist. `ask.md` has a
similar reference in Step 6 suggest text where it says `/epistract-ingest` on line 112
(acquire.md Step 6, not ask.md — see below).

Also in `commands/acquire.md` Step 6 (line 112): "Suggest next step:
`/epistract-ingest <output_dir>`" — should be `/epistract:ingest`.

**Fix:**
```
# epistemic.md lines 63-64:
- Use `/epistract:query` to search within the claims layer
- Export with `/epistract:export` — claims_layer.json is included in exports

# acquire.md line 112:
- Suggest next step: `/epistract:ingest <output_dir>` to build the knowledge graph
```

---

_Reviewed: 2026-04-18T12:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
