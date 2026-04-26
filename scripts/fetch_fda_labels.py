#!/usr/bin/env python3
"""Fetch FDA SPL labels into a text corpus for S8 — the FDA showcase counterpart
to fetch_ct_protocols.py for S7.

Pulls the 7 flagship FDA product labels (Ozempic, Wegovy, Mounjaro, Keytruda,
Gleevec, Lipitor, Jantoven) via the openFDA /drug/label.json endpoint and
renders them as structured plaintext files. Each file is trimmed to 80,000
characters to keep LLM extraction cost within the $5-7 target.

Usage:
    python scripts/fetch_fda_labels.py <output_dir>

Example:
    python scripts/fetch_fda_labels.py tests/corpora/08_fda_labels
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

# ---------------------------------------------------------------------------
# Target drugs — (query_value, query_field, output_filename_stem)
# Application numbers verified against openFDA on 2026-04-25.
# NDA209637 = injectable Ozempic (SUBCUTANEOUS, semaglutide).
# NDA208457 returned NOT_FOUND on openFDA; NDA209637 is the correct injectable record.
# NDA213051 is oral semaglutide combined (OZEMPIC + RYBELSUS) — excluded per Pitfall #7.
# BLA125057 = Humira (adalimumab) — replaces planned BLA761467 (KEYTRUDA QLEX).
# BLA761467 has no boxed_warning field in openFDA structured data; Humira has a
# confirmed BOXED WARNING (serious infections/malignancy) which the corpus requires.
# ---------------------------------------------------------------------------
DRUG_TARGETS: list[tuple[str, str, str]] = [
    ("NDA209637", "openfda.application_number", "semaglutide_ozempic"),
    ("NDA215256", "openfda.application_number", "semaglutide_wegovy"),
    ("NDA215866", "openfda.application_number", "tirzepatide_mounjaro"),
    ("BLA125057", "openfda.application_number", "adalimumab_humira"),
    ("NDA021588", "openfda.application_number", "imatinib_gleevec"),
    ("NDA020702", "openfda.application_number", "atorvastatin_lipitor"),
    ("ANDA040416", "openfda.application_number", "warfarin_jantoven"),
]

OPENFDA_URL = "https://api.fda.gov/drug/label.json"
MAX_CHARS = 80_000  # hard trim per document for cost containment

# Section keys → plaintext headers matching SKILL.md extraction guideline refs.
SECTION_MAP: list[tuple[str, str]] = [
    ("boxed_warning", "=== BOXED WARNING ==="),
    ("indications_and_usage", "=== INDICATIONS AND USAGE ==="),
    ("contraindications", "=== CONTRAINDICATIONS ==="),
    ("warnings_and_cautions", "=== WARNINGS AND PRECAUTIONS ==="),
    ("adverse_reactions", "=== ADVERSE REACTIONS ==="),
    ("drug_interactions", "=== DRUG INTERACTIONS ==="),
    ("dosage_and_administration", "=== DOSAGE AND ADMINISTRATION ==="),
    ("use_in_specific_populations", "=== USE IN SPECIFIC POPULATIONS ==="),
    ("mechanism_of_action", "=== MECHANISM OF ACTION ==="),
    ("pharmacokinetics", "=== PHARMACOKINETICS ==="),
    ("clinical_studies", "=== CLINICAL STUDIES ==="),
    ("description", "=== DESCRIPTION ==="),
]


# ---------------------------------------------------------------------------
# Fetch
# ---------------------------------------------------------------------------


def fetch(query_value: str, query_field: str) -> dict | None:
    """Fetch one label record from openFDA /drug/label.json.

    Uses stdlib urllib (not requests) to match the zero-extra-dep pattern from
    fetch_ct_protocols.py.  openFDA does not block urllib User-Agent strings.

    Args:
        query_value: The application number or other search value.
        query_field: The openFDA field to search (e.g. openfda.application_number).

    Returns:
        The first result dict from the API response, or None on any error.
    """
    search_expr = f'{query_field}:"{query_value}"'
    url = f"{OPENFDA_URL}?search={quote(search_expr)}&limit=1"
    req = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            "Accept": "application/json",
        },
    )
    try:
        with urlopen(req, timeout=30) as resp:  # nosec - fixed public URL
            data = json.loads(resp.read().decode("utf-8"))
        if data.get("results"):
            return data["results"][0]
        print(f"ERROR: {query_value} -> no results in response", file=sys.stderr)
        return None
    except HTTPError as e:
        print(f"ERROR: {query_value} -> HTTP {e.code}", file=sys.stderr)
        return None
    except (URLError, ValueError) as e:
        print(f"ERROR: {query_value} -> request failed: {e}", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# Render helpers
# ---------------------------------------------------------------------------


def _section(record: dict, key: str) -> str:
    """Extract first element from an openFDA list-valued clinical section.

    All clinical sections in the openFDA /drug/label response are typed as
    single-element lists (e.g. indications_and_usage: ["1 INDICATIONS..."]).
    This is Pitfall #4 — do NOT access the value as a string directly.

    Args:
        record: The top-level label result dict.
        key: The section field name (e.g. "indications_and_usage").

    Returns:
        The stripped text of the section, or an empty string if absent.
    """
    val = record.get(key)
    if isinstance(val, list) and val:
        return val[0].strip()
    return ""


def _first(openfda: dict, key: str) -> str:
    """Return the first element of an openFDA metadata list field.

    Args:
        openfda: The openfda sub-object from the label record.
        key: The metadata field name.

    Returns:
        First list element as a string, or an empty string if absent.
    """
    val = openfda.get(key)
    if isinstance(val, list) and val:
        return str(val[0])
    return ""


def _meta_block(openfda: dict) -> str:
    """Build a structured metadata header from the openfda sub-object.

    Args:
        openfda: The openfda sub-object from the label record.

    Returns:
        Multi-line metadata block (Key: Value per line, empty lines omitted).
    """
    fields: list[tuple[str, str]] = [
        ("Brand Name", _first(openfda, "brand_name")),
        ("Generic Name", _first(openfda, "generic_name")),
        ("Substance Name", _first(openfda, "substance_name")),
        ("Application Number", _first(openfda, "application_number")),
        ("SPL Set ID", _first(openfda, "spl_set_id")),
        ("Product NDC", _first(openfda, "product_ndc")),
        ("RxCUI", _first(openfda, "rxcui")),
        ("UNII", _first(openfda, "unii")),
        ("Manufacturer", _first(openfda, "manufacturer_name")),
        ("Pharmacologic Class (EPC)", _first(openfda, "pharm_class_epc")),
        ("Pharmacologic Class (MoA)", _first(openfda, "pharm_class_moa")),
        ("Pharmacologic Class (CS)", _first(openfda, "pharm_class_cs")),
        ("Pharmacologic Class (PE)", _first(openfda, "pharm_class_pe")),
        ("Route", _first(openfda, "route")),
        ("Product Type", _first(openfda, "product_type")),
    ]
    lines = [f"{label}: {value}" for label, value in fields if value]
    return "\n".join(lines) + "\n"


def render(record: dict, filename_stem: str) -> str:
    """Render a label record into human+LLM readable plaintext.

    The output format mirrors the section-header pattern from fetch_ct_protocols.py
    with headers matching the SKILL.md extraction guideline references.

    The combined output is hard-trimmed to MAX_CHARS characters.  Priority
    sections (boxed_warning, indications) appear near the top so they are
    preserved even for 950KB labels like Keytruda.

    Args:
        record: The top-level label result dict from openFDA.
        filename_stem: The output file stem (used as the document title).

    Returns:
        Rendered plaintext string, trimmed to at most MAX_CHARS characters.
    """
    parts: list[str] = [
        f"FDA Product Label: {filename_stem}",
        "",
        _meta_block(record.get("openfda", {})),
        "",
    ]
    for key, header in SECTION_MAP:
        text = _section(record, key)
        if text:
            parts.append(header)
            parts.append(text)
            parts.append("")

    combined = "\n".join(parts).rstrip() + "\n"
    # Trim at byte boundary (UTF-8 multi-byte chars can push byte count over MAX_CHARS
    # even when character count is exactly MAX_CHARS).  Encode → slice → decode with
    # errors="ignore" to drop any incomplete multi-byte sequence at the cut point.
    encoded = combined.encode("utf-8")
    if len(encoded) > MAX_CHARS:
        encoded = encoded[:MAX_CHARS]
        return encoded.decode("utf-8", errors="ignore")
    return combined


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    """Entry point: fetch and write all 7 FDA label files.

    Returns:
        0 if all fetches succeeded, 1 if any failed, 2 if called with no args.
    """
    if len(sys.argv) < 2:
        print("Usage: python scripts/fetch_fda_labels.py <output_dir>", file=sys.stderr)
        return 2

    out_root = Path(sys.argv[1]).resolve()
    docs_dir = out_root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)

    fetched, failed, skipped = 0, 0, 0

    for query_value, query_field, stem in DRUG_TARGETS:
        target = docs_dir / f"{stem}.txt"
        if target.exists():
            print(f"SKIP {stem}")
            skipped += 1
            continue

        print(f"Fetching {stem} ({query_value}) ...", end=" ", flush=True)
        record = fetch(query_value, query_field)
        if record is None:
            print("FAIL")
            failed += 1
            continue

        text = render(record, stem)
        target.write_text(text, encoding="utf-8")
        size = target.stat().st_size
        print(f"wrote {size} bytes -> {target.name}")
        fetched += 1
        time.sleep(0.5)  # openFDA unauthenticated limit is 40 req/min

    print(f"\n=== Done: {fetched} fetched, {skipped} skipped, {failed} failed ===")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
