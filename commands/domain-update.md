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
  4. Re-run corpus analysis            — analyze new documents and suggest schema additions

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
  4. Re-run corpus analysis            — analyze new documents and suggest schema additions

Type 1, 2, 3, or 4 to continue, or anything else to cancel.
```

**Wait for the user to respond before proceeding. Do not auto-advance. Do not skip this
step.**

- If user types `1`: proceed to the **Schema Branch** (Step 3a).
- If user types `2`: proceed to the **Extraction Prompt Branch** (Step 3b).
- If user types `3`: proceed to the **Epistemic Analysis Branch** (Step 3c).
- If user types `4`: proceed to the **Corpus Re-run Branch** (Step 3d).
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

## Corpus Re-run Branch

### Step 3d: Ask for document paths

Prompt the user:

```
Provide paths to 2–5 documents to analyze (can be new documents or documents from the
original corpus).
```

**Wait for the user to respond before proceeding. Do not auto-advance. Do not skip this
step.**

- If the user provides fewer than 2 paths: report "At least 2 documents are required for
  corpus analysis." Return to this prompt. Do NOT advance.
- If the user provides 2–5 paths: verify each path exists and is readable. If any path is
  unreadable, warn the user and ask them to re-enter. After confirming each path exists and
  is readable, also reject any path that:
  - Contains `..` components after resolving the real path (`os.path.realpath()`)
  - Does not end in a supported document extension (`.pdf`, `.docx`, `.html`, `.txt`,
    `.xls`, `.xlsx`, `.eml`, `.md`, or other common text/document formats)
  - Is a symlink pointing outside the directory of the first provided path

  Report rejected paths with a clear reason and ask the user to re-enter valid paths.
  Proceed to Step 4d once 2 or more valid paths are confirmed.

### Step 4d: Read current schema and run 3-pass corpus analysis

Run the following to read the current entity type names, relation type names, and domain
description from `domain.yaml`:

```bash
python3 -c "
import yaml, json
from pathlib import Path
schema = yaml.safe_load(Path('<dir>/domain.yaml').read_text())
et = sorted((schema.get('entity_types') or {}).keys())
rt = sorted((schema.get('relation_types') or {}).keys())
desc = schema.get('description', '') or ''
print(json.dumps({'entity_types': et, 'relation_types': rt, 'description': desc}))
"
```

Store the current entity type names, relation type names, and `domain_description` for
use in the diff step and in the 3-pass analysis prompts.

Run the multi-pass LLM analysis pipeline against the user-provided documents:

```python
from core.domain_wizard import (
    read_sample_documents, build_schema_discovery_prompt,
    build_consolidation_prompt, build_final_schema_prompt
)
```

**Pass 1 — Per-document entity/relation discovery:**
For each document path:
1. Read text using `read_sample_documents(doc_paths)`
2. Build the discovery prompt: `build_schema_discovery_prompt(doc["text"], domain_description)`
3. Send prompt to Claude. Parse the JSON response to get candidate entity types and
   relation types for this document. Collect all Pass 1 candidate dicts.

**Pass 2 — Cross-document consolidation:**
1. Build consolidation prompt: `build_consolidation_prompt(all_candidates, domain_description)`
2. Send to Claude. Parse the JSON response to get deduplicated consolidated types.

**Pass 3 — Final schema proposal:**
1. Build final prompt: `build_final_schema_prompt(consolidated, domain_description)`
2. Send to Claude. Parse the JSON response to get `proposed` — a dict with
   `entity_types` and `relation_types` keys, each mapping type names to
   `{"description": "..."}` dicts.

### Step 5d: Diff proposed schema against current schema

Run the following to compute the net-new type suggestions (set subtraction on key names
only — existing type descriptions are never compared per D-01):

Store the Pass 3 JSON response string in the variable `PASS3_JSON` (the raw JSON text
returned by Claude, not evaluated as Python). Then run:

```bash
python3 << 'DIFF_EOF'
import yaml, json
from pathlib import Path

current = yaml.safe_load(Path('<dir>/domain.yaml').read_text())
current_entities = set((current.get('entity_types') or {}).keys())
current_relations = set((current.get('relation_types') or {}).keys())

# Load Pass 3 output via json.loads() — never embed LLM output as Python source
proposed = json.loads('<pass3-output-as-json-string>')
proposed_entities = set(proposed.get('entity_types', {}).keys())
proposed_relations = set(proposed.get('relation_types', {}).keys())

net_new_entities = proposed_entities - current_entities
net_new_relations = proposed_relations - current_relations

