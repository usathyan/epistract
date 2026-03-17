#!/usr/bin/env python3
"""Assemble S6 GLP-1 corpus from PubMed, Google Scholar, and Google Patents via SerpAPI."""

import json
import os
import re
import time
from pathlib import Path

import requests

DOCS_DIR = Path(__file__).parent / "docs"
DOCS_DIR.mkdir(exist_ok=True)

SERPAPI_KEY = os.environ["SERPAPI_API_KEY"]

# ── PubMed via Entrez ──────────────────────────────────────────────────────

PUBMED_QUERIES = [
    # Core GLP-1 RA clinical landscape
    '"semaglutide" AND "cardiovascular" AND "clinical trial"',
    '"tirzepatide" AND "obesity" AND "efficacy"',
    '"orforglipron" AND "oral" AND "GLP-1"',
    '"survodutide" AND "NASH"',
    '"retatrutide" AND "triple agonist"',
    '"CagriSema" AND "obesity"',
    # Emerging indications
    '"GLP-1 receptor agonist" AND "Alzheimer"',
    '"semaglutide" AND "MASH" OR "NASH"',
    '"GLP-1" AND "addiction" AND "alcohol"',
]


def fetch_pubmed(query: str, max_results: int = 2) -> list[dict]:
    """Fetch abstracts from PubMed E-utilities."""
    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    # Search
    resp = requests.get(f"{base}/esearch.fcgi", params={
        "db": "pubmed", "term": query, "retmax": max_results,
        "sort": "relevance", "retmode": "json",
    })
    ids = resp.json().get("esearchresult", {}).get("idlist", [])
    if not ids:
        return []

    time.sleep(0.5)  # rate limit between search and fetch

    # Fetch
    resp = requests.get(f"{base}/efetch.fcgi", params={
        "db": "pubmed", "id": ",".join(ids), "rettype": "abstract", "retmode": "xml",
    })

    import xml.etree.ElementTree as ET
    try:
        root = ET.fromstring(resp.text)
    except ET.ParseError:
        print(f"  [PubMed] XML parse error for query: {query[:50]}... skipping")
        return []
    articles = []
    for art in root.findall(".//PubmedArticle"):
        pmid = art.findtext(".//PMID")
        title = art.findtext(".//ArticleTitle") or ""
        abstract = art.findtext(".//AbstractText") or ""
        # Some abstracts have multiple sections
        abs_parts = art.findall(".//AbstractText")
        if len(abs_parts) > 1:
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

        if abstract and len(abstract) > 100:
            articles.append({
                "pmid": pmid, "title": title, "abstract": abstract,
                "authors": authors, "journal": journal, "year": year,
                "mesh": mesh_terms,
            })
    return articles


# ── SerpAPI Google Scholar ─────────────────────────────────────────────────

SCHOLAR_QUERIES = [
    "GLP-1 receptor agonist competitive landscape 2024",
    "semaglutide tirzepatide head-to-head comparison",
    "oral GLP-1 agonist orforglipron danuglipron clinical",
]


def fetch_scholar(query: str, max_results: int = 3) -> list[dict]:
    """Fetch from Google Scholar via SerpAPI."""
    resp = requests.get("https://serpapi.com/search", params={
        "engine": "google_scholar", "q": query, "num": max_results,
        "api_key": SERPAPI_KEY,
    })
    data = resp.json()
    results = []
    for r in data.get("organic_results", [])[:max_results]:
        title = r.get("title", "")
        snippet = r.get("snippet", "")
        pub_info = r.get("publication_info", {}).get("summary", "")
        link = r.get("link", "")
        if snippet and len(snippet) > 50:
            results.append({
                "source": "google_scholar",
                "title": title,
                "snippet": snippet,
                "pub_info": pub_info,
                "link": link,
            })
    return results


# ── SerpAPI Google Patents ─────────────────────────────────────────────────

PATENT_QUERIES = [
    "GLP-1 receptor agonist peptide semaglutide analog",
    "tirzepatide GIP GLP-1 dual agonist composition",
    "oral GLP-1 small molecule agonist",
]


