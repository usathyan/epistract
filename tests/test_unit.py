#!/usr/bin/env python3
"""Unit tests for epistract plugin components.

Maps to TEST_REQUIREMENTS.md unit tests UT-001 through UT-014.
Run: python -m pytest tests/test_unit.py -v
"""
import json
import sys
import tempfile
from pathlib import Path
from unittest import mock

import pytest

# Add project paths for imports
PROJECT_ROOT = Path(__file__).parent.parent
VALIDATION_SCRIPTS = PROJECT_ROOT / "skills" / "drug-discovery-extraction" / "validation-scripts"
SCRIPTS = PROJECT_ROOT / "scripts"
DOMAIN_YAML = PROJECT_ROOT / "skills" / "drug-discovery-extraction" / "domain.yaml"
sys.path.insert(0, str(VALIDATION_SCRIPTS))
sys.path.insert(0, str(SCRIPTS))

# ---------------------------------------------------------------------------
# Availability flags
# ---------------------------------------------------------------------------
try:
    from sift_kg import load_domain
    HAS_SIFTKG = True
except ImportError:
    HAS_SIFTKG = False

try:
    from rdkit import Chem  # noqa: F401
    HAS_RDKIT = True
except ImportError:
    HAS_RDKIT = False

try:
    from Bio.Seq import Seq  # noqa: F401
    HAS_BIOPYTHON = True
except ImportError:
    HAS_BIOPYTHON = False

# ---------------------------------------------------------------------------
# Always-available imports from the project itself
# ---------------------------------------------------------------------------
from scan_patterns import scan_text
from validate_sequences import detect_type
from build_extraction import write_extraction

# Conditional imports
if HAS_RDKIT:
    from validate_smiles import validate_smiles
if HAS_BIOPYTHON:
    from validate_sequences import validate_sequence


# ========================================================================
# UT-001: Domain YAML Loads Successfully
# ========================================================================
@pytest.mark.skipif(not HAS_SIFTKG, reason="sift-kg not installed")
def test_ut001_domain_loads():
    """Load domain.yaml via sift-kg DomainLoader, assert 17 entity types and 30 relation types."""
    domain = load_domain(domain_path=DOMAIN_YAML)
    assert len(domain.entity_types) == 17, f"Expected 17 entity types, got {len(domain.entity_types)}"
    assert len(domain.relation_types) == 30, f"Expected 30 relation types, got {len(domain.relation_types)}"


# ========================================================================
# UT-002: Pattern Scanner Detects SMILES
# ========================================================================
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
@pytest.mark.skipif(not HAS_RDKIT, reason="RDKit not installed")
def test_ut007_validate_smiles_invalid():
    """validate_smiles with invalid string returns valid=False."""
    result = validate_smiles("not_a_smiles")
    assert result["valid"] is False
    assert "error" in result


# ========================================================================
# UT-008: SMILES Validator Graceful Without RDKit
# ========================================================================
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
def test_ut011_detect_type():
    """detect_type correctly identifies DNA, RNA, and protein sequences."""
    assert detect_type("ATCGATCG") == "DNA"
    assert detect_type("AUGCUAGC") == "RNA"
    assert detect_type("MTEYKLVVV") == "protein"


# ========================================================================
# UT-012: Extraction Adapter Writes Valid JSON
# ========================================================================
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
        cmd_build(tmpdir, domain_path=str(DOMAIN_YAML))

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
            [sys.executable, str(SCRIPTS / "validate_molecules.py"), tmpdir],
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
# Phase 3: Entity Extraction & Graph Construction (UT-030+)
# ---------------------------------------------------------------------------

FIXTURES = PROJECT_ROOT / "tests" / "fixtures"
CONTRACT_TEXT_FIXTURE = FIXTURES / "sample_contract_text.txt"
UNSTRUCTURED_TEXT_FIXTURE = FIXTURES / "sample_contract_unstructured.txt"


def test_ut030_chunk_document_clause_split():
    """Clause-aware chunking splits structured contract at Article/Section boundaries."""
    from chunk_document import chunk_document

    text = CONTRACT_TEXT_FIXTURE.read_text()
    chunks = chunk_document(text, "test_contract")
    # Must produce multiple chunks (at least 3 for 3 articles)
    assert len(chunks) >= 3, f"Expected >= 3 chunks, got {len(chunks)}"
    # Each chunk has required keys
    for c in chunks:
        assert "chunk_id" in c, "Missing chunk_id"
        assert "text" in c, "Missing text"
        assert "section_header" in c, "Missing section_header"
        assert "char_offset" in c, "Missing char_offset"
    # At least one chunk mentions ARTICLE
    headers = [c["section_header"] for c in chunks]
    assert any("ARTICLE" in h.upper() for h in headers if h), f"No ARTICLE header found in {headers}"


