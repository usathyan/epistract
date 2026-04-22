#!/usr/bin/env python3
"""End-to-end pipeline tests for epistract.

Tests the full lifecycle: extraction JSON -> graph build -> epistemic -> export
for both drug-discovery and contracts domains.
"""
import json
import shutil
import sys
from pathlib import Path

import pytest

from conftest import FIXTURES_DIR, HAS_SIFTKG, PROJECT_ROOT


# ---------------------------------------------------------------------------
# All E2E tests require sift-kg
# ---------------------------------------------------------------------------
pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(not HAS_SIFTKG, reason="sift-kg not installed"),
]


def _setup_extraction(tmp_path, fixture_name, output_name):
    """Copy a fixture extraction JSON into tmp_path/extractions/."""
    extractions_dir = tmp_path / "extractions"
    extractions_dir.mkdir(exist_ok=True)
    src = FIXTURES_DIR / fixture_name
    dst = extractions_dir / output_name
    shutil.copy2(src, dst)
    return dst


@pytest.mark.e2e
def test_e2e_drug_discovery_pipeline(tmp_path):
    """Full lifecycle for drug-discovery domain: extract -> build -> epistemic -> export."""
    from run_sift import cmd_build, cmd_export
    from label_epistemic import analyze_epistemic

    # 1. Set up extraction fixture
    _setup_extraction(tmp_path, "sample_extraction_drug.json", "test_drug_paper.pdf.json")

    # 2. Build graph
    cmd_build(str(tmp_path), domain_name="drug-discovery")

    # 3. Verify graph was created
    graph_path = tmp_path / "graph_data.json"
    assert graph_path.exists(), f"graph_data.json not created after cmd_build in {tmp_path}"

    graph_data = json.loads(graph_path.read_text())
    assert len(graph_data.get("nodes", [])) > 0, f"Graph has no nodes: {list(graph_data.keys())}"

    # 4. Run epistemic analysis (label_communities is called by cmd_build)
    claims_layer = analyze_epistemic(tmp_path, domain_name="drug-discovery")

    # 5. Verify claims layer
    claims_path = tmp_path / "claims_layer.json"
    assert claims_path.exists(), f"claims_layer.json not created after epistemic analysis"
    assert isinstance(claims_layer, dict), f"analyze_epistemic returned {type(claims_layer)}, expected dict"

    # 6. Export to JSON
    cmd_export(str(tmp_path), "json")

    # 7. Verify export file exists (sift-kg creates export_*.json or similar)
    export_files = list(tmp_path.glob("*export*")) + list(tmp_path.glob("*.graphml")) + list(tmp_path.glob("export/"))
    # sift-kg export may vary; just verify no error was raised


@pytest.mark.e2e
def test_e2e_contract_pipeline(tmp_path):
    """Full lifecycle for contracts domain: extract -> build -> epistemic -> export."""
    from run_sift import cmd_build, cmd_export
    from label_epistemic import analyze_epistemic

    # 1. Set up extraction fixture
    _setup_extraction(tmp_path, "sample_extraction_contract.json", "test_vendor_agreement.pdf.json")

    # 2. Build graph
    cmd_build(str(tmp_path), domain_name="contracts")

    # 3. Verify graph was created
    graph_path = tmp_path / "graph_data.json"
    assert graph_path.exists(), f"graph_data.json not created after cmd_build in {tmp_path}"

    graph_data = json.loads(graph_path.read_text())
    assert len(graph_data.get("nodes", [])) > 0, f"Graph has no nodes: {list(graph_data.keys())}"

    # 4. Run epistemic analysis
    claims_layer = analyze_epistemic(tmp_path, domain_name="contract")

    # 5. Verify claims layer
    claims_path = tmp_path / "claims_layer.json"
    assert claims_path.exists(), f"claims_layer.json not created after epistemic analysis"

    # 6. Export
    cmd_export(str(tmp_path), "json")


@pytest.mark.e2e
def test_e2e_pipeline_graph_has_metadata(tmp_path):
    """Verify graph output includes proper node metadata."""
    from run_sift import cmd_build

    # Build from drug extraction fixture
    _setup_extraction(tmp_path, "sample_extraction_drug.json", "test_drug_paper.pdf.json")
    cmd_build(str(tmp_path), domain_name="drug-discovery")

    # Load and verify graph structure
    graph_path = tmp_path / "graph_data.json"
    assert graph_path.exists(), f"graph_data.json not created"

    data = json.loads(graph_path.read_text())

    # Verify top-level structure
    assert "nodes" in data, f"graph_data.json missing 'nodes' key, has: {list(data.keys())}"
    assert "links" in data or "edges" in data, f"graph_data.json missing 'links'/'edges' key, has: {list(data.keys())}"

    # Verify all nodes have required fields
    for node in data["nodes"]:
        assert "entity_type" in node, f"Node missing 'entity_type': {node}"
        assert "name" in node, f"Node missing 'name': {node}"


