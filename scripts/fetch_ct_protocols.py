#!/usr/bin/env python3
"""Fetch ClinicalTrials.gov v2 study records into a text corpus for S7.

Pulls the key GLP-1 Phase 3 trials the S6 narrator flagged as "missing from
the graph" — SURPASS, SURMOUNT, STEP, PIONEER, SUSTAIN, ACHIEVE. Writes one
plaintext file per trial into <output_dir>/docs/ with enough structured
content (title, phase, status, enrollment, arms, primary/secondary outcomes,
eligibility) for the extractor to build a rich knowledge graph.

Usage:
    python scripts/fetch_ct_protocols.py <output_dir>
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


# GLP-1 Phase 3 / pivotal trials called out by the S6 narrator or directly
# relevant to the competitive-intelligence narrative.
NCT_IDS = [
    ("NCT03987919", "SURPASS-2"),       # tirzepatide vs semaglutide in T2DM
    ("NCT04184622", "SURMOUNT-1"),      # tirzepatide in obesity
    ("NCT03548935", "STEP-1"),          # semaglutide in obesity
    ("NCT03552757", "STEP-2"),          # semaglutide in T2DM + obesity
    ("NCT03611582", "STEP-3"),          # semaglutide + intensive behavioral therapy
    ("NCT02906930", "PIONEER-1"),       # oral semaglutide monotherapy
    ("NCT02692716", "PIONEER-6"),       # oral semaglutide CV outcomes
    ("NCT01720446", "SUSTAIN-6"),       # semaglutide CV outcomes
    ("NCT05715307", "ACHIEVE-1"),       # orforglipron in T2DM
    ("NCT05822830", "SURMOUNT-5"),      # tirzepatide vs semaglutide in obesity
]


def fetch(nct_id: str) -> dict | None:
    """Fetch a CT.gov v2 study record using stdlib urllib.

    httpx (and requests) default headers trigger a 403 from CT.gov's
    envoy front-end; urllib's leaner profile is accepted.
    """
    url = f"https://clinicaltrials.gov/api/v2/studies/{nct_id}"
    req = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            "Accept": "application/json",
        },
    )
    try:
        with urlopen(req, timeout=30) as resp:  # nosec - fixed public URL
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        print(f"ERROR: {nct_id} → HTTP {e.code}", file=sys.stderr)
        return None
    except (URLError, ValueError) as e:
        print(f"ERROR: {nct_id} request failed: {e}", file=sys.stderr)
        return None


def _get(d, *keys, default=""):
    """Safe nested dict getter."""
    for k in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(k)
    return d if d is not None else default


def render(study: dict, acronym: str) -> str:
    """Render study JSON into human+LLM readable plaintext."""
    proto = study.get("protocolSection", {}) or {}
    lines: list[str] = []

    ident = proto.get("identificationModule", {}) or {}
    status = proto.get("statusModule", {}) or {}
    design = proto.get("designModule", {}) or {}
    conds = proto.get("conditionsModule", {}) or {}
    armsint = proto.get("armsInterventionsModule", {}) or {}
    outcomes = proto.get("outcomesModule", {}) or {}
    elig = proto.get("eligibilityModule", {}) or {}
    sponsor = proto.get("sponsorCollaboratorsModule", {}) or {}
    description = proto.get("descriptionModule", {}) or {}

    nct = ident.get("nctId", "")
    title = ident.get("briefTitle", "") or ident.get("officialTitle", "")

    lines.append(f"Title: {title}")
    lines.append(f"NCT ID: {nct}")
    lines.append(f"Acronym: {ident.get('acronym', acronym)}")
    lines.append(f"Status: {status.get('overallStatus', '')}")

    phases = design.get("phases") or []
    if phases:
        lines.append(f"Phase: {', '.join(phases)}")
    lines.append(f"Study Type: {design.get('studyType', '')}")

    enroll = _get(design, "enrollmentInfo", "count", default="")
    if enroll != "":
        lines.append(f"Enrollment: {enroll}")

    start = _get(status, "startDateStruct", "date", default="")
    comp = _get(status, "completionDateStruct", "date", default="")
    if start:
        lines.append(f"Start Date: {start}")
    if comp:
        lines.append(f"Completion Date: {comp}")

    lead = _get(sponsor, "leadSponsor", "name", default="")
    if lead:
        lines.append(f"Lead Sponsor: {lead}")

    collab = sponsor.get("collaborators") or []
    if collab:
        lines.append("Collaborators: " + ", ".join(c.get("name", "") for c in collab if c.get("name")))

    conditions = conds.get("conditions") or []
    if conditions:
        lines.append("Conditions: " + "; ".join(conditions))

    keywords = conds.get("keywords") or []
    if keywords:
        lines.append("Keywords: " + "; ".join(keywords))

    lines.append("")
    lines.append("=== BRIEF SUMMARY ===")
    lines.append(description.get("briefSummary", "").strip())

    detailed = description.get("detailedDescription", "").strip()
    if detailed:
        lines.append("")
        lines.append("=== DETAILED DESCRIPTION ===")
        lines.append(detailed)

    arms = armsint.get("armGroups") or []
    if arms:
        lines.append("")
        lines.append("=== STUDY ARMS / COHORTS ===")
        for a in arms:
            label = a.get("label", "")
            atype = a.get("type", "")
            desc = (a.get("description") or "").strip()
            intv_labels = a.get("interventionNames") or []
            lines.append(f"- {label} ({atype})")
            if desc:
                lines.append(f"    {desc}")
            if intv_labels:
                lines.append(f"    Interventions: {'; '.join(intv_labels)}")

    interventions = armsint.get("interventions") or []
    if interventions:
        lines.append("")
        lines.append("=== INTERVENTIONS ===")
        for i in interventions:
            itype = i.get("type", "")
            iname = i.get("name", "")
            idesc = (i.get("description") or "").strip()
            lines.append(f"- {iname} [{itype}]")
            if idesc:
                lines.append(f"    {idesc}")
            synonyms = i.get("otherNames") or []
            if synonyms:
                lines.append(f"    Also known as: {', '.join(synonyms)}")

    primary = outcomes.get("primaryOutcomes") or []
    if primary:
        lines.append("")
        lines.append("=== PRIMARY OUTCOMES ===")
        for o in primary:
            measure = o.get("measure", "")
            desc = (o.get("description") or "").strip()
            timeframe = o.get("timeFrame", "")
            lines.append(f"- {measure}")
            if desc:
                lines.append(f"    {desc}")
            if timeframe:
                lines.append(f"    Time Frame: {timeframe}")

    secondary = outcomes.get("secondaryOutcomes") or []
    if secondary:
        lines.append("")
        lines.append("=== SECONDARY OUTCOMES ===")
        for o in secondary[:10]:
            measure = o.get("measure", "")
            timeframe = o.get("timeFrame", "")
            lines.append(f"- {measure}" + (f" (Time Frame: {timeframe})" if timeframe else ""))

    criteria = elig.get("eligibilityCriteria", "").strip()
    if criteria:
        lines.append("")
        lines.append("=== ELIGIBILITY CRITERIA ===")
        lines.append(criteria)

    healthy = elig.get("healthyVolunteers")
    sex = elig.get("sex", "")
    minage = elig.get("minimumAge", "")
    maxage = elig.get("maximumAge", "")
    pop_bits = []
    if sex:
        pop_bits.append(f"Sex: {sex}")
    if minage:
        pop_bits.append(f"Min Age: {minage}")
    if maxage:
        pop_bits.append(f"Max Age: {maxage}")
    if healthy is not None:
        pop_bits.append(f"Healthy Volunteers: {healthy}")
    if pop_bits:
        lines.append("")
        lines.append("Population: " + "; ".join(pop_bits))

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python fetch_ct_protocols.py <output_dir>", file=sys.stderr)
        return 2

    out_root = Path(sys.argv[1]).resolve()
    docs_dir = out_root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)

    fetched = 0
    failed = 0
    for nct, acronym in NCT_IDS:
        print(f"Fetching {nct} ({acronym}) ...", end=" ", flush=True)
        study = fetch(nct)
        if study is None:
            print("FAIL")
            failed += 1
            continue
        text = render(study, acronym)
        target = docs_dir / f"{nct.lower()}_{acronym.lower().replace('-', '_')}.txt"
        target.write_text(text, encoding="utf-8")
        size = target.stat().st_size
        print(f"wrote {size} bytes → {target.name}")
        fetched += 1
        time.sleep(0.2)

    print(f"\n=== Done: {fetched} trials fetched, {failed} failed ===")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
