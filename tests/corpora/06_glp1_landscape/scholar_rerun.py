#!/usr/bin/env python3
"""Re-run Google Scholar queries with full API params to discover papers/patents beyond PubMed."""

import json
import os
import time

import requests

SERPAPI_KEY = os.environ["SERPAPI_API_KEY"]

QUERIES = [
    # CI-focused queries
    "GLP-1 receptor agonist competitive landscape pipeline 2024",
    "semaglutide tirzepatide orforglipron clinical comparison",
    "GLP-1 agonist patent peptide sequence molecular structure",
    # Emerging indications
    "semaglutide Alzheimer neurodegeneration neuroprotection",
    "GLP-1 agonist addiction alcohol substance use",
    # Triple agonists / next-gen
    "retatrutide survodutide triple agonist GIP GLP-1 glucagon",
    "CagriSema amylin semaglutide combination obesity",
    # Oral small molecule
    "orforglipron danuglipron oral small molecule GLP-1 nonpeptide",
]


def search_scholar(query: str) -> list[dict]:
    resp = requests.get("https://serpapi.com/search", params={
        "engine": "google_scholar",
        "q": query,
        "num": 10,
        "as_sdt": "7",       # include patents
        "scisbd": "0",       # relevance sort
        "api_key": SERPAPI_KEY,
    })
    data = resp.json()
    results = []
    for r in data.get("organic_results", []):
        results.append({
            "title": r.get("title", ""),
            "link": r.get("link", ""),
            "snippet": r.get("snippet", ""),
            "pub_info": r.get("publication_info", {}).get("summary", ""),
            "cited_by": r.get("inline_links", {}).get("cited_by", {}).get("total", 0),
            "type": r.get("type", ""),
            "result_id": r.get("result_id", ""),
        })
    return results


if __name__ == "__main__":
    all_results = []
    seen_titles = set()

    for q in QUERIES:
        print(f"\n=== Query: {q[:70]} ===")
        results = search_scholar(q)
        for r in results:
            title_key = r["title"].lower().strip()
            if title_key in seen_titles:
                continue
            seen_titles.add(title_key)
            all_results.append(r)

            # Flag if it looks like a patent
            is_patent = "patent" in r["link"].lower() or r["type"] == "Patent"
            tag = " [PATENT]" if is_patent else ""
            print(f"  {r['cited_by']:>5} cites | {r['title'][:80]}{tag}")
            print(f"           | {r['pub_info'][:80]}")
            print(f"           | {r['link'][:80]}")
            if r["snippet"]:
                print(f"           | snippet: {r['snippet'][:120]}...")
            print()

        time.sleep(1.5)

    # Save raw results for review
    out_path = "/Users/umeshbhatt/code/epistract/tests/corpora/06_glp1_landscape/scholar_raw_results.json"
    with open(out_path, "w") as f:
        json.dump(all_results, f, indent=2)

    print(f"\n=== Total unique results: {len(all_results)} ===")
    print(f"Saved to {out_path}")

    # Count patents
    patents = [r for r in all_results if "patent" in r["link"].lower() or r["type"] == "Patent"]
    print(f"Patents found: {len(patents)}")
