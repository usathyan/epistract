#!/usr/bin/env python3
"""Fetch openFDA FAERS adverse event reports as a narrative-style test corpus
for the pharmacovigilance domain.

Pulls a varied set of reports across drugs chosen for diverse epistemic signal
profiles -- positive dechallenge/rechallenge, cross-database contested, known
regulatory action, and broad spontaneous reporting -- then renders each report
as a narrative Markdown case document the ingest pipeline can read.

openFDA fields are decoded into human-readable narratives using the official
field reference at:
    https://open.fda.gov/apis/drug/event/searchable-fields/
    https://open.fda.gov/apis/drug/event/understanding-the-api-results/

Usage:
    uv run python scripts/fetch_faers_corpus.py [-o OUTPUT_DIR] [--mode MODE]

Modes:
    default              -- pull most recent reports across the target drugs.
                            Whatever FAERS returned first; not curated for any
                            specific epistemic signal.
    rechallenge-positive -- restrict to reports where ``patient.drug.drugrecuraction``
                            equals 1 (positive rechallenge -- event recurred when
                            the drug was reintroduced). These are the strongest
                            single-case causality signals under Bradford-Hill and
                            exercise the RESOLVED_ON_DECHALLENGE /
                            RECURRED_ON_RECHALLENGE relations in the
                            pharmacovigilance domain.

Default output_dir depends on mode:
    default              -> corpora/pharmacovigilance-faers
    rechallenge-positive -> corpora/pharmacovigilance-faers-rechallenge

API:
    Public; no API key required for low-volume queries (240 req/min anonymous).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


# ---------------------------------------------------------------------------
# Target drugs -- (search_term, output_stem, rationale)
# Chosen to exercise diverse epistemic signals downstream:
#   - warfarin     : strong dechallenge/rechallenge bleeding signals
#   - montelukast  : neuropsychiatric AE -- contested across FAERS/EU databases
#   - rosiglitazone: cardiovascular signal triggering 2007 boxed warning + later
#                    REMS -- regulatory action lineage
#   - valsartan    : 2018 NDMA contamination -- recall lineage
#   - methotrexate : oncology + RA dual indication, drug-drug interaction load
# ---------------------------------------------------------------------------
DRUG_TARGETS: list[tuple[str, str, str]] = [
    ("warfarin", "warfarin", "dechallenge_rechallenge_signal"),
    ("montelukast", "montelukast", "cross_database_contested"),
    ("rosiglitazone", "rosiglitazone", "regulatory_action_lineage"),
    ("valsartan", "valsartan", "recall_lineage"),
    ("methotrexate", "methotrexate", "drug_drug_interaction"),
]

OPENFDA_URL = "https://api.fda.gov/drug/event.json"
REPORTS_PER_DRUG = 4
REQUEST_PAUSE_S = 0.5  # courtesy throttle below the 240/min anonymous cap


# ---------------------------------------------------------------------------
# openFDA enum decoders
# Source: https://open.fda.gov/apis/drug/event/searchable-fields/
# ---------------------------------------------------------------------------

DRUG_CHARACTERIZATION = {
    "1": "Suspect",
    "2": "Concomitant",
    "3": "Interacting",
}

ACTION_DRUG = {
    "1": "Drug withdrawn",
    "2": "Dose reduced",
    "3": "Dose increased",
    "4": "Dose not changed",
    "5": "Unknown",
    "6": "Not applicable",
}

DRUG_RECUR_ACTION = {
    "1": "Yes -- positive rechallenge (event recurred)",
    "2": "No -- negative rechallenge (event did not recur)",
    "3": "Event recurred but drug not reintroduced",
    "4": "Unknown",
}

REACTION_OUTCOME = {
    "1": "Recovered/resolved",
    "2": "Recovering/resolving",
    "3": "Not recovered/not resolved",
    "4": "Recovered/resolved with sequelae",
    "5": "Fatal",
    "6": "Unknown",
}

REPORTER_QUALIFICATION = {
    "1": "Physician",
    "2": "Pharmacist",
    "3": "Other health professional",
    "4": "Lawyer",
    "5": "Consumer or non-health professional",
}

PATIENT_SEX = {"0": "Unknown", "1": "Male", "2": "Female"}

ONSET_AGE_UNIT = {
    "800": "Decade",
    "801": "Year",
    "802": "Month",
    "803": "Week",
    "804": "Day",
    "805": "Hour",
}


# ---------------------------------------------------------------------------
# Fetch
# ---------------------------------------------------------------------------


def fetch_reports(drug: str, limit: int, mode: str = "default") -> list[dict]:
    """Fetch ``limit`` adverse-event reports for a drug from openFDA.

    Uses ``patient.drug.medicinalproduct`` field search. Falls back to the
    broader ``patient.drug.openfda.generic_name`` field when the primary
    search returns nothing (some FAERS records do not populate the
    medicinalproduct text).

    Mode-specific predicates are AND-ed onto the base drug query:
        default              -- no extra predicate
        rechallenge-positive -- AND patient.drug.drugrecuraction:1
                                (event recurred on rechallenge)
    """
    base_queries = [
        f'patient.drug.medicinalproduct:"{drug}"',
        f"patient.drug.openfda.generic_name:{drug}",
    ]

    extra: str | None = None
    if mode == "rechallenge-positive":
        # The `drugrecurrence` array on a drug record holds the MedDRA PTs
        # that recurred when the drug was reintroduced -- its mere existence
        # is the openFDA-equivalent of a positive-rechallenge case (FDA does
        # not expose the ICH E2B "drugrecuraction" 1=Yes/2=No enum as a
        # searchable scalar; only the recurred-PT array). Filter on
        # `_exists_:patient.drug.drugrecurrence` to surface them. ~33k
        # reports across the dataset; well-distributed across our targets
        # except rosiglitazone (0 hits -- itself a signal).
        extra = "_exists_:patient.drug.drugrecurrence"
    elif mode != "default":
        raise ValueError(f"Unknown mode: {mode!r}")

    queries = [
        f"{q}+AND+{extra}" if extra else q
        for q in base_queries
    ]
    # Predicates are pre-quoted (drug term in double-quotes) and the
    # `+AND+` glue must remain literal `+`s -- so we URL-quote with
    # this safe-char set to preserve operator and field syntax.
    safe_chars = '+:"'
    for q in queries:
        encoded_q = quote(q, safe=safe_chars)
        url = f"{OPENFDA_URL}?search={encoded_q}&limit={limit}"
        try:
            req = Request(url, headers={"User-Agent": "epistract-fetch/1.0"})
            with urlopen(req, timeout=30) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except HTTPError as e:
            if e.code == 404:
                continue
            raise
        except URLError:
            return []

        results = payload.get("results", [])
        if results:
            return results

    return []


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------


def _format_date(yyyymmdd: str | None) -> str:
    if not yyyymmdd or len(yyyymmdd) != 8:
        return yyyymmdd or "unknown"
    return f"{yyyymmdd[:4]}-{yyyymmdd[4:6]}-{yyyymmdd[6:8]}"


def _format_age(report: dict) -> str:
    p = report.get("patient", {})
    age = p.get("patientonsetage")
    unit = ONSET_AGE_UNIT.get(str(p.get("patientonsetageunit", "")), "")
    if age and unit:
        return f"{age} {unit.lower()}{'s' if str(age) != '1' else ''}"
    if age:
        return str(age)
    return "unknown"


def _serious_flags(report: dict) -> list[str]:
    flag_map = {
        "seriousnessdeath": "Death",
        "seriousnesslifethreatening": "Life-threatening",
        "seriousnesshospitalization": "Hospitalization (initial or prolonged)",
        "seriousnessdisabling": "Disabling / incapacitating",
        "seriousnesscongenitalanomali": "Congenital anomaly / birth defect",
        "seriousnessother": "Other medically significant",
    }
    flags: list[str] = []
    for key, label in flag_map.items():
        if str(report.get(key, "0")) == "1":
            flags.append(label)
    return flags


def _drug_recurrence_pts(drug: dict) -> list[str]:
    """Extract MedDRA PTs that recurred on rechallenge for this drug.

    openFDA encodes positive rechallenge as a ``drugrecurrence`` array of
    objects each containing a ``drugrecuraction`` MedDRA-PT string -- one
    entry per reaction that recurred when the drug was reintroduced.
    """
    arr = drug.get("drugrecurrence") or []
    pts: list[str] = []
    for item in arr:
        pt = (item or {}).get("drugrecuraction")
        if pt:
            pts.append(pt)
    return pts


def _render_drug_block(drug: dict) -> str:
    name = drug.get("medicinalproduct") or "(unnamed product)"
    chars = DRUG_CHARACTERIZATION.get(str(drug.get("drugcharacterization", "")), "Unknown role")
    indication = drug.get("drugindication", "")
    route = drug.get("drugadministrationroute", "")
    dosage = drug.get("drugdosagetext", "")
    auth = drug.get("drugauthorizationnumb", "")
    action = ACTION_DRUG.get(str(drug.get("actiondrug", "")), "")
    recur = DRUG_RECUR_ACTION.get(str(drug.get("drugrecuraction", "")), "")
    recurred_pts = _drug_recurrence_pts(drug)

    lines = [f"### Drug -- {name}", f"- Role: **{chars}**"]
    if indication:
        lines.append(f"- Indication: {indication}")
    if route:
        lines.append(f"- Route: {route}")
    if dosage:
        lines.append(f"- Dosage: {dosage}")
    if auth:
        lines.append(f"- Authorization number: {auth}")
    if action:
        lines.append(f"- Action taken with drug: **{action}**")
    if recurred_pts:
        lines.append(
            "- **Positive rechallenge — events that recurred when drug "
            "was reintroduced:**"
        )
        for pt in recurred_pts:
            lines.append(f"  - {pt}")
    if recur:
        lines.append(f"- Rechallenge: **{recur}**")

    openfda = drug.get("openfda", {}) or {}
    if openfda:
        substances = openfda.get("substance_name") or []
        atcs = openfda.get("pharm_class_epc") or openfda.get("pharm_class_moa") or []
        rxcui = openfda.get("rxcui") or []
        if substances:
            lines.append(f"- Substance name(s): {', '.join(substances[:3])}")
        if atcs:
            lines.append(f"- Pharmacological class: {', '.join(atcs[:3])}")
        if rxcui:
            lines.append(f"- RxCUI: {', '.join(map(str, rxcui[:3]))}")

    return "\n".join(lines)


def _render_reaction_block(reaction: dict) -> str:
    pt = reaction.get("reactionmeddrapt", "(no preferred term)")
    outcome = REACTION_OUTCOME.get(str(reaction.get("reactionoutcome", "")), "")
    bits = [f"- **MedDRA Preferred Term:** {pt}"]
    if outcome:
        bits.append(f"  - Outcome: **{outcome}**")
    return "\n".join(bits)


def render_report(report: dict, drug_label: str, rationale: str) -> str:
    """Render an openFDA report as a narrative Markdown case document."""
    rid = report.get("safetyreportid", "unknown")
    company = report.get("companynumb", "")
    receipt_date = _format_date(report.get("receiptdate"))
    receive_date = _format_date(report.get("receivedate"))
    sender = (report.get("sender") or {}).get("sendertype", "")
    receiver = (report.get("receiver") or {}).get("receivertype", "")
    expedited = "Yes" if str(report.get("fulfillexpeditecriteria", "0")) == "1" else "No"
    serious = "Yes" if str(report.get("serious", "0")) == "1" else "No"
    serious_flags = _serious_flags(report)

    primary_source = report.get("primarysource", {}) or {}
    qualification = REPORTER_QUALIFICATION.get(
        str(primary_source.get("qualification", "")), "Unknown"
    )
    reporter_country = primary_source.get("reportercountry", "")

    patient = report.get("patient", {}) or {}
    sex = PATIENT_SEX.get(str(patient.get("patientsex", "")), "Unknown")
    age = _format_age(report)
    death_block = patient.get("patientdeath")
    death_date = _format_date((death_block or {}).get("patientdeathdate"))

    drugs = patient.get("drug", []) or []
    reactions = patient.get("reaction", []) or []

    suspect_drugs = [d for d in drugs if str(d.get("drugcharacterization", "")) == "1"]
    concomitant_drugs = [d for d in drugs if str(d.get("drugcharacterization", "")) == "2"]
    interacting_drugs = [d for d in drugs if str(d.get("drugcharacterization", "")) == "3"]

    parts: list[str] = []
    parts.append(f"# FAERS Adverse Event Report -- safetyreportid {rid}")
    parts.append("")
    parts.append(
        "> **Source:** openFDA `/drug/event.json` (FAERS public release). "
        "Records are de-identified and reflect submitted reports without verification "
        "by FDA. NOT a 21 CFR Part 11 audit-trail output."
    )
    parts.append("")

    parts.append("## Report Metadata")
    parts.append(f"- Safety report ID: `{rid}`")
    parts.append(f"- Report type: **Spontaneous (FAERS)**")
    parts.append(f"- Pulled-for drug: `{drug_label}` (rationale: {rationale})")
    parts.append(f"- Receipt date: {receipt_date}")
    parts.append(f"- Receive date: {receive_date}")
    parts.append(f"- Sender type: {sender or 'unknown'}")
    parts.append(f"- Receiver type: {receiver or 'unknown'}")
    parts.append(f"- Company number: {company or 'unknown'}")
    parts.append(f"- Expedited criteria fulfilled: {expedited}")
    parts.append(f"- Serious: **{serious}**")
    if serious_flags:
        for f in serious_flags:
            parts.append(f"  - Seriousness flag: {f}")
    parts.append("")

    parts.append("## Reporter")
    parts.append(f"- Primary source qualification: **{qualification}**")
    if reporter_country:
        parts.append(f"- Reporter country: {reporter_country}")
    parts.append("")

    parts.append("## Patient")
    parts.append(f"- Sex: {sex}")
    parts.append(f"- Age at onset: {age}")
    if death_block:
        parts.append(f"- **Patient died.** Death date: {death_date}")
    parts.append("")

    parts.append("## Reactions (MedDRA-coded adverse events)")
    if reactions:
        for r in reactions:
            parts.append(_render_reaction_block(r))
    else:
        parts.append("- (no reactions recorded)")
    parts.append("")

    if suspect_drugs:
        parts.append("## Suspect Drug(s)")
        for d in suspect_drugs:
            parts.append(_render_drug_block(d))
            parts.append("")

    if interacting_drugs:
        parts.append("## Interacting Drug(s)")
        for d in interacting_drugs:
            parts.append(_render_drug_block(d))
            parts.append("")

    if concomitant_drugs:
        parts.append("## Concomitant Drug(s)")
        for d in concomitant_drugs:
            parts.append(_render_drug_block(d))
            parts.append("")

    # Narrative synthesis paragraph -- gives the LLM extractor running prose
    # to anchor entity/relation extraction on (the structured fields above
    # are accurate but anaemic).
    parts.append("## Narrative Synthesis")
    suspect_names = [d.get("medicinalproduct", "") for d in suspect_drugs] or [drug_label]
    reaction_names = [r.get("reactionmeddrapt", "") for r in reactions]
    age_phrase = f"a {sex.lower()} patient aged {age}" if sex != "Unknown" else f"a patient aged {age}"

    narrative_lines: list[str] = []
    if suspect_names and reaction_names:
        narrative_lines.append(
            f"This case describes {age_phrase} who experienced "
            f"{', '.join([r for r in reaction_names if r][:5])} after exposure to "
            f"{', '.join([s for s in suspect_names if s][:3])}."
        )
    if suspect_drugs:
        first = suspect_drugs[0]
        action = ACTION_DRUG.get(str(first.get("actiondrug", "")), "")
        recur = DRUG_RECUR_ACTION.get(str(first.get("drugrecuraction", "")), "")
        recurred_pts = _drug_recurrence_pts(first)
        if action:
            narrative_lines.append(f"Action taken with the suspect drug: {action.lower()}.")
        if recur:
            narrative_lines.append(f"On rechallenge information: {recur.lower()}.")
        if recurred_pts:
            narrative_lines.append(
                "**Positive rechallenge documented:** the following events recurred "
                f"when the suspect drug was reintroduced — {', '.join(recurred_pts[:5])}. "
                "Under Bradford-Hill criteria this is the strongest single-case "
                "causality signal available."
            )
    if death_block:
        narrative_lines.append("The reported outcome included patient death.")
    elif reactions:
        first_outcome = REACTION_OUTCOME.get(
            str(reactions[0].get("reactionoutcome", "")), ""
        )
        if first_outcome:
            narrative_lines.append(
                f"The first-listed adverse event outcome was: {first_outcome.lower()}."
            )
    narrative_lines.append(
        f"The report was submitted by a **{qualification.lower()}**"
        + (f" in {reporter_country}" if reporter_country else "")
        + "."
    )
    parts.append(" ".join(narrative_lines))
    parts.append("")

    parts.append("## Disclaimer")
    parts.append(
        "RESEARCH-GRADE ONLY. openFDA explicitly disclaims that the data should not be "
        "used to make medical decisions. FAERS reports are voluntary, unverified, and "
        "subject to substantial reporting bias. This document is a derivative rendering "
        "of the public openFDA record for pipeline testing only -- it is not a regulatory "
        "submission deliverable."
    )

    return "\n".join(parts) + "\n"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


DEFAULT_OUTPUT_DIRS = {
    "default": Path("corpora/pharmacovigilance-faers"),
    "rechallenge-positive": Path("corpora/pharmacovigilance-faers-rechallenge"),
}


def _build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Fetch openFDA FAERS adverse event reports as a narrative-style "
            "test corpus for the pharmacovigilance domain."
        ),
    )
    parser.add_argument(
        "output_dir",
        nargs="?",
        default=None,
        help=(
            "Where to write the corpus. Defaults to "
            "corpora/pharmacovigilance-faers (default mode) or "
            "corpora/pharmacovigilance-faers-rechallenge (rechallenge-positive mode)."
        ),
    )
    parser.add_argument(
        "--mode",
        choices=("default", "rechallenge-positive"),
        default="default",
        help=(
            "default: most-recent reports across the target drugs. "
            "rechallenge-positive: restrict to reports where the suspect drug "
            "had drugrecuraction=1 (event recurred on rechallenge) -- the "
            "strongest single-case Bradford-Hill causality signal."
        ),
    )
    parser.add_argument(
        "-n",
        "--per-drug",
        type=int,
        default=REPORTS_PER_DRUG,
        help=f"Reports to pull per drug (default: {REPORTS_PER_DRUG}).",
    )
    return parser


def main(argv: list[str]) -> int:
    args = _build_argparser().parse_args(argv[1:])

    out_dir = (
        Path(args.output_dir) if args.output_dir else DEFAULT_OUTPUT_DIRS[args.mode]
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    print(
        f"Mode: {args.mode}  ({args.per_drug} reports/drug -> {out_dir}/)",
        file=sys.stderr,
    )

    total = 0
    skipped: list[str] = []
    for drug, stem, rationale in DRUG_TARGETS:
        print(f"Fetching {args.per_drug} reports for `{drug}` ...", file=sys.stderr)
        reports = fetch_reports(drug, args.per_drug, mode=args.mode)
        if not reports:
            msg = f"  (no reports returned for {drug} in mode={args.mode})"
            print(msg, file=sys.stderr)
            skipped.append(drug)
            continue
        for i, report in enumerate(reports, start=1):
            md = render_report(report, drug_label=drug, rationale=rationale)
            rid = report.get("safetyreportid") or f"{stem}_{i}"
            # Tag rechallenge-positive corpus filenames so a mixed scratch
            # directory stays disambiguated.
            mode_tag = "_rechallenge" if args.mode == "rechallenge-positive" else ""
            path = out_dir / f"faers_{stem}{mode_tag}_{rid}.md"
            path.write_text(md, encoding="utf-8")
            total += 1
            print(f"  -> {path}", file=sys.stderr)
        time.sleep(REQUEST_PAUSE_S)

    print(f"\nWrote {total} reports to {out_dir}/", file=sys.stderr)
    if skipped:
        print(
            f"Drugs with no matching reports in mode={args.mode}: "
            f"{', '.join(skipped)}",
            file=sys.stderr,
        )
    return 0 if total > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
