---
name: epistract-add-url
description: Fetch one or more URLs into an epistract project corpus (deduplicated by content hash)
---

Download content from one or more URLs directly into a project's corpus. Fetched
content is deduplicated by sha256 content hash and recorded in the project manifest.

## Usage Guard

**If invoked with no arguments or with `--help`:** Display the following usage block verbatim and stop.

```
Usage: /epistract:add-url <url>... [--project <name>]

Required:
  <url>...           One or more URLs to fetch into the corpus

Options:
  --project <name>   Target project (default: project detected from the current
                     directory, or $EPISTRACT_PROJECT)

Examples:
  /epistract:add-url https://example.com/report.html --project acme-contracts
  /epistract:add-url https://arxiv.org/abs/2502.14802 --project kg-research
```

## Arguments
- `urls` (required): One or more URLs.
- `--project` (optional): Target project name.

```bash
PYTHONPATH="${CLAUDE_PLUGIN_ROOT}" python3 -m core.cli add url <url>... [--project NAME]
```

Report the fetch status for each URL (added / skipped duplicate). For PubMed corpora,
prefer `/epistract:acquire`, which uses E-utilities metadata. Then suggest
`/epistract:index <project>`.
