#!/usr/bin/env python3
"""Replace short scholar docs with full abstracts by searching PubMed for the same topics."""

import time
from pathlib import Path

import requests
import xml.etree.ElementTree as ET

DOCS_DIR = Path(__file__).parent / "docs"
BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def fetch_by_pmid(pmid: str) -> dict | None:
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
    abstract = " ".join(
        (f"{p.get('Label', '')}: " if p.get('Label') else "") + (p.text or "")
        for p in abs_parts
    ) if abs_parts else ""

    authors = []
    for au in art.findall(".//Author"):
        ln = au.findtext("LastName") or ""
        fn = au.findtext("ForeName") or ""
        if ln:
            authors.append(f"{ln} {fn}".strip())

    journal = art.findtext(".//Journal/Title") or ""
    year = art.findtext(".//PubDate/Year") or ""
    mesh = [m.text for m in art.findall(".//MeshHeading/DescriptorName") if m.text]

    return {"pmid": pmid, "title": title, "abstract": abstract,
            "authors": authors, "journal": journal, "year": year, "mesh": mesh}


def search_pmids(query: str, max_results: int = 1) -> list[str]:
    resp = requests.get(f"{BASE}/esearch.fcgi", params={
        "db": "pubmed", "term": query, "retmax": max_results,
        "sort": "relevance", "retmode": "json",
    })
    return resp.json().get("esearchresult", {}).get("idlist", [])


def write_doc(data: dict, fname: str, source_note: str = "PubMed"):
    mesh_line = f"MeSH Terms: {', '.join(data['mesh'])}\n" if data['mesh'] else ""
    content = (
        f"Title: {data['title']}\n"
        f"Authors: {', '.join(data['authors'][:5])}\n"
        f"Journal: {data['journal']} ({data['year']})\n"
        f"PMID: {data['pmid']}\n"
        f"Source: {source_note}\n"
        f"{mesh_line}\n"
        f"ABSTRACT:\n{data['abstract']}\n"
    )
    (DOCS_DIR / fname).write_text(content)
    print(f"  Written: {fname} ({len(data['abstract'])} chars)")


if __name__ == "__main__":
    # Get existing PMIDs
    existing_pmids = set()
    for f in DOCS_DIR.glob("*.txt"):
        content = f.read_text()
        for line in content.split('\n'):
            if line.startswith("PMID:"):
                existing_pmids.add(line.split(":")[1].strip())

    print(f"Existing PMIDs: {len(existing_pmids)}")

    # Remove all scholar files (they're too short) and replace with proper PubMed papers
    for f in sorted(DOCS_DIR.glob("scholar_*.txt")):
        print(f"  Removing short scholar file: {f.name}")
        f.unlink()

    # Now fetch targeted papers that cover the Scholar topics
    PAPERS = [
        # Semaglutide vs tirzepatide comparison
        ("semaglutide tirzepatide comparison weight loss real-world", "Google Scholar topic: head-to-head comparison"),
        # Oral GLP-1 landscape
        ("oral nonpeptide GLP-1 receptor agonist review 2024", "Google Scholar topic: oral GLP-1 landscape"),
        # GLP-1 competitive landscape / market
        ("GLP-1 receptor agonist landscape obesity review 2024", "Google Scholar topic: GLP-1 competitive landscape"),
        # Danuglipron vs orforglipron
        ("danuglipron orforglipron efficacy safety comparison", "Google Scholar topic: oral small molecule comparison"),
        # GLP-1 and kidney disease
        ("GLP-1 receptor agonist chronic kidney disease CKD", "Emerging indication: CKD"),
        # GLP-1 and sleep apnea
        ("semaglutide obstructive sleep apnea", "Emerging indication: sleep apnea"),
        # GLP-1 and PCOS
        ("GLP-1 receptor agonist polycystic ovary syndrome PCOS", "Emerging indication: PCOS"),
    ]

    for query, source_note in PAPERS:
        print(f"\nSearching: {query[:60]}...")
        ids = search_pmids(query, max_results=1)
        time.sleep(0.5)

        if not ids:
            print(f"  -> No results")
            continue

        pmid = ids[0]
        if pmid in existing_pmids:
            print(f"  -> PMID {pmid} already in corpus")
            continue

        data = fetch_by_pmid(pmid)
        time.sleep(0.5)

        if not data or len(data.get("abstract", "")) < 100:
            print(f"  -> PMID {pmid} has no/short abstract")
            continue

        existing_pmids.add(pmid)
        fname = f"pmid_{pmid}.txt"
        write_doc(data, fname, source_note)

    total = len(list(DOCS_DIR.glob("*.txt")))
    print(f"\n=== Total documents: {total} ===")
