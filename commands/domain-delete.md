---
name: epistract-domain-delete
description: Remove a domain — archive to a recoverable location or permanently delete — with explicit confirmation
---

# /epistract:domain-delete

Remove a domain package from the epistract installation. Two options are available:

- **Archive** — moves the domain directory to `domains/_archived/<name>/`. The domain
  will appear in `/epistract:domain-list` with status "archived" and will be excluded
  from the pipeline, but files remain on disk and can be recovered manually.
- **Remove** — permanently deletes the domain directory. **This cannot be undone.**

The command requires two explicit user confirmations before any filesystem change is made.

## Usage Guard

**If invoked with `--help` or with no arguments:** Display the following and stop.
Otherwise proceed to Steps.

```
Usage: /epistract:domain-delete <name>

Arguments:
  <name>    Name of the domain to delete (e.g. "contracts", "drug-discovery")

Options:
  archive   Move domain to domains/_archived/<name>/ (recoverable)
  remove    Permanently delete the domain directory (cannot be undone)

Examples:
  /epistract:domain-delete contracts
  /epistract:domain-delete old-domain

To see available domains: /epistract:domain-list
```

## Steps

### Step 1: Validate domain exists

Run:

```bash
python3 scripts/manage_domains.py info <name>
```

- If exit non-zero: display the error message from the script output. Report that the
  domain was not found and no changes have been made. **STOP — do not proceed to Step 2.**
- If exit 0: note the `name` and `file_count` values from the JSON output. Proceed to
  Step 2.

### Step 2: Present domain info and ask archive or remove

Display the domain name and file count to the user. Then present the two options:

```
Domain: <name> (<file_count> files)

Choose an action:
  1. archive — Move to domains/_archived/<name>/ (recoverable)
  2. remove  — Permanently delete (cannot be undone)

Type "archive" or "remove" to continue, or anything else to cancel.
```

**Wait for the user to respond before proceeding to Step 3.** If the user does not type
'archive' or 'remove', report 'Cancelled. No changes made.' and stop.

- If user types `archive`: set action=archive. Proceed to Step 3.
- If user types `remove`: set action=remove. Proceed to Step 3.
- Anything else: report "Cancelled. No changes made." **STOP.**

### Step 3: Confirm destructive action

Present a confirmation prompt based on the chosen action:

For **archive**:

> You are about to archive domain **<name>** (<file_count> files).
> The domain will be moved to `domains/_archived/<name>/` and excluded from the pipeline.
> This action is recoverable — files remain on disk.
>
> Type "yes" to confirm, or anything else to cancel.

For **remove**:

> You are about to **permanently delete** domain **<name>** (<file_count> files).
> **This cannot be undone.** All domain files will be deleted from disk.
>
> Type "yes" to confirm, or anything else to cancel.

**Wait for the user to respond before proceeding to Step 4. Do not auto-advance. Do not
skip this step.** If the user does not type 'yes', report 'Cancelled. No changes made.'
and stop.

- If user types `yes`: proceed to Step 4.
- Anything else: report "Cancelled. No changes made." **STOP.**

### Step 4: Execute

For **archive**:

```bash
python3 scripts/manage_domains.py archive <name>
```

For **remove**:

```bash
python3 scripts/manage_domains.py remove <name>
```

- If exit non-zero: display the error output. Report that the operation failed and no
  changes (or partial changes) may have occurred. Suggest running
  `/epistract:domain-list` to verify current state. **STOP.**
- If exit 0: proceed to Step 5.

### Step 5: Report result

For **archive**:

```
Domain "<name>" has been archived.
  Location: domains/_archived/<name>/
  Status in /epistract:domain-list: "archived"
  Effect: excluded from the pipeline immediately

To permanently remove the archived copy later, run:
  /epistract:domain-delete <name>
```

For **remove**:

```
Domain "<name>" has been permanently deleted.
  All <file_count> files have been removed from disk.
  The domain no longer appears in /epistract:domain-list.
```

## Error Handling

- **Archive collision** — `domains/_archived/<name>/` already exists: display the script
  error. Suggest removing the existing archived copy first with
  `python3 scripts/manage_domains.py remove <name>` (targeting the archived copy), or
  rename it manually before retrying.
- **Domain is archived** — if `info` returns `status: "archived"`, note that the domain
  is already archived. Running the command again will offer permanent removal of the
  archived copy.
- **Unexpected errors**: Display the raw script output. Suggest running
  `/epistract:domain-list` to verify current state before retrying.
