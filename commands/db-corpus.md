---
name: epistract-db-corpus
description: Build an Epistract corpus from a SQL or Neo4j database (one .txt per record), then hand off to /epistract:ingest
---

# Epistract Database Corpus Builder

You are helping a structured-data expert convert records from a relational
database (PostgreSQL, MySQL, SQLite) or Neo4j graph database into a
plain-text corpus that the existing `/epistract:ingest` pipeline can
consume. Speak in DB terms (table, primary key, connection string, query,
node label, Cypher). Do not describe rows as "documents" until they have
been written to disk.

## Usage Guard

**If invoked with no arguments or with `--help`:** Display the following
usage block verbatim and stop — do not run any pipeline steps.

```
Usage: /epistract:db-corpus <output_dir> --source <sqlite|sql|neo4j> --conn <url> [options]

Required:
  <output_dir>             Directory where docs/ will be written
  --source <type>          Database type: sqlite, sql (PostgreSQL/MySQL), or neo4j
  --conn <connection_str>  SQLAlchemy URL or Bolt URI

SQL options (--source sqlite OR --source sql):
  --table <name>           Table to read from (required for sqlite)
  --pk <col>               Primary-key column for filename + Row_ID (required for sqlite)
  --query <sql>            SELECT statement (required for --source sql).
                           Trusted SQL only — never paste user input.
  --limit <n>              Max rows to fetch (default: 500)

Neo4j options (--source neo4j):
  --query <cypher>         MATCH/RETURN Cypher (required). Trusted Cypher only.
  --neo4j-user <user>      Neo4j user (default: neo4j)
  --neo4j-password-env VAR Env var holding the Neo4j password
                           (default: NEO4J_PASSWORD)
  --limit <n>              Max nodes to fetch (default: 500)

Examples:
  /epistract:db-corpus ./out --source sqlite --conn sqlite:///./patients.db --table patients --pk id
  /epistract:db-corpus ./out --source sql --conn "postgresql+psycopg2://user:pass@host/db" --query "SELECT * FROM trials" --table trials --pk nct_id
  /epistract:db-corpus ./out --source neo4j --conn bolt://localhost:7687 --query "MATCH (n:Patient) RETURN n"

Note: CSV and JSON files do NOT need this command. Point /epistract:ingest
directly at them — Kreuzberg reads CSV/JSON natively.

Connection-string credentials are redacted from all output (.txt headers,
summary JSON, error messages). For Neo4j, prefer setting NEO4J_PASSWORD
in your shell over passing credentials in the URI.
```

## Prerequisites

Optional drivers — only required for the source type the user picks:
- SQLite: nothing extra (Python stdlib).
- PostgreSQL: `uv pip install sqlalchemy psycopg2-binary`
- MySQL/MariaDB: `uv pip install sqlalchemy pymysql`
- Neo4j: `uv pip install neo4j`

If the user invokes the command and the script reports
`ImportError: ... uv pip install ...`, run that exact install command,
then retry.

## Arguments

- `output_dir` (required): Directory to write `docs/` into.
- `--source` (required): One of `sqlite`, `sql`, `neo4j`.
- `--conn` (required): SQLAlchemy URL (`postgresql+psycopg2://...`,
  `mysql+pymysql://...`, `sqlite:///...`) or Bolt URI (`bolt://host:7687`).
- `--query`, `--table`, `--pk`, `--limit`, `--neo4j-user`,
  `--neo4j-password-env`: see Usage block.

## Pipeline Steps

### Step 1: Confirm DB Connectivity Plan

Repeat back to the user (in DB terms): which database, which table or
Cypher pattern, expected row count, primary key column. If anything is
missing, ask before proceeding. Do NOT echo the password portion of the
connection string back — quote only the redacted form (substitute
`***` for any user:password segment).

### Step 2: Verify Optional Driver Available

For `--source sql`: check that `sqlalchemy` is importable.
For `--source neo4j`: check that `neo4j` is importable.
If missing, instruct the user to run the appropriate `uv pip install`
command (see Prerequisites), wait for confirmation, then continue.

### Step 3: Build Corpus

Invoke the serializer:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/write_db_corpus.py "<output_dir>" \
    --source <source> --conn "<conn>" \
    [--query "<query>"] [--table <table>] [--pk <pk>] \
    [--limit <n>] [--neo4j-user <user>] [--neo4j-password-env <env_var>]
```

The script prints a JSON summary to stdout. Capture and display:
- `docs_dir` (where the corpus landed)
- `source` and `redacted_url` (no creds)
- `rows_fetched`, `written`, `skipped_empty`
- First 5 entries of `files`

If `rows_fetched == limit` (default 500), warn the user that the result
set may have been truncated and suggest re-running with a larger
`--limit` or a more selective `--query`.

### Step 4: Offer Ingest Hand-off

Tell the user:

> Corpus built at `<docs_dir>`. Next step:
> `/epistract:ingest <output_dir> --domain <domain_name>`
>
> Pick a domain (`drug-discovery`, `contracts`, `clinicaltrials`,
> `fda-product-labels`) appropriate to your data. The corpus contains
> one `.txt` per record; the ingest pipeline will chunk, extract, and
> build a knowledge graph.

Do NOT auto-invoke `/epistract:ingest` — the user picks the domain.

### Step 5: Report Summary

Single-line summary:
`db-corpus: <source> → <written>/<rows_fetched> rows written to <docs_dir> (skipped <skipped_empty> empty rows)`

## Anti-Patterns to Avoid

- Do NOT echo the raw connection string with credentials in any message
  back to the user. Always redact via the script's `redacted_url` output.
- Do NOT auto-invoke `/epistract:ingest` — the domain choice is the
  user's call.
- Do NOT suggest CSV/JSON go through this command — direct `/epistract:ingest`.
- Do NOT change `core/` — this command lives entirely in `commands/`
  and `scripts/`.
