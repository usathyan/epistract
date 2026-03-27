#!/usr/bin/env python3
"""Write PubMed article metadata to the epistract corpus text format.

Produces plain-text files matching the format used by existing test corpora
(Title, Authors, Journal, PMID, MeSH, ABSTRACT), so that /epistract-ingest
can process them without modification.

Usage:
    echo '<json>' | python write_pubmed_doc.py <output_dir>
    python write_pubmed_doc.py <output_dir> --json '<json>'

Input JSON schema:
    {
        "articles": [
            {
                "pmid": "12345678",
                "title": "...",
                "abstract": "...",
                "authors": ["Last First", ...],
                "journal": "...",
                "year": "2024",
                "mesh_terms": ["term1", "term2"],
                "pmc_id": "PMC1234567",       // optional
                "doi": "10.1234/...",          // optional
                "full_text": "..."             // optional, from PMC
            }
        ]
    }

Output:
    <output_dir>/docs/pmid_<PMID>.txt  (one per article)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def write_article(article: dict, docs_dir: Path) -> str | None:
    """Write a single article to the corpus directory.

    Returns the filename written, or None if skipped.
    """
    pmid = article.get("pmid", "").strip()
    if not pmid:
        return None

    title = article.get("title", "").strip()
    abstract = article.get("abstract", "").strip()
    full_text = article.get("full_text", "").strip()

    # Skip articles with no usable text
    if not abstract and not full_text:
        return None

    authors = article.get("authors", [])
    if isinstance(authors, str):
        authors = [a.strip() for a in authors.split(",")]
    author_line = ", ".join(authors[:10])

    journal = article.get("journal", "").strip()
    year = article.get("year", "").strip()
    mesh_terms = article.get("mesh_terms", [])
    doi = article.get("doi", "").strip()
    pmc_id = article.get("pmc_id", "").strip()

    # Build metadata header
    lines = [
        f"Title: {title}",
        f"Authors: {author_line}",
        f"Journal: {journal} ({year})" if year else f"Journal: {journal}",
        f"PMID: {pmid}",
    ]
    if doi:
        lines.append(f"DOI: {doi}")
    if pmc_id:
        lines.append(f"PMC: {pmc_id}")
    lines.append("Source: PubMed via Claude PubMed Connector")
    if mesh_terms:
        lines.append(f"MeSH Terms: {', '.join(mesh_terms)}")

    # Body: prefer full text when available, fall back to abstract
    if full_text:
        lines.append("")
        lines.append("FULL TEXT:")
        lines.append(full_text)
    elif abstract:
        lines.append("")
        lines.append("ABSTRACT:")
        lines.append(abstract)

    fname = f"pmid_{pmid}.txt"
    out_path = docs_dir / fname
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return fname


def main() -> None:
    args = sys.argv[1:]

    if not args:
        print(
            f"Usage: {sys.argv[0]} <output_dir> [--json '<json>']",
            file=sys.stderr,
        )
        sys.exit(1)

    output_dir = Path(args[0])
    docs_dir = output_dir / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)

    # Read input JSON
    if "--json" in args:
        data = json.loads(args[args.index("--json") + 1])
    else:
        data = json.load(sys.stdin)

    articles = data.get("articles", [])
    if not articles:
        print("No articles in input", file=sys.stderr)
        sys.exit(1)

    # Check for existing PMIDs to avoid duplicates
    existing_pmids: set[str] = set()
    for f in docs_dir.glob("pmid_*.txt"):
        existing_pmids.add(f.stem.removeprefix("pmid_"))

    written = []
    skipped_dup = 0
    skipped_empty = 0

    for article in articles:
        pmid = article.get("pmid", "").strip()
        if pmid in existing_pmids:
            skipped_dup += 1
            continue

        fname = write_article(article, docs_dir)
        if fname:
            written.append(fname)
            existing_pmids.add(pmid)
        else:
            skipped_empty += 1

    print(json.dumps({
        "docs_dir": str(docs_dir),
        "written": len(written),
        "skipped_duplicate": skipped_dup,
        "skipped_empty": skipped_empty,
        "files": written,
    }, indent=2))


if __name__ == "__main__":
    main()
