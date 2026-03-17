#!/usr/bin/env python3
"""Enrich scholar docs by finding the same papers on PubMed and getting full abstracts."""

import re
import time
from pathlib import Path

import requests
import xml.etree.ElementTree as ET

DOCS_DIR = Path(__file__).parent / "docs"
BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def search_pubmed(title: str) -> str | None:
    """Search PubMed by title, return PMID if found."""
    # Use first 100 chars of title for search
    query = title[:100].replace('"', '').strip()
    resp = requests.get(f"{BASE}/esearch.fcgi", params={
        "db": "pubmed", "term": f'"{query}"[Title]',
        "retmax": 1, "retmode": "json",
    })
    ids = resp.json().get("esearchresult", {}).get("idlist", [])
    return ids[0] if ids else None


def fetch_abstract(pmid: str) -> dict | None:
    """Fetch full abstract from PubMed."""
    resp = requests.get(f"{BASE}/efetch.fcgi", params={
        "db": "pubmed", "id": pmid, "rettype": "abstract", "retmode": "xml",
    })
    try:
        root = ET.fromstring(resp.text)
    except ET.ParseError:
        return None

    art = root.find(".//PubmedArticle")
    if art is None:
        return None

    title = art.findtext(".//ArticleTitle") or ""
    abs_parts = art.findall(".//AbstractText")
    if not abs_parts:
        return None

    abstract = " ".join(
        (f"{p.get('Label', '')}: " if p.get('Label') else "") + (p.text or "")
        for p in abs_parts
    )

    authors = []
    for au in art.findall(".//Author"):
        ln = au.findtext("LastName") or ""
        fn = au.findtext("ForeName") or ""
        if ln:
            authors.append(f"{ln} {fn}".strip())

    journal = art.findtext(".//Journal/Title") or ""
    year = art.findtext(".//PubDate/Year") or art.findtext(".//PubDate/MedlineDate") or ""
    mesh_terms = [m.text for m in art.findall(".//MeshHeading/DescriptorName") if m.text]

    return {
        "pmid": pmid, "title": title, "abstract": abstract,
        "authors": authors, "journal": journal, "year": year,
        "mesh": mesh_terms,
    }


def enrich_scholar_file(fpath: Path):
    """Try to find paper on PubMed and replace with full abstract."""
    content = fpath.read_text()
    title_match = re.search(r'^Title:\s*(.+)', content, re.MULTILINE)
    if not title_match:
        return

    title = title_match.group(1).strip()
    print(f"  Searching: {title[:80]}...")

    pmid = search_pubmed(title)
    time.sleep(0.5)

    if not pmid:
        print(f"    -> Not found on PubMed")
        return

    data = fetch_abstract(pmid)
    time.sleep(0.5)

    if not data or len(data["abstract"]) < 100:
        print(f"    -> PMID {pmid} but abstract too short or missing")
        return

    # Check if we already have this PMID as a separate file
    existing = DOCS_DIR / f"pmid_{pmid}.txt"
    if existing.exists():
        print(f"    -> Already have pmid_{pmid}.txt, removing scholar duplicate")
        fpath.unlink()
        return

    # Rewrite the scholar file with full PubMed data
    url_match = re.search(r'^URL:\s*(.+)', content, re.MULTILINE)
    url = url_match.group(1).strip() if url_match else ""
    pub_info_match = re.search(r'^Publication Info:\s*(.+)', content, re.MULTILINE)
    pub_info = pub_info_match.group(1).strip() if pub_info_match else ""

    mesh_line = f"MeSH Terms: {', '.join(data['mesh'])}\n" if data['mesh'] else ""
    new_content = (
        f"Title: {data['title']}\n"
        f"Authors: {', '.join(data['authors'][:5])}\n"
        f"Journal: {data['journal']} ({data['year']})\n"
        f"PMID: {data['pmid']}\n"
        f"Source: Google Scholar → PubMed\n"
        f"Scholar URL: {url}\n"
        f"{mesh_line}\n"
        f"ABSTRACT:\n{data['abstract']}\n"
    )
    fpath.write_text(new_content)
    print(f"    -> Enriched with PMID {pmid} ({len(data['abstract'])} chars)")


if __name__ == "__main__":
    print("=== Enriching Scholar documents ===")
    for fpath in sorted(DOCS_DIR.glob("scholar_*.txt")):
        enrich_scholar_file(fpath)
        time.sleep(0.5)

    # Final count
    total = len(list(DOCS_DIR.glob("*.txt")))
    print(f"\n=== Total documents: {total} ===")