def fetch_patents(query: str, max_results: int = 2) -> list[dict]:
    """Fetch from Google Patents via SerpAPI."""
    resp = requests.get("https://serpapi.com/search", params={
        "engine": "google_patents", "q": query, "num": max_results,
        "api_key": SERPAPI_KEY,
    })
    data = resp.json()
    results = []
    for r in data.get("organic_results", [])[:max_results]:
        title = r.get("title", "")
        snippet = r.get("snippet", "")
        patent_id = r.get("patent_id", r.get("publication_number", ""))
        assignee = r.get("assignee", "")
        filing_date = r.get("filing_date", r.get("priority_date", ""))
        pdf_link = r.get("pdf", "")
        if snippet and len(snippet) > 50:
            results.append({
                "source": "google_patents",
                "title": title,
                "snippet": snippet,
                "patent_id": patent_id,
                "assignee": assignee,
                "filing_date": filing_date,
                "pdf_link": pdf_link,
            })
    return results


# ── Write documents ────────────────────────────────────────────────────────

def write_pubmed_doc(art: dict):
    fname = f"pmid_{art['pmid']}.txt"
    path = DOCS_DIR / fname
    if path.exists():
        return
    mesh_line = f"MeSH Terms: {', '.join(art['mesh'])}\n" if art['mesh'] else ""
    content = (
        f"Title: {art['title']}\n"
        f"Authors: {', '.join(art['authors'][:5])}\n"
        f"Journal: {art['journal']} ({art['year']})\n"
        f"PMID: {art['pmid']}\n"
        f"{mesh_line}\n"
        f"ABSTRACT:\n{art['abstract']}\n"
    )
    path.write_text(content)
    print(f"  [PubMed] {fname}: {art['title'][:80]}")


def write_scholar_doc(r: dict, idx: int):
    slug = re.sub(r'[^a-z0-9]+', '_', r['title'].lower())[:60].strip('_')
    fname = f"scholar_{idx:02d}_{slug}.txt"
    path = DOCS_DIR / fname
    if path.exists():
        return
    content = (
        f"Title: {r['title']}\n"
        f"Source: Google Scholar\n"
        f"Publication Info: {r['pub_info']}\n"
        f"URL: {r['link']}\n\n"
        f"ABSTRACT:\n{r['snippet']}\n"
    )
    path.write_text(content)
    print(f"  [Scholar] {fname}: {r['title'][:80]}")


def write_patent_doc(r: dict, idx: int):
    pid = re.sub(r'[^A-Za-z0-9]+', '_', r['patent_id'] or f"patent_{idx}")
    fname = f"patent_{idx:02d}_{pid}.txt"
    path = DOCS_DIR / fname
    if path.exists():
        return
    content = (
        f"Title: {r['title']}\n"
        f"Source: Google Patents\n"
        f"Patent ID: {r['patent_id']}\n"
        f"Assignee: {r['assignee']}\n"
        f"Filing Date: {r['filing_date']}\n"
        f"PDF: {r['pdf_link']}\n\n"
        f"ABSTRACT/DESCRIPTION:\n{r['snippet']}\n"
    )
    path.write_text(content)
    print(f"  [Patent] {fname}: {r['title'][:80]}")


# ── Main ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    seen_pmids = set()

    # PubMed
    print("=== PubMed ===")
    for q in PUBMED_QUERIES:
        articles = fetch_pubmed(q, max_results=2)
        for a in articles:
            if a["pmid"] not in seen_pmids:
                seen_pmids.add(a["pmid"])
                write_pubmed_doc(a)
        time.sleep(1.0)  # NCBI rate limit

    # Google Scholar
    print("\n=== Google Scholar ===")
    scholar_idx = 0
    for q in SCHOLAR_QUERIES:
        results = fetch_scholar(q, max_results=3)
        for r in results:
            scholar_idx += 1
            write_scholar_doc(r, scholar_idx)
        time.sleep(1)

    # Google Patents
    print("\n=== Google Patents ===")
    patent_idx = 0
    for q in PATENT_QUERIES:
        results = fetch_patents(q, max_results=2)
        for r in results:
            patent_idx += 1
            write_patent_doc(r, patent_idx)
        time.sleep(1)

    total = len(list(DOCS_DIR.glob("*.txt")))
    print(f"\n=== Total documents: {total} ===")
