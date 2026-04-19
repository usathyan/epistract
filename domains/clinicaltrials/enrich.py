#!/usr/bin/env python3
"""ClinicalTrials.gov + PubChem enrichment for the clinicaltrials domain.

Post-build enrichment step invoked by /epistract:ingest when --enrich is
passed with --domain clinicaltrials. Reads the built graph via
sift_kg.KnowledgeGraph.load(), patches Trial nodes with CT.gov v2 metadata
(overall_status, phase, enrollment, dates, title) and Compound nodes with
PubChem PUG REST molecular data (CID, formula, weight, SMILES, InChI),
then saves and writes _enrichment_report.json.

Non-blocking: API failures log counts but never abort the pipeline.
ARCH-03: no core/ changes required; this module lives in the domain package.

Usage:
    python3 domains/clinicaltrials/enrich.py <output_dir>
"""
from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

NCT_PATTERN = re.compile(r"NCT\d{8}", re.IGNORECASE)

CTGOV_URL = "https://clinicaltrials.gov/api/v2/studies/{nct_id}"
CTGOV_TIMEOUT = 15
CTGOV_RATE_SLEEP = 0.1  # per-request courtesy delay (CT.gov has no documented limit)

PUBCHEM_PROPS = "MolecularFormula,MolecularWeight,CanonicalSMILES,InChI"
PUBCHEM_URL = (
    "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{name}/"
    "property/{props}/JSON"
)
PUBCHEM_TIMEOUT = 30
PUBCHEM_RATE_SLEEP = 0.2  # 5 req/sec official limit
PUBCHEM_MAX_RETRIES = 3

# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def _extract_nct_id(text: str) -> str | None:
    """Return the first NCT number in text, uppercased, or None."""
    if not text:
        return None
    m = NCT_PATTERN.search(text)
    return m.group().upper() if m else None


def _fetch_ct_gov(nct_id: str) -> dict | None:
    """Fetch trial metadata from ClinicalTrials.gov v2 API.

    Returns a flat dict with ct_* keys, or None on 404 / any error.
    """
    try:
        resp = requests.get(CTGOV_URL.format(nct_id=nct_id), timeout=CTGOV_TIMEOUT)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        body = resp.json()
    except (requests.RequestException, ValueError):
        return None

    ps = body.get("protocolSection", {}) or {}
    id_mod = ps.get("identificationModule", {}) or {}
    status_mod = ps.get("statusModule", {}) or {}
    design_mod = ps.get("designModule", {}) or {}
    phases = design_mod.get("phases") or []
    enrollment_info = design_mod.get("enrollmentInfo") or {}
    start_struct = status_mod.get("startDateStruct") or {}
    completion_struct = status_mod.get("completionDateStruct") or {}
    return {
        "ct_overall_status": status_mod.get("overallStatus"),
        "ct_phase": phases[0] if phases else None,
        "ct_enrollment": enrollment_info.get("count"),
        "ct_start_date": start_struct.get("date"),
        "ct_completion_date": completion_struct.get("date"),
        "ct_brief_title": id_mod.get("briefTitle"),
    }


def _fetch_pubchem(compound_name: str) -> dict | None:
    """Fetch molecular data from PubChem PUG REST.

    Retries up to PUBCHEM_MAX_RETRIES times on 429 with exponential backoff.
    Reads ConnectivitySMILES from response (PubChem API quirk — see
    21-RESEARCH.md Pitfall 2: the request asks for CanonicalSMILES but the
    JSON response always returns the key 'ConnectivitySMILES').
    Returns None on 404 or after exhausted retries.
    """
    url = PUBCHEM_URL.format(
        name=requests.utils.quote(compound_name),
        props=PUBCHEM_PROPS,
    )
    for attempt in range(PUBCHEM_MAX_RETRIES):
        try:
            resp = requests.get(url, timeout=PUBCHEM_TIMEOUT)
            if resp.status_code == 404:
                return None
            if resp.status_code == 429:
                time.sleep(2 ** attempt)
                continue
            resp.raise_for_status()
            body = resp.json()
        except (requests.RequestException, ValueError):
            if attempt == PUBCHEM_MAX_RETRIES - 1:
                return None
            time.sleep(2 ** attempt)
            continue

        props_list = (body.get("PropertyTable") or {}).get("Properties") or []
        if not props_list:
            return None
        p = props_list[0]
        return {
            "pubchem_cid": p.get("CID"),
            "molecular_formula": p.get("MolecularFormula"),
            "molecular_weight": p.get("MolecularWeight"),
            # CRITICAL: response key is ConnectivitySMILES (Pitfall 2)
            "canonical_smiles": p.get("ConnectivitySMILES"),
            "inchi": p.get("InChI"),
        }
    return None


