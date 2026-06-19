---
name: epistract-domain-list
description: List all installed domains — active and archived — with entity type count, relation type count, last-modified date, and status
---

# /epistract:domain-list

List all installed domains — both active and archived — in a formatted table. Shows entity
type count, relation type count, last-modified date, and pipeline status for each domain.
Active domains are available to the pipeline; archived domains are excluded from resolution
but kept on disk at `domains/_archived/<name>/`.

## Usage Guard

**If invoked with `--help`:** Display the following and stop. Otherwise proceed to Steps.

```
Usage: /epistract:domain-list

Lists all installed domains with:
  - Name
  - Entity type count
  - Relation type count
  - Last-modified date (from domain.yaml mtime)
  - File count
  - Status (active / archived)

Archived domains are excluded from the pipeline but kept on disk.
To remove a domain: /epistract:domain-delete <name>
To create a new domain: /epistract:domain
```

## Steps

### Step 1: Fetch domain data

Run:

```bash
python3 scripts/manage_domains.py list
```

- If the command exits non-zero: display the error output and stop. Suggest running
  `/epistract:setup` if the script is missing or the environment is misconfigured.
- If the output is an empty JSON array (`[]`): report "No domains installed. Run
  `/epistract:domain` to create one." and stop.
- If successful (exit 0, non-empty array): proceed to Step 2.

### Step 2: Format and display

Parse the JSON array returned by Step 1.

Separate rows into two groups:
- **Active** — rows where `status == "active"`
- **Archived** — rows where `status == "archived"`

Display active domains as a markdown table:

```
| Name | Entity Types | Relation Types | Last Modified | Files |
|------|-------------|----------------|---------------|-------|
| contracts | 9 | 9 | 2026-04-23 | 11 |
| drug-discovery | 17 | 30 | 2026-04-20 | 8 |
```

If archived rows exist, display a second table beneath the first:

```
### Archived Domains

The following domains are archived and excluded from the pipeline.
Run `/epistract:domain-delete <name>` to permanently remove an archived domain.

| Name | Entity Types | Relation Types | Last Modified | Files |
|------|-------------|----------------|---------------|-------|
| old-domain | 2 | 1 | 2026-03-10 | 3 |
```

If no archived rows exist, omit the archived section entirely.

## Error Handling

- **Non-zero exit from script**: Display the raw error output. Suggest `/epistract:setup`
  to verify the Python environment and dependencies.
- **Empty JSON array**: "No domains installed. Run `/epistract:domain` to create one."
- **JSON parse error**: Display the raw output, note that `scripts/manage_domains.py` may
  be corrupted or outdated.