def test_ut031_chunk_document_fallback():
    """Unstructured text falls back to fixed-size paragraph-based chunks."""
    from chunk_document import chunk_document

    text = UNSTRUCTURED_TEXT_FIXTURE.read_text()
    chunks = chunk_document(text, "test_unstructured")
    # Short text produces 1 chunk (below max size)
    assert len(chunks) >= 1, "Expected at least 1 chunk"
    for c in chunks:
        assert "chunk_id" in c
        assert "text" in c
        assert len(c["text"]) <= 11000, "Chunk exceeds max size"


def test_ut032_chunk_document_writes_files(tmp_path):
    """CLI mode writes chunk files to ingested/<doc_id>_chunks/ directory."""
    from chunk_document import chunk_document_to_files

    text = CONTRACT_TEXT_FIXTURE.read_text()
    ingested_dir = tmp_path / "ingested"
    ingested_dir.mkdir()
    (ingested_dir / "test_contract.txt").write_text(text)
    chunk_dir = chunk_document_to_files("test_contract", tmp_path)
    assert chunk_dir.exists(), f"Chunk dir {chunk_dir} does not exist"
    chunk_files = list(chunk_dir.glob("*.json"))
    assert len(chunk_files) >= 3, f"Expected >= 3 chunk files, got {len(chunk_files)}"
    # Each file is valid JSON with expected structure
    for f in chunk_files:
        data = json.loads(f.read_text())
        assert "chunk_id" in data
        assert "text" in data


def test_ut033_legal_suffix_stripping():
    """Legal suffix normalization strips LLC, Inc, etc."""
    from entity_resolution import normalize_party_name

    assert normalize_party_name("Aramark Sports & Entertainment Services, LLC") == "Aramark Sports & Entertainment Services"
    assert normalize_party_name("PSAV Presentation Services, Inc.") == "PSAV Presentation Services"
    assert normalize_party_name("Freeman Decorating Co.") == "Freeman Decorating"
    # Should NOT strip "Authority" from proper names
    assert "Authority" in normalize_party_name("Pennsylvania Convention Center Authority")


def test_ut034_alias_resolution():
    """Defined-term alias extraction from contract text."""
    from entity_resolution import extract_defined_aliases

    text = 'Aramark Sports & Entertainment Services, LLC (hereinafter referred to as "Caterer")'
    aliases = extract_defined_aliases(text)
    assert "Caterer" in aliases, f"Expected 'Caterer' in {aliases}"


def test_ut035_merge_chunk_extractions():
    """Chunk-level extractions merge with within-document dedup."""
    from entity_resolution import merge_chunk_extractions

    chunk1 = {
        "entities": [
            {"name": "Aramark", "entity_type": "PARTY", "confidence": 0.9},
            {"name": "Hall A", "entity_type": "VENUE", "confidence": 0.8},
        ],
        "relations": [{"source_entity": "Aramark", "target_entity": "Hall A", "relation_type": "PROVIDES", "confidence": 0.85}],
    }
    chunk2 = {
        "entities": [
            {"name": "Aramark", "entity_type": "PARTY", "confidence": 0.95},  # duplicate, higher confidence
            {"name": "$5000 cancellation fee", "entity_type": "COST", "confidence": 0.9},
        ],
        "relations": [],
    }
    merged = merge_chunk_extractions([chunk1, chunk2], "test_doc")
    # Dedup: Aramark appears once, confidence updated to max
    party_entities = [e for e in merged["entities"] if e["name"] == "Aramark"]
    assert len(party_entities) == 1, f"Expected 1 Aramark, got {len(party_entities)}"
    assert party_entities[0]["confidence"] == 0.95, "Confidence should be max"
    # Total unique entities: 3 (Aramark, Hall A, $5000 fee)
    assert len(merged["entities"]) == 3
    # Relations preserved
    assert len(merged["relations"]) == 1
    assert merged["chunks_processed"] == 2