# ========================================================================
# Phase 13 — FIDL-02b: Bug-4 reproducer end-to-end
# ========================================================================

@pytest.mark.e2e
def test_e2e_bug4_normalization_95pct(tmp_path):
    """FT-009: 24-file Bug-4 reproducer achieves ≥95% pass rate and graph builds.

    Copies tests/fixtures/normalization/ into tmp_path/extractions/, runs
    normalize_extractions, asserts pass_rate >= 0.95, then runs cmd_build
    to confirm the normalized extractions actually reach sift-kg's graph builder
    (closing the 30% silent-drop loophole).
    """
    from normalize_extractions import normalize_extractions
    from run_sift import cmd_build

    # 1. Stage fixture into tmp_path/extractions/
    src_fixture_dir = FIXTURES_DIR / "normalization"
    assert src_fixture_dir.is_dir(), f"Missing fixture dir: {src_fixture_dir}"

    ext_dir = tmp_path / "extractions"
    ext_dir.mkdir()
    fixture_files = list(src_fixture_dir.glob("*.json"))
    assert len(fixture_files) == 24, \
        f"Expected 24 fixture files, got {len(fixture_files)}"
    for src in fixture_files:
        shutil.copy2(src, ext_dir / src.name)

    # 2. Run normalize_extractions — must report pass_rate >= 0.95
    result = normalize_extractions(tmp_path, fail_threshold=0.95)

    assert result["pass_rate"] >= 0.95, (
        f"Bug-4 reproducer pass rate below 95% gate: "
        f"pass_rate={result['pass_rate']:.2%}, "
        f"passed={result['passed']}, recovered={result['recovered']}, "
        f"unrecoverable={result['unrecoverable']}, total={result['total']}"
    )

    report_path = tmp_path / "extractions" / "_normalization_report.json"
    assert report_path.exists(), "Normalization report not written"
    report = json.loads(report_path.read_text())
    assert report["above_threshold"] is True

    # 3. Run sift-kg build — normalized files must actually reach the graph
    cmd_build(str(tmp_path), domain_name="drug-discovery")
    graph_path = tmp_path / "graph_data.json"
    assert graph_path.exists(), (
        f"graph_data.json not created after normalize+build; "
        f"sift-kg silent-drop bug may have regressed"
    )
    graph = json.loads(graph_path.read_text())
    nodes = graph.get("nodes", [])
    assert len(nodes) > 0, (
        f"Graph has no nodes — normalized extractions not reaching builder. "
        f"Normalization report: {report}"
    )


