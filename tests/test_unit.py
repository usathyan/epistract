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

from conftest import HAS_BIOPYTHON, HAS_RDKIT, HAS_SIFTKG, PROJECT_ROOT

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
    assert len(domain.entity_types) == 17, f"Expected 17 entity types, got {len(domain.entity_types)}"
    assert len(domain.relation_types) == 30, f"Expected 30 relation types, got {len(domain.relation_types)}"


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
        assert "not installed" in result.get("error", "").lower() or "rdkit" in result.get("error", "").lower()
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
        assert results_path.exists(), f"results.json not created. stderr: {result.stderr}"

        data = json.loads(results_path.read_text())
        total_matches = data["stats"]["total_matches"]
        assert total_matches > 0, f"Expected identifiers_found > 0, got stats: {data['stats']}"


# ---------------------------------------------------------------------------
# Epistemic dispatcher generalization tests (Phase 8)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_epistemic_dispatcher_generic_contract():
    """Verify dispatcher resolves 'contract' to analyze_contract_epistemic via convention."""
    from core.label_epistemic import _load_domain_epistemic

    mod = _load_domain_epistemic("contract")
    assert mod is not None, "Failed to load contract epistemic module"
    assert hasattr(mod, "analyze_contract_epistemic"), "Missing analyze_contract_epistemic function"


@pytest.mark.unit
def test_epistemic_dispatcher_generic_biomedical():
    """Verify dispatcher resolves 'drug-discovery' to analyze_biomedical_epistemic via convention."""
    from core.label_epistemic import _load_domain_epistemic

    mod = _load_domain_epistemic("drug-discovery")
    assert mod is not None, "Failed to load drug-discovery epistemic module"
    assert hasattr(mod, "analyze_biomedical_epistemic"), "Missing analyze_biomedical_epistemic function"


@pytest.mark.unit
def test_epistemic_dispatcher_alias_resolution():
    """Verify dispatcher handles aliases like 'biomedical' -> 'drug-discovery'."""
    from core.label_epistemic import _load_domain_epistemic

    mod = _load_domain_epistemic("biomedical")
    assert mod is not None, "Failed to load biomedical alias"
    assert hasattr(mod, "analyze_biomedical_epistemic"), "Alias didn't resolve to drug-discovery module"


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
    relation_types = {"LEASES_TO": {"description": "Landlord leases property to tenant"}}
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
                "test_doc", tmpdir,
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
    payload = json.dumps({
        "entities": [{"name": "x", "entity_type": "COMPOUND"}],
        "relations": [],
    })
    result = subprocess.run(
        ["python3", str(script), "test_doc", str(tmp_path),
         "--model", "claude-sonnet-4-5", "--json", payload],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT),
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
    payload = json.dumps({
        "entities": [{"name": "x", "entity_type": "COMPOUND"}],
        "relations": [],
    })
    env = dict(_os.environ)
    env["EPISTRACT_MODEL"] = "claude-opus-4-7"
    result = subprocess.run(
        ["python3", str(script), "test_doc", str(tmp_path), "--json", payload],
        capture_output=True, text=True, env=env, cwd=str(PROJECT_ROOT),
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
    payload = json.dumps({
        "entities": [{"name": "x", "entity_type": "COMPOUND"}],
        "relations": [],
    })
    result = subprocess.run(
        ["python3", str(script), "test_doc", str(tmp_path),
         "--cost", "0.0123", "--json", payload],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT),
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    out = json.loads((tmp_path / "extractions" / "test_doc.json").read_text())
    # pytest.approx avoids direct float-equality fragility across round-trip JSON serialization
    assert out["cost_usd"] == pytest.approx(0.0123)


@pytest.mark.unit
@pytest.mark.skipif(not HAS_SIFTKG, reason="sift-kg not installed")
def test_build_extraction_no_hardcoded_model(tmp_path):
    """UT-029: model_used defaults to null when no --model and no EPISTRACT_MODEL."""
    import subprocess, os as _os

    script = PROJECT_ROOT / "core" / "build_extraction.py"
    payload = json.dumps({
        "entities": [{"name": "x", "entity_type": "COMPOUND"}],
        "relations": [],
    })
    env = {k: v for k, v in _os.environ.items() if k != "EPISTRACT_MODEL"}
    result = subprocess.run(
        ["python3", str(script), "test_doc", str(tmp_path), "--json", payload],
        capture_output=True, text=True, env=env, cwd=str(PROJECT_ROOT),
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    out = json.loads((tmp_path / "extractions" / "test_doc.json").read_text())
    assert out["model_used"] is None, f"Expected null, got {out['model_used']!r}"


@pytest.mark.unit
@pytest.mark.skipif(not HAS_SIFTKG, reason="sift-kg not installed")
def test_build_extraction_no_hardcoded_cost(tmp_path):
    """UT-030: cost_usd defaults to null when no --cost flag provided."""
    import subprocess

    script = PROJECT_ROOT / "core" / "build_extraction.py"
    payload = json.dumps({
        "entities": [{"name": "x", "entity_type": "COMPOUND"}],
        "relations": [],
    })
    result = subprocess.run(
        ["python3", str(script), "test_doc", str(tmp_path), "--json", payload],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT),
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    out = json.loads((tmp_path / "extractions" / "test_doc.json").read_text())
    assert out["cost_usd"] is None, f"Expected null, got {out['cost_usd']!r}"
