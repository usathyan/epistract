---
name: epistract-acquire
description: Search PubMed and download articles into a local corpus for epistract ingestion
---

# Epistract PubMed Acquisition

You are building a document corpus from PubMed for the epistract knowledge graph pipeline.

## Prerequisites

The **PubMed connector** must be available. If it is not connected, tell the user:

> PubMed connector not found. Connect it in Claude settings (Settings > Connectors > PubMed)
> or in Claude Code: `/plugin marketplace add anthropics/life-sciences && /plugin install pubmed@life-sciences`

## Arguments
- `query` (required): PubMed search query (supports standard PubMed syntax)
- `--max` (optional): Maximum articles to fetch (default: 20)
- `--output` (optional): Output directory (default: ./epistract-corpus)
- `--full-text` (optional): Attempt to fetch full text from PMC when available (default: true)

## Pipeline Steps

### Step 1: Search PubMed

Use the PubMed connector to search for articles matching the query. Respect NCBI rate limits — if you receive a rate limit message, wait briefly and retry.

Refine the query if needed for better results. For example, add date filters, MeSH terms, or journal restrictions based on the user's intent.

### Step 2: Fetch Article Metadata

For each result, collect:
- PMID
- Title
- Authors (list)
- Journal name
- Publication year
- Abstract text
- MeSH terms (if available)
- DOI (if available)
- PMC ID (if available)

### Step 3: Fetch Full Text (when available)

If `--full-text` is enabled and a PMC ID is present, use the PubMed connector to retrieve the full article text from PubMed Central. Not all articles have full text — this is expected. Abstracts are sufficient for extraction.

### Step 4: Deduplicate

Check the output directory for existing `pmid_*.txt` files. Skip articles already in the corpus.

### Step 5: Write Corpus Files

Build a JSON array of articles and write them to disk:

```bash
echo '<articles_json>' | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/write_pubmed_doc.py <output_dir>
```

The JSON format expected by the script:
```json
{
  "articles": [
    {
      "pmid": "12345678",
      "title": "...",
      "abstract": "...",
      "authors": ["Last First"],
      "journal": "...",
      "year": "2024",
      "mesh_terms": ["term1"],
      "doi": "10.1234/...",
      "pmc_id": "PMC1234567",
      "full_text": "..."
    }
  ]
}
```

**For 10+ articles:** Use the Agent tool to dispatch parallel acquirer agents (batches of 5) for speed.

### Step 6: Report Summary

Tell the user:
- Total articles found vs fetched
- Abstracts vs full-text breakdown
- Duplicates skipped
- MeSH term coverage (top terms across the corpus)
- Output directory location
- Suggest next step: `/epistract-ingest <output_dir>` to build the knowledge graph

### Step 7: Offer Corpus Expansion

If the result set is small (<10 articles), suggest:
- Related search terms the user might try
- PubMed syntax tips (date ranges, MeSH qualifiers, author filters)
- Cross-referencing with related articles from the connector