suggestions = [
    {'kind': 'entity_type', 'name': n, 'definition': proposed['entity_types'][n]}
    for n in sorted(net_new_entities)
] + [
    {'kind': 'relation_type', 'name': n, 'definition': proposed['relation_types'][n]}
    for n in sorted(net_new_relations)
]
print(json.dumps({'suggestions': suggestions, 'count': len(suggestions)}))
DIFF_EOF
```

- If `count` is 0: report "Corpus analysis complete. No new entity types or relation types
  were suggested." **STOP.**
- Otherwise: proceed to Step 6d with the `suggestions` list.

### Step 6d: Review suggestions one at a time

Report the total count before entering the review loop:

```
N suggestions found — reviewing now.
```

For each suggestion in the list (repeat until all suggestions are reviewed):

Display a human-readable summary:
- Entity type: `New entity type: TYPE_NAME — <description> (e.g., <example if present>)`
- Relation type: `New relation type: REL_NAME — <description>`

Then prompt:

```
Add this? (yes/no)
```

**Wait for the user to respond before proceeding to the next suggestion. Do not
auto-advance. Do not skip this step.**

- If user types `yes`: mark this suggestion as accepted.
- If user types `no`: mark this suggestion as rejected. This is a normal expected action,
  not a cancellation. Do NOT display "Cancelled." Do NOT stop the review loop. Continue to
  the next suggestion.

After all suggestions have been reviewed, proceed to Step 7d.

### Step 7d: Merge accepted suggestions and validate

If zero suggestions were accepted: report "No changes made." **STOP.**

Otherwise, merge the accepted suggestions into the current schema. Always start from the
full current schema dict to preserve all top-level fields (name, version, description,
system_context, fallback_relation, community_label_anchors, etc.):

```python
import yaml
from pathlib import Path

current = yaml.safe_load(Path('<dir>/domain.yaml').read_text())
merged = dict(current)

merged_entities = dict(current.get('entity_types') or {})
for suggestion in accepted_entity_suggestions:
    merged_entities[suggestion['name']] = suggestion['definition']
merged['entity_types'] = merged_entities

merged_relations = dict(current.get('relation_types') or {})
for suggestion in accepted_relation_suggestions:
    merged_relations[suggestion['name']] = suggestion['definition']
merged['relation_types'] = merged_relations

merged_yaml = yaml.safe_dump(
    merged,
    default_flow_style=False,
    sort_keys=False,
    allow_unicode=True,
)
```

Run the temp-dir validation gate on the merged schema before writing:

```bash
TMPDIR=$(mktemp -d)
mkdir -p "$TMPDIR/_validate_tmp"
VALIDATE_PATH="$TMPDIR/_validate_tmp/domain.yaml"
export VALIDATE_PATH
python3 -c "
import os, sys
from pathlib import Path
Path(os.environ['VALIDATE_PATH']).write_text(sys.stdin.read())
" << 'SCHEMA_EOF'
<merged domain.yaml content as YAML string>
SCHEMA_EOF

EPISTRACT_DOMAINS_DIR="$TMPDIR" python3 scripts/manage_domains.py validate _validate_tmp
rm -rf "$TMPDIR"
```

- If `valid` is `false`: display the errors in the format below. Report "No changes made."
  **STOP.** Do NOT write `domain.yaml`.

  ```
  Schema validation failed:
  - <error 1>
  - <error 2>
  ```

- If `valid` is `true`: proceed to Step 8d.

### Step 8d: Write merged domain.yaml and report summary

Write the merged schema using Python `Path.write_text()`:

```bash
python3 -c "
from pathlib import Path
import sys
Path('<dir>/domain.yaml').write_text(sys.stdin.read())
" << 'CONTENT_EOF'
<merged domain.yaml as YAML string>
CONTENT_EOF
```

Report: `X of Y suggestions accepted. domain.yaml updated.` **STOP.**

(X = count of accepted suggestions, Y = total suggestion count from Step 6d.)

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
- **LLM returns invalid JSON (corpus re-run passes)**: Retry the pass once with explicit
  "Return ONLY the JSON object, no commentary." prepended to the prompt. If the second
  attempt also fails, report the raw error and stop: "Corpus analysis failed. No changes
  made."
- **Fewer than 2 readable documents (corpus re-run)**: Report "At least 2 documents are
  required for corpus analysis." Return to Step 3d.
- **Schema validation fails after merge**: Display the errors from `manage_domains.py
  validate`. Report "No changes made." Do NOT write `domain.yaml`.
