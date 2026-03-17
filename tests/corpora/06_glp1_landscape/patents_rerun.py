#!/usr/bin/env python3
"""Re-run Google Patents search with proper API parameters."""

import json
import os
import time

import requests

SERPAPI_KEY = os.environ["SERPAPI_API_KEY"]

QUERIES = [
    {
        "q": "GLP-1 receptor agonist peptide",
        "assignee": "Novo Nordisk",
        "after": "filing:20150101",
        "country": "US",
        "status": "GRANT",
        "num": 10,
    },
    {
        "q": "GIP GLP-1 dual agonist tirzepatide",
        "assignee": "Eli Lilly",
        "country": "US",
        "status": "GRANT",
        "num": 10,
    },
    {
        "q": "GLP-1 receptor agonist small molecule oral nonpeptide",
        "country": "US,WO",
        "after": "filing:20170101",
        "num": 10,
    },
    {
        "q": "GLP-1 GIP glucagon triple agonist",
        "country": "US,WO",
        "after": "filing:20180101",
        "num": 10,
    },
    {
        "q": "semaglutide oral tablet formulation SNAC",
        "country": "US",
        "num": 10,
    },
]


def search_patents(params: dict) -> list[dict]:
    params["engine"] = "google_patents"
    params["api_key"] = SERPAPI_KEY
    resp = requests.get("https://serpapi.com/search", params=params)
    data = resp.json()
    results = []
    for r in data.get("organic_results", []):
        results.append({
            "title": r.get("title", ""),
            "patent_id": r.get("patent_id", ""),
            "assignee": r.get("assignee", ""),
            "filing_date": r.get("filing_date", ""),
            "publication_date": r.get("grant_date", r.get("publication_date", "")),
            "snippet": r.get("snippet", ""),
            "pdf": r.get("pdf", ""),
            "thumbnail": r.get("thumbnail", ""),
        })
    return results


if __name__ == "__main__":
    all_results = []
    seen_ids = set()

    for params in QUERIES:
        label = f"{params['q'][:50]} | {params.get('assignee', 'any')}"
        print(f"\n=== {label} ===")
        results = search_patents(params)
        for r in results:
            pid = r["patent_id"]
            if pid in seen_ids:
                continue
            seen_ids.add(pid)
            all_results.append(r)
            print(f"  {pid:20s} | {r['assignee'][:30]:30s} | {r['filing_date']:12s} | {r['title'][:70]}")
            if r["snippet"]:
                print(f"  {'':20s} | snippet: {r['snippet'][:120]}...")
        time.sleep(1.5)

    out_path = "/Users/umeshbhatt/code/epistract/tests/corpora/06_glp1_landscape/patents_raw_results.json"
    with open(out_path, "w") as f:
        json.dump(all_results, f, indent=2)

    print(f"\n=== Total unique patents: {len(all_results)} ===")