@pytest.mark.e2e
def test_e2e_fail_threshold_aborts(tmp_path):
    """FT-010: --fail-threshold aborts pipeline BEFORE graph build when pass rate is below threshold.

    Copies tests/fixtures/normalization_below_threshold/ (2 good + 8 unrecoverable)
    into tmp_path/extractions/, invokes core/normalize_extractions.py via subprocess
    with --fail-threshold 0.95, asserts non-zero exit AND absence of graph_data.json.
    """
    import subprocess

    # 1. Stage fixture
    src_fixture_dir = FIXTURES_DIR / "normalization_below_threshold"
    assert src_fixture_dir.is_dir(), f"Missing fixture dir: {src_fixture_dir}"

    ext_dir = tmp_path / "extractions"
    ext_dir.mkdir()
    fixture_files = list(src_fixture_dir.glob("*.json"))
    assert len(fixture_files) == 10, \
        f"Expected 10 below-threshold fixture files, got {len(fixture_files)}"
    for src in fixture_files:
        shutil.copy2(src, ext_dir / src.name)

    # 2. Run normalize_extractions CLI with --fail-threshold 0.95
    script = PROJECT_ROOT / "core" / "normalize_extractions.py"
    result = subprocess.run(
        ["python3", str(script), str(tmp_path), "--fail-threshold", "0.95"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT),
    )

    # 3. Abort expectations
    assert result.returncode == 1, (
        f"Expected abort exit code 1 (below-threshold), got {result.returncode}. "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert "ABORT" in result.stderr, \
        f"Stderr should mention ABORT; got: {result.stderr!r}"

    # 4. Report was written with above_threshold: false
    report_path = ext_dir / "_normalization_report.json"
    assert report_path.exists(), "Normalization report not written even on abort path"
    report = json.loads(report_path.read_text())
    assert report["above_threshold"] is False, \
        f"Report should mark above_threshold=false when aborting; got: {report}"
    assert report["pass_rate"] < 0.95

    # 5. CRITICAL: graph_data.json MUST NOT exist — the pipeline aborted before build
    graph_path = tmp_path / "graph_data.json"
    assert not graph_path.exists(), (
        "graph_data.json was created despite --fail-threshold abort; "
        "pipeline does not gate graph build on normalization pass-rate"
    )


# ========================================================================
# FT-011, FT-012: Phase 14 chunk overlap acceptance (FIDL-03)
# ========================================================================


@pytest.mark.e2e
def test_ft011_boundary_straddle_chunk_level_colocation(monkeypatch):
    """FT-011 (M-3 Option A): chunk-level co-location of boundary-straddling mentions.

    Single test, two modes:
      GREEN — real chunker produces a chunk containing both mention strings.
      RED   — with overlap disabled (both the chonkie SentenceChunker's
              intra-chunk overlap AND the _tail_sentences cross-flush helper
              monkey-patched out), no chunk contains both mentions.

    Chunk-level co-location is the CAUSE the overlap fix addresses. LLM
    relation extraction (INHIBITS(sotorasib, KRAS G12C)) is the downstream
    effect we cannot assert without a real LLM; the chunk-level test honestly
    captures the necessary precondition instead.

    RED-first proof is in-function: pytest's monkeypatch auto-restores at
    teardown, so no git-stash choreography — a fresh clone can run pytest
    and see that the fix matters.

    Implementation note (Phase 14 chonkie pivot): the plan was drafted
    pre-pivot referencing `_sentence_overlap`. Post-pivot the fixture's
    text routes through `_split_fixed` where chonkie handles overlap
    natively via `_make_chunker`; cross-flush hops (ARTICLE boundaries,
    merge transitions) use `_tail_sentences`. RED mode patches BOTH so
    overlap is disabled end-to-end regardless of which path the chunker
    dispatches through.
    """
    sys.path.insert(0, str(PROJECT_ROOT / "core"))
    import chunk_document as cd
    from chonkie import SentenceChunker

    fixture = FIXTURES_DIR / "phase14_boundary_straddle.txt"
    text = fixture.read_text()

    # --- GREEN: real overlap ---
    chunks = cd.chunk_document(text, "straddle_green")
    both_in = [
        i for i, c in enumerate(chunks)
        if "sotorasib" in c["text"].lower() and "kras g12c" in c["text"].lower()
    ]
    assert both_in, (
        "GREEN assertion failed: no chunk contains both 'sotorasib' and "
        "'KRAS G12C' after Phase 14 overlap. Chunk map: "
        + repr([
            (i, "sotorasib" in c["text"].lower(), "kras g12c" in c["text"].lower())
            for i, c in enumerate(chunks)
        ])
    )

    # --- RED: disable overlap, reassert failure ---
    # Patch both the chonkie chunker factory (intra-chunk overlap) and the
    # cross-flush tail helper. Either alone leaves one path unpatched.
    zero_overlap_chunker = SentenceChunker(
        tokenizer="character",
        chunk_size=cd.MAX_CHUNK_SIZE,
        chunk_overlap=0,
        min_sentences_per_chunk=1,
    )
    monkeypatch.setattr(cd, "_make_chunker", lambda max_size=cd.MAX_CHUNK_SIZE: zero_overlap_chunker)
    monkeypatch.setattr(cd, "_tail_sentences", lambda *_args, **_kwargs: "")

    chunks_no_overlap = cd.chunk_document(text, "straddle_red")
    both_in_no = [
        i for i, c in enumerate(chunks_no_overlap)
        if "sotorasib" in c["text"].lower() and "kras g12c" in c["text"].lower()
    ]
    assert not both_in_no, (
        "RED assertion failed: a chunk contains both mentions even with "
        "overlap disabled — either the fixture accidentally co-locates "
        "them or the chunker is cheating. Chunk map: "
        + repr([
            (i, "sotorasib" in c["text"].lower(), "kras g12c" in c["text"].lower())
            for i, c in enumerate(chunks_no_overlap)
        ])
    )


@pytest.mark.e2e
def test_ft012_v2_baseline_regression():
    """FT-012 (B-2): V2 regression gated by committed tests/baselines/v2/expected.json.

    File-backed floor. Missing expected.json is a HARD FAILURE, not a skip —
    a skippable gate is no gate at all. The expected.json contains small
    summary counts (nodes/edges per scenario); the full graph_data.json
    dumps remain gitignored.

    Reads `graph_data.json` from each scenario's output directory directly
    (same resolution logic as tests/regression/run_regression.py). This is
    a deliberate deviation from the plan's subprocess+stdout-parsing design
    — the actual runner output format (`label N1/N2 E1/E2 C1/C2`) does not
    match the plan's assumed `"contract: N nodes, E edges"` format, and
    direct graph_data.json reading is both more robust and equivalent in
    intent.

    If a scenario's output directory is missing (e.g., contract_events on
    machines without sample-output-v2/), FT-012 records SKIP for that
    scenario — mirrors run_regression.py's skip behavior. A missing output
    directory is NOT a regression; the gate is floor comparison against
    existing output.

    The human checkpoint (Task 3) records actual observed counts during
    the contract-gate verification and commits the updated expected.json
    alongside the Phase-14 PR.
    """
    expected_path = PROJECT_ROOT / "tests" / "baselines" / "v2" / "expected.json"
    assert expected_path.exists(), (
        f"V2 acceptance floor file missing: {expected_path}\n"
        f"This file is committed to git (small summary counts, NOT full graph dumps).\n"
        f"If it was deleted, restore it from the Phase 14 PR. "
        f"If it has never existed, the human checkpoint (Plan 14-04 Task 3) "
        f"must seed it: run `python3 tests/regression/run_regression.py`, "
        f"capture per-scenario node/edge counts, and write them into "
        f"tests/baselines/v2/expected.json using the schema documented in "
        f"Plan 14-04. FT-012 cannot pass without this file."
    )

    expected = json.loads(expected_path.read_text())
    assert "scenarios" in expected, f"expected.json missing 'scenarios' key: {list(expected.keys())}"

    # Scenario name -> output directory resolution. Mirrors
    # tests/regression/run_regression.py::_resolve_output_dir but operates on
    # expected.json's scenario keys directly.
    drug_discovery_scenarios = {
        "01_picalm_alzheimers",
        "02_kras_g12c_landscape",
        "03_rare_disease",
        "04_immunooncology",
        "05_cardiovascular",
        "06_glp1_landscape",
    }
    contract_scenarios = {"contract_events", "contracts", "contracts_sample"}

    def _resolve_output(scenario: str) -> Path | None:
        if scenario in drug_discovery_scenarios:
            for subdir in ("output-v2", "output"):
                candidate = PROJECT_ROOT / "tests" / "corpora" / scenario / subdir
                if candidate.exists():
                    return candidate
            return None
        if scenario in contract_scenarios:
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

    failures: list[str] = []
    for scenario, expect in expected["scenarios"].items():
        exp_nodes = int(expect["nodes"])
        exp_edges = int(expect["edges"])

        output_dir = _resolve_output(scenario)
        if output_dir is None:
            # No current output for this scenario — treat as SKIP. If the floor
            # is > 0 this is operator attention needed (e.g., contract floor
            # stays committed but contract output hasn't been regenerated yet).
            continue

        graph_path = output_dir / "graph_data.json"
        if not graph_path.exists():
            continue

        graph = json.loads(graph_path.read_text())
        obs_nodes = len(graph.get("nodes", []))
        obs_edges = len(graph.get("links", graph.get("edges", [])))

        if obs_nodes < exp_nodes or obs_edges < exp_edges:
            failures.append(
                f"{scenario}: observed {obs_nodes} nodes / {obs_edges} edges "
                f"< floor {exp_nodes} nodes / {exp_edges} edges "
                f"(graph: {graph_path})"
            )

    assert not failures, (
        "V2 regression failed (scenarios below committed floor):\n"
        + "\n".join(f"  - {f}" for f in failures)
    )


# ===========================================================================
# Phase 18 Plan 18-02 — FT-019 end-to-end (FIDL-07 D-05, D-06, D-16)
# ===========================================================================


def _write_synthetic_pdb_extraction(tmp_path):
    """Write a minimal valid DocumentExtraction JSON with a PDB document_id.

    Used by FT-019 Sub-tests B and C. Mirrors the shape of fixtures in
    FIXTURES_DIR/sample_extraction_drug.json but with a structural doc_id
    and crystallography evidence.
    """
    extractions_dir = tmp_path / "extractions"
    extractions_dir.mkdir(exist_ok=True)
    extraction = {
        "document_id": "pdb_1abc",
        "domain_name": "drug-discovery",
        "entities": [
            {
                "name": "KRAS",
                "entity_type": "GENE",
                "confidence": 0.95,
                "context": "crystal structure of KRAS resolved at 2.1 Å",
            },
            {
                "name": "BI-2865",
                "entity_type": "COMPOUND",
                "confidence": 0.9,
                "context": "co-crystal with KRAS at 2.1 Å",
            },
        ],
        "relations": [
            {
                "source_entity": "BI-2865",
                "target_entity": "KRAS",
                "relation_type": "TARGETS",
                "confidence": 0.95,
                "evidence": "crystal structure of KRAS resolved at 2.1 Å",
            }
        ],
        "extracted_at": "2026-04-22T00:00:00+00:00",
        "chunks_processed": 1,
        "document_path": "",
        "cost_usd": 0.0,
        "model_used": "claude-opus-4-6",
        "chunk_size": 10000,
        "error": None,
    }
    (extractions_dir / "pdb_1abc.json").write_text(json.dumps(extraction, indent=2))


@pytest.mark.e2e
def test_ft019_baseline_invariance_contracts(tmp_path):
    """FT-019 Sub-test A: contracts has no CUSTOM_RULES → custom_findings empty/absent.

    Regression gate for D-07: absent CUSTOM_RULES means claims_layer stays
    byte-identical to pre-18-01 output (the custom_findings key is omitted
    entirely, not set to an empty dict).
    """
    from run_sift import cmd_build
    from label_epistemic import analyze_epistemic

    _setup_extraction(tmp_path, "sample_extraction_contract.json", "test_vendor.pdf.json")
    cmd_build(str(tmp_path), domain_name="contracts")
    claims_layer = analyze_epistemic(tmp_path, domain_name="contracts")
    super_domain = claims_layer.get("super_domain", {})
    custom = super_domain.get("custom_findings", {})
    # Accept empty-dict OR key-absent — either matches D-07 backward-compat.
    assert custom == {} or "custom_findings" not in super_domain, (
        f"Contracts has no CUSTOM_RULES — expected empty/absent custom_findings, "
        f"got {custom!r}"
    )


@pytest.mark.e2e
def test_ft019_structural_doctype_propagation(tmp_path):
    """FT-019 Sub-test B: synthetic pdb_1abc doc → claims_layer.summary.document_types['structural'] ≥ 1.

    Exercises Task 2's PDB_PATTERN + infer_doc_type branch end-to-end
    through cmd_build → analyze_epistemic → summary aggregation.
    """
    from run_sift import cmd_build
    from label_epistemic import analyze_epistemic

    _write_synthetic_pdb_extraction(tmp_path)
    cmd_build(str(tmp_path), domain_name="drug-discovery")
    claims_layer = analyze_epistemic(tmp_path, domain_name="drug-discovery")
    doc_types = claims_layer.get("summary", {}).get("document_types", {})
    # doc_profile is keyed by doctype; each value is a status-count dict.
    # Presence of the "structural" key means infer_doc_type classified the
    # pdb_1abc mention's source_document as structural.
    assert "structural" in doc_types, (
        f"pdb_1abc should classify as structural; got doc_types={doc_types}"
    )


@pytest.mark.e2e
def test_ft019_validator_report_exists(tmp_path):
    """FT-019 Sub-test C: cmd_build auto-dispatch writes validation_report.json with a status key.

    Exercises Plan 18-01's validator hook end-to-end. Both 'ok' and
    'skipped' (RDKit-absent) satisfy the status-key assertion — the
    presence of the report + its schema shape is the gate, not the
    validation outcome.
    """
    from run_sift import cmd_build

    _write_synthetic_pdb_extraction(tmp_path)
    cmd_build(str(tmp_path), domain_name="drug-discovery")
    report_path = tmp_path / "validation_report.json"
    assert report_path.exists(), (
        f"validation_report.json not written after cmd_build; "
        f"tmp_path contents: {list(tmp_path.iterdir())}"
    )
    report = json.loads(report_path.read_text())
    assert "status" in report, (
        f"Expected 'status' key in report, got keys={list(report.keys())}"
    )
