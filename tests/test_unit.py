#!/usr/bin/env python3
"""Unit tests for epistract plugin components.

Maps to TEST_REQUIREMENTS.md unit tests UT-001 through UT-014.
Run: python -m pytest tests/test_unit.py -m unit -v
"""

import json
import sys
import tempfile

import yaml
from pathlib import Path
from unittest import mock

import pytest

from conftest import FIXTURES_DIR, HAS_BIOPYTHON, HAS_RDKIT, HAS_SIFTKG, PROJECT_ROOT
from unittest.mock import patch, MagicMock  # noqa: E402 — CTDM tests require patch/MagicMock

# ---------------------------------------------------------------------------
# Always-available imports from the project itself
# ---------------------------------------------------------------------------
from scan_patterns import scan_text
from validate_sequences import detect_type
from build_extraction import write_extraction

# Domain paths
DRUG_DISCOVERY_DIR = PROJECT_ROOT / "domains" / "drug-discovery"
DOMAIN_YAML = DRUG_DISCOVERY_DIR / "domain.yaml"

# Conditional imports
if HAS_RDKIT:
    from validate_smiles import validate_smiles
if HAS_BIOPYTHON:
    from validate_sequences import validate_sequence


# ========================================================================
# UT-001: Domain YAML Loads Successfully
# ========================================================================
@pytest.mark.unit
@pytest.mark.skipif(not HAS_SIFTKG, reason="sift-kg not installed")
def test_ut001_domain_loads():
    """Load domain.yaml via sift-kg DomainLoader, assert 17 entity types and 30 relation types."""
    from sift_kg import load_domain

    domain = load_domain(domain_path=DOMAIN_YAML)
    assert len(domain.entity_types) == 17, (
        f"Expected 17 entity types, got {len(domain.entity_types)}"
    )
    assert len(domain.relation_types) == 30, (
        f"Expected 30 relation types, got {len(domain.relation_types)}"
    )


# ========================================================================
# UT-002: Pattern Scanner Detects SMILES
# ========================================================================
@pytest.mark.unit
def test_ut002_scan_smiles():
    """scan_text with SMILES string returns match with pattern_type containing 'SMILES'."""
    text = "The aspirin structure is SMILES: CC(=O)Oc1ccccc1C(=O)O which is well known."
    results = scan_text(text)
    smiles_matches = [r for r in results if "SMILES" in r["pattern_type"]]
    assert len(smiles_matches) >= 1, f"Expected SMILES match, got: {results}"
    assert "CC(=O)Oc1ccccc1C(=O)O" in smiles_matches[0]["value"]


# ========================================================================
# UT-003: Pattern Scanner Detects NCT Numbers
# ========================================================================
@pytest.mark.unit
def test_ut003_scan_nct():
    """scan_text with NCT number returns match with pattern_type NCT_NUMBER."""
    text = "The trial NCT04303780 evaluated sotorasib in NSCLC patients."
    results = scan_text(text)
    nct_matches = [r for r in results if r["pattern_type"] == "NCT_NUMBER"]
    assert len(nct_matches) >= 1, f"Expected NCT match, got: {results}"
    assert nct_matches[0]["value"] == "NCT04303780"


# ========================================================================
# UT-004: Pattern Scanner Detects DNA Sequences
# ========================================================================
@pytest.mark.unit
def test_ut004_scan_dna():
    """scan_text with DNA sequence (>=15 chars) returns match with pattern_type DNA_SEQUENCE."""
    text = "The primer sequence ATCGATCGATCGATCG was used for amplification."
    results = scan_text(text)
    dna_matches = [r for r in results if r["pattern_type"] == "DNA_SEQUENCE"]
    assert len(dna_matches) >= 1, f"Expected DNA match, got: {results}"
    assert dna_matches[0]["value"] == "ATCGATCGATCGATCG"


# ========================================================================
# UT-005: Pattern Scanner Detects CAS Numbers
# ========================================================================
@pytest.mark.unit
def test_ut005_scan_cas():
    """scan_text with CAS number returns match with pattern_type CAS_NUMBER."""
    text = "Sotorasib (CAS 2252403-56-6) is a KRAS G12C inhibitor."
    results = scan_text(text)
    cas_matches = [r for r in results if r["pattern_type"] == "CAS_NUMBER"]
    assert len(cas_matches) >= 1, f"Expected CAS match, got: {results}"
    assert cas_matches[0]["value"] == "2252403-56-6"


# ========================================================================
# UT-006: SMILES Validator Returns Properties (valid)
# ========================================================================
@pytest.mark.unit
@pytest.mark.skipif(not HAS_RDKIT, reason="RDKit not installed")
def test_ut006_validate_smiles_valid():
    """validate_smiles with aspirin SMILES returns valid=True with properties."""
    result = validate_smiles("CC(=O)Oc1ccccc1C(=O)O")
    assert result["valid"] is True
    assert "molecular_weight" in result
    assert "canonical_smiles" in result
    # Aspirin MW ~180
    assert 170 < result["molecular_weight"] < 190


# ========================================================================
# UT-007: SMILES Validator Rejects Invalid SMILES
# ========================================================================
@pytest.mark.unit
@pytest.mark.skipif(not HAS_RDKIT, reason="RDKit not installed")
def test_ut007_validate_smiles_invalid():
    """validate_smiles with invalid string returns valid=False."""
    result = validate_smiles("not_a_smiles")
    assert result["valid"] is False
    assert "error" in result


# ========================================================================
# UT-008: SMILES Validator Graceful Without RDKit
# ========================================================================
@pytest.mark.unit
def test_ut008_validate_smiles_no_rdkit():
    """With RDKit not importable, validate_smiles returns valid=None."""
    # We need to reload validate_smiles with rdkit unavailable
    # Import the module fresh with mocked rdkit
    import importlib
    import validate_smiles as vs_mod

    # Save original state
    orig_available = vs_mod.RDKIT_AVAILABLE

    try:
        vs_mod.RDKIT_AVAILABLE = False
        result = vs_mod.validate_smiles("CC(=O)Oc1ccccc1C(=O)O")
        assert result["valid"] is None
        assert (
            "not installed" in result.get("error", "").lower()
            or "rdkit" in result.get("error", "").lower()
        )
    finally:
        vs_mod.RDKIT_AVAILABLE = orig_available


# ========================================================================
# UT-009: Sequence Validator Validates DNA
# ========================================================================
@pytest.mark.unit
@pytest.mark.skipif(not HAS_BIOPYTHON, reason="Biopython not installed")
def test_ut009_validate_dna():
    """validate_sequence with DNA returns valid=True, type=DNA, gc_content present."""
    result = validate_sequence("ATCGATCGATCGATCG")
    assert result["valid"] is True
    assert result["type"] == "DNA"
    assert "gc_content" in result


# ========================================================================
# UT-010: Sequence Validator Validates Protein
# ========================================================================
@pytest.mark.unit
@pytest.mark.skipif(not HAS_BIOPYTHON, reason="Biopython not installed")
def test_ut010_validate_protein():
    """validate_sequence with protein returns valid=True, type=protein, molecular_weight present."""
    result = validate_sequence("MTEYKLVVVGAGGVGKSALT")
    assert result["valid"] is True
    assert result["type"] == "protein"
    assert "molecular_weight" in result


# ========================================================================
# UT-011: Sequence Validator Auto-Detects Type
# ========================================================================
@pytest.mark.unit
def test_ut011_detect_type():
    """detect_type correctly identifies DNA, RNA, and protein sequences."""
    assert detect_type("ATCGATCG") == "DNA"
    assert detect_type("AUGCUAGC") == "RNA"
    assert detect_type("MTEYKLVVV") == "protein"


