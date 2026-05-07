---
name: epistract-domain-update
description: Edit a domain component — schema, extraction prompt, or epistemic analysis — via a guided conversational wizard
---

# /epistract:domain-update

Edit an installed domain by updating one of its three components:

- **Schema** (`domain.yaml`) — add, remove, or rename entity types and relation types
- **Extraction prompt** (`SKILL.md`) — revise the LLM instructions used during document ingestion
- **Epistemic analysis** (`epistemic.py`) — adjust confidence tiers, hedging patterns, and conflict rules

One component is edited per invocation. After the write completes the wizard exits. Re-invoke to edit another component.

## Usage Guard

**If invoked with `--help` or with no arguments:** Display the following and stop.
Otherwise proceed to Steps.

```
Usage: /epistract:domain-update <name>

Arguments:
  <name>    Name of the domain to update (e.g. "contracts", "drug-discovery")

Editable components:
  1. Schema (domain.yaml)              — add/remove/rename entity and relation types
  2. Extraction prompt (SKILL.md)      — revise LLM extraction instructions
  3. Epistemic analysis (epistemic.py) — adjust confidence tiers and conflict rules

Examples:
  /epistract:domain-update contracts
  /epistract:domain-update drug-discovery

To see available domains: /epistract:domain-list
```

> **Implementation notes — read before starting:**
>
> - `<name>` is the domain name argument from the user invocation.
> - `<dir>` is the absolute path from the `dir` field of Step 1's JSON output. Use it for
>   all subsequent file operations. Never construct the path manually from `<name>`.
> - Write `domain.yaml` via Python `Path.write_text()`, not a bare heredoc, to prevent
>   shell metacharacter corruption in YAML descriptions that contain backticks or `$`.
> - Write `SKILL.md` and `epistemic.py` via heredoc with a single-quoted delimiter
>   `<< 'CONTENT_EOF'` to prevent shell expansion of `$`, backticks, and backslashes.
> - Do **NOT** round-trip proposed YAML through `yaml.safe_load()` + `yaml.dump()` —
>   write verbatim to preserve formatting and inline comments.
> - The wizard exits after one component edit (one component per invocation). The user
>   re-invokes to edit additional components.

## Steps

### Step 1: Validate domain exists

Run:

```bash
python3 scripts/manage_domains.py info <name>
```

- If exit non-zero: display the error message from the script output. Report that the
  domain was not found and no changes have been made. **STOP — do not proceed to Step 2.**
- If exit 0: extract the `name`, `dir`, and `status` values from the JSON output.
- If `status == "archived"`: display the following warning and wait for the user:

  > Domain **\<name\>** is archived and excluded from the active pipeline. Edits will apply
  > to the archived copy at `<dir>`. Continue? (yes/no)

  **Wait for the user to respond before proceeding to Step 2. Do not auto-advance. Do not
  skip this step.** If the user does not type `yes`, report "Cancelled. No changes made."
  and stop.

- If `status == "active"` (or archived and user confirmed `yes`): proceed to Step 2.

### Step 2: Present top-level menu

Display the domain name and the following numbered menu:

```
Domain: <name>

What would you like to edit?

  1. Schema (domain.yaml)              — add/remove/rename entity and relation types
  2. Extraction prompt (SKILL.md)      — revise LLM extraction instructions
  3. Epistemic analysis (epistemic.py) — adjust confidence tiers and conflict rules

Type 1, 2, or 3 to continue, or anything else to cancel.
```

**Wait for the user to respond before proceeding. Do not auto-advance. Do not skip this
step.**

- If user types `1`: proceed to the **Schema Branch** (Step 3a).
- If user types `2`: proceed to the **Extraction Prompt Branch** (Step 3b).
- If user types `3`: proceed to the **Epistemic Analysis Branch** (Step 3c).
- Anything else: report "Cancelled. No changes made." **STOP.**

---

## Schema Branch

### Step 3a: Summarize current schema

Run the following to extract entity type and relation type names from `domain.yaml`:

```bash
python3 -c "
import yaml, json
from pathlib import Path
schema = yaml.safe_load(Path('<dir>/domain.yaml').read_text())
et = schema.get('entity_types', {}) or {}
rt = schema.get('relation_types', {}) or {}
print(json.dumps({'entity_types': list(et.keys()), 'relation_types': list(rt.keys())}))
"
```

Display the result in this summary format (do **not** display raw YAML):

```
Domain: <name>
Entity types (<count>): <comma-separated names>
Relation types (<count>): <comma-separated names>
```

### Step 4a: Ask what to change

Show the user examples of supported change requests:

```
Examples of changes you can request:
  - "Add entity type BIOMARKER with description 'A measurable biological indicator'"
  - "Remove entity type GENE"
  - "Rename entity type COMPOUND to MOLECULE"
  - "Add relation type INHIBITS from COMPOUND to PROTEIN"
  - "Remove relation type CAUSES"
  - "Rename relation type TARGETS to BINDS_TO"
```

Then prompt:

```
Describe your change:
```

**Wait for the user to respond before proceeding to Step 5a. Do not auto-advance. Do not
skip this step.**

### Step 5a: Propose updated schema

Read the current `domain.yaml` content from `<dir>/domain.yaml`. Apply the user's
natural-language request to produce a proposed full `domain.yaml`. Display the proposed
`entity_types` and `relation_types` sections to the user in a readable form (not as a raw
PyYAML dump). Explain what changed.

### Step 6a: Validate proposed schema

Run the following to validate the proposed schema before presenting the confirmation gate.
Validation must pass before the user is asked to confirm the write:

Write the proposed domain.yaml to a temporary file, then validate it using the
`manage_domains.py validate` subcommand. This avoids fragile `sys.path` manipulation
that breaks when `EPISTRACT_DOMAINS_DIR` is overridden.

