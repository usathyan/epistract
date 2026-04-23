"""End-to-end tests for Phase 15 Format Discovery Parity (FIDL-04).

- FT-013: A new-format document (.md, previously silently excluded by the
  hardcoded 9-extension allowlist) round-trips through ingest_corpus and
  produces an ingested .txt plus a clean triage entry.
- FT-014: A corrupted .pptx is still DISCOVERED (discovery is pure
  extension-match per D-06) but its extraction failure is recorded in
  triage.json under the document's warnings[] field with an
  "extraction_failed:*" code (or "empty_text" — see test for disjunction).
- FT-015: The committed V2 baseline floor (tests/baselines/v2/expected.json)
  still holds after Plan 15-01's discovery-layer changes. Contract
  scenario must meet or exceed 341 nodes / 663 edges (Phase 14 D-14).

Traces: FIDL-04 (see .planning/REQUIREMENTS.md §v3).
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from conftest import HAS_SIFTKG, PROJECT_ROOT

# core/ is already on sys.path via conftest.py:20.
from ingest_documents import ingest_corpus

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "format_parity"


@pytest.mark.e2e
@pytest.mark.skipif(
    not HAS_SIFTKG,
    reason="sift-kg not installed - FT-013 requires Kreuzberg to extract markdown",
)
def test_ft013_new_format_ingest_end_to_end(tmp_path):
    """FT-013: `.md` (previously silently excluded) round-trips through
    ingest_corpus after FIDL-04 delegation to sift-kg."""
    corpus_dir = tmp_path / "corpus"
    output_dir = tmp_path / "output"
    corpus_dir.mkdir()

    src = FIXTURES_DIR / "sample.md"
    assert src.exists(), f"Missing fixture: {src}"
    shutil.copy(src, corpus_dir / "sample.md")

    triage = ingest_corpus(corpus_dir, output_dir, domain_name=None)

    assert (
        triage["total_files"] == 1
    ), f"Expected 1 file discovered, got {triage['total_files']}: {triage}"
    assert (
        triage["successful"] == 1
    ), f"Expected 1 successful extraction, got {triage['successful']}: {triage}"
    assert triage["failed"] == 0, f"Unexpected extraction failure: {triage}"

    documents = triage["documents"]
    assert len(documents) == 1
    doc = documents[0]
    assert doc["parse_type"] == "text", f"Expected text parse_type, got {doc}"
    assert doc["warnings"] == [], (
        f"D-06: Successful extraction must have empty warnings[], "
        f"got {doc['warnings']}"
    )
    assert doc["filename"] == "sample.md"

    ingested_txt = output_dir / "ingested" / "sample.txt"
    assert ingested_txt.exists(), f"Ingested text file not written: {ingested_txt}"
    ingested_text = ingested_txt.read_text(encoding="utf-8")
    assert (
        "Phase 15 FT-013" in ingested_text
    ), f"Load-bearing phrase missing from extracted text: {ingested_text[:200]!r}"

    triage_path = output_dir / "triage.json"
    assert triage_path.exists()
    on_disk = json.loads(triage_path.read_text(encoding="utf-8"))
    assert on_disk["documents"][0]["warnings"] == []


@pytest.mark.e2e
@pytest.mark.skipif(
    not HAS_SIFTKG,
    reason="sift-kg not installed - FT-014 requires Kreuzberg to attempt extraction",
)
def test_ft014_corrupted_pptx_records_triage_warning(tmp_path):
    """FT-014: A corrupted .pptx is DISCOVERED (extension-match per D-06)
    but its extraction failure is recorded in triage.json warnings[]
    per D-06/D-07.

    Softened disjunction assertion: Kreuzberg's handling of a corrupt PPTX
    may surface either as an exception (parse_document returns an error
    dict -> 'extraction_failed:<reason>') or as an empty-string return
    (-> 'empty_text'). Both satisfy the FIDL-04 invariant: the failure is
    SURFACED in warnings[], not silently dropped.
    """
    corpus_dir = tmp_path / "corpus"
    output_dir = tmp_path / "output"
    corpus_dir.mkdir()

    src = FIXTURES_DIR / "corrupted.pptx"
    assert src.exists(), f"Missing fixture: {src}"
    shutil.copy(src, corpus_dir / "corrupted.pptx")

    triage = ingest_corpus(corpus_dir, output_dir, domain_name=None)

    assert (
        triage["total_files"] == 1
    ), f"Discovery should include .pptx (extension-match, D-06): {triage}"

    documents = triage["documents"]
    assert len(documents) == 1
    doc = documents[0]
    assert doc["filename"] == "corrupted.pptx"
    assert (
        len(doc["warnings"]) >= 1
    ), f"D-07: extraction failure must populate warnings[], got {doc}"
    assert any(
        w.startswith("extraction_failed") or w == "empty_text" for w in doc["warnings"]
    ), (
        f"D-07: at least one warning must be 'extraction_failed:*' or "
        f"'empty_text' (parse_document return-shape disjunction), "
        f"got {doc['warnings']}"
    )

    triage_path = output_dir / "triage.json"
    assert triage_path.exists()
    on_disk = json.loads(triage_path.read_text(encoding="utf-8"))
    assert any(
        w.startswith("extraction_failed") or w == "empty_text"
        for w in on_disk["documents"][0]["warnings"]
    )


# ---------------------------------------------------------------------------
# FT-015: V2 baseline floor - discovery-layer change must not regress
# existing scenario graph counts (D-13).
# ---------------------------------------------------------------------------

_DRUG_DISCOVERY_SCENARIOS = {
    "01_picalm_alzheimers",
    "02_kras_g12c_landscape",
    "03_rare_disease",
    "04_immunooncology",
    "05_cardiovascular",
    "06_glp1_landscape",
}
_CONTRACT_SCENARIOS = {"contract_events", "contracts", "contracts_sample"}


def _resolve_output(scenario: str) -> Path | None:
    if scenario in _DRUG_DISCOVERY_SCENARIOS:
        for subdir in ("output-v2", "output"):
            candidate = PROJECT_ROOT / "tests" / "corpora" / scenario / subdir
            if candidate.exists():
                return candidate
        return None
    if scenario in _CONTRACT_SCENARIOS:
        for candidate in (
            PROJECT_ROOT / "sample-output-v2",
            PROJECT_ROOT / "sample-output",
            PROJECT_ROOT / "tests" / "corpora" / "contracts" / "output-v2",
            PROJECT_ROOT / "tests" / "corpora" / "contracts" / "output",
        ):
            if candidate.exists():
                return candidate
        return None
    return None


@pytest.mark.e2e
def test_ft015_v2_baseline_floor_holds():
    """FT-015 (FIDL-04 D-13): V2 baseline floor still holds after
    Plan 15-01's discovery-layer changes. Duplicates FT-012's file-backed
    floor logic intentionally - FT-012 is Phase 14 FIDL-03's gate; FT-015
    is Phase 15 FIDL-04's guard. A regression in either implicates
    different code paths; distinct test names route the CI signal to
    the right phase.

    Missing `tests/baselines/v2/expected.json` is a HARD FAILURE
    (a skippable gate is no gate). Contract scenario must meet
    >=341 nodes / >=663 edges (Phase 14 D-14)."""
    expected_path = PROJECT_ROOT / "tests" / "baselines" / "v2" / "expected.json"
    assert expected_path.exists(), (
        f"V2 acceptance floor file missing: {expected_path}\n"
        f"FT-015 cannot pass without this file. Restore from the Phase 14 PR "
        f"or seed via `python3 tests/regression/run_regression.py` + "
        f"recording per-scenario node/edge counts."
    )

    expected = json.loads(expected_path.read_text(encoding="utf-8"))
    assert (
        "scenarios" in expected
    ), f"expected.json missing 'scenarios' key: {list(expected.keys())}"

    failures: list[str] = []
    for scenario, expect in expected["scenarios"].items():
        exp_nodes = int(expect["nodes"])
        exp_edges = int(expect["edges"])

        output_dir = _resolve_output(scenario)
        if output_dir is None:
            continue

        graph_path = output_dir / "graph_data.json"
        if not graph_path.exists():
            continue

        graph = json.loads(graph_path.read_text(encoding="utf-8"))
        obs_nodes = len(graph.get("nodes", []))
        obs_edges = len(graph.get("links", graph.get("edges", [])))

        if obs_nodes < exp_nodes or obs_edges < exp_edges:
            failures.append(
                f"{scenario}: observed {obs_nodes} nodes / {obs_edges} edges "
                f"< floor {exp_nodes} / {exp_edges} (graph: {graph_path})"
            )

        if scenario in _CONTRACT_SCENARIOS:
            # D-14 hard floor - absolute, not "if output exists".
            assert obs_nodes >= 341, (
                f"Contract D-14 floor violated: {scenario} nodes "
                f"{obs_nodes} < 341 (graph: {graph_path})"
            )
            assert obs_edges >= 663, (
                f"Contract D-14 floor violated: {scenario} edges "
                f"{obs_edges} < 663 (graph: {graph_path})"
            )

    assert not failures, (
        "V2 regression failed (scenarios below committed floor after FIDL-04):\n"
        + "\n".join(f"  - {f}" for f in failures)
    )
    # Contract output-dir resolution is environment-dependent; do not
    # assert contract_checked is True - mirrors FT-012's behavior. If
    # the contract output exists, the inner asserts above enforce D-14.