# ========================================================================
# UT-012: Extraction Adapter Writes Valid JSON
# ========================================================================
@pytest.mark.unit
def test_ut012_extraction_adapter():
    """write_extraction creates valid JSON matching sift-kg schema."""
    entities = [
        {
            "name": "sotorasib",
            "entity_type": "COMPOUND",
            "confidence": 0.95,
            "context": "Sotorasib is a KRAS G12C inhibitor.",
        }
    ]
    relations = [
        {
            "source_entity": "sotorasib",
            "target_entity": "KRAS G12C",
            "relation_type": "INHIBITS",
            "confidence": 0.9,
            "evidence": "Sotorasib inhibits KRAS G12C.",
        }
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        path = write_extraction("test_doc", tmpdir, entities, relations)
        assert Path(path).exists()

        data = json.loads(Path(path).read_text())
        # Required fields
        assert data["document_id"] == "test_doc"
        assert isinstance(data["entities"], list)
        assert isinstance(data["relations"], list)
        assert len(data["entities"]) == 1
        assert len(data["relations"]) == 1
        assert "extracted_at" in data
        assert "domain_name" in data


# ========================================================================
# UT-013: run_sift.py Build Command Works
# ========================================================================
@pytest.mark.unit
@pytest.mark.skipif(not HAS_SIFTKG, reason="sift-kg not installed")
def test_ut013_run_sift_build():
    """Create test extractions, run build, verify graph_data.json created."""
    from run_sift import cmd_build

    entities = [
        {
            "name": "sotorasib",
            "entity_type": "COMPOUND",
            "confidence": 0.95,
            "context": "Sotorasib is a KRAS G12C inhibitor.",
        },
        {
            "name": "KRAS G12C",
            "entity_type": "GENE",
            "confidence": 0.9,
            "context": "KRAS G12C is a mutant oncogene.",
        },
    ]
    relations = [
        {
            "source_entity": "sotorasib",
            "target_entity": "KRAS G12C",
            "relation_type": "INHIBITS",
            "confidence": 0.9,
            "evidence": "Sotorasib inhibits KRAS G12C.",
        }
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        # Write extraction
        write_extraction("test_doc_001", tmpdir, entities, relations)

        # Run build
        cmd_build(tmpdir, domain_name="drug-discovery")

        # Verify graph_data.json
        graph_path = Path(tmpdir) / "graph_data.json"
        assert graph_path.exists(), "graph_data.json was not created"

        graph_data = json.loads(graph_path.read_text())
        # Should have at least the entities we provided
        nodes = graph_data.get("nodes", graph_data.get("entities", []))
        assert len(nodes) > 0, "Graph has no entities"


# ========================================================================
# UT-014: Validation Orchestrator Scans Extractions
# ========================================================================
@pytest.mark.unit
def test_ut014_validation_orchestrator():
    """Create extraction with SMILES in context, run validate_molecules, verify results."""
    entities = [
        {
            "name": "aspirin",
            "entity_type": "COMPOUND",
            "confidence": 0.95,
            "context": "Aspirin has the structure SMILES: CC(=O)Oc1ccccc1C(=O)O and is used as an analgesic.",
        }
    ]
    relations = []

    with tempfile.TemporaryDirectory() as tmpdir:
        # Write extraction
        write_extraction("smiles_test", tmpdir, entities, relations)

        # Run validate_molecules via subprocess to avoid import side effects
        import subprocess

        result = subprocess.run(
            [sys.executable, str(DRUG_DISCOVERY_DIR / "validate_molecules.py"), tmpdir],
            capture_output=True,
            text=True,
        )

        # Check results.json was created
        results_path = Path(tmpdir) / "validation" / "results.json"
        assert results_path.exists(), (
            f"results.json not created. stderr: {result.stderr}"
        )

        data = json.loads(results_path.read_text())
        total_matches = data["stats"]["total_matches"]
        assert total_matches > 0, (
            f"Expected identifiers_found > 0, got stats: {data['stats']}"
        )


# ---------------------------------------------------------------------------
# Epistemic dispatcher generalization tests (Phase 8)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_epistemic_dispatcher_generic_contract():
    """Verify dispatcher resolves 'contract' to analyze_contract_epistemic via convention."""
    from core.label_epistemic import _load_domain_epistemic

    mod = _load_domain_epistemic("contract")
    assert mod is not None, "Failed to load contract epistemic module"
    assert hasattr(mod, "analyze_contract_epistemic"), (
        "Missing analyze_contract_epistemic function"
    )


@pytest.mark.unit
def test_epistemic_dispatcher_generic_biomedical():
    """Verify dispatcher resolves 'drug-discovery' to analyze_biomedical_epistemic via convention."""
    from core.label_epistemic import _load_domain_epistemic

    mod = _load_domain_epistemic("drug-discovery")
    assert mod is not None, "Failed to load drug-discovery epistemic module"
    assert hasattr(mod, "analyze_biomedical_epistemic"), (
        "Missing analyze_biomedical_epistemic function"
    )


@pytest.mark.unit
def test_epistemic_dispatcher_alias_resolution():
    """Verify dispatcher handles aliases like 'biomedical' -> 'drug-discovery'."""
    from core.label_epistemic import _load_domain_epistemic

    mod = _load_domain_epistemic("biomedical")
    assert mod is not None, "Failed to load biomedical alias"
    assert hasattr(mod, "analyze_biomedical_epistemic"), (
        "Alias didn't resolve to drug-discovery module"
    )


@pytest.mark.unit
def test_epistemic_dispatcher_unknown_domain_returns_none():
    """Verify dispatcher returns None for nonexistent domain (no crash)."""
    from core.label_epistemic import _load_domain_epistemic

    mod = _load_domain_epistemic("nonexistent-domain-xyz")
    assert mod is None, "Should return None for unknown domain"


@pytest.mark.unit
def test_wizard_fixtures_exist():
    """Verify wizard test fixtures are present."""
    fixtures_dir = Path(__file__).parent / "fixtures" / "wizard"
    assert fixtures_dir.is_dir(), f"Missing wizard fixtures directory: {fixtures_dir}"
    samples = list(fixtures_dir.glob("sample_lease_*.txt"))
    assert len(samples) >= 2, f"Need at least 2 sample docs, found {len(samples)}"
    for sample in samples:
        text = sample.read_text()
        assert len(text) > 100, f"Sample {sample.name} too short ({len(text)} chars)"


# ---------------------------------------------------------------------------
# Domain wizard generation tests (Phase 8, Plan 02)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_wizard_read_sample_docs():
    """read_sample_documents returns doc info for 3 fixture files."""
    from core.domain_wizard import read_sample_documents

    fixtures = Path(__file__).parent / "fixtures" / "wizard"
    paths = sorted(fixtures.glob("sample_lease_*.txt"))
    result = read_sample_documents(paths)
    assert len(result) == 3
    for doc in result:
        assert "path" in doc
        assert "text" in doc
        assert "char_count" in doc
        assert doc["char_count"] > 100


@pytest.mark.unit
def test_wizard_read_sample_docs_too_few():
    """read_sample_documents raises ValueError with < 2 docs."""
    from core.domain_wizard import read_sample_documents

    fixtures = Path(__file__).parent / "fixtures" / "wizard"
    paths = [next(fixtures.glob("sample_lease_1.txt"))]
    with pytest.raises(ValueError, match="at least 2"):
        read_sample_documents(paths)


@pytest.mark.unit
def test_wizard_generates_domain_yaml():
    """generate_domain_yaml produces valid YAML with required keys."""
    from core.domain_wizard import generate_domain_yaml

    entity_types = {
        "LANDLORD": {"description": "Property owner"},
        "TENANT": {"description": "Lessee"},
    }
    relation_types = {
        "LEASES_TO": {"description": "Landlord leases property to tenant"}
    }
    result = generate_domain_yaml(
        "Real Estate Leases",
        "Lease analysis domain",
        "You are analyzing lease agreements.",
        entity_types,
        relation_types,
    )
    parsed = yaml.safe_load(result)
    assert parsed["name"] == "Real Estate Leases"
    assert "LANDLORD" in parsed["entity_types"]
    assert "LEASES_TO" in parsed["relation_types"]
    assert parsed["version"] == "1.0.0"


@pytest.mark.unit
def test_wizard_generates_skill_md():
    """generate_skill_md produces markdown with required sections."""
    from core.domain_wizard import generate_skill_md

    entity_types = {"LANDLORD": {"description": "Property owner"}}
    relation_types = {"LEASES_TO": {"description": "Leases property"}}
    result = generate_skill_md(
        "Real Estate Leases",
        "Analyzing lease agreements.",
        entity_types,
        relation_types,
        "Extract all parties and obligations.",
    )
    assert "## Entity Types" in result
    assert "## Relation Types" in result
    assert "LANDLORD" in result
    assert "LEASES_TO" in result


@pytest.mark.unit
def test_wizard_generates_epistemic_py():
    """generate_epistemic_py produces valid Python with correct function name."""
    from core.domain_wizard import generate_epistemic_py

    import ast

    code = generate_epistemic_py(
        "real_estate",
        {"LANDLORD": {"description": "Owner"}, "TENANT": {"description": "Lessee"}},
        [("exclusive", "non-exclusive")],
        {"coverage": ["LANDLORD"]},
        {"high": 0.9, "medium": 0.7, "low": 0.5},
    )
    ast.parse(code)  # Must not raise
    assert "def analyze_real_estate_epistemic(" in code
    assert "metadata" in code
    assert "summary" in code
    # FIDL-07 D-10: wizard emits CUSTOM_RULES stub + pointer to canonical doc.
    assert "CUSTOM_RULES" in code, "Wizard must emit CUSTOM_RULES stub (FIDL-07 D-10)"
    assert "docs/known-limitations.md" in code, (
        "Wizard must link to canonical extensibility doc"
    )


@pytest.mark.unit
def test_wizard_generates_custom_rules_stub():
    """FIDL-07 D-10: generate_epistemic_py output ends with a no-op CUSTOM_RULES stub.

    Separate test function (not just an extended existing one) so the
    D-10 contract is independently traceable. Asserts both the literal
    stub line and the rule-signature comment referenced by the FIDL-07
    known-limitations section.
    """
    from core.domain_wizard import generate_epistemic_py

    import ast

    code = generate_epistemic_py(
        "fake_domain",
        {"ENTITY_A": {"description": "A"}},
        [],
        {},
        {"high": 0.9, "medium": 0.7, "low": 0.5},
    )
    # Generated code must remain syntactically valid Python.
    ast.parse(code)
    # The stub itself
    assert "CUSTOM_RULES: list = []" in code, (
        "Wizard must emit literal CUSTOM_RULES stub (FIDL-07 D-10)"
    )
    # The rule-signature comment
    assert "(nodes, links, context)" in code, (
        "Wizard must document rule callable signature in a comment"
    )
    # The canonical-doc pointer
    assert "docs/known-limitations.md" in code, (
        "Wizard must point at canonical extensibility doc"
    )


@pytest.mark.unit
def test_wizard_validates_epistemic_good():
    """validate_generated_epistemic returns valid=True for correct code."""
    from core.domain_wizard import generate_epistemic_py, validate_generated_epistemic

    code = generate_epistemic_py(
        "test_domain",
        {"ENTITY_A": {"description": "A"}},
        [],
        {},
        {"high": 0.9},
    )
    result = validate_generated_epistemic(code, "test_domain")
    assert result["valid"] is True, f"Validation failed: {result.get('error')}"


@pytest.mark.unit
def test_wizard_validates_epistemic_bad_syntax():
    """validate_generated_epistemic catches syntax errors."""
    from core.domain_wizard import validate_generated_epistemic

    bad_code = "def broken(:\n    pass"
    result = validate_generated_epistemic(bad_code, "broken")
    assert result["valid"] is False
    assert "SyntaxError" in result["error"]


@pytest.mark.unit
def test_wizard_generates_reference_docs():
    """generate_reference_docs produces markdown with entity/relation headers."""
    from core.domain_wizard import generate_reference_docs

    entity_types = {
        "LANDLORD": {"description": "Property owner"},
        "TENANT": {"description": "Lessee"},
    }
    relation_types = {"LEASES_TO": {"description": "Leases property"}}
    entity_md, relation_md = generate_reference_docs(entity_types, relation_types)
    assert "## LANDLORD" in entity_md
    assert "## TENANT" in entity_md
    assert "## LEASES_TO" in relation_md


@pytest.mark.unit
def test_wizard_check_domain_exists():
    """check_domain_exists detects existing domains and aliases."""
    from core.domain_wizard import check_domain_exists

    assert check_domain_exists("contracts") is True
    assert check_domain_exists("contract") is True  # alias
    assert check_domain_exists("nonexistent-domain-xyz") is False


@pytest.mark.unit
def test_wizard_schema_discovery_prompt():
    """build_schema_discovery_prompt includes domain description in prompt."""
    from core.domain_wizard import build_schema_discovery_prompt

    prompt = build_schema_discovery_prompt(
        "Sample lease text here...", "Real estate lease agreements"
    )
    assert "Real estate lease agreements" in prompt
    assert "entity" in prompt.lower()
    assert "relation" in prompt.lower()


@pytest.mark.unit
@pytest.mark.skipif(not HAS_SIFTKG, reason="sift-kg not installed")
def test_wizard_reads_pdf_as_text():
    """FIDL-01: PDF samples are read as extracted text, not as %PDF binary header."""
    from core.domain_wizard import read_sample_documents

    fixtures = Path(__file__).parent / "fixtures" / "wizard"
    pdf_path = fixtures / "sample_lease_2.pdf"
    txt_path = fixtures / "sample_lease_1.txt"

    assert pdf_path.exists(), f"Missing PDF fixture: {pdf_path}"

    result = read_sample_documents([pdf_path, txt_path])

    by_path = {doc["path"]: doc for doc in result}
    pdf_doc = by_path[str(pdf_path)]

    # The critical assertion: we got extracted text, not the raw %PDF header.
    assert not pdf_doc["text"].startswith("%PDF"), (
        f"PDF was read as raw binary — FIDL-01 regression. "
        f"First 20 chars: {pdf_doc['text'][:20]!r}"
    )
    assert pdf_doc["char_count"] > 0, "PDF extraction returned empty text"
    assert "text" in pdf_doc and isinstance(pdf_doc["text"], str)


@pytest.mark.unit
def test_wizard_skips_binary_when_sift_reader_missing():
    """FIDL-01: When sift-kg is not installed, binary files are skipped rather than
    silently read as %PDF garbage — caller hits MIN_SAMPLE_DOCS ValueError instead."""
    from core import domain_wizard

    fixtures = Path(__file__).parent / "fixtures" / "wizard"
    pdf_path = fixtures / "sample_lease_2.pdf"

    assert pdf_path.exists(), f"Missing PDF fixture: {pdf_path}"

    with mock.patch.object(domain_wizard, "HAS_SIFT_READER", False):
        with pytest.raises(ValueError, match="at least 2"):
            # Two PDFs, no sift-kg: both should be skipped, triggering the
            # MIN_SAMPLE_DOCS guard. Crucially, no dict with text=="%PDF..."
            # is returned.
            domain_wizard.read_sample_documents([pdf_path, pdf_path])


# ========================================================================
# Phase 16 — FIDL-05: Wizard Sample Window Beyond 8KB
# ========================================================================


@pytest.mark.unit
def test_build_excerpts():
    """UT-042: _build_excerpts returns [] for ≤12K docs and 3 slices for >12K docs (D-01, D-02, D-03)."""
    from core.domain_wizard import (
        EXCERPT_CHARS,
        MULTI_EXCERPT_THRESHOLD,
        _build_excerpts,
    )

    # Sanity-check constants
    assert EXCERPT_CHARS == 4000, f"EXCERPT_CHARS should be 4000, got {EXCERPT_CHARS}"
    assert MULTI_EXCERPT_THRESHOLD == 12000, (
        f"MULTI_EXCERPT_THRESHOLD should be 12000, got {MULTI_EXCERPT_THRESHOLD}"
    )

    # Short-doc branch: strictly ≤ threshold returns []
    assert _build_excerpts("x" * 11999) == [], "len=11999 must be short-doc path"
    assert _build_excerpts("x" * 12000) == [], (
        "len=12000 is boundary — must still be short-doc (uses > threshold, not >=)"
    )

    # Long-doc branch: 3 slices of 4000 chars each
    long_result = _build_excerpts("x" * 12001)
    assert isinstance(long_result, list), f"Expected list, got {type(long_result)}"
    assert len(long_result) == 3, f"Expected 3 excerpts, got {len(long_result)}"
    assert all(isinstance(s, str) for s in long_result), "All excerpts must be str"
    assert all(len(s) == 4000 for s in long_result[:1]), (
        "Head must be exactly 4000 chars"
    )

    # D-01 + D-03 — explicit offsets for a 30000-char doc
    payload_30k = "a" * 30000
    slices = _build_excerpts(payload_30k)
    assert slices[0] == "a" * 4000, "Head slice must equal doc_text[:4000] (D-01)"
    assert slices[1] == "a" * 4000, (
        "Middle slice must equal doc_text[13000:17000] for 30K doc (D-03: centered)"
    )
    assert slices[2] == "a" * 4000, "Tail slice must equal doc_text[-4000:] (D-01)"

    # Structural markers — head / middle / tail each pick up their own sentinel
    head_mark = "HEAD_MARK"
    mid_mark = "MID_MARK"
    tail_mark = "TAIL_MARK"
    structured = head_mark + ("." * 20000) + mid_mark + ("." * 20000) + tail_mark
    struct_slices = _build_excerpts(structured)
    assert head_mark in struct_slices[0], (
        f"Head slice missing {head_mark!r}: {struct_slices[0][:100]!r}"
    )
    assert mid_mark in struct_slices[1], (
        f"Middle slice missing {mid_mark!r}: {struct_slices[1][:100]!r}"
    )
    assert tail_mark in struct_slices[2], (
        f"Tail slice missing {tail_mark!r}: {struct_slices[2][-100:]!r}"
    )


@pytest.mark.unit
def test_multi_excerpt_prompt_contains_markers():
    """UT-043: build_schema_discovery_prompt emits 3 excerpt markers + 3 sentinels for long docs (D-04, D-05, D-10, D-11).

    Fixture dependency — tests/fixtures/wizard_sample_window/long_contract.txt is created in
    Plan 16-02 Task 1. This test is RED until that task lands and GREEN thereafter.
    """
    from core.domain_wizard import build_schema_discovery_prompt

    fixture_path = (
        PROJECT_ROOT
        / "tests"
        / "fixtures"
        / "wizard_sample_window"
        / "long_contract.txt"
    )
    fixture_text = fixture_path.read_text(encoding="utf-8")
    assert len(fixture_text) > 12000, (
        f"Fixture must be >12K chars to trigger multi-excerpt path, got {len(fixture_text)}"
    )

    prompt = build_schema_discovery_prompt(
        fixture_text, "Synthetic long contract domain"
    )

    # D-04: three explicit excerpt markers on their own lines
    assert "[EXCERPT 1/3 — chars 0 to 4000 (head)]" in prompt, (
        "Head marker missing or wrong format (D-04 requires em-dash and exact phrasing)"
    )
    assert "[EXCERPT 2/3 — chars " in prompt, "Middle marker prefix missing"
    assert "[EXCERPT 3/3 — chars " in prompt, "Tail marker prefix missing"

    # D-05: preface + plural header
    assert (
        "The following are three excerpts from a larger document. "
        "Treat them as non-contiguous samples of the same document, "
        "not as a single continuous passage." in prompt
    ), "D-05 preface missing or altered"
    assert "**Document excerpts:**" in prompt, (
        "Plural header missing (D-05 long-doc path)"
    )
    assert "**Document text:**" not in prompt, (
        "Singular header leaked into long-doc path (D-05 violation)"
    )

    # D-10: all three sentinel phrases from the Plan 16-02 fixture appear
    assert "PARTY_SENTINEL_HEAD" in prompt, "Head sentinel missing from rendered prompt"
    assert "OBLIGATION_SENTINEL_MIDDLE" in prompt, (
        "Middle sentinel missing from rendered prompt"
    )
    assert "TERMINATION_SENTINEL_TAIL" in prompt, (
        "Tail sentinel missing from rendered prompt"
    )

    # Domain description still interpolated
    assert "Synthetic long contract domain" in prompt, "Domain description missing"

    # -------------------------------------------------------------------
    # Short-doc path: backward compat (D-02) — no fixture needed
    # -------------------------------------------------------------------
    short_prompt = build_schema_discovery_prompt(
        "Sample lease text here...", "Real estate lease agreements"
    )
    assert "**Document text:**" in short_prompt, (
        "Short-doc path must use singular header (D-02 backward compat)"
    )
    assert "Sample lease text here..." in short_prompt, (
        "Short-doc path must include full doc_text verbatim"
    )
    assert "[EXCERPT" not in short_prompt, (
        "Short-doc path must NOT emit excerpt markers"
    )
    assert "three excerpts from a larger document" not in short_prompt, (
        "Short-doc path must NOT emit the multi-excerpt preface"
    )


@pytest.mark.unit
def test_ft016_long_doc_captures_all_three_sentinels():
    """FT-016: end-to-end sentinel coverage — the rendered Pass-1 prompt includes
    all 3 head/middle/tail sentinels AND all 3 excerpt markers for the 60200-char
    synthetic fixture. Belt-and-suspenders variant of UT-043 with explicit marker
    bound assertions (chars 28100 to 32100 for middle; 56200 to 60200 for tail).
    """
    from core.domain_wizard import build_schema_discovery_prompt

    fixture_path = (
        PROJECT_ROOT
        / "tests"
        / "fixtures"
        / "wizard_sample_window"
        / "long_contract.txt"
    )
    fixture_text = fixture_path.read_text(encoding="utf-8")
    assert len(fixture_text) == 60200, (
        f"Fixture length must be exactly 60200 chars for stable marker bounds, "
        f"got {len(fixture_text)}"
    )

    prompt = build_schema_discovery_prompt(
        fixture_text, "Synthetic long contract domain for Phase 16 FT-016"
    )

    # Sentinels — exactly one occurrence each
    assert prompt.count("PARTY_SENTINEL_HEAD") == 1, (
        f"Expected exactly 1 head sentinel, got {prompt.count('PARTY_SENTINEL_HEAD')}"
    )
    assert prompt.count("OBLIGATION_SENTINEL_MIDDLE") == 1, (
        f"Expected exactly 1 middle sentinel, got {prompt.count('OBLIGATION_SENTINEL_MIDDLE')}"
    )
    assert prompt.count("TERMINATION_SENTINEL_TAIL") == 1, (
        f"Expected exactly 1 tail sentinel, got {prompt.count('TERMINATION_SENTINEL_TAIL')}"
    )

    # Markers — exact literals with computed bounds for 60200-char doc
    assert "[EXCERPT 1/3 — chars 0 to 4000 (head)]" in prompt
    assert "[EXCERPT 2/3 — chars 28100 to 32100 (middle)]" in prompt, (
        "Middle marker bounds must be 28100 to 32100 for a 60200-char doc"
    )
    assert "[EXCERPT 3/3 — chars 56200 to 60200 (tail)]" in prompt, (
        "Tail marker bounds must be 56200 to 60200 for a 60200-char doc"
    )

    # Long-doc headers and preface
    assert "**Document excerpts:**" in prompt
    assert "The following are three excerpts from a larger document." in prompt

    # Short-doc header must NOT leak
    assert "**Document text:**" not in prompt

    # Domain description interpolated
    assert "Synthetic long contract domain for Phase 16 FT-016" in prompt


_FT017_SHORT_DOC_STRUCTURAL_SUBSTRINGS = [
    "You are an expert knowledge graph schema designer.",
    "**Domain description:** Real estate lease agreements",
    "**Document text:**",
    "**Instructions:**",
    "Propose 5-15 entity types and 5-20 relation types.",
    "SCREAMING_SNAKE_CASE",
    "Output format (JSON):",
    "Return ONLY the JSON object, no commentary.",
]

_FT017_LONG_DOC_MARKER_SUBSTRINGS = [
    "[EXCERPT ",
    "three excerpts from a larger document",
    "**Document excerpts:**",
]


@pytest.mark.unit
def test_ft017_short_doc_prompt_is_strict_superset_of_pre_phase16():
    """FT-017: D-12 regression gate — for each Phase-8 wizard fixture (all ≤12K chars),
    the Phase 16 prompt is a strict superset of the pre-Phase-16 prompt shape:
    full doc_text preserved verbatim, all 8 structural substrings present, no long-doc
    markers leak in.
    """
    from core.domain_wizard import build_schema_discovery_prompt

    fixtures_dir = PROJECT_ROOT / "tests" / "fixtures" / "wizard"
    fixture_names = ["sample_lease_1.txt", "sample_lease_2.txt", "sample_lease_3.txt"]

    for name in fixture_names:
        fixture_path = fixtures_dir / name
        assert fixture_path.exists(), f"Missing Phase-8 wizard fixture: {fixture_path}"

        text = fixture_path.read_text(encoding="utf-8")
        assert len(text) <= 12000, (
            f"{name} must be ≤12000 chars to exercise the short-doc branch, got {len(text)}"
        )

        prompt = build_schema_discovery_prompt(text, "Real estate lease agreements")

        # Superset of content — full text appears verbatim
        assert text in prompt, (
            f"Full doc_text must appear verbatim in short-doc prompt for {name}"
        )

        # Every structural substring a pre-Phase-16 caller relied on is present
        for needle in _FT017_SHORT_DOC_STRUCTURAL_SUBSTRINGS:
            assert needle in prompt, (
                f"Phase-16 short-doc prompt for {name} missing pre-Phase-16 substring {needle!r}"
            )

        # No long-doc markers leak into the short-doc path
        for marker in _FT017_LONG_DOC_MARKER_SUBSTRINGS:
            assert marker not in prompt, (
                f"Long-doc marker {marker!r} leaked into short-doc prompt for {name}"
            )


# ========================================================================
# Phase 13 — FIDL-02c: write-time validation + provenance threading
# ========================================================================


@pytest.mark.unit
def test_normalize_coerces_schema_drift():
    """UT-022a: build_extraction._normalize_fields coerces drift.

    Parseable string confidence → float, unparseable string → 0.5 Pydantic default,
    type → entity_type, missing context/evidence/attributes filled.
    """
    from build_extraction import _normalize_fields

    entities = [
        {"name": "x", "type": "COMPOUND", "confidence": "0.9"},
        {"name": "y", "type": "GENE", "confidence": "not-a-number"},
    ]
    relations = [{"source_entity": "x", "target_entity": "y", "type": "INHIBITS"}]
    entities, relations = _normalize_fields(entities, relations)

    # Parseable string → float
    assert entities[0]["entity_type"] == "COMPOUND"
    assert "type" not in entities[0]
    assert entities[0]["confidence"] == 0.9
    assert entities[0]["context"] == ""
    assert entities[0]["attributes"] == {}

    # Unparseable string → 0.5 (Pydantic default, per RESEARCH.md §664)
    assert entities[1]["confidence"] == 0.5

    # Relation normalization
    assert relations[0]["relation_type"] == "INHIBITS"
    assert relations[0]["evidence"] == ""


@pytest.mark.unit
@pytest.mark.skipif(not HAS_SIFTKG, reason="sift-kg not installed")
def test_build_extraction_raises_on_missing_doc_id():
    """UT-024: DocumentExtraction Pydantic model rejects payloads missing document_id,
    and write_extraction wraps the failure into a ValueError on malformed records.

    Per RESEARCH.md: agents may construct dicts and pass them via `**record` expansion
    into write_extraction, in which case an omitted document_id slips past the Python-level
    signature and is caught only by Pydantic's DocumentExtraction validation — which this
    test exercises directly for unambiguous coverage.
    """
    from pydantic import ValidationError
    from sift_kg.extract.models import DocumentExtraction
    import build_extraction

    # Part A: The Pydantic model itself rejects a payload missing document_id
    with pytest.raises(ValidationError) as exc_info:
        DocumentExtraction(document_path="x.pdf", entities=[], relations=[])
    assert "document_id" in str(exc_info.value)

    # Part B: write_extraction wraps downstream Pydantic failures into ValueError.
    # Drive this with an entity missing entity_type (which _normalize_fields cannot
    # rescue because there is no 'type' alias) — the internal
    # DocumentExtraction(**extraction) call must fail and be re-raised as ValueError.
    with tempfile.TemporaryDirectory() as tmpdir:
        bad_entities = [{"name": "foo"}]  # missing entity_type, no 'type' alias
        with pytest.raises(ValueError, match="DocumentExtraction"):
            build_extraction.write_extraction("test_doc", tmpdir, bad_entities, [])


@pytest.mark.unit
@pytest.mark.skipif(not HAS_SIFTKG, reason="sift-kg not installed")
def test_build_extraction_raises_on_invalid_entity():
    """UT-025: write_extraction raises ValueError on entity missing both type and entity_type."""
    import build_extraction

    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(ValueError) as exc_info:
            build_extraction.write_extraction(
                "test_doc",
                tmpdir,
                entities=[{"name": "x"}],  # missing entity_type
                relations=[],
            )
        # Must mention the Pydantic model + the offending field
        assert "DocumentExtraction" in str(exc_info.value)
        assert "entity_type" in str(exc_info.value)


@pytest.mark.unit
@pytest.mark.skipif(not HAS_SIFTKG, reason="sift-kg not installed")
def test_build_extraction_threads_model_flag(tmp_path):
    """UT-026: --model flag threads into output JSON model_used field."""
    import subprocess

    script = PROJECT_ROOT / "core" / "build_extraction.py"
    payload = json.dumps(
        {
            "entities": [{"name": "x", "entity_type": "COMPOUND"}],
            "relations": [],
        }
    )
    result = subprocess.run(
        [
            "python3",
            str(script),
            "test_doc",
            str(tmp_path),
            "--model",
            "claude-sonnet-4-5",
            "--json",
            payload,
        ],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    out = json.loads((tmp_path / "extractions" / "test_doc.json").read_text())
    assert out["model_used"] == "claude-sonnet-4-5"


@pytest.mark.unit
@pytest.mark.skipif(not HAS_SIFTKG, reason="sift-kg not installed")
def test_build_extraction_reads_model_env(tmp_path):
    """UT-027: EPISTRACT_MODEL env var is used when --model is absent."""
    import subprocess, os as _os

    script = PROJECT_ROOT / "core" / "build_extraction.py"
    payload = json.dumps(
        {
            "entities": [{"name": "x", "entity_type": "COMPOUND"}],
            "relations": [],
        }
    )
    env = dict(_os.environ)
    env["EPISTRACT_MODEL"] = "claude-opus-4-7"
    result = subprocess.run(
        ["python3", str(script), "test_doc", str(tmp_path), "--json", payload],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(PROJECT_ROOT),
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    out = json.loads((tmp_path / "extractions" / "test_doc.json").read_text())
    assert out["model_used"] == "claude-opus-4-7"


@pytest.mark.unit
@pytest.mark.skipif(not HAS_SIFTKG, reason="sift-kg not installed")
def test_build_extraction_threads_cost_flag(tmp_path):
    """UT-028: --cost flag threads into output JSON cost_usd field (float via pytest.approx)."""
    import subprocess

    script = PROJECT_ROOT / "core" / "build_extraction.py"
    payload = json.dumps(
        {
            "entities": [{"name": "x", "entity_type": "COMPOUND"}],
            "relations": [],
        }
    )
    result = subprocess.run(
        [
            "python3",
            str(script),
            "test_doc",
            str(tmp_path),
            "--cost",
            "0.0123",
            "--json",
            payload,
        ],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    out = json.loads((tmp_path / "extractions" / "test_doc.json").read_text())
    # pytest.approx avoids direct float-equality fragility across round-trip JSON serialization
    assert out["cost_usd"] == pytest.approx(0.0123)


@pytest.mark.unit
@pytest.mark.skipif(not HAS_SIFTKG, reason="sift-kg not installed")
def test_build_extraction_no_hardcoded_model(tmp_path):
    """UT-029: model_used is empty (sift-kg default) — not fabricated — when no --model and no EPISTRACT_MODEL.

    On-disk contract: the file must be loadable via sift_kg.graph.builder without
    a prior normalize_extractions pass, so we write the sift-kg DocumentExtraction
    default (``""``) instead of ``null``. The meaningful assertion is the absence
    of any fabricated provenance string (e.g., ``claude-opus-4-6``).
    """
    import subprocess, os as _os

    script = PROJECT_ROOT / "core" / "build_extraction.py"
    payload = json.dumps(
        {
            "entities": [{"name": "x", "entity_type": "COMPOUND"}],
            "relations": [],
        }
    )
    env = {k: v for k, v in _os.environ.items() if k != "EPISTRACT_MODEL"}
    result = subprocess.run(
        ["python3", str(script), "test_doc", str(tmp_path), "--json", payload],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(PROJECT_ROOT),
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    out = json.loads((tmp_path / "extractions" / "test_doc.json").read_text())
    assert out["model_used"] == "", (
        f"Expected empty sift-kg default, got {out['model_used']!r}"
    )
    assert "claude-opus" not in (out["model_used"] or ""), (
        "No fabricated model name on disk"
    )


@pytest.mark.unit
@pytest.mark.skipif(not HAS_SIFTKG, reason="sift-kg not installed")
def test_build_extraction_no_hardcoded_cost(tmp_path):
    """UT-030: cost_usd is 0.0 (sift-kg default) — not fabricated — when no --cost flag provided.

    On-disk contract: the file must be loadable via sift_kg.graph.builder without
    a prior normalize_extractions pass, so we write the sift-kg DocumentExtraction
    default (``0.0``) instead of ``null``. The meaningful assertion is that the
    value is not a fabricated per-chunk cost estimate.
    """
    import subprocess

    script = PROJECT_ROOT / "core" / "build_extraction.py"
    payload = json.dumps(
        {
            "entities": [{"name": "x", "entity_type": "COMPOUND"}],
            "relations": [],
        }
    )
    result = subprocess.run(
        ["python3", str(script), "test_doc", str(tmp_path), "--json", payload],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    out = json.loads((tmp_path / "extractions" / "test_doc.json").read_text())
    assert out["cost_usd"] == 0.0, (
        f"Expected 0.0 sift-kg default, got {out['cost_usd']!r}"
    )


# ========================================================================
# Phase 13 — FIDL-02b: normalize_extractions module
# ========================================================================


def _write_extraction_file(
    path: Path, doc_id: str | None, n_entities: int = 1, n_relations: int = 0
) -> None:
    """Helper: write a valid extraction JSON at `path`. Omit doc_id by passing None."""
    body = {
        "document_path": "",
        "chunks_processed": 1,
        "entities": [
            {
                "name": f"e{i}",
                "entity_type": "COMPOUND",
                "attributes": {},
                "confidence": 0.9,
                "context": "",
            }
            for i in range(n_entities)
        ],
        "relations": [
            {
                "relation_type": "INHIBITS",
                "source_entity": "e0",
                "target_entity": f"e{i}",
                "confidence": 0.9,
                "evidence": "",
            }
            for i in range(n_relations)
        ],
        "cost_usd": None,
        "model_used": None,
        "domain_name": "drug-discovery",
        "chunk_size": 10000,
        "extracted_at": "2026-04-17T00:00:00+00:00",
        "error": None,
    }
    if doc_id is not None:
        body["document_id"] = doc_id
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body, indent=2))


@pytest.mark.unit
@pytest.mark.skipif(not HAS_SIFTKG, reason="sift-kg not installed")
def test_normalize_renames_variant_filenames(tmp_path):
    """UT-019: Variant filenames (_raw, _extraction_input, -extraction) renamed to <doc_id>.json."""
    from normalize_extractions import normalize_extractions

    ext = tmp_path / "extractions"
    _write_extraction_file(ext / "foo_raw.json", doc_id="foo")
    _write_extraction_file(ext / "bar_extraction_input.json", doc_id="bar")
    _write_extraction_file(ext / "baz-extraction.json", doc_id="baz")

    result = normalize_extractions(tmp_path)

    assert (ext / "foo.json").exists()
    assert (ext / "bar.json").exists()
    assert (ext / "baz.json").exists()
    assert not (ext / "foo_raw.json").exists()
    assert not (ext / "bar_extraction_input.json").exists()
    assert not (ext / "baz-extraction.json").exists()
    assert result["recovered"] == 3


@pytest.mark.unit
@pytest.mark.skipif(not HAS_SIFTKG, reason="sift-kg not installed")
def test_normalize_infers_document_id(tmp_path):
    """UT-020: Missing document_id inferred from filename stem."""
    from normalize_extractions import normalize_extractions

    ext = tmp_path / "extractions"
    _write_extraction_file(ext / "my_doc_42.json", doc_id=None)

    result = normalize_extractions(tmp_path)

    body = json.loads((ext / "my_doc_42.json").read_text())
    assert body["document_id"] == "my_doc_42"
    assert result["pass_rate"] == 1.0


@pytest.mark.unit
@pytest.mark.skipif(not HAS_SIFTKG, reason="sift-kg not installed")
def test_normalize_dedupes_keeps_richer(tmp_path):
    """UT-021: Same doc_id -> richer version wins, loser archived."""
    from normalize_extractions import normalize_extractions

    ext = tmp_path / "extractions"
    # Both have document_id="dupe"; differ on entity count
    _write_extraction_file(ext / "dupe_a.json", doc_id="dupe", n_entities=2)
    _write_extraction_file(ext / "dupe_b.json", doc_id="dupe", n_entities=8)

    result = normalize_extractions(tmp_path)

    # Survivor is the canonical <doc_id>.json with 8 entities
    survivor = ext / "dupe.json"
    assert survivor.exists()
    body = json.loads(survivor.read_text())
    assert len(body["entities"]) == 8

    # Loser archived
    archive = ext / "_dedupe_archive"
    assert archive.is_dir()
    archived_files = list(archive.glob("*.json"))
    assert len(archived_files) == 1


@pytest.mark.unit
@pytest.mark.skipif(not HAS_SIFTKG, reason="sift-kg not installed")
def test_normalize_coerces_schema_drift_via_module(tmp_path):
    """UT-022b: Module-level normalize delegates to _normalize_fields, coercing type->entity_type.

    Companion to UT-022a (test_normalize_coerces_schema_drift) in Plan 01, which exercises
    build_extraction._normalize_fields directly. This test verifies the delegation path
    through the normalize_extractions() entry-point and that the coerced record is written
    back to disk.
    """
    from normalize_extractions import normalize_extractions

    ext = tmp_path / "extractions"
    ext.mkdir(parents=True)
    drift = {
        "document_id": "drift",
        "document_path": "",
        "entities": [
            {"name": "x", "type": "COMPOUND", "confidence": "0.9"}
        ],  # schema drift
        "relations": [],
    }
    (ext / "drift.json").write_text(json.dumps(drift, indent=2))

    result = normalize_extractions(tmp_path)

    body = json.loads((ext / "drift.json").read_text())
    assert body["entities"][0]["entity_type"] == "COMPOUND"
    assert "type" not in body["entities"][0]
    assert isinstance(body["entities"][0]["confidence"], float)
    assert result["pass_rate"] == 1.0


@pytest.mark.unit
@pytest.mark.skipif(not HAS_SIFTKG, reason="sift-kg not installed")
def test_normalize_writes_report(tmp_path):
    """UT-023: _normalization_report.json is written with required keys."""
    from normalize_extractions import normalize_extractions

    ext = tmp_path / "extractions"
    _write_extraction_file(ext / "good.json", doc_id="good")

    result = normalize_extractions(tmp_path)

    report_path = ext / "_normalization_report.json"
    assert report_path.exists()
    report = json.loads(report_path.read_text())
    for key in (
        "total",
        "passed",
        "recovered",
        "unrecoverable",
        "pass_rate",
        "fail_threshold",
        "above_threshold",
        "actions",
    ):
        assert key in report, f"Missing key in report: {key}"
    assert report["total"] == 1
    assert 0.0 <= report["pass_rate"] <= 1.0


# ========================================================================
# Phase 13 — FIDL-02a: extractor.md contract
# ========================================================================


@pytest.mark.unit
def test_extractor_prompt_required_fields():
    """UT-017: agents/extractor.md declares document_id, entities, relations as REQUIRED; forbids direct Write."""
    prompt = (PROJECT_ROOT / "agents" / "extractor.md").read_text()

    assert "REQUIRED top-level fields" in prompt, (
        "Missing REQUIRED top-level fields block (FIDL-02a D-09)"
    )
    assert "document_id" in prompt, "Required field document_id not mentioned"
    assert "entities" in prompt, "Required field entities not mentioned"
    assert "relations" in prompt, "Required field relations not mentioned"
    assert "DO NOT fall back to the Write tool" in prompt, (
        "Missing Write-tool ban (FIDL-02a D-10)"
    )
    assert "build_extraction.py" in prompt, "Agent must invoke build_extraction.py"


@pytest.mark.unit
def test_extractor_prompt_stdin_fallback():
    """UT-018: agents/extractor.md documents stdin-pipe fallback AND corrected core/ path."""
    prompt = (PROJECT_ROOT / "agents" / "extractor.md").read_text()

    # Stdin fallback is documented
    assert "stdin pipe" in prompt.lower() or "echo '<" in prompt, (
        "Stdin fallback invocation not documented"
    )

    # Path bug fix: must reference core/, never scripts/
    assert "${CLAUDE_PLUGIN_ROOT}/core/build_extraction.py" in prompt, (
        "Missing corrected core/ path"
    )
    assert "/scripts/build_extraction.py" not in prompt, (
        "Obsolete scripts/ path still present — path bug regression"
    )

    # "report the failure" guidance so agents don't silently fall back to Write
    assert "report the failure" in prompt.lower(), (
        "Missing report-failure guidance (FIDL-02a D-10)"
    )


# ========================================================================
# UT-031..UT-035 + UT-033b: Phase 14 chunk overlap substrate (FIDL-03)
# ========================================================================


@pytest.mark.unit
def test_ut031_chonkie_imports():
    """UT-031: chonkie imports and SentenceChunker round-trips on a 3-sentence string."""
    from chonkie import SentenceChunker

    chunker = SentenceChunker(
        tokenizer="character",
        chunk_size=1000,
        chunk_overlap=150,
        min_sentences_per_chunk=1,
    )
    chunks = chunker.chunk(
        "Sentence one here. Sentence two follows. Sentence three trails."
    )
    assert len(chunks) >= 1, f"expected >=1 chunk, got {len(chunks)}"
    c0 = chunks[0]
    # Every Chunk must expose the four fields Plan 14-03 will consume
    for attr in ("text", "start_index", "end_index", "token_count"):
        assert hasattr(c0, attr), f"Chunk missing attribute {attr!r}"
    assert isinstance(c0.start_index, int) and c0.start_index >= 0
    assert isinstance(c0.end_index, int) and c0.end_index > c0.start_index


@pytest.mark.unit
def test_ut032_tail_returns_last_n_sentences():
    """UT-032: _tail_sentences returns exactly the last OVERLAP_SENTENCES sentences when they fit the cap."""
    from chunk_document import _tail_sentences, OVERLAP_MAX_CHARS

    sentences = [f"Sentence number {i} with some padding words." for i in range(10)]
    text = " ".join(sentences)
    tail = _tail_sentences(text)

    # Last 3 present
    assert "Sentence number 7" in tail, f"missing sentence 7 in tail: {tail!r}"
    assert "Sentence number 8" in tail, f"missing sentence 8 in tail: {tail!r}"
    assert "Sentence number 9" in tail, f"missing sentence 9 in tail: {tail!r}"
    # Earlier absent
    assert "Sentence number 6" not in tail, f"unexpected sentence 6 in tail: {tail!r}"
    assert "Sentence number 0" not in tail, f"unexpected sentence 0 in tail: {tail!r}"
    # Under cap
    assert len(tail) <= OVERLAP_MAX_CHARS, f"tail {len(tail)} > cap {OVERLAP_MAX_CHARS}"


@pytest.mark.unit
def test_ut033_tail_truncates_under_cap():
    """UT-033: when last-N sentences exceed cap, helper returns most-recent whole sentences under the cap."""
    from chunk_document import _tail_sentences, OVERLAP_MAX_CHARS

    big = "A" * 700
    text = f"First sentence: {big}. Second sentence: {big}. Third sentence: {big}."
    tail = _tail_sentences(text)

    assert len(tail) <= OVERLAP_MAX_CHARS, f"tail {len(tail)} > cap {OVERLAP_MAX_CHARS}"

    # Must start on a sentence boundary — locate tail in source and confirm
    # the preceding char is punctuation/whitespace (or tail is at index 0).
    if tail:
        idx = text.find(tail[:50])
        assert idx >= 0, f"tail not found in source: {tail[:50]!r}"
        if idx > 0:
            prev_char = text[idx - 1]
            assert prev_char in " \t\n", (
                f"tail does not start on sentence boundary — preceding char is {prev_char!r}"
            )


@pytest.mark.unit
def test_ut033b_partial_fit_three_sentences():
    """UT-033b (M-5): D-02 ∩ D-03 intersection — 2 of 3 last sentences fit under cap.

    Three sentences ~600 chars each: total ~1800 (over 1500 cap), but the
    last two total ~1200 (fit). Pins the right-to-left accumulation
    boundary: sentence 1 (oldest) dropped, 2 and 3 (most-recent) survive.
    """
    from chunk_document import _tail_sentences, OVERLAP_MAX_CHARS

    s1 = "FIRSTSENT " + ("a" * 590) + "."
    s2 = "SECONDSENT " + ("b" * 590) + "."
    s3 = "THIRDSENT " + ("c" * 590) + "."
    text = f"{s1} {s2} {s3}"
    tail = _tail_sentences(text)

    assert len(tail) <= OVERLAP_MAX_CHARS, f"tail {len(tail)} > cap {OVERLAP_MAX_CHARS}"
    assert "SECONDSENT" in tail, f"missing SECONDSENT: {tail[:200]!r}"
    assert "THIRDSENT" in tail, f"missing THIRDSENT: {tail[-200:]!r}"
    assert "FIRSTSENT" not in tail, (
        f"FIRSTSENT should be dropped (pushes total over cap): {tail[:200]!r}"
    )


@pytest.mark.unit
def test_ut034_tail_handles_edges():
    """UT-034: empty → empty; single short sentence → that sentence; single > cap → empty."""
    from chunk_document import _tail_sentences, OVERLAP_MAX_CHARS

    assert _tail_sentences("") == "", "empty input should return empty tail"

    result = _tail_sentences("Only one sentence here.")
    assert "Only one sentence here" in result, f"missing content in: {result!r}"

    huge = "X" * (OVERLAP_MAX_CHARS + 500) + "."
    assert _tail_sentences(huge) == "", (
        "single sentence larger than cap should return empty (refuse mid-sentence truncation)"
    )


@pytest.mark.unit
def test_ut035_missing_chonkie_raises_loud(monkeypatch):
    """UT-035 (B-3): importing chunk_document with chonkie absent raises ImportError with install hint.

    monkeypatch auto-restores sys.modules at teardown — safe under
    pytest-randomly / pytest-xdist.
    """
    import importlib
    import sys

    monkeypatch.setitem(sys.modules, "chonkie", None)
    monkeypatch.delitem(sys.modules, "chunk_document", raising=False)

    with pytest.raises(ImportError) as excinfo:
        importlib.import_module("chunk_document")
    msg = str(excinfo.value)
    assert "chonkie" in msg, f"ImportError message missing 'chonkie': {msg!r}"
    assert "uv pip install" in msg or "/epistract:setup" in msg, (
        f"ImportError missing install hint: {msg!r}"
    )


# ========================================================================
# UT-036, UT-036b, UT-037, UT-038: Phase 14 chunk overlap wiring (FIDL-03)
# ========================================================================


@pytest.mark.unit
def test_ut036_chunk_json_schema():
    """UT-036: every chunk has overlap_prev/next_chars, is_overlap_region, honest char_offset; (cont.) header on sub-chunks (D-12)."""
    from chunk_document import chunk_document

    # Multi-article oversized clause-aware case — forces sub-division inside
    # the first ARTICLE so (cont.) headers are emitted. Using varied sentence
    # content (not pure repetition) because chonkie 1.6.2 collapses repeated
    # identical sentences into a single chunk; multi-word repeated content
    # (23-char sentences * 1500 → 34.5K chars) splits cleanly.
    text = (
        "ARTICLE I. DEFINITIONS\n\n"
        + ("Sentence content here. " * 1500)
        + "\n\nARTICLE II. SCOPE\n\nShort body for article two."
    )
    chunks = chunk_document(text, "ut036_doc")

    assert len(chunks) >= 2, f"expected multi-chunk, got {len(chunks)}"

    for i, c in enumerate(chunks):
        for key in (
            "overlap_prev_chars",
            "overlap_next_chars",
            "is_overlap_region",
            "char_offset",
        ):
            assert key in c, f"chunk {i} missing key {key!r}: {list(c.keys())}"
        assert c["is_overlap_region"] is False
        assert isinstance(c["overlap_prev_chars"], int) and c["overlap_prev_chars"] >= 0
        assert isinstance(c["overlap_next_chars"], int) and c["overlap_next_chars"] >= 0
        assert isinstance(c["char_offset"], int) and c["char_offset"] >= 0

    # Boundary zeroes
    assert chunks[0]["overlap_prev_chars"] == 0
    assert chunks[-1]["overlap_next_chars"] == 0

    # Middle chunks have incoming overlap
    if len(chunks) >= 3:
        assert chunks[1]["overlap_prev_chars"] > 0, (
            f"middle chunk should have incoming overlap, got {chunks[1]['overlap_prev_chars']}"
        )

    # Honest per-sub-chunk offsets — strictly increasing (D-11)
    offsets = [c["char_offset"] for c in chunks]
    assert offsets == sorted(offsets), f"char_offsets not monotonic: {offsets}"
    assert len(set(offsets)) == len(offsets), (
        f"char_offsets not unique (D-11 violation): {offsets}"
    )

    # D-12: sub-chunks after the first of an oversized section get "(cont.)"
    assert any(c["section_header"].endswith("(cont.)") for c in chunks[1:]), (
        f"expected at least one (cont.) header in sub-chunks, got: "
        f"{[c['section_header'] for c in chunks]}"
    )


@pytest.mark.unit
def test_ut036b_honest_offset_across_whitespace_gaps():
    """UT-036b: char_offset stays honest across whitespace-only paragraph gaps.

    Chonkie operates on the buffered text as-is (including blank paragraphs),
    so start_index is honest automatically. For chunks emitted by _split_fixed
    (no clause structure), chonkie's Chunk.text IS the slice of source text
    starting at cc.start_index — including any overlap prefix chonkie copied
    from the previous chunk. So the honest-offset invariant is:

        source_text[char_offset : char_offset + 30] == chunk.text[:30]

    This pins that M-6 (blank-paragraph offset drift) is dissolved by chonkie
    — chonkie operates on the buffered text as-is, blank paragraphs stay
    in place, and start_index never drifts.
    """
    from chunk_document import chunk_document, MAX_CHUNK_SIZE

    paragraph = "Distinct paragraph content. It has three sentences. Each sentence is unique to this paragraph."
    separators = ["\n\n\n\n", "\n\n\n", "\n\n\n\n\n"]
    segments = [paragraph.replace("Distinct", f"Distinct{i}") for i in range(200)]
    text = ""
    for i, seg in enumerate(segments):
        text += seg
        if i < len(segments) - 1:
            text += separators[i % len(separators)]
    assert len(text) > MAX_CHUNK_SIZE, f"test text too short: {len(text)}"

    chunks = chunk_document(text, "ut036b_doc")
    assert len(chunks) >= 2

    # All fallback chunks: section_header == "" (proves _split_fixed path)
    for c in chunks:
        assert c["section_header"] == "", (
            f"expected fallback path (no headers), got: {c['section_header']!r}"
        )

    # Honest-offset invariant: chunk.text[:N] == source_text[char_offset:char_offset+N]
    # for each chunk, including blank-paragraph regions in the source.
    for i, c in enumerate(chunks):
        char_offset = c["char_offset"]
        body = c["text"]

        probe = body[:30]
        expected = text[char_offset : char_offset + 30]
        assert probe == expected, (
            f"chunk {i} offset drift: char_offset={char_offset}\n"
            f"chunk.text[:30]: {probe!r}\n"
            f"expected text[{char_offset}:{char_offset + 30}]: {expected!r}"
        )


@pytest.mark.unit
def test_ut037_overlap_at_article_boundary():
    """UT-037 (M-1/M-2): ARTICLE-boundary flush prepends previous article's RAW tail to the new article.

    Pins the invariant that cross-flush overlap is computed from the
    PREVIOUS flush's RAW body (via nonlocal _pending_tail + _tail_sentences),
    NOT from chunks[-1]["text"].
    """
    from chunk_document import chunk_document, _tail_sentences

    article_1_body = (
        "This is the first sentence of article one. "
        "This is the second sentence of article one. "
        "This is the third sentence of article one. "
        "This is a fourth trailing sentence."
    )
    article_1 = "ARTICLE I. PARTIES\n\n" + article_1_body
    article_2 = (
        "ARTICLE II. OBLIGATIONS\n\n"
        "The vendor shall deliver the widgets. "
        "Delivery is due by the end of month. "
        "Payment follows net thirty."
    )
    text = article_1 + "\n\n" + article_2
    chunks = chunk_document(text, "ut037_doc")

    assert len(chunks) >= 2, (
        f"expected 2+ chunks for 2 articles, got {len(chunks)}: "
        f"{[c['section_header'] for c in chunks]}"
    )

    a2_idx = next(
        (
            i
            for i, c in enumerate(chunks)
            if c["section_header"].upper().startswith("ARTICLE II")
        ),
        None,
    )
    assert a2_idx is not None, (
        f"could not find ARTICLE II chunk in {[c['section_header'] for c in chunks]}"
    )
    assert a2_idx >= 1, "ARTICLE II chunk should not be the first chunk"

    a2_chunk = chunks[a2_idx]

    # CRITICAL INVARIANT (M-1/M-2): expected tail is computed from the RAW
    # article-1 text (header + body as buffered before flush), NOT from
    # chunks[a2_idx - 1]["text"] which may carry its own overlap prefix.
    expected_tail = _tail_sentences(article_1)
    assert expected_tail, "expected non-empty tail from article 1"

    assert a2_chunk["overlap_prev_chars"] == len(expected_tail), (
        f"ARTICLE II overlap_prev_chars = {a2_chunk['overlap_prev_chars']}, "
        f"expected {len(expected_tail)} (raw tail of article 1). "
        f"A mismatch suggests the chunker read chunks[-1]['text'] instead "
        f"of using the nonlocal _pending_tail cache (M-1/M-2 regression)."
    )
    assert a2_chunk["text"].startswith(expected_tail), (
        f"ARTICLE II text does not start with expected RAW tail.\n"
        f"Tail: {expected_tail!r}\nHead of chunk: {a2_chunk['text'][:200]!r}"
    )


@pytest.mark.unit
def test_ut038_overlap_at_split_fixed_fallback():
    """UT-038: _split_fixed fallback path emits overlap on middle chunks (D-04 #3, D-05)."""
    from chunk_document import chunk_document, MAX_CHUNK_SIZE, OVERLAP_MAX_CHARS

    # No section headers anywhere — forces _split_fixed
    paragraphs = [
        f"Paragraph {i} body. This paragraph has distinct sentence content. "
        f"Every sentence is unique. Content continues for paragraph {i}."
        for i in range(400)
    ]
    text = "\n\n".join(paragraphs)
    assert len(text) > MAX_CHUNK_SIZE

    chunks = chunk_document(text, "ut038_doc")

    for c in chunks:
        assert c["section_header"] == "", (
            f"fallback should have empty section_header, got {c['section_header']!r}"
        )

    assert len(chunks) >= 2
    assert chunks[0]["overlap_prev_chars"] == 0
    assert chunks[-1]["overlap_next_chars"] == 0
    assert chunks[1]["overlap_prev_chars"] > 0, (
        "second chunk in fallback path should have overlap from first"
    )
    assert chunks[1]["overlap_prev_chars"] <= OVERLAP_MAX_CHARS


# ---------------------------------------------------------------------------
# FIDL-04 — Format Discovery Parity (Phase 15)
# ---------------------------------------------------------------------------
_FIDL04_TEXT_EXTENSIONS = [
    ".pdf",
    ".pptx",
    ".md",
    ".epub",
    ".rtf",
    ".odt",
    ".csv",
    ".xml",
    ".json",
    ".yaml",
    ".log",
    ".ipynb",
    ".bib",
    ".fb2",
    ".msg",
]


@pytest.mark.unit
@pytest.mark.skipif(not HAS_SIFTKG, reason="sift-kg not installed")
def test_discover_corpus_runtime_extension_set(tmp_path):
    """UT-039: discover_corpus delegates to sift-kg; returns 15 text-class
    files and skips .zip (D-05) and .png (D-04 default ocr=False)."""
    import ingest_documents
    from ingest_documents import discover_corpus

    # Reset the lazy cache so the test sees a pristine delegation path.
    ingest_documents._SUPPORTED_EXTENSIONS_CACHE = None

    for ext in _FIDL04_TEXT_EXTENSIONS:
        (tmp_path / f"foo{ext}").write_text("stub", encoding="utf-8")
    # Exclusions:
    (tmp_path / "foo.zip").write_bytes(b"PK\x03\x04stub")
    (tmp_path / "foo.png").write_bytes(b"\x89PNG\r\n\x1a\nstub")

    result = discover_corpus(tmp_path)
    suffixes = sorted(p.suffix.lower() for p in result)

    assert len(result) == len(_FIDL04_TEXT_EXTENSIONS), (
        f"Expected {len(_FIDL04_TEXT_EXTENSIONS)} files, got {len(result)}: {suffixes}"
    )
    assert ".zip" not in suffixes, "D-05: .zip must be excluded"
    assert ".png" not in suffixes, "D-04: images must be excluded without ocr=True"
    assert result == sorted(result), "discover_corpus must return sorted paths"

    # SUPPORTED_EXTENSIONS is materialized lazily via __getattr__ (D-03).
    exts = ingest_documents.SUPPORTED_EXTENSIONS
    assert len(exts) >= 28, (
        f"Runtime Kreuzberg extension set should be >=28 after D-05 filter, "
        f"got {len(exts)}: {sorted(exts)}"
    )
    for pin in (".pdf", ".pptx", ".md", ".epub"):
        assert pin in exts, f"{pin} missing from runtime SUPPORTED_EXTENSIONS"
    assert ".zip" not in exts, "D-05: .zip must not leak through __getattr__"
    assert ".png" not in exts, "D-04: images not in default SUPPORTED_EXTENSIONS"


@pytest.mark.unit
@pytest.mark.skipif(not HAS_SIFTKG, reason="sift-kg not installed")
def test_discover_corpus_ocr_gate_includes_images(tmp_path):
    """UT-040: Image extensions gated by ocr=True (D-04)."""
    import ingest_documents
    from ingest_documents import discover_corpus

    ingest_documents._SUPPORTED_EXTENSIONS_CACHE = None

    (tmp_path / "sample.pdf").write_text("stub", encoding="utf-8")
    (tmp_path / "sample.png").write_bytes(b"\x89PNG\r\n\x1a\nstub")
    (tmp_path / "sample.jpg").write_bytes(b"\xff\xd8\xff\xe0stub")

    default_result = discover_corpus(tmp_path)
    assert len(default_result) == 1, (
        f"Default (ocr=False) should return only the PDF, got "
        f"{[p.name for p in default_result]}"
    )
    assert default_result[0].suffix.lower() == ".pdf"

    ocr_result = discover_corpus(tmp_path, ocr=True)
    ocr_suffixes = sorted(p.suffix.lower() for p in ocr_result)
    assert ocr_suffixes == [".jpg", ".pdf", ".png"], (
        f"ocr=True should include images, got {ocr_suffixes}"
    )


@pytest.mark.unit
def test_discover_corpus_raises_when_sift_reader_missing(tmp_path):
    """UT-041: Missing sift-kg -> ImportError, not silent 9-extension fallback (D-02)."""
    import ingest_documents

    (tmp_path / "foo.pdf").write_text("stub", encoding="utf-8")

    # Also reset the cache so the patched flag actually drives behavior.
    ingest_documents._SUPPORTED_EXTENSIONS_CACHE = None

    with mock.patch.object(ingest_documents, "HAS_SIFT_READER", False):
        with pytest.raises(ImportError, match=r"sift.?kg|/epistract:setup"):
            ingest_documents.discover_corpus(tmp_path)
        with pytest.raises(ImportError, match=r"sift.?kg|/epistract:setup"):
            _ = ingest_documents.SUPPORTED_EXTENSIONS


# ---------------------------------------------------------------------------
# FIDL-06 — Domain Awareness in Consumers (Phase 17)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_cmd_build_writes_domain_metadata(tmp_path, monkeypatch):
    """UT-044: cmd_build persists metadata.domain into graph_data.json (D-01, D-02)."""
    import json as _json
    import sys as _sys

    # Ensure `run_sift` imports cleanly from the tests/conftest-configured sys.path.
    _sys.path.insert(0, str(PROJECT_ROOT))  # for examples.workbench and core.*
    import run_sift  # from core/ on sys.path (per conftest line 20)

    def _stub_import_sift(names):
        def stub_run_build(output_dir, domain):
            gp = Path(output_dir) / "graph_data.json"
            gp.parent.mkdir(parents=True, exist_ok=True)
            gp.write_text(
                _json.dumps(
                    {
                        "metadata": {
                            "created_at": "2026-04-21T00:00:00+00:00",
                            "updated_at": "2026-04-21T00:00:00+00:00",
                            "entity_count": 0,
                            "relation_count": 0,
                            "document_count": 0,
                            "entity_type_summary": {},
                            "sift_kg_version": "0.9.0-stub",
                        },
                        "nodes": [],
                        "links": [],
                    }
                )
            )

            class _Stub:
                entity_count = 0
                relation_count = 0

            return _Stub()

        def stub_load_domain(domain_path=None):
            return None

        table = {"run_build": stub_run_build, "load_domain": stub_load_domain}
        return tuple(table[n] for n in names)

    monkeypatch.setattr(run_sift, "_import_sift", _stub_import_sift)

    # Also stub the community-labeling import path so the try/except doesn't
    # crash when label_communities can't run against a zero-node graph.
    import core.label_communities as lc

    monkeypatch.setattr(lc, "label_communities", lambda _p: None)

    # Branch 1: explicit domain
    out1 = tmp_path / "out1"
    run_sift.cmd_build(str(out1), domain_name="contracts")
    graph1 = _json.loads((out1 / "graph_data.json").read_text(encoding="utf-8"))
    assert graph1["metadata"]["domain"] == "contracts"
    # D-02: all pre-existing metadata keys preserved
    for key in (
        "created_at",
        "updated_at",
        "entity_count",
        "relation_count",
        "document_count",
        "entity_type_summary",
        "sift_kg_version",
    ):
        assert key in graph1["metadata"], f"metadata key {key!r} was dropped"
    assert graph1["nodes"] == [] and graph1["links"] == []

    # Branch 2: domain_name=None → metadata.domain is JSON null (None in Python)
    out2 = tmp_path / "out2"
    run_sift.cmd_build(str(out2), domain_name=None)
    graph2 = _json.loads((out2 / "graph_data.json").read_text(encoding="utf-8"))
    assert graph2["metadata"]["domain"] is None, (
        "cmd_build(None) must write JSON null, not the string 'None'"
    )


@pytest.mark.unit
def test_resolve_domain_precedence(tmp_path, capsys):
    """UT-045: resolve_domain honors explicit > metadata > fallback (D-03, D-07, D-08, D-09, D-11)."""
    import json as _json
    import sys as _sys

    _sys.path.insert(0, str(PROJECT_ROOT))
    from examples.workbench.template_loader import resolve_domain

    def _write(path, metadata):
        path.mkdir(parents=True, exist_ok=True)
        (path / "graph_data.json").write_text(
            _json.dumps(
                {
                    "metadata": metadata,
                    "nodes": [],
                    "links": [],
                }
            )
        )

    # Branch 1: explicit wins over metadata (D-09)
    dir1 = tmp_path / "dir1"
    _write(dir1, {"domain": "contracts"})
    resolved, source = resolve_domain(dir1, "drug-discovery")
    assert (resolved, source) == ("drug-discovery", "explicit")

    # Branch 2: metadata happy path (D-03)
    resolved, source = resolve_domain(dir1, None)
    assert (resolved, source) == ("contracts", "metadata")

    # Branch 3: legacy graph — metadata dict present but no `domain` key (D-08)
    dir2 = tmp_path / "dir2"
    _write(dir2, {"created_at": "2026-04-21T00:00:00+00:00"})
    capsys.readouterr()  # clear any prior output
    resolved, source = resolve_domain(dir2, None)
    assert (resolved, source) == (None, "fallback")
    captured = capsys.readouterr()
    assert "graph_data.json" in captured.err
    assert "domain" in captured.err.lower()

    # Branch 4: graph_data.json missing entirely
    dir3 = tmp_path / "dir3"
    dir3.mkdir()
    resolved, source = resolve_domain(dir3, None)
    assert (resolved, source) == (None, "fallback")


@pytest.mark.unit
def test_build_system_prompt_loads_analysis_patterns(capsys, monkeypatch):
    """UT-046: build_system_prompt reads template['analysis_patterns'] and falls back with a warning (FIDL-06 D-06)."""
    import sys as _sys

    _sys.path.insert(0, str(PROJECT_ROOT))
    import examples.workbench.system_prompt as sp
    from examples.workbench.system_prompt import build_system_prompt

    class _StubData:
        def __init__(self, claims):
            self.graph_data = {"nodes": [], "edges": []}
            self.claims_layer = claims
            self.communities = {}

    xref_claims = {
        "cross_references": [
            {"entity": "Aramark", "appears_in": ["PCC", "Catering"]},
        ],
        "conflicts": [],
        "gaps": [],
        "risks": [],
    }

    # Branch 1: contracts template uses contracts heading
    contracts_template = {
        "persona": "stub persona",
        "analysis_patterns": {
            "cross_references_heading": "CROSS-CONTRACT REFERENCES",
            "appears_in_phrase": "appears in",
        },
    }
    prompt = build_system_prompt(_StubData(xref_claims), contracts_template)
    assert "### CROSS-CONTRACT REFERENCES (1 entities)" in prompt
    assert "Aramark appears in: PCC, Catering" in prompt

    # Branch 2: drug-discovery template uses drug-discovery heading
    dd_template = {
        "persona": "stub persona",
        "analysis_patterns": {
            "cross_references_heading": "CROSS-STUDY REFERENCES",
            "appears_in_phrase": "appears in",
        },
    }
    prompt = build_system_prompt(_StubData(xref_claims), dd_template)
    assert "### CROSS-STUDY REFERENCES (1 entities)" in prompt
    assert "### CROSS-CONTRACT REFERENCES" not in prompt

    # Branch 3: legacy template (no analysis_patterns) — fallback with warning
    monkeypatch.setattr(sp, "_warned_about_missing_analysis_patterns", False)
    capsys.readouterr()  # clear prior output
    legacy_template = {"persona": "stub persona"}  # no analysis_patterns key
    prompt = build_system_prompt(_StubData(xref_claims), legacy_template)
    assert "### CROSS-CONTRACT REFERENCES (1 entities)" in prompt, (
        "Fallback must use contracts-default heading per D-06"
    )
    captured = capsys.readouterr()
    assert "analysis_patterns" in captured.err, (
        f"D-06 visible warning expected on stderr, got: {captured.err!r}"
    )

    # Branch 4: no cross_references in claims → no heading regardless of template
    empty_claims = {"conflicts": [], "gaps": [], "risks": []}
    prompt = build_system_prompt(_StubData(empty_claims), legacy_template)
    assert "CROSS-CONTRACT REFERENCES" not in prompt
    assert "CROSS-STUDY REFERENCES" not in prompt


# ---------------------------------------------------------------------------
# FIDL-07 — Per-Domain Epistemic & Validator Extensibility (Phase 18)
# ---------------------------------------------------------------------------


def _build_synthetic_domain(tmp_root, domain_name, epistemic_src):
    """Build a minimal synthetic domain at tmp_root/domains/<domain_name>/.

    Writes domain.yaml (minimal valid schema) and epistemic.py with the
    provided source. Returns (domain_dir, module_path).
    """
    from pathlib import Path as _P

    domain_dir = _P(tmp_root) / "domains" / domain_name
    domain_dir.mkdir(parents=True, exist_ok=True)
    (domain_dir / "domain.yaml").write_text(
        "version: 1.0\n"
        f"name: {domain_name}\n"
        "entity_types:\n"
        "  - name: THING\n"
        "    description: test\n"
        "relation_types:\n"
        "  - name: RELATES_TO\n"
        "    description: test\n"
    )
    module_path = domain_dir / "epistemic.py"
    module_path.write_text(epistemic_src)
    return domain_dir, module_path


def _write_stub_graph(output_dir, domain_name):
    import json as _json
    from pathlib import Path as _P

    out = _P(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "graph_data.json").write_text(
        _json.dumps(
            {
                "metadata": {
                    "created_at": "2026-04-22T00:00:00+00:00",
                    "updated_at": "2026-04-22T00:00:00+00:00",
                    "entity_count": 0,
                    "relation_count": 0,
                    "document_count": 0,
                    "entity_type_summary": {},
                    "sift_kg_version": "0.9.0-stub",
                    "domain": domain_name,
                },
                "nodes": [],
                "links": [],
            }
        )
    )
    return out


def _load_synthetic_module(module_path, mod_name):
    import importlib.util as _il

    spec = _il.spec_from_file_location(mod_name, module_path)
    mod = _il.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.unit
def test_custom_rules_dispatch(tmp_path, monkeypatch):
    """UT-047: CUSTOM_RULES findings merge into claims_layer.super_domain.custom_findings (D-01, D-02, D-12)."""
    sys.path.insert(0, str(PROJECT_ROOT))
    import core.label_epistemic as le

    epistemic_src = (
        "CONTEXT_CAPTURE = {}\n"
        "\n"
        "def good_rule(nodes, links, context):\n"
        "    CONTEXT_CAPTURE.update(context)\n"
        "    return [{'rule_name': 'good_rule', 'type': 'demo', 'severity': 'INFO',\n"
        "             'description': 'hello', 'evidence': {}}]\n"
        "\n"
        "CUSTOM_RULES = [good_rule]\n"
        "\n"
        "def analyze_testdomain_epistemic(output_dir, graph_data):\n"
        "    return {\n"
        "        'metadata': {'domain': 'testdomain'},\n"
        "        'summary': {'total_relations': 0, 'epistemic_status_counts': {}},\n"
        "        'base_domain': {'asserted_relations': []},\n"
        "        'super_domain': {},\n"
        "    }\n"
    )
    _, module_path = _build_synthetic_domain(tmp_path, "testdomain", epistemic_src)
    out = _write_stub_graph(tmp_path / "out", "testdomain")
    mod = _load_synthetic_module(module_path, "domains.testdomain.epistemic")

    monkeypatch.setattr(le, "_load_domain_epistemic", lambda name: mod)

    le.analyze_epistemic(out, domain_name="testdomain")

    claims = json.loads((out / "claims_layer.json").read_text())
    cf = claims["super_domain"]["custom_findings"]
    assert "good_rule" in cf, f"custom_findings missing good_rule; got {list(cf)}"
    assert cf["good_rule"][0]["description"] == "hello"
    assert cf["good_rule"][0]["rule_name"] == "good_rule"

    # Context plumbing
    assert "output_dir" in mod.CONTEXT_CAPTURE
    assert "graph_data" in mod.CONTEXT_CAPTURE
    assert "domain_name" in mod.CONTEXT_CAPTURE
    assert mod.CONTEXT_CAPTURE["domain_name"] == "testdomain"


@pytest.mark.unit
def test_get_validation_dir_resolution():
    """UT-048: get_validation_dir + resolve_domain['validation_dir'] (D-03, D-13)."""
    sys.path.insert(0, str(PROJECT_ROOT))
    from core.domain_resolver import get_validation_dir, resolve_domain

    # Branch 1: drug-discovery has validation/run_validation.py (after Task 3 Sub-step D)
    dd = get_validation_dir("drug-discovery")
    assert dd is not None, "drug-discovery validation/ should be discovered"
    assert dd.name == "validation"
    assert (dd / "run_validation.py").exists(), (
        "Task 3 Sub-step D must create run_validation.py for UT-048 to pass GREEN"
    )

    # Branch 2: contracts has no validation/ dir
    assert get_validation_dir("contracts") is None

    # Branch 3: unknown domain
    assert get_validation_dir("nonexistent-domain-xyz") is None

    # Branch 4: resolve_domain exposes the key + preserves pre-existing keys
    info_dd = resolve_domain("drug-discovery")
    assert "validation_dir" in info_dd
    assert info_dd["validation_dir"] == str(dd)
    for key in ("name", "dir", "yaml_path", "skill_path", "schema"):
        assert key in info_dd, f"resolve_domain dropped pre-existing key {key!r}"

    info_c = resolve_domain("contracts")
    assert info_c["validation_dir"] is None
    for key in ("name", "dir", "yaml_path", "skill_path", "schema"):
        assert key in info_c


@pytest.mark.unit
def test_rule_failure_isolation(tmp_path, monkeypatch):
    """UT-050: one broken rule does not abort the phase; error recorded, others still run (D-02, D-09, D-15)."""
    sys.path.insert(0, str(PROJECT_ROOT))
    import core.label_epistemic as le

    epistemic_src = (
        "def good_rule_a(nodes, links, context):\n"
        "    return [{'rule_name': 'good_rule_a', 'description': 'a',\n"
        "             'type': 'demo', 'severity': 'INFO', 'evidence': {}}]\n"
        "\n"
        "def broken_rule(nodes, links, context):\n"
        "    raise ValueError('boom')\n"
        "\n"
        "def good_rule_b(nodes, links, context):\n"
        "    return [{'rule_name': 'good_rule_b', 'description': 'b',\n"
        "             'type': 'demo', 'severity': 'INFO', 'evidence': {}}]\n"
        "\n"
        "CUSTOM_RULES = [good_rule_a, broken_rule, good_rule_b]\n"
        "\n"
        "def analyze_testdomain_epistemic(output_dir, graph_data):\n"
        "    return {\n"
        "        'metadata': {'domain': 'testdomain'},\n"
        "        'summary': {'total_relations': 0, 'epistemic_status_counts': {}},\n"
        "        'base_domain': {'asserted_relations': []},\n"
        "        'super_domain': {},\n"
        "    }\n"
    )
    _, module_path = _build_synthetic_domain(tmp_path, "testdomain", epistemic_src)
    out = _write_stub_graph(tmp_path / "out", "testdomain")
    mod = _load_synthetic_module(module_path, "domains.testdomain.epistemic")

    monkeypatch.setattr(le, "_load_domain_epistemic", lambda name: mod)

    # Must not raise — the isolation guard is the whole point of UT-050.
    le.analyze_epistemic(out, domain_name="testdomain")

    claims = json.loads((out / "claims_layer.json").read_text())
    cf = claims["super_domain"]["custom_findings"]

    assert cf["good_rule_a"][0]["description"] == "a"
    assert cf["good_rule_b"][0]["description"] == "b"
    assert cf["broken_rule"][0]["status"] == "error"
    assert "boom" in cf["broken_rule"][0]["error"]
    assert cf["broken_rule"][0]["rule_name"] == "broken_rule"


# ===========================================================================
# Phase 18 Plan 18-02 — UT-049 structural doctype detection (FIDL-07 D-05/D-06)
# ===========================================================================


@pytest.mark.unit
def test_ut049_structural_doctype_detection():
    """UT-049: PDB prefix → structural doc_type; ≥0.9 structural → asserted override.

    Two-site convention sync (D-05): both drug-discovery and core modules
    must recognize the same PDB_PATTERN + apply the same ≥0.9 short-circuit
    in classify_epistemic_status. No shared import — each module carries
    its own copy kept in sync by convention.
    """
    import importlib.util as _il

    sys.path.insert(0, str(PROJECT_ROOT))

    # Dynamic-load drug-discovery epistemic (hyphenated package; not importable
    # via regular import). Mirrors core.label_epistemic._load_domain_epistemic.
    dd_path = PROJECT_ROOT / "domains" / "drug-discovery" / "epistemic.py"
    spec = _il.spec_from_file_location("dd_epistemic_ut049", dd_path)
    dd = _il.module_from_spec(spec)
    spec.loader.exec_module(dd)

    from core import label_epistemic as le

    for mod, name in [(dd, "drug-discovery"), (le, "core.label_epistemic")]:
        # (1) PDB underscore variant → structural
        assert mod.infer_doc_type("pdb_1abc") == "structural", (
            f"{name}: pdb_1abc should classify as structural"
        )
        # (2) PDB hyphen variant, case-insensitive
        assert mod.infer_doc_type("pdb-7xyz") == "structural", (
            f"{name}: pdb-7xyz (hyphen, case-insensitive) should classify as structural"
        )
        # (3) Regression guard: pmid_ still returns "paper"
        assert mod.infer_doc_type("pmid_12345") == "paper", (
            f"{name}: regression — pmid_* should still be paper"
        )
        # (4) Content signal detection
        assert (
            mod._detect_structural_content(
                "Crystal structure of KRAS resolved at 2.1 Å"
            )
            is True
        ), f"{name}: crystal structure + resolution content signal"
        # Regression guard: generic text should NOT trigger
        assert (
            mod._detect_structural_content("This paper studies protein folding")
            is False
        ), f"{name}: generic text should not be structural content"
        # (5) High-confidence structural beats hedging (D-06)
        assert (
            mod.classify_epistemic_status("hypothesized structure", 0.95, "structural")
            == "asserted"
        ), f"{name}: high-conf structural overrides hedging regex (D-06)"
        # (6) Low-confidence structural falls through to hedging
        assert (
            mod.classify_epistemic_status("suggests mechanism", 0.7, "structural")
            == "hypothesized"
        ), f"{name}: low-conf structural falls through to hedging detection"


# ---------------------------------------------------------------------------
# FIDL-08 — Wizard & CLI Ergonomics (Phase 19)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("Q&A Analysis (v2)", "q-a-analysis-v2"),
        ("  Hello World  ", "hello-world"),
        ("multi--dash", "multi-dash"),
        ("drug-discovery", "drug-discovery"),  # D-14 backward-compat invariant
        ("contracts", "contracts"),  # D-14 backward-compat invariant
        ("中文 Analysis", "analysis"),  # NFKD + ASCII-ignore strips non-Latin
    ],
)
def test_generate_slug_edge_cases(raw, expected):
    """UT-051: generate_slug produces safe directory names across edge cases.

    Covers D-15 lock table (Q&A, whitespace, double-dash, existing domains,
    non-ASCII). Both existing domains (drug-discovery, contracts) are
    byte-identical under the new helper — Phase 19 introduces no drift for
    already-clean slugs (D-14 backward-compat gate).
    """
    from core.domain_wizard import generate_slug

    result = generate_slug(raw)
    assert result == expected, (
        f"generate_slug({raw!r}) -> {result!r}, expected {expected!r}"
    )
    # Post-condition invariants (D-01 + D-03)
    assert result == result.strip("-"), f"slug has leading/trailing hyphen: {result!r}"
    assert "--" not in result, f"slug has double hyphen: {result!r}"
    assert all(c in "abcdefghijklmnopqrstuvwxyz0123456789-" for c in result), (
        f"slug has invalid char: {result!r}"
    )
    assert result != "", "slug is empty (should have raised)"


@pytest.mark.parametrize("raw", ["", "   ", "\t\n"])
def test_generate_slug_rejects_empty(raw):
    """UT-051 (cont.): generate_slug raises ValueError for empty/whitespace-only input."""
    from core.domain_wizard import generate_slug

    with pytest.raises(ValueError):
        generate_slug(raw)


def test_generate_workbench_template_shape():
    """UT-052: generate_workbench_template emits WorkbenchTemplate-valid YAML.

    Validates the Phase 17 Pydantic contract (D-16), deterministic palette
    rotation (alphabetical sort → modulo cycle), and required analysis_patterns
    + dashboard keys. Determinism gate: two calls with same inputs produce
    byte-identical output.
    """
    from core.domain_wizard import generate_workbench_template
    from examples.workbench.template_schema import WorkbenchTemplate

    entity_types = {
        "Foo": {"description": "x"},
        "Bar": {"description": "y"},
        "Baz": {"description": "z"},
    }

    emitted = generate_workbench_template("test-domain", entity_types)
    assert isinstance(emitted, str)

    parsed = yaml.safe_load(emitted)
    assert isinstance(parsed, dict)

    # (1) Phase 17 Pydantic contract — shape gate
    WorkbenchTemplate.model_validate(parsed)  # raises ValidationError on mismatch

    # (2) entity_colors cardinality
    assert set(parsed["entity_colors"].keys()) == {"Foo", "Bar", "Baz"}

    # (3) Deterministic palette rotation — alphabetical sort: Bar, Baz, Foo
    # First three DEFAULT_ENTITY_COLORS entries:
    assert parsed["entity_colors"]["Bar"] == "#97c2fc"
    assert parsed["entity_colors"]["Baz"] == "#ffa07a"
    assert parsed["entity_colors"]["Foo"] == "#90ee90"

    # (4) analysis_patterns required keys
    assert "cross_references_heading" in parsed["analysis_patterns"]
    assert "appears_in_phrase" in parsed["analysis_patterns"]

    # (5) dashboard shape
    assert isinstance(parsed["dashboard"], dict)
    assert "title" in parsed["dashboard"]
    assert "subtitle" in parsed["dashboard"]

    # (6) Determinism — second call byte-identical
    emitted_again = generate_workbench_template("test-domain", entity_types)
    assert emitted == emitted_again, "generate_workbench_template is not deterministic"


def test_resolve_domain_arg_path_shim(tmp_path, capsys):
    """UT-053: --domain shim accepts name, extracts from path, errors on outside paths.

    FIDL-08 D-07, D-08:
      - Bare name (no slash, no .yaml) → passthrough (filesystem never touched).
      - Path inside DOMAINS_DIR matching <DOMAINS_DIR>/<name>/domain.yaml → return <name>.
      - Path outside DOMAINS_DIR → stderr error + SystemExit(non-zero).
    """
    from core.run_sift import resolve_domain_arg
    from core.domain_resolver import DOMAINS_DIR

    # (a) bare name passthrough — no filesystem touch
    assert resolve_domain_arg("contracts") == "contracts"
    assert resolve_domain_arg("drug-discovery") == "drug-discovery"

    # (b) valid path → name extraction (uses real domains/ layout)
    contracts_yaml = DOMAINS_DIR / "contracts" / "domain.yaml"
    assert contracts_yaml.exists(), "test prerequisite: contracts domain must exist"
    assert resolve_domain_arg(str(contracts_yaml)) == "contracts"

    dd_yaml = DOMAINS_DIR / "drug-discovery" / "domain.yaml"
    assert dd_yaml.exists(), "test prerequisite: drug-discovery domain must exist"
    assert resolve_domain_arg(str(dd_yaml)) == "drug-discovery"

    # (c) outside-domains path → SystemExit with clear stderr message
    alien_dir = tmp_path / "alien"
    alien_dir.mkdir()
    alien_yaml = alien_dir / "domain.yaml"
    alien_yaml.write_text("# synthetic outside-domains/ file\n")

    with pytest.raises(SystemExit) as exc_info:
        resolve_domain_arg(str(alien_yaml))
    assert exc_info.value.code != 0, (
        f"expected non-zero exit, got {exc_info.value.code}"
    )

    captured = capsys.readouterr()
    assert "--domain expects a name registered under domains/" in captured.err, (
        f"error message missing expected text; stderr was: {captured.err!r}"
    )


def test_wizard_schema_bypass_skips_llm(tmp_path, monkeypatch):
    """UT-054: --schema bypass skips LLM discovery entirely.

    Monkeypatches litellm to fail on import. If the bypass accidentally
    takes the 3-pass LLM path, the import failure surfaces and the test
    fails. Also monkeypatches DOMAINS_DIR → tmp_path/domains so no
    permanent pollution of the real domains/ dir.

    FIDL-08 D-09, D-10, D-11, D-18.
    """
    # (a) block litellm import — any accidental LLM call path raises
    monkeypatch.setitem(sys.modules, "litellm", None)

    # (b) synthetic schema
    schema = {
        "entity_types": {
            "FOO": {"description": "test entity foo"},
            "BAR": {"description": "test entity bar"},
        },
        "relation_types": {
            "REL_A": {"description": "test relation a"},
        },
        "description": "UT-054 test schema",
        "system_context": "test",
        "extraction_guidelines": "test",
    }
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(json.dumps(schema, indent=2))

    # (c) redirect DOMAINS_DIR so the generated domain lands in tmp_path
    # (CRITICAL: prevents permanent ut054-test-domain pollution of real domains/)
    fake_domains = tmp_path / "domains"
    fake_domains.mkdir()
    monkeypatch.setattr("core.domain_wizard.DOMAINS_DIR", fake_domains)

    # (d) invoke wizard main() directly with synthetic argv
    from core.domain_wizard import main

    exit_code = main(
        [
            "--schema",
            str(schema_path),
            "--name",
            "ut054-test-domain",
        ]
    )

    # (e) bypass completed successfully
    assert exit_code == 0, f"expected exit 0, got {exit_code}"

    # (f) domain package written to tmp/domains/ut054-test-domain/
    domain_dir = fake_domains / "ut054-test-domain"
    assert (domain_dir / "domain.yaml").exists()
    assert (domain_dir / "SKILL.md").exists()
    assert (domain_dir / "epistemic.py").exists()
    assert (domain_dir / "workbench" / "template.yaml").exists()


def test_ut055_narrator_load_domain_persona():
    """UT-055: _load_domain_persona reads the persona from workbench template.yaml.

    Validates the single-source-of-truth contract: the same persona used by
    the workbench chat (reactive) is what the label_epistemic narrator reads
    (proactive). A drug-discovery persona is always present after Phase 21
    and must include the epistemic-status vocabulary ('asserted', 'prophetic').
    """
    from core.label_epistemic import _load_domain_persona

    persona = _load_domain_persona("drug-discovery")
    assert isinstance(persona, str) and persona
    # Epistemic vocabulary commitments — these must live in the persona so the
    # narrator knows to classify relations using this language.
    for token in ("asserted", "prophetic", "hypothesized", "contested"):
        assert token in persona.lower(), (
            f"drug-discovery persona must commit to epistemic status '{token}'"
        )

    # Missing domain → None (not raise)
    assert _load_domain_persona("this-domain-does-not-exist") is None

    # Unknown alias also → None
    assert _load_domain_persona("") is None
    assert _load_domain_persona(None) is None


def test_ut056_narrator_summarize_graph_shape():
    """UT-056: _summarize_graph_for_narrator produces markdown with all sections.

    The summary is the sole factual payload passed to the LLM. If a section is
    silently dropped the narrative will hallucinate — so each expected heading
    must appear when the corresponding data is present.
    """
    from core.label_epistemic import _summarize_graph_for_narrator

    graph_data = {
        "nodes": [
            {"entity_type": "COMPOUND", "name": "semaglutide"},
            {"entity_type": "DISEASE", "name": "obesity"},
        ],
        "links": [
            {
                "source_entity": "semaglutide",
                "target_entity": "obesity",
                "relation_type": "INDICATED_FOR",
                "epistemic_status": "prophetic",
                "source_documents": ["patent_01"],
                "evidence": "is expected to reduce weight in obese patients",
            },
            {
                "source_entity": "semaglutide",
                "target_entity": "obesity",
                "relation_type": "INDICATED_FOR",
                "epistemic_status": "hypothesized",
            },
        ],
    }
    claims_layer = {
        "summary": {
            "epistemic_status_counts": {"prophetic": 1, "hypothesized": 1},
        },
        "super_domain": {
            "contradictions": [{"source": "x", "target": "y"}],
            "hypotheses": [{"label": "H1", "members": [1, 2]}],
            "contested_claims": [
                {
                    "source_entity": "semaglutide",
                    "target_entity": "obesity",
                    "relation_type": "INDICATED_FOR",
                    "epistemic_status": "hypothesized",
                }
            ],
        },
    }
    summary = _summarize_graph_for_narrator(graph_data, claims_layer)

    # Structural gates — every non-empty section must produce a heading
    assert "## GRAPH SUMMARY" in summary
    assert "Entities: 2" in summary
    assert "Relations: 2" in summary
    assert "COMPOUND: 1" in summary
    assert "## EPISTEMIC STATUS COUNTS" in summary
    assert "## CONTRADICTIONS" in summary
    assert "## HYPOTHESIS GROUPS" in summary
    assert "## PROPHETIC CLAIMS" in summary
    assert "## CONTESTED CLAIMS" in summary
    # Verify the prophetic claim made it into the text
    assert "is expected to reduce weight" in summary


def test_ut057_narrator_non_blocking_on_missing_credentials(tmp_path, monkeypatch):
    """UT-057: narrator failure never blocks claims_layer.json.

    The narrator is ADDITIVE — if credentials are absent or the LLM call
    fails, `/epistract:epistemic` must still succeed and write the rule-based
    claims_layer.json. This is the core reliability contract.
    """
    from core import label_epistemic

    # Clear all LLM credentials so resolve_api_config returns None
    for var in (
        "AZURE_FOUNDRY_API_KEY",
        "ANTHROPIC_FOUNDRY_API_KEY",
        "ANTHROPIC_API_KEY",
        "OPENROUTER_API_KEY",
    ):
        monkeypatch.delenv(var, raising=False)

    # Minimal graph: one node, one asserted relation
    graph_data = {
        "metadata": {"domain": "drug-discovery"},
        "nodes": [{"id": "x", "name": "x", "entity_type": "COMPOUND"}],
        "links": [
            {
                "source": "x",
                "target": "x",
                "source_entity": "x",
                "target_entity": "x",
                "relation_type": "ACTIVATES",
                "evidence": "activates x",
                "confidence": 0.9,
            }
        ],
    }
    (tmp_path / "graph_data.json").write_text(json.dumps(graph_data))

    # Run with narrate=True — should SUCCEED despite missing credentials
    result = label_epistemic.analyze_epistemic(
        tmp_path,
        domain_name="drug-discovery",
        narrate=True,
    )

    # claims_layer.json must exist regardless of narrator outcome
    claims_path = tmp_path / "claims_layer.json"
    assert claims_path.exists(), "claims_layer.json must ship even when narrator fails"
    # No narrative file should have been created
    assert not (tmp_path / "epistemic_narrative.md").exists()
    # Returned claims layer is well-formed
    assert "summary" in result


# ========================================================================
# Phase 21: ClinicalTrials + PubChem Domain (CTDM-01..CTDM-06)
# Wave 0 stub tests — expected RED until Plans 21-01 and 21-02 land.
# ========================================================================

CLINICALTRIALS_DIR = PROJECT_ROOT / "domains" / "clinicaltrials"
CT_FIXTURES = FIXTURES_DIR / "clinicaltrials"


@pytest.mark.unit
@pytest.mark.skipif(not HAS_SIFTKG, reason="sift-kg not installed")
def test_ctdm01_clinicaltrials_domain_yaml():
    """CTDM-01: domain.yaml declares 12 entity types and 10 relation types."""
    from sift_kg import load_domain

    yaml_path = CLINICALTRIALS_DIR / "domain.yaml"
    assert yaml_path.exists(), f"Missing {yaml_path}"
    domain = load_domain(domain_path=yaml_path)
    assert len(domain.entity_types) == 12, (
        f"Expected 12 entity types, got {len(domain.entity_types)}"
    )
    assert len(domain.relation_types) == 10, (
        f"Expected 10 relation types, got {len(domain.relation_types)}"
    )


@pytest.mark.unit
def test_ctdm01_clinicaltrials_in_list_domains():
    """CTDM-01: domain is discovered by domain_resolver."""
    from core.domain_resolver import list_domains

    assert "clinicaltrials" in list_domains()


@pytest.mark.unit
def test_ctdm01_clinicaltrials_alias_resolves():
    """CTDM-01: 'clinicaltrial' (singular) alias resolves to clinicaltrials directory."""
    from core.domain_resolver import resolve_domain

    info = resolve_domain("clinicaltrial")
    assert info["name"] == "clinicaltrial"
    assert "clinicaltrials" in info["dir"]


@pytest.mark.unit
def test_ctdm02_clinicaltrials_skill_md():
    """CTDM-02: SKILL.md contains NCT ID directive and Phase classification guidance."""
    skill_path = CLINICALTRIALS_DIR / "SKILL.md"
    assert skill_path.exists(), f"Missing {skill_path}"
    text = skill_path.read_text()
    assert "NCT" in text, "SKILL.md must mention NCT ID capture"
    assert "Phase" in text, "SKILL.md must mention trial phase classification"


@pytest.mark.unit
def test_ctdm03_clinicaltrials_epistemic_module():
    """CTDM-03: dispatcher finds analyze_clinicaltrials_epistemic (exact name per Pitfall 1)."""
    from core.label_epistemic import _load_domain_epistemic

    mod = _load_domain_epistemic("clinicaltrials")
    assert mod is not None, "Failed to load clinicaltrials epistemic module"
    assert hasattr(mod, "analyze_clinicaltrials_epistemic"), (
        "Missing analyze_clinicaltrials_epistemic — dispatcher derives this from domain slug"
    )


@pytest.mark.unit
def test_ctdm03_clinicaltrials_epistemic_callable(tmp_path):
    """CTDM-03: analyze_clinicaltrials_epistemic returns the claims layer schema."""
    from core.label_epistemic import _load_domain_epistemic

    mod = _load_domain_epistemic("clinicaltrials")
    result = mod.analyze_clinicaltrials_epistemic(tmp_path, {"nodes": [], "links": []})
    assert isinstance(result, dict)
    for key in ("metadata", "summary", "base_domain", "super_domain"):
        assert key in result, f"claims layer missing '{key}'"


@pytest.mark.unit
def test_ctdm04_ctgov_enrich_mock():
    """CTDM-04: _fetch_ct_gov returns trial metadata from CT.gov v2 response."""
    sys.path.insert(0, str(CLINICALTRIALS_DIR))
    import importlib

    enrich = importlib.import_module("enrich")
    mock_body = json.loads((CT_FIXTURES / "mock_ctgov_NCT04303780.json").read_text())
    with patch.object(enrich.requests, "get") as m:
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = mock_body
        m.return_value = resp
        result = enrich._fetch_ct_gov("NCT04303780")
    assert result is not None
    assert result["ct_overall_status"] == "ACTIVE_NOT_RECRUITING"
    assert result["ct_enrollment"] == 345
    assert result["ct_phase"] == "PHASE3"


@pytest.mark.unit
def test_ctdm04_ctgov_404_returns_none():
    """CTDM-04: 404 response yields None, not exception."""
    sys.path.insert(0, str(CLINICALTRIALS_DIR))
    import importlib

    enrich = importlib.import_module("enrich")
    with patch.object(enrich.requests, "get") as m:
        resp = MagicMock()
        resp.status_code = 404
        m.return_value = resp
        assert enrich._fetch_ct_gov("NCT99999999") is None


@pytest.mark.unit
def test_ctdm05_pubchem_enrich_mock():
    """CTDM-05: _fetch_pubchem reads ConnectivitySMILES (Pitfall 2)."""
    sys.path.insert(0, str(CLINICALTRIALS_DIR))
    import importlib

    enrich = importlib.import_module("enrich")
    mock_body = json.loads((CT_FIXTURES / "mock_pubchem_remdesivir.json").read_text())
    with patch.object(enrich.requests, "get") as m:
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = mock_body
        m.return_value = resp
        result = enrich._fetch_pubchem("remdesivir")
    assert result is not None
    assert result["pubchem_cid"] == 121304016
    assert result["molecular_formula"] == "C27H35N6O8P"
    assert result["canonical_smiles"] and result["canonical_smiles"].startswith(
        "CCC"
    ), "canonical_smiles must be populated from ConnectivitySMILES response key"


@pytest.mark.unit
def test_ctdm05_pubchem_404_returns_none():
    """CTDM-05: PubChem 404 yields None without raising."""
    sys.path.insert(0, str(CLINICALTRIALS_DIR))
    import importlib

    enrich = importlib.import_module("enrich")
    with patch.object(enrich.requests, "get") as m:
        resp = MagicMock()
        resp.status_code = 404
        m.return_value = resp
        assert enrich._fetch_pubchem("unobtanium-xyz") is None


@pytest.mark.unit
def test_ctdm06_enrich_report_written(tmp_path):
    """CTDM-06: enrich_graph writes _enrichment_report.json in the output dir."""
    sys.path.insert(0, str(CLINICALTRIALS_DIR))
    import importlib

    enrich = importlib.import_module("enrich")
    # Minimal fake graph — one Trial node, one Compound node
    graph_data = {
        "nodes": [
            {"id": "trial:nct04303780", "name": "NCT04303780", "entity_type": "Trial"},
            {
                "id": "compound:remdesivir",
                "name": "remdesivir",
                "entity_type": "Compound",
            },
        ],
        "links": [],
    }
    (tmp_path / "graph_data.json").write_text(json.dumps(graph_data))
    with patch.object(enrich.requests, "get") as m:
        m.return_value = MagicMock(status_code=404)
        enrich.enrich_graph(tmp_path)
    report_path = tmp_path / "extractions" / "_enrichment_report.json"
    assert report_path.exists(), f"report not written at {report_path}"
    report = json.loads(report_path.read_text())
    assert "trials" in report and "compounds" in report
    assert report["domain"] == "clinicaltrials"


@pytest.mark.unit
def test_ctdm06_enrich_non_blocking():
    """CTDM-06: ConnectionError during enrichment does NOT raise — logged as failure count."""
    sys.path.insert(0, str(CLINICALTRIALS_DIR))
    import importlib
    import requests as _requests

    enrich = importlib.import_module("enrich")
    with patch.object(enrich.requests, "get") as m:
        m.side_effect = _requests.exceptions.ConnectionError("network down")
        # Must return None, not raise
        assert enrich._fetch_ct_gov("NCT04303780") is None
        assert enrich._fetch_pubchem("remdesivir") is None


# ---------------------------------------------------------------------------
# FDA-09: community_label_anchors — Task 1 tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_fda09_domain_yaml_has_anchors():
    """FDA-09 SC1: fda-product-labels domain.yaml contains community_label_anchors list."""
    import yaml
    from core.domain_resolver import DOMAINS_DIR

    yaml_path = DOMAINS_DIR / "fda-product-labels" / "domain.yaml"
    schema = yaml.safe_load(yaml_path.read_text())
    assert "community_label_anchors" in schema, (
        "community_label_anchors missing from domain.yaml"
    )
    anchors = schema["community_label_anchors"]
    assert anchors == [
        "DRUG_PRODUCT",
        "ACTIVE_INGREDIENT",
        "INDICATION",
        "MANUFACTURER",
    ]


@pytest.mark.unit
def test_fda09_anchor_types_exist_in_entity_types():
    """FDA-09: all anchor types must be defined entity_types in the schema."""
    import yaml
    from core.domain_resolver import DOMAINS_DIR

    yaml_path = DOMAINS_DIR / "fda-product-labels" / "domain.yaml"
    schema = yaml.safe_load(yaml_path.read_text())
    entity_type_names = set(schema.get("entity_types", {}).keys())
    for anchor in schema["community_label_anchors"]:
        assert anchor in entity_type_names, (
            f"Anchor {anchor!r} not found in entity_types"
        )


# ---------------------------------------------------------------------------
# FDA-09: _anchor_label() unit tests — Task 2
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_fda09_anchor_label_single_match():
    from core.label_communities import _anchor_label

    members = [{"name": "Fluconazole", "entity_type": "DRUG_PRODUCT"}]
    anchors = ["DRUG_PRODUCT", "ACTIVE_INGREDIENT", "INDICATION"]
    assert _anchor_label(members, anchors) == "Fluconazole"


@pytest.mark.unit
def test_fda09_anchor_label_two_matches_slash():
    from core.label_communities import _anchor_label

    members = [
        {"name": "Aspirin", "entity_type": "DRUG_PRODUCT"},
        {"name": "Ibuprofen", "entity_type": "DRUG_PRODUCT"},
    ]
    result = _anchor_label(members, ["DRUG_PRODUCT"])
    assert result == "Aspirin / Ibuprofen"


@pytest.mark.unit
def test_fda09_anchor_label_three_plus_more():
    from core.label_communities import _anchor_label

    members = [
        {"name": "Alpha", "entity_type": "DRUG_PRODUCT"},
        {"name": "Beta", "entity_type": "DRUG_PRODUCT"},
        {"name": "Gamma", "entity_type": "DRUG_PRODUCT"},
    ]
    result = _anchor_label(members, ["DRUG_PRODUCT"])
    assert result == "Alpha + 2 more"


@pytest.mark.unit
def test_fda09_anchor_label_truncation():
    from core.label_communities import _anchor_label

    long_name = "A" * 50  # 50 chars; _clean_name title-cases but 'A'*50 stays 50 'A's
    members = [{"name": long_name, "entity_type": "DRUG_PRODUCT"}]
    result = _anchor_label(members, ["DRUG_PRODUCT"])
    assert result is not None
    assert result.endswith("…"), f"Expected ellipsis suffix, got: {result!r}"
    assert len(result) == 41  # 40 chars + 1 ellipsis char


@pytest.mark.unit
def test_fda09_anchor_label_priority_fallback():
    """DRUG_PRODUCT absent; falls back to ACTIVE_INGREDIENT."""
    from core.label_communities import _anchor_label

    members = [{"name": "Fluoxetine", "entity_type": "ACTIVE_INGREDIENT"}]
    result = _anchor_label(members, ["DRUG_PRODUCT", "ACTIVE_INGREDIENT", "INDICATION"])
    assert result == "Fluoxetine"


@pytest.mark.unit
def test_fda09_anchor_label_no_match_returns_none():
    from core.label_communities import _anchor_label

    members = [
        {"name": "Some Mechanism", "entity_type": "MECHANISM_OF_ACTION"},
        {"name": "500mg Tablet Daily", "entity_type": "DOSAGE_REGIMEN"},
    ]
    result = _anchor_label(members, ["DRUG_PRODUCT", "ACTIVE_INGREDIENT", "INDICATION"])
    assert result is None


@pytest.mark.unit
def test_fda09_backward_compat_no_anchors(tmp_path, monkeypatch):
    """Domains without community_label_anchors must use _generate_label (no crash)."""
    import json
    import core.label_communities as lc

    monkeypatch.setattr(lc, "_load_domain_anchors", lambda gd: [])

    communities = {"gene:tp53": "community_0"}
    graph_data = {
        "metadata": {"domain": "drug-discovery"},
        "nodes": [{"id": "gene:tp53", "name": "TP53", "entity_type": "GENE"}],
    }
    (tmp_path / "communities.json").write_text(json.dumps(communities))
    (tmp_path / "graph_data.json").write_text(json.dumps(graph_data))

    result = lc.label_communities(tmp_path)
    assert isinstance(result, dict)
    assert len(result) == 1


@pytest.mark.unit
def test_fda09_backward_compat_missing_domain_metadata(tmp_path):
    """graph_data.json with no metadata.domain -> _generate_label fallback (no crash)."""
    import json
    import core.label_communities as lc

    communities = {"gene:brca1": "community_0"}
    graph_data = {
        "nodes": [{"id": "gene:brca1", "name": "BRCA1", "entity_type": "GENE"}],
    }
    (tmp_path / "communities.json").write_text(json.dumps(communities))
    (tmp_path / "graph_data.json").write_text(json.dumps(graph_data))

    result = lc.label_communities(tmp_path)
    assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# FDA-09: domain_wizard community_label_anchors emission — Task 3
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_fda09_wizard_generate_domain_yaml_with_anchors():
    """generate_domain_yaml with anchors emits community_label_anchors in YAML."""
    import yaml
    from core.domain_wizard import generate_domain_yaml

    result = generate_domain_yaml(
        domain_name="Test Domain",
        description="A test domain",
        system_context="Extract test entities",
        entity_types={"FOO": {"description": "Foo entity"}},
        relation_types={"HAS_FOO": {"description": "Has foo"}},
        community_label_anchors=["FOO"],
    )
    parsed = yaml.safe_load(result)
    assert "community_label_anchors" in parsed, "anchors missing from generated YAML"
    assert parsed["community_label_anchors"] == ["FOO"]


@pytest.mark.unit
def test_fda09_wizard_generate_domain_yaml_without_anchors():
    """generate_domain_yaml without anchors does NOT emit community_label_anchors (backward compat)."""
    import yaml
    from core.domain_wizard import generate_domain_yaml

    result = generate_domain_yaml(
        domain_name="Test Domain",
        description="A test domain",
        system_context="Extract test entities",
        entity_types={"FOO": {"description": "Foo entity"}},
        relation_types={"HAS_FOO": {"description": "Has foo"}},
    )
    parsed = yaml.safe_load(result)
    assert "community_label_anchors" not in parsed, (
        "community_label_anchors should be absent when not provided"
    )


# ========================================================================
# Phase 05: Workbench model selector (WB-MODEL-01)
# Wave 0 stub tests — RED until Plan 05-03 Tasks 2-3 land.
# ========================================================================

WORKBENCH_LLM_ENV_VARS = (
    "AZURE_FOUNDRY_API_KEY",
    "ANTHROPIC_FOUNDRY_API_KEY",
    "AZURE_FOUNDRY_BASE_URL",
    "ANTHROPIC_FOUNDRY_BASE_URL",
    "AZURE_FOUNDRY_RESOURCE",
    "AZURE_FOUNDRY_DEPLOYMENT",
    "ANTHROPIC_FOUNDRY_DEPLOYMENT",
    "ANTHROPIC_API_KEY",
    "OPENROUTER_API_KEY",
)


def _clear_llm_env(monkeypatch):
    """Remove every LLM-related env var so tests start from a clean slate."""
    for var in WORKBENCH_LLM_ENV_VARS:
        monkeypatch.delenv(var, raising=False)


@pytest.mark.unit
def test_chat_request_model_field(monkeypatch):
    """WB-MODEL-01: ChatRequest accepts optional `model` field; omission is backward-compatible."""
    _clear_llm_env(monkeypatch)
    from examples.workbench.api_chat import ChatRequest

    # Omission: model defaults to None
    req_no_model = ChatRequest(question="hello")
    assert req_no_model.model is None, (
        f"Expected model=None when omitted, got {req_no_model.model!r}"
    )

    # Explicit value: passes through unchanged
    req_with_model = ChatRequest(
        question="hello",
        model="claude-haiku-3-5-20241022",
    )
    assert req_with_model.model == "claude-haiku-3-5-20241022"

    # history field remains intact. Items are ChatMessage instances after the
    # SEC-03 / VUL-05 hardening (Literal["user","assistant"] role allowlist).
    req_with_history = ChatRequest(
        question="hello",
        history=[{"role": "user", "content": "prior"}],
        model="claude-opus-4-20250514",
    )
    assert [m.model_dump() for m in req_with_history.history] == [
        {"role": "user", "content": "prior"}
    ]
    assert req_with_history.model == "claude-opus-4-20250514"


@pytest.mark.unit
def test_resolve_api_config_model_override(monkeypatch):
    """WB-MODEL-01: _resolve_api_config(model_override=...) substitutes for Anthropic/OpenRouter; ignored by Foundry."""
    from examples.workbench.api_chat import _resolve_api_config

    # --- Case A: ANTHROPIC_API_KEY only ---
    _clear_llm_env(monkeypatch)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-anthropic")

    # No override → default model
    _, _, default_model, provider = _resolve_api_config()
    assert provider == "anthropic"
    assert default_model == "claude-sonnet-4-20250514"

    # Override non-empty → substituted
    _, _, overridden, _ = _resolve_api_config(model_override="claude-opus-4-20250514")
    assert overridden == "claude-opus-4-20250514"

    # Empty string → coerced to default
    _, _, empty_override, _ = _resolve_api_config(model_override="")
    assert empty_override == "claude-sonnet-4-20250514"

    # Whitespace-only → coerced to default
    _, _, ws_override, _ = _resolve_api_config(model_override="   ")
    assert ws_override == "claude-sonnet-4-20250514"

    # --- Case B: OPENROUTER_API_KEY only ---
    _clear_llm_env(monkeypatch)
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test-openrouter")

    _, _, or_default, or_provider = _resolve_api_config()
    assert or_provider == "openrouter"
    assert or_default == "anthropic/claude-sonnet-4"

    _, _, or_override, _ = _resolve_api_config(
        model_override="anthropic/claude-haiku-4"
    )
    assert or_override == "anthropic/claude-haiku-4"

    # --- Case C: Foundry (AZURE_FOUNDRY_API_KEY + AZURE_FOUNDRY_RESOURCE) ---
    # Override must be IGNORED — deployment name comes from env/default.
    _clear_llm_env(monkeypatch)
    monkeypatch.setenv("AZURE_FOUNDRY_API_KEY", "sk-test-foundry")
    monkeypatch.setenv("AZURE_FOUNDRY_RESOURCE", "test-resource")

    _, _, foundry_default, foundry_provider = _resolve_api_config()
    assert foundry_provider == "anthropic"  # Foundry uses native format
    assert foundry_default == "claude-sonnet-4-6"  # the compiled default

    # Override is silently ignored — still returns the env deployment
    _, _, foundry_ignored, _ = _resolve_api_config(
        model_override="anthropic/claude-haiku-4"
    )
    assert foundry_ignored == "claude-sonnet-4-6", (
        "Foundry must IGNORE model_override — deployment is determined by "
        "AZURE_FOUNDRY_DEPLOYMENT, not the request body"
    )


@pytest.mark.unit
def test_get_models_no_key(tmp_path, monkeypatch):
    """WB-MODEL-01: GET /api/models returns empty payload (not 500) when no API key is configured."""
    _clear_llm_env(monkeypatch)

    # Build a minimal graph_data.json so create_app() doesn't blow up
    (tmp_path / "graph_data.json").write_text(
        json.dumps({"nodes": [], "links": [], "metadata": {"domain": "contracts"}})
    )

    from examples.workbench.server import create_app
    from starlette.testclient import TestClient

    app = create_app(tmp_path, domain="contracts")
    client = TestClient(app)

    resp = client.get("/api/models")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data == {"provider": None, "default_model": None, "models": []}, (
        f"Expected empty payload when no API key set; got {data}"
    )


@pytest.mark.unit
def test_get_models_anthropic(tmp_path, monkeypatch):
    """WB-MODEL-01: GET /api/models returns curated Anthropic list when ANTHROPIC_API_KEY is set."""
    _clear_llm_env(monkeypatch)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-anthropic")

    (tmp_path / "graph_data.json").write_text(
        json.dumps({"nodes": [], "links": [], "metadata": {"domain": "contracts"}})
    )

    from examples.workbench.server import create_app
    from starlette.testclient import TestClient

    app = create_app(tmp_path, domain="contracts")
    client = TestClient(app)

    resp = client.get("/api/models")
    assert resp.status_code == 200
    data = resp.json()
    assert data["provider"] == "anthropic"
    assert data["default_model"] == "claude-sonnet-4-20250514"
    assert isinstance(data["models"], list)
    assert len(data["models"]) >= 3, (
        f"Expected >=3 Anthropic models, got {len(data['models'])}"
    )
    # Every entry must have id + label (both strings)
    for entry in data["models"]:
        assert "id" in entry and isinstance(entry["id"], str) and entry["id"]
        assert "label" in entry and isinstance(entry["label"], str) and entry["label"]
    # First entry is the default
    assert data["models"][0]["id"] == data["default_model"]


# ========================================================================
# Phase 05-04: Live OpenRouter model browser (WB-MODEL-01 extension)
# Wave 0 stub tests — RED until Plan 05-04 Task 2 lands.
# ========================================================================


@pytest.mark.unit
def test_filter_or_models_text_only():
    """05-04: _filter_and_group_or_models drops models where output_modalities != ['text']."""
    from examples.workbench.server import _filter_and_group_or_models

    raw = [
        {
            "id": "anthropic/claude-sonnet-4",
            "name": "Anthropic: Claude Sonnet 4",
            "architecture": {"output_modalities": ["text"]},
            "pricing": {"prompt": "0.000003", "completion": "0.000015"},
            "context_length": 200000,
            "expiration_date": None,
        },
        {
            "id": "openai/dall-e-3",
            "name": "OpenAI: DALL-E 3",
            "architecture": {"output_modalities": ["image"]},
            "pricing": {"prompt": "0.00004", "completion": "0.00004"},
            "context_length": 4096,
            "expiration_date": None,
        },
    ]
    result = _filter_and_group_or_models(raw)
    assert len(result) == 1, f"Expected 1 text-only model, got {len(result)}"
    assert result[0]["id"] == "anthropic/claude-sonnet-4", (
        f"Expected anthropic/claude-sonnet-4, got {result[0]['id']}"
    )


@pytest.mark.unit
def test_filter_or_models_excludes_routers():
    """05-04: _filter_and_group_or_models excludes openrouter/ prefix, negative pricing, and expired models."""
    from examples.workbench.server import _filter_and_group_or_models

    raw = [
        {
            "id": "anthropic/claude-haiku-4",
            "name": "Anthropic: Claude Haiku 4",
            "architecture": {"output_modalities": ["text"]},
            "pricing": {"prompt": "0.0000008", "completion": "0.000001"},
            "context_length": 200000,
            "expiration_date": None,
        },
        {
            "id": "openrouter/auto",
            "name": "OpenRouter: Auto",
            "architecture": {"output_modalities": ["text"]},
            "pricing": {"prompt": "0", "completion": "0"},
            "context_length": 200000,
            "expiration_date": None,
        },
        {
            "id": "some-provider/variable-model",
            "name": "Some Provider: Variable",
            "architecture": {"output_modalities": ["text"]},
            "pricing": {"prompt": "-1", "completion": "-1"},
            "context_length": 200000,
            "expiration_date": None,
        },
        {
            "id": "old-provider/expired-model",
            "name": "Old Provider: Expired",
            "architecture": {"output_modalities": ["text"]},
            "pricing": {"prompt": "0.000001", "completion": "0.000002"},
            "context_length": 8192,
            "expiration_date": "2000-01-01",
        },
    ]
    result = _filter_and_group_or_models(raw)
    ids = [m["id"] for m in result]
    assert "openrouter/auto" not in ids, "openrouter/ prefix must be excluded"
    assert "some-provider/variable-model" not in ids, (
        "negative pricing must be excluded"
    )
    assert "old-provider/expired-model" not in ids, "expired models must be excluded"
    assert "anthropic/claude-haiku-4" in ids, "valid model must be included"
    assert len(result) == 1, f"Expected 1 valid model, got {len(result)}: {ids}"


@pytest.mark.unit
def test_filter_or_models_grouping():
    """05-04: _filter_and_group_or_models assigns correct group labels including tilde-alias handling."""
    from examples.workbench.server import _filter_and_group_or_models

    def _make_model(model_id):
        return {
            "id": model_id,
            "name": f"Model: {model_id}",
            "architecture": {"output_modalities": ["text"]},
            "pricing": {"prompt": "0.000001", "completion": "0.000002"},
            "context_length": 8192,
            "expiration_date": None,
        }

    raw = [
        _make_model("anthropic/x"),
        _make_model("openai/x"),
        _make_model("meta-llama/x"),
        _make_model("~anthropic/y"),
        _make_model("some-unknown-vendor/x"),
    ]
    result = _filter_and_group_or_models(raw)
    group_map = {m["id"]: m["group"] for m in result}

    assert group_map["anthropic/x"] == "Claude (Anthropic)", (
        f"Expected 'Claude (Anthropic)', got {group_map['anthropic/x']!r}"
    )
    assert group_map["openai/x"] == "GPT / O-series (OpenAI)", (
        f"Expected 'GPT / O-series (OpenAI)', got {group_map['openai/x']!r}"
    )
    assert group_map["meta-llama/x"] == "Llama (Meta)", (
        f"Expected 'Llama (Meta)', got {group_map['meta-llama/x']!r}"
    )
    assert group_map["~anthropic/y"] == "Claude (Anthropic)", (
        "Tilde-alias '~anthropic/y' must resolve to 'Claude (Anthropic)' after stripping '~'"
    )
    assert group_map["some-unknown-vendor/x"] == "Other", (
        f"Expected 'Other' for unknown vendor, got {group_map['some-unknown-vendor/x']!r}"
    )


@pytest.mark.unit
def test_filter_or_models_label_format():
    """05-04: _filter_and_group_or_models formats labels with cost suffix and strips provider prefix."""
    from examples.workbench.server import _filter_and_group_or_models

    raw = [
        {
            "id": "anthropic/claude-sonnet-4",
            "name": "Anthropic: Claude Sonnet 4",
            "architecture": {"output_modalities": ["text"]},
            "pricing": {"prompt": "0.000003", "completion": "0.000015"},
            "context_length": 200000,
            "expiration_date": None,
        },
        {
            "id": "meta-llama/llama-3-8b",
            "name": "Meta: Llama 3 8B",
            "architecture": {"output_modalities": ["text"]},
            "pricing": {"prompt": "0", "completion": "0"},
            "context_length": 8192,
            "expiration_date": None,
        },
    ]
    result = _filter_and_group_or_models(raw)
    result_map = {m["id"]: m for m in result}

    paid = result_map["anthropic/claude-sonnet-4"]
    assert "($3.00/M)" in paid["label"], (
        f"Expected '($3.00/M)' in label, got {paid['label']!r}"
    )
    assert "Anthropic: " not in paid["label"], (
        f"'Anthropic: ' prefix must be stripped from label, got {paid['label']!r}"
    )
    assert paid["input_cost"] == 3.0, (
        f"Expected input_cost=3.0, got {paid['input_cost']}"
    )
    assert paid["free"] is False, f"Expected free=False, got {paid['free']}"

    free = result_map["meta-llama/llama-3-8b"]
    assert "(free)" in free["label"], (
        f"Expected '(free)' in label, got {free['label']!r}"
    )
    assert free["free"] is True, f"Expected free=True, got {free['free']}"


@pytest.mark.unit
def test_get_models_openrouter_live(tmp_path, monkeypatch):
    """05-04: GET /api/models with OPENROUTER_API_KEY fetches live list and returns grouped models."""
    import json as _json
    from unittest.mock import AsyncMock, MagicMock, patch

    import examples.workbench.server as srv

    _clear_llm_env(monkeypatch)
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-test-key")

    # Reset cache so the test always triggers a fresh fetch
    srv._or_models_cache["data"] = None
    srv._or_models_cache["fetched_at"] = 0.0

    (tmp_path / "graph_data.json").write_text(
        _json.dumps({"nodes": [], "links": [], "metadata": {"domain": "contracts"}})
    )

    # Synthetic OpenRouter API response: 2 text-output, 1 image-output
    mock_data = {
        "data": [
            {
                "id": "anthropic/claude-sonnet-4",
                "name": "Anthropic: Claude Sonnet 4",
                "architecture": {"output_modalities": ["text"]},
                "pricing": {"prompt": "0.000003", "completion": "0.000015"},
                "context_length": 200000,
                "expiration_date": None,
            },
            {
                "id": "meta-llama/llama-3-8b",
                "name": "Meta: Llama 3 8B",
                "architecture": {"output_modalities": ["text"]},
                "pricing": {"prompt": "0", "completion": "0"},
                "context_length": 8192,
                "expiration_date": None,
            },
            {
                "id": "openai/dall-e-3",
                "name": "OpenAI: DALL-E 3",
                "architecture": {"output_modalities": ["image"]},
                "pricing": {"prompt": "0.00004", "completion": "0.00004"},
                "context_length": 4096,
                "expiration_date": None,
            },
        ]
    }

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value=mock_data)

    async def mock_get_fn(url, *args, **kwargs):
        if "/endpoints" in str(url):
            healthy = MagicMock()
            healthy.raise_for_status = MagicMock()
            healthy.json = MagicMock(
                return_value={
                    "data": {
                        "endpoints": [{"uptime_last_5m": 99.9, "uptime_last_1d": 99.9}]
                    }
                }
            )
            return healthy
        return mock_response

    from examples.workbench.server import create_app
    from starlette.testclient import TestClient

    app = create_app(tmp_path, domain="contracts")
    client = TestClient(app)

    with patch("httpx.AsyncClient.get", new=AsyncMock(side_effect=mock_get_fn)):
        resp = client.get("/api/models")

    assert resp.status_code == 200
    data = resp.json()
    assert data["provider"] == "openrouter", (
        f"Expected provider=openrouter, got {data['provider']!r}"
    )
    assert len(data["models"]) == 2, (
        f"Expected 2 text-only models (image filtered out), got {len(data['models'])}"
    )
    for m in data["models"]:
        assert "group" in m, f"Every model must have 'group' field, missing in {m}"
        assert "input_cost" in m, (
            f"Every model must have 'input_cost' field, missing in {m}"
        )
    valid_ids = {m["id"] for m in data["models"]}
    assert (
        data["default_model"] in valid_ids
        or data["default_model"] == "anthropic/claude-sonnet-4"
    ), (
        f"default_model must be in models list or the fallback id; got {data['default_model']!r}"
    )


@pytest.mark.unit
def test_get_models_openrouter_fallback(tmp_path, monkeypatch):
    """05-04: GET /api/models falls back to PROVIDER_MODELS['openrouter'] when fetch fails."""
    import json as _json
    from unittest.mock import AsyncMock, patch

    import httpx

    import examples.workbench.server as srv
    from examples.workbench.api_chat import PROVIDER_MODELS

    _clear_llm_env(monkeypatch)
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-test-key")

    # Reset cache so the test always triggers a fresh fetch
    srv._or_models_cache["data"] = None
    srv._or_models_cache["fetched_at"] = 0.0

    (tmp_path / "graph_data.json").write_text(
        _json.dumps({"nodes": [], "links": [], "metadata": {"domain": "contracts"}})
    )

    async def mock_get_fn(*args, **kwargs):
        raise httpx.ConnectError("boom")

    from examples.workbench.server import create_app
    from starlette.testclient import TestClient

    app = create_app(tmp_path, domain="contracts")
    client = TestClient(app)

    with patch("httpx.AsyncClient.get", new=AsyncMock(side_effect=mock_get_fn)):
        resp = client.get("/api/models")

    assert resp.status_code == 200
    data = resp.json()
    assert data["provider"] == "openrouter", (
        f"Expected provider=openrouter even on fallback, got {data['provider']!r}"
    )
    assert data["models"] == PROVIDER_MODELS["openrouter"], (
        "On network failure, models must equal static PROVIDER_MODELS['openrouter'] fallback"
    )
    for m in data["models"]:
        assert "group" not in m, (
            f"Static fallback models must NOT have 'group' field, found in {m}"
        )


# ========================================================================
# Phase 05-05: OpenRouter model health filtering (WB-MODEL-02)
# ========================================================================


@pytest.mark.unit
def test_check_or_model_health_no_endpoints():
    """05-05: Empty endpoints array excludes both free and paid models."""
    import asyncio
    from unittest.mock import AsyncMock, MagicMock

    from examples.workbench.server import _check_or_model_health

    models = [
        {"id": "google/broken:free", "free": True, "label": "Broken (free)"},
        {"id": "anthropic/broken-paid", "free": False, "label": "Broken ($5/M)"},
    ]

    async def mock_get(url, **kwargs):
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        resp.json = MagicMock(return_value={"data": {"endpoints": []}})
        return resp

    client = MagicMock()
    client.get = AsyncMock(side_effect=mock_get)

    result = asyncio.run(_check_or_model_health(models, client))
    ids = [m["id"] for m in result]
    assert "google/broken:free" not in ids, (
        f"Free model with 0 endpoints must be excluded; got {ids}"
    )
    assert "anthropic/broken-paid" not in ids, (
        f"Paid model with 0 endpoints must be excluded; got {ids}"
    )


@pytest.mark.unit
def test_check_or_model_health_low_uptime():
    """05-05: Free model with uptime_last_5m < 70% is excluded (5m signal overrides 1d)."""
    import asyncio
    from unittest.mock import AsyncMock, MagicMock

    from examples.workbench.server import _check_or_model_health

    models = [
        {
            "id": "google/gemma-3-27b-it:free",
            "free": True,
            "label": "Gemma 3 27B (free)",
        },
    ]

    async def mock_get(url, **kwargs):
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        resp.json = MagicMock(
            return_value={
                "data": {
                    "endpoints": [{"uptime_last_5m": 37.8, "uptime_last_1d": 99.2}]
                }
            }
        )
        return resp

    client = MagicMock()
    client.get = AsyncMock(side_effect=mock_get)

    result = asyncio.run(_check_or_model_health(models, client))
    assert len(result) == 0, (
        f"Free model with uptime_5m=37.8 must be excluded; got {result}"
    )


@pytest.mark.unit
def test_check_or_model_health_null_5m_good_1d():
    """05-05: Free model with null uptime_5m but uptime_1d >= 80% is kept (low-traffic historical)."""
    import asyncio
    from unittest.mock import AsyncMock, MagicMock

    from examples.workbench.server import _check_or_model_health

    models = [
        {"id": "google/gemma-3-9b-it:free", "free": True, "label": "Gemma 3 9B (free)"},
    ]

    async def mock_get(url, **kwargs):
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        resp.json = MagicMock(
            return_value={
                "data": {
                    "endpoints": [{"uptime_last_5m": None, "uptime_last_1d": 99.9}]
                }
            }
        )
        return resp

    client = MagicMock()
    client.get = AsyncMock(side_effect=mock_get)

    result = asyncio.run(_check_or_model_health(models, client))
    ids = [m["id"] for m in result]
    assert "google/gemma-3-9b-it:free" in ids, (
        f"Free model with null 5m but 1d=99.9 must be kept; got {ids}"
    )


@pytest.mark.unit
def test_check_or_model_health_null_5m_bad_1d():
    """05-05: Free model with null uptime_5m and uptime_1d < 80% is excluded."""
    import asyncio
    from unittest.mock import AsyncMock, MagicMock

    from examples.workbench.server import _check_or_model_health

    models = [
        {"id": "google/gemma-2-9b-it:free", "free": True, "label": "Gemma 2 9B (free)"},
    ]

    async def mock_get(url, **kwargs):
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        resp.json = MagicMock(
            return_value={
                "data": {
                    "endpoints": [{"uptime_last_5m": None, "uptime_last_1d": 45.0}]
                }
            }
        )
        return resp

    client = MagicMock()
    client.get = AsyncMock(side_effect=mock_get)

    result = asyncio.run(_check_or_model_health(models, client))
    assert len(result) == 0, (
        f"Free model with null 5m and 1d=45.0 must be excluded; got {result}"
    )


@pytest.mark.unit
def test_check_or_model_health_network_error():
    """05-05: Network error during health check is fail-open — model is kept."""
    import asyncio
    from unittest.mock import AsyncMock, MagicMock

    from examples.workbench.server import _check_or_model_health

    models = [
        {
            "id": "google/gemma-3-27b-it:free",
            "free": True,
            "label": "Gemma 3 27B (free)",
        },
    ]

    async def mock_get(url, **kwargs):
        import httpx

        raise httpx.ConnectError("boom")

    client = MagicMock()
    client.get = AsyncMock(side_effect=mock_get)

    result = asyncio.run(_check_or_model_health(models, client))
    ids = [m["id"] for m in result]
    assert "google/gemma-3-27b-it:free" in ids, (
        f"Network error must be fail-open (model kept); got {ids}"
    )


@pytest.mark.unit
def test_check_or_model_health_paid_uptime_passthrough():
    """05-05: Paid model with very low uptime_5m is kept — uptime exclusion applies to free only."""
    import asyncio
    from unittest.mock import AsyncMock, MagicMock

    from examples.workbench.server import _check_or_model_health

    models = [
        {
            "id": "anthropic/claude-sonnet-4",
            "free": False,
            "label": "Claude Sonnet 4 ($3.00/M)",
        },
    ]

    async def mock_get(url, **kwargs):
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        resp.json = MagicMock(
            return_value={
                "data": {
                    "endpoints": [{"uptime_last_5m": 20.0, "uptime_last_1d": 55.0}]
                }
            }
        )
        return resp

    client = MagicMock()
    client.get = AsyncMock(side_effect=mock_get)

    result = asyncio.run(_check_or_model_health(models, client))
    ids = [m["id"] for m in result]
    assert "anthropic/claude-sonnet-4" in ids, (
        f"Paid model must NOT be excluded on uptime grounds; got {ids}"
    )


@pytest.mark.unit
def test_check_or_model_health_paid_no_endpoints():
    """05-05: Paid model with empty endpoints array IS excluded (no_endpoints applies to all)."""
    import asyncio
    from unittest.mock import AsyncMock, MagicMock

    from examples.workbench.server import _check_or_model_health

    models = [
        {
            "id": "~anthropic/claude-opus-latest",
            "free": False,
            "label": "Claude Opus Latest ($15.00/M)",
        },
    ]

    async def mock_get(url, **kwargs):
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        resp.json = MagicMock(return_value={"data": {"endpoints": []}})
        return resp

    client = MagicMock()
    client.get = AsyncMock(side_effect=mock_get)

    result = asyncio.run(_check_or_model_health(models, client))
    assert len(result) == 0, (
        f"Paid model with 0 endpoints must be excluded; got {result}"
    )


@pytest.mark.unit
def test_get_models_openrouter_health_filtered(tmp_path, monkeypatch):
    """05-05: GET /api/models filters out broken model (empty endpoints) via health check."""
    import json as _json
    from unittest.mock import AsyncMock, MagicMock, patch

    import examples.workbench.server as srv

    _clear_llm_env(monkeypatch)
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-test-key")

    # Reset cache so the test always triggers a fresh fetch
    srv._or_models_cache["data"] = None
    srv._or_models_cache["fetched_at"] = 0.0

    (tmp_path / "graph_data.json").write_text(
        _json.dumps({"nodes": [], "links": [], "metadata": {"domain": "contracts"}})
    )

    async def mock_get_fn(url, *args, **kwargs):
        url_s = str(url)
        if "/endpoints" in url_s:
            resp = MagicMock()
            resp.raise_for_status = MagicMock()
            if "google/broken:free" in url_s:
                resp.json = MagicMock(return_value={"data": {"endpoints": []}})
            else:
                resp.json = MagicMock(
                    return_value={
                        "data": {
                            "endpoints": [
                                {"uptime_last_5m": 99.9, "uptime_last_1d": 99.9}
                            ]
                        }
                    }
                )
            return resp
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        resp.json = MagicMock(
            return_value={
                "data": [
                    {
                        "id": "google/broken:free",
                        "name": "Google: Broken",
                        "architecture": {"output_modalities": ["text"]},
                        "pricing": {"prompt": "0", "completion": "0"},
                        "context_length": 8192,
                        "expiration_date": None,
                    },
                    {
                        "id": "keepme/healthy:free",
                        "name": "KeepMe: Healthy",
                        "architecture": {"output_modalities": ["text"]},
                        "pricing": {"prompt": "0", "completion": "0"},
                        "context_length": 8192,
                        "expiration_date": None,
                    },
                    {
                        "id": "anthropic/claude-sonnet-4",
                        "name": "Anthropic: Claude Sonnet 4",
                        "architecture": {"output_modalities": ["text"]},
                        "pricing": {"prompt": "0.000003", "completion": "0.000015"},
                        "context_length": 200000,
                        "expiration_date": None,
                    },
                ]
            }
        )
        return resp

    from examples.workbench.server import create_app
    from starlette.testclient import TestClient

    app = create_app(tmp_path, domain="contracts")
    client = TestClient(app)

    with patch("httpx.AsyncClient.get", new=AsyncMock(side_effect=mock_get_fn)):
        resp = client.get("/api/models")

    assert resp.status_code == 200
    data = resp.json()
    assert data["provider"] == "openrouter", (
        f"Expected provider=openrouter, got {data['provider']!r}"
    )
    model_ids = {m["id"] for m in data["models"]}
    assert len(data["models"]) == 2, (
        f"Expected 2 models after health filter (broken excluded); got {len(data['models'])}: {model_ids}"
    )
    assert "google/broken:free" not in model_ids, (
        f"Broken model (empty endpoints) must be excluded; got {model_ids}"
    )
    assert "keepme/healthy:free" in model_ids, (
        f"Healthy free model must be kept; got {model_ids}"
    )
    assert "anthropic/claude-sonnet-4" in model_ids, (
        f"Healthy paid model must be kept; got {model_ids}"
    )


# ========================================================================
# Phase 12: Domain List and Delete Commands (LIST-01, LIST-02, DEL-01–DEL-04)
# Wave 1 stub tests — RED until Plan 12-02 (manage_domains.py) lands.
# ========================================================================

import importlib
import subprocess as _subprocess


def _make_synthetic_domain(parent: Path, name: str) -> Path:
    """Create a minimal domain directory with domain.yaml for testing."""
    domain_dir = parent / name
    domain_dir.mkdir(parents=True, exist_ok=True)
    yaml_content = (
        "entity_types:\n"
        "  PERSON: {description: A person}\n"
        "  ORG: {description: An organization}\n"
        "relation_types:\n"
        "  WORKS_FOR: {description: Employment relation}\n"
    )
    (domain_dir / "domain.yaml").write_text(yaml_content)
    (domain_dir / "SKILL.md").write_text("# Skill\nExtract entities.")
    return domain_dir


@pytest.mark.unit
def test_manage_domains_list_active(tmp_path):
    """LIST-01: cmd_list() returns at least one row with status='active' for active domains."""
    import sys
    import json as _json
    import os as _os
    domains_dir = tmp_path / "domains"
    _make_synthetic_domain(domains_dir, "test-domain")

    manage_script = PROJECT_ROOT / "scripts" / "manage_domains.py"
    result = _subprocess.run(
        [sys.executable, str(manage_script), "list"],
        capture_output=True, text=True,
        env={**_os.environ, "EPISTRACT_DOMAINS_DIR": str(domains_dir)},
    )
    assert result.returncode == 0, f"list returned non-zero: {result.stderr}"
    rows = _json.loads(result.stdout)
    active_rows = [r for r in rows if r.get("status") == "active"]
    assert len(active_rows) >= 1, f"Expected at least one active row, got: {rows}"


@pytest.mark.unit
def test_manage_domains_row_fields(tmp_path):
    """LIST-02: Each row from cmd_list() contains all required fields."""
    import sys, json as _json, os as _os
    domains_dir = tmp_path / "domains"
    _make_synthetic_domain(domains_dir, "test-domain")

    manage_script = PROJECT_ROOT / "scripts" / "manage_domains.py"
    result = _subprocess.run(
        [sys.executable, str(manage_script), "list"],
        capture_output=True, text=True,
        env={**_os.environ, "EPISTRACT_DOMAINS_DIR": str(domains_dir)},
    )
    assert result.returncode == 0, f"list returned non-zero: {result.stderr}"
    rows = _json.loads(result.stdout)
    assert len(rows) >= 1, "Expected at least one domain row"
    row = rows[0]
    for field in ("name", "entity_types", "relation_types", "last_modified", "status", "file_count", "dir"):
        assert field in row, f"Row missing field '{field}': {row}"
    assert isinstance(row["entity_types"], int), "entity_types must be an int"
    assert isinstance(row["relation_types"], int), "relation_types must be an int"
    assert row["entity_types"] == 2, f"Expected 2 entity_types, got {row['entity_types']}"
    assert row["relation_types"] == 1, f"Expected 1 relation_type, got {row['relation_types']}"
    assert row["status"] == "active"


@pytest.mark.unit
def test_manage_domains_info_missing(tmp_path):
    """DEL-01: cmd_info for a nonexistent domain returns error JSON and exit code 1."""
    import sys, json as _json, os as _os
    domains_dir = tmp_path / "domains"
    domains_dir.mkdir()

    manage_script = PROJECT_ROOT / "scripts" / "manage_domains.py"
    result = _subprocess.run(
        [sys.executable, str(manage_script), "info", "nonexistent-domain"],
        capture_output=True, text=True,
        env={**_os.environ, "EPISTRACT_DOMAINS_DIR": str(domains_dir)},
    )
    assert result.returncode == 1, f"Expected exit 1 for missing domain, got {result.returncode}"
    data = _json.loads(result.stdout)
    assert "error" in data, f"Expected 'error' key in output: {data}"
    assert "nonexistent-domain" in data["error"], (
        f"Error message should name the missing domain: {data['error']}"
    )
    # No filesystem mutation: domains_dir is still empty (no subdirectories created)
    subdirs = [p for p in domains_dir.iterdir() if p.is_dir()]
    assert subdirs == [], f"No dirs should be created for missing domain lookup, got: {subdirs}"


@pytest.mark.unit
def test_manage_domains_info_fields(tmp_path):
    """DEL-03: cmd_info returns JSON with 'name' and 'file_count' keys."""
    import sys, json as _json, os as _os
    domains_dir = tmp_path / "domains"
    _make_synthetic_domain(domains_dir, "test-domain")

    manage_script = PROJECT_ROOT / "scripts" / "manage_domains.py"
    result = _subprocess.run(
        [sys.executable, str(manage_script), "info", "test-domain"],
        capture_output=True, text=True,
        env={**_os.environ, "EPISTRACT_DOMAINS_DIR": str(domains_dir)},
    )
    assert result.returncode == 0, f"info returned non-zero: {result.stderr}"
    data = _json.loads(result.stdout)
    assert "name" in data, f"Missing 'name' key: {data}"
    assert "file_count" in data, f"Missing 'file_count' key: {data}"
    assert data["name"] == "test-domain"
    assert isinstance(data["file_count"], int)
    assert data["file_count"] >= 2, (
        f"Expected at least 2 files (domain.yaml + SKILL.md), got {data['file_count']}"
    )


@pytest.mark.unit
def test_manage_domains_archive_moves(tmp_path):
    """DEL-02, DEL-04b: cmd_archive moves domain to _archived/<name>/ and returns success JSON."""
    import sys, json as _json, os as _os
    domains_dir = tmp_path / "domains"
    _make_synthetic_domain(domains_dir, "test-domain")

    manage_script = PROJECT_ROOT / "scripts" / "manage_domains.py"
    result = _subprocess.run(
        [sys.executable, str(manage_script), "archive", "test-domain"],
        capture_output=True, text=True,
        env={**_os.environ, "EPISTRACT_DOMAINS_DIR": str(domains_dir)},
    )
    assert result.returncode == 0, f"archive returned non-zero: {result.stderr}"
    data = _json.loads(result.stdout)
    assert "archived" in data, f"Expected 'archived' key in output: {data}"
    assert data["archived"] == "test-domain"

    # Source directory must no longer exist at active location
    assert not (domains_dir / "test-domain").exists(), "Source dir should be gone after archive"
    # Destination must exist at _archived/test-domain/
    archived_path = domains_dir / "_archived" / "test-domain"
    assert archived_path.is_dir(), f"Archived dir not found at {archived_path}"
    assert (archived_path / "domain.yaml").exists(), (
        "domain.yaml must be present in archived location"
    )


@pytest.mark.unit
def test_manage_domains_remove_active(tmp_path):
    """DEL-02: cmd_remove on an active domain permanently deletes it."""
    import sys, json as _json, os as _os
    domains_dir = tmp_path / "domains"
    _make_synthetic_domain(domains_dir, "test-domain")

    manage_script = PROJECT_ROOT / "scripts" / "manage_domains.py"
    result = _subprocess.run(
        [sys.executable, str(manage_script), "remove", "test-domain"],
        capture_output=True, text=True,
        env={**_os.environ, "EPISTRACT_DOMAINS_DIR": str(domains_dir)},
    )
    assert result.returncode == 0, f"remove returned non-zero: {result.stderr}"
    data = _json.loads(result.stdout)
    assert "removed" in data, f"Expected 'removed' key: {data}"
    assert data["removed"] == "test-domain"
    assert data["from"] == "active"
    assert not (domains_dir / "test-domain").exists(), "Domain dir must be gone after remove"


@pytest.mark.unit
def test_list_domains_excludes_archived(tmp_path, monkeypatch):
    """DEL-04a: list_domains() excludes directories starting with '_' (e.g. _archived/)."""
    from core import domain_resolver

    domains_dir = tmp_path / "domains"
    _make_synthetic_domain(domains_dir, "active-domain")
    # Create _archived dir with a valid domain inside — must be excluded from list_domains
    archived_inner = domains_dir / "_archived" / "old-domain"
    archived_inner.mkdir(parents=True)
    (archived_inner / "domain.yaml").write_text("entity_types: {}\nrelation_types: {}\n")

    monkeypatch.setattr(domain_resolver, "DOMAINS_DIR", domains_dir)
    result = domain_resolver.list_domains()
    assert "active-domain" in result, f"Active domain must appear: {result}"
    assert "_archived" not in result, f"_archived must be excluded from list_domains: {result}"
    assert "old-domain" not in result, (
        f"Archived subdomain must not appear in active list: {result}"
    )


@pytest.mark.unit
def test_manage_domains_list_archived(tmp_path):
    """DEL-04b: cmd_list() includes rows with status='archived' from domains/_archived/."""
    import sys, json as _json, os as _os
    domains_dir = tmp_path / "domains"
    _make_synthetic_domain(domains_dir, "active-domain")
    # Manually place an archived domain
    archived_dir = domains_dir / "_archived" / "old-domain"
    archived_dir.mkdir(parents=True)
    (archived_dir / "domain.yaml").write_text(
        "entity_types:\n  PERSON: {description: A person}\n"
        "relation_types:\n  KNOWS: {description: Relationship}\n"
    )

    manage_script = PROJECT_ROOT / "scripts" / "manage_domains.py"
    result = _subprocess.run(
        [sys.executable, str(manage_script), "list"],
        capture_output=True, text=True,
        env={**_os.environ, "EPISTRACT_DOMAINS_DIR": str(domains_dir)},
    )
    assert result.returncode == 0, f"list returned non-zero: {result.stderr}"
    rows = _json.loads(result.stdout)
    archived_rows = [r for r in rows if r.get("status") == "archived"]
    assert len(archived_rows) >= 1, f"Expected at least one archived row, got: {rows}"
    assert archived_rows[0]["name"] == "old-domain"
