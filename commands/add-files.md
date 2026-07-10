---
name: epistract-add-files
description: Add source documents to an epistract project corpus (deduplicated by content hash)
---

Copy one or more source documents into a project's corpus. Files are deduplicated by
sha256 content hash and recorded in the project manifest, which is what makes
`/epistract:index` incremental — re-indexing skips unchanged sources.

## Usage Guard

**If invoked with no arguments or with `--help`:** Display the following usage block verbatim and stop.

```
Usage: /epistract:add-files <path>... [--project <name>]

Required:
  <path>...          One or more file paths to add to the corpus

Options:
  --project <name>   Target project (default: project detected from the current
                     directory, or $EPISTRACT_PROJECT)

Examples:
  /epistract:add-files paper1.pdf paper2.pdf --project glp1-research
  /epistract:add-files ~/downloads/*.pdf --project acme-contracts
```

## Arguments
- `paths` (required): One or more file paths.
- `--project` (optional): Target project name.

```bash
PYTHONPATH="${CLAUDE_PLUGIN_ROOT}" python3 -m core.cli add files <path>... [--project NAME]
```

Report how many files were added, how many were skipped as duplicates, and any missing
paths. Then suggest running `/epistract:index <project>` to extract and index the new documents.