```bash
TMPDIR=$(mktemp -d)
cat > "$TMPDIR/domain.yaml" << 'SCHEMA_EOF'
<proposed full domain.yaml content>
SCHEMA_EOF

# Write to a throwaway domain directory so the validate subcommand can find it
mkdir -p "$TMPDIR/_validate_tmp"
cp "$TMPDIR/domain.yaml" "$TMPDIR/_validate_tmp/domain.yaml"
EPISTRACT_DOMAINS_DIR="$TMPDIR" python3 scripts/manage_domains.py validate _validate_tmp
rm -rf "$TMPDIR"
```

- If `valid` is `false`: display errors in the following format. Then **return to Step 4a**
  for a revised request. Do **NOT** advance to Step 7a.

  ```
  Schema validation failed:
  - <error 1>
  - <error 2>

  Please revise your request.
  ```

- If `valid` is `true`: proceed to Step 7a.

### Step 7a: Confirm and write domain.yaml

Display the complete proposed `domain.yaml` content (or a clear diff summary of the
changes). Then present the confirmation prompt:

> The above changes will be written to `<dir>/domain.yaml`.
>
> Type "yes" to confirm, or anything else to cancel.

**Wait for the user to respond before proceeding. Do not auto-advance. Do not skip this
step.**

- Anything else: report "Cancelled. No changes made." **STOP.**
- If user types `yes`: write the file using Python `Path.write_text()`:

```bash
python3 -c "
from pathlib import Path
import sys
Path('<dir>/domain.yaml').write_text(sys.stdin.read())
" << 'CONTENT_EOF'
<proposed domain.yaml content>
CONTENT_EOF
```

Report: `domain.yaml updated successfully.` **STOP.**

---

## Extraction Prompt Branch

### Step 3b: Display current SKILL.md

Run:

```bash
cat '<dir>/SKILL.md'
```

Display the full file content to the user.

### Step 4b: Ask what to change

Provide context on the kinds of changes users typically make:

```
Examples of changes you can request:
  - "Add extraction hints for a new entity type added to the schema"
  - "Strengthen the instructions for capturing numeric values with units"
  - "Add a note that compound names should be captured with their CAS numbers"
  - "Remove the section about patent-specific language"
```

Then prompt:

```
What do you want to change in the extraction prompt?
```

**Wait for the user to respond before proceeding to Step 5b. Do not auto-advance. Do not
skip this step.**

### Step 5b: Propose updated SKILL.md

Rewrite only the affected section of `SKILL.md` based on the user's description. Display
the complete proposed new `SKILL.md` content.

### Step 6b: Confirm and write SKILL.md

Present the confirmation prompt:

> The above content will be written to `<dir>/SKILL.md`.
>
> Type "yes" to confirm, or anything else to cancel.

**Wait for the user to respond before proceeding. Do not auto-advance. Do not skip this
step.**

- Anything else: report "Cancelled. No changes made." **STOP.**
- If user types `yes`: write the file via heredoc with single-quoted delimiter:

```bash
cat > '<dir>/SKILL.md' << 'CONTENT_EOF'
<proposed SKILL.md content>
CONTENT_EOF
```

Report: `SKILL.md updated successfully.` **STOP.**

---

## Epistemic Analysis Branch

### Step 3c: Display current epistemic.py

Run:

```bash
cat '<dir>/epistemic.py'
```

Display the full file content to the user.

### Step 4c: Ask what to change

Provide context on the kinds of changes users typically make:

```
Examples of changes you can request:
  - "Add a new confidence tier for regulatory guidance documents at 0.85"
  - "Add 'may indicate' to the hedging language patterns"
  - "Add a new evidence type 'regulatory_submission' at tier 3"
  - "Lower the threshold for the 'hypothesized' classification from 0.6 to 0.5"
```

Then prompt:

```
What do you want to change in the epistemic analysis?
```

**Wait for the user to respond before proceeding to Step 5c. Do not auto-advance. Do not
skip this step.**

### Step 5c: Propose updated epistemic.py

Rewrite only the affected section of `epistemic.py` based on the user's description.
Display the complete proposed new `epistemic.py` content.

### Step 6c: Confirm and write epistemic.py

Present the confirmation prompt:

> The above content will be written to `<dir>/epistemic.py`.
>
> Type "yes" to confirm, or anything else to cancel.

**Wait for the user to respond before proceeding. Do not auto-advance. Do not skip this
step.**

- Anything else: report "Cancelled. No changes made." **STOP.**
- If user types `yes`: write the file via heredoc with single-quoted delimiter:

```bash
cat > '<dir>/epistemic.py' << 'CONTENT_EOF'
<proposed epistemic.py content>
CONTENT_EOF
```

Report: `epistemic.py updated successfully.` **STOP.**

---

## Error Handling

- **Domain not found** — `manage_domains.py info` exits non-zero: display the error
  message from the script output. Report that the domain was not found and no changes
  have been made. Suggest running `/epistract:domain-list` to see available domains.
- **Schema validation failure** — `validate_schema` returns errors: display each error
  with the format shown in Step 6a, return to Step 4a for a revised request. Do **not**
  write `domain.yaml` until validation passes.
- **File not found** — `cat` fails for `SKILL.md` or `epistemic.py`: display the error
  output. The file may be missing from the domain directory. Suggest running
  `/epistract:domain-list` to check the domain's file count and verify the installation.
- **Write failure** — `Path.write_text()` or `cat >` exits non-zero: display the raw
  error output. No partial write should have occurred. Suggest checking filesystem
  permissions on the domain directory.
- **Unexpected errors**: Display the raw script output. Suggest running
  `/epistract:domain-list` to verify current state before retrying.
