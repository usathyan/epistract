#!/usr/bin/env python3
"""Replace short scholar docs with full PubMed abstracts for the same or similar papers."""

import time
from pathlib import Path

import requests
import xml.etree.ElementTree as ET

DOCS_DIR = Path(__file__).parent / "docs"
BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

# Map scholar files to PubMed search queries that should find them
REPLACEMENTS = {
    "scholar_01": {
        "query": '"GLP-1 receptor agonist" AND "pharmaceutical landscape" AND "competitive"',
        "fallback_query": '"GLP-1 receptor agonist" AND "market" AND "landscape" AND 2024',
    },
    "scholar_02": {
        "query": '"GLP-1" AND "bibliometric" AND "landscape"',
        "fallback_query": '"GLP-1 receptor agonist" AND "bibliometric analysis"',
    },
    "scholar_03": {
        "query": '"GLP-1 receptor agonist" AND "Brazil" AND "consumption"',
        "fallback_query": '"GLP-1" AND "Brazil" AND "regulatory"',
    },
    "scholar_04": {
        "query": '"tirzepatide" AND "semaglutide" AND "head-to-head" AND "weight loss"',
        "fallback_query": '"tirzepatide" AND "semaglutide" AND "comparison" AND "systematic review"',
    },
    "scholar_05": {
        "query": '"tirzepatide" AND "semaglutide" AND "weight loss" AND "type 2 diabetes" AND "systematic review"',
        "fallback_query": '"tirzepatide versus semaglutide" AND "weight"',
    },
    "scholar_06": {
        "query": '"semaglutide" AND "tirzepatide" AND "overweight" AND "obesity" AND "JAMA"',
        "fallback_query": '"semaglutide versus tirzepatide" AND "adults"',
    },
    "scholar_07": {
        "query": '"oral" AND "small molecule" AND "GLP-1 receptor agonist" AND "orforglipron" AND "danuglipron"',
        "fallback_query": '"oral nonpeptide GLP-1" AND "review"',
    },
    "scholar_08": {
        "query": '"danuglipron" AND "orforglipron" AND "efficacy" AND "safety"',
        "fallback_query": '"danuglipron" AND "orforglipron" AND "meta-analysis"',
    },
    "scholar_09": {
        "query": '"orforglipron" AND "oral" AND "obesity" AND "adults"',
        "fallback_query": '"orforglipron" AND "obesity" AND "phase"',
    },
}


def search_and_fetch(query: str) -> dict | None:
    resp = requests.get(f"{BASE}/esearch.fcgi", params={
        "db": "pubmed", "term": query, "retmax": 1,
        "sort": "relevance", "retmode": "json",
    })
    ids = resp.json().get("esearchresult", {}).get("idlist", [])
    if not ids:
        return None

    time.sleep(0.5)

    resp = requests.get(f"{BASE}/efetch.fcgi", params={
        "db": "pubmed", "id": ids[0], "rettype": "abstract", "retmode": "xml",
    })
    try:
        root = ET.fromstring(resp.text)
    except ET.ParseError:
        return None

    art = root.find(".//PubmedArticle")
    if art is None:
        return None

    pmid = art.findtext(".//PMID")
    title = art.findtext(".//ArticleTitle") or ""
    abs_parts = art.findall(".//AbstractText")
    if not abs_parts:
        return None
    abstract = " ".join(
        (f"{p.get('Label', '')}: " if p.get('Label') else "") + (p.text or "")
        for p in abs_parts
    )
    if len(abstract) < 100:
        return None

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


if __name__ == "__main__":
    # Track existing PMIDs to avoid duplicates
    existing_pmids = set()
    for f in DOCS_DIR.glob("pmid_*.txt"):
        pmid = f.stem.replace("pmid_", "")
        existing_pmids.add(pmid)
    print(f"Existing PMIDs: {len(existing_pmids)}")

    for prefix, queries in REPLACEMENTS.items():
        # Find the scholar file
        matches = list(DOCS_DIR.glob(f"{prefix}_*.txt"))
        if not matches:
            print(f"\n{prefix}: no file found, skipping")
            continue
        fpath = matches[0]
        print(f"\n{prefix}: {fpath.name}")

        data = search_and_fetch(queries["query"])
        time.sleep(0.5)
        if not data:
            print(f"  Primary query failed, trying fallback...")
            data = search_and_fetch(queries["fallback_query"])
            time.sleep(0.5)

        if not data:
            print(f"  -> No PubMed match found")
            continue

        if data["pmid"] in existing_pmids:
            print(f"  -> PMID {data['pmid']} already exists, removing duplicate scholar file")
            fpath.unlink()
            continue

        existing_pmids.add(data["pmid"])
        mesh_line = f"MeSH Terms: {', '.join(data['mesh'])}\n" if data['mesh'] else ""
        content = (
            f"Title: {data['title']}\n"
            f"Authors: {', '.join(data['authors'][:5])}\n"
            f"Journal: {data['journal']} ({data['year']})\n"
            f"PMID: {data['pmid']}\n"
            f"Source: Google Scholar (enriched via PubMed)\n"
            f"{mesh_line}\n"
            f"ABSTRACT:\n{data['abstract']}\n"
        )
        fpath.write_text(content)
        print(f"  -> Replaced with PMID {data['pmid']}: {data['title'][:70]}... ({len(data['abstract'])} chars)")

    total = len(list(DOCS_DIR.glob("*.txt")))
    print(f"\n=== Total documents: {total} ===")
