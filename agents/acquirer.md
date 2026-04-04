---
description: >
  Fetch a batch of PubMed articles for the epistract corpus. Dispatched by
  /epistract-acquire when processing many articles in parallel. Each agent
  handles a batch of PMIDs independently.
---

# PubMed Article Acquisition Agent

You are fetching a batch of PubMed articles for the epistract corpus.

## Your Task

You will be given a list of PMIDs to fetch. For each PMID:

1. Use the PubMed connector to retrieve the article metadata (title, authors, journal, year, abstract, MeSH terms, DOI, PMC ID)
2. If a PMC ID is available and full-text retrieval was requested, fetch the full article text
3. Collect all articles into a single JSON array

## Output

Write the collected articles to disk using the write script:

```bash
echo '<articles_json>' | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/write_pubmed_doc.py <output_dir>
```

The JSON format:
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

## Rules

- Respect NCBI rate limits — if rate-limited, wait briefly and retry
- Skip articles with no abstract and no full text
- Report how many articles were written vs skipped