# ---------------------------------------------------------------------------
# Main enrichment function
# ---------------------------------------------------------------------------


def enrich_graph(output_dir: Path, domain: str = "clinicaltrials") -> dict:
    """Load graph, enrich Trial + Compound nodes, save, write report.

    Args:
        output_dir: Directory containing graph_data.json.
        domain: Domain name stamped into the report.

    Returns:
        Report dict with domain, trials counts, compounds counts, hit_rate.
    """
    output_dir = Path(output_dir)
    graph_path = output_dir / "graph_data.json"
    if not graph_path.exists():
        report = _build_report(domain, 0, 0, 0, 0, 0, 0, 0, 0)
        _write_report(output_dir, report)
        return report

    # Load via sift-kg; fall back to raw JSON if sift-kg is unavailable
    try:
        from sift_kg import KnowledgeGraph
        kg = KnowledgeGraph.load(graph_path)
        node_iter = list(kg.graph.nodes(data=True))
    except ImportError:
        kg = None
        raw = json.loads(graph_path.read_text())
        node_iter = [(n.get("id"), n) for n in raw.get("nodes", [])]

    trials_total = trials_enriched = trials_not_found = trials_failed = 0
    compounds_total = compounds_enriched = compounds_not_found = compounds_failed = 0

    for node_id, data in node_iter:
        etype = str(data.get("entity_type", "")).lower()
        if etype == "trial":
            trials_total += 1
            # Look for NCT ID in name first, then attributes, then context
            candidate = _extract_nct_id(str(data.get("name", "")))
            if not candidate:
                attrs = data.get("attributes") or {}
                if isinstance(attrs, dict):
                    candidate = _extract_nct_id(str(attrs.get("nct_id", "")))
            if not candidate:
                candidate = _extract_nct_id(str(data.get("context", "")))
            if not candidate:
                trials_not_found += 1
                continue
            time.sleep(CTGOV_RATE_SLEEP)
            enrichment = _fetch_ct_gov(candidate)
            if enrichment:
                data.update(enrichment)
                trials_enriched += 1
            else:
                trials_failed += 1
        elif etype == "compound":
            compounds_total += 1
            name = str(data.get("name", "")).strip()
            if not name:
                compounds_not_found += 1
                continue
            time.sleep(PUBCHEM_RATE_SLEEP)
            enrichment = _fetch_pubchem(name)
            if enrichment:
                data.update(enrichment)
                compounds_enriched += 1
            else:
                compounds_failed += 1

    # Persist mutations
    if kg is not None:
        kg.save(graph_path)
    else:
        # Non-sift-kg path: write back raw JSON (best effort)
        raw_nodes = [data for _, data in node_iter]
        raw_data = json.loads(graph_path.read_text())
        raw_data["nodes"] = raw_nodes
        graph_path.write_text(json.dumps(raw_data, indent=2))

    report = _build_report(
        domain,
        trials_total, trials_enriched, trials_not_found, trials_failed,
        compounds_total, compounds_enriched, compounds_not_found, compounds_failed,
    )
    _write_report(output_dir, report)
    return report


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _build_report(
    domain: str,
    t_total: int, t_enriched: int, t_not_found: int, t_failed: int,
    c_total: int, c_enriched: int, c_not_found: int, c_failed: int,
) -> dict:
    """Build the enrichment report dict matching 21-RESEARCH.md schema."""
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "domain": domain,
        "trials": {
            "total": t_total,
            "enriched": t_enriched,
            "not_found": t_not_found,
            "failed": t_failed,
        },
        "compounds": {
            "total": c_total,
            "enriched": c_enriched,
            "not_found": c_not_found,
            "failed": c_failed,
        },
        "hit_rate": {
            "trials": round(t_enriched / t_total, 3) if t_total else 0.0,
            "compounds": round(c_enriched / c_total, 3) if c_total else 0.0,
        },
    }


def _write_report(output_dir: Path, report: dict) -> Path | None:
    """Write _enrichment_report.json under <output_dir>/extractions/.

    Returns the path on success, or None if the directory cannot be created
    (e.g., output_dir is a nonexistent path on a read-only filesystem).
    """
    try:
        extractions_dir = output_dir / "extractions"
        extractions_dir.mkdir(parents=True, exist_ok=True)
        report_path = extractions_dir / "_enrichment_report.json"
        report_path.write_text(json.dumps(report, indent=2))
        return report_path
    except OSError:
        return None


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in ("--help", "-h"):
        print(__doc__)
        sys.exit(0 if "--help" in sys.argv or "-h" in sys.argv else 1)
    report = enrich_graph(Path(sys.argv[1]))
    print(json.dumps(report, indent=2))
