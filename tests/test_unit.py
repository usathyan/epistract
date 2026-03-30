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
# Ingestion module availability
# ---------------------------------------------------------------------------
try:
    from ingest_documents import (
        discover_corpus,
        sanitize_doc_id,
        detect_category,
        parse_document,
        ingest_corpus,
    )

    HAS_INGEST = True
except ImportError:
    HAS_INGEST = False

FIXTURES = PROJECT_ROOT / "tests" / "fixtures"


# ========================================================================
# UT-020: discover_corpus finds all files recursively
# ========================================================================
@pytest.mark.skipif(not HAS_INGEST, reason="ingest_documents not available")
def test_ingest_discover_corpus():
    """discover_corpus(fixtures_path) finds all files recursively."""
    files = discover_corpus(FIXTURES)
    assert len(files) >= 3, f"Expected >= 3 files, got {len(files)}"
    extensions = {f.suffix.lower() for f in files}
    assert ".pdf" in extensions, f"Expected .pdf in extensions, got {extensions}"
    assert ".xlsx" in extensions, f"Expected .xlsx in extensions, got {extensions}"


# ========================================================================
# UT-021: sanitize_doc_id normalizes filenames
# ========================================================================
@pytest.mark.skipif(not HAS_INGEST, reason="ingest_documents not available")
def test_ingest_sanitize_doc_id_basic():
    """sanitize_doc_id normalizes filenames to lowercase with underscores."""
    result = sanitize_doc_id("Aramark Contract.pdf")
    assert result == "aramark_contract", f"Expected 'aramark_contract', got '{result}'"


@pytest.mark.skipif(not HAS_INGEST, reason="ingest_documents not available")
def test_ingest_sanitize_doc_id_parens():
    """sanitize_doc_id handles parentheses and special characters."""
    result = sanitize_doc_id("PCC Rental Agreement (2026).PDF")
    assert result == "pcc_rental_agreement__2026_", f"Expected 'pcc_rental_agreement__2026_', got '{result}'"


# ========================================================================
# UT-022: detect_category from folder structure
# ========================================================================
@pytest.mark.skipif(not HAS_INGEST, reason="ingest_documents not available")
def test_ingest_detect_category_known():
    """detect_category returns lowercase folder name for known categories."""
    result = detect_category(Path("corpus/Hotel/contract.pdf"), Path("corpus"))
    assert result == "hotel", f"Expected 'hotel', got '{result}'"


@pytest.mark.skipif(not HAS_INGEST, reason="ingest_documents not available")
def test_ingest_detect_category_unknown():
    """detect_category returns 'uncategorized' for unknown folder names."""
    result = detect_category(Path("corpus/Unknown/file.pdf"), Path("corpus"))
    assert result == "uncategorized", f"Expected 'uncategorized', got '{result}'"


@pytest.mark.skipif(not HAS_INGEST, reason="ingest_documents not available")
def test_ingest_detect_category_nested():
    """detect_category uses top-level folder for nested files."""
    result = detect_category(Path("corpus/Hotel/SubDir/file.pdf"), Path("corpus"))
    assert result == "hotel", f"Expected 'hotel', got '{result}'"


# ========================================================================
# UT-023: parse_document reads PDF content
# ========================================================================
@pytest.mark.skipif(not HAS_INGEST, reason="ingest_documents not available")
def test_ingest_parse_document_pdf():
    """parse_document on a valid PDF returns non-empty string."""
    result = parse_document(FIXTURES / "sample_contract_a.pdf")
    assert isinstance(result, str), f"Expected str, got {type(result)}"
    assert len(result) > 0, "Expected non-empty text from PDF"


@pytest.mark.skipif(not HAS_INGEST, reason="ingest_documents not available")
def test_ingest_parse_document_missing():
    """parse_document on nonexistent file returns error dict."""
    result = parse_document(Path("/nonexistent/file.pdf"))
    assert isinstance(result, dict), f"Expected dict for missing file, got {type(result)}"
    assert "error" in result, f"Expected 'error' key in result, got {result}"


# ========================================================================
# UT-024: ingest_corpus writes text files
# ========================================================================
@pytest.mark.skipif(not HAS_INGEST, reason="ingest_documents not available")
def test_ingest_corpus_writes_txt():
    """ingest_corpus writes .txt files to ingested/ subdirectory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output = Path(tmpdir)
        result = ingest_corpus(FIXTURES, output)
        ingested_dir = output / "ingested"
        assert ingested_dir.exists(), "ingested/ directory not created"
        txt_files = list(ingested_dir.glob("*.txt"))
        assert len(txt_files) >= 1, f"Expected >= 1 .txt files, got {len(txt_files)}"
        assert result["successful"] >= 1, f"Expected >= 1 successful, got {result}"


# ---------------------------------------------------------------------------
# Integration tests for triage output and error handling (Plan 02)
# ---------------------------------------------------------------------------
import shutil  # noqa: E402


@pytest.mark.skipif(not HAS_INGEST, reason="ingest_documents not available")
def test_ingest_integration_triage_json_structure(tmp_path):
    """ingest_corpus produces triage.json with all required top-level keys."""
    # Create mock corpus with category folders
    corpus = tmp_path / "corpus"
    hotel_dir = corpus / "Hotel"
    av_dir = corpus / "AV"
    hotel_dir.mkdir(parents=True)
    av_dir.mkdir(parents=True)
    # Copy fixtures into category folders
    shutil.copy(FIXTURES / "sample_contract_a.pdf", hotel_dir / "contract_a.pdf")
    shutil.copy(FIXTURES / "sample_contract_b.pdf", av_dir / "contract_b.pdf")

    output = tmp_path / "output"
    _result = ingest_corpus(corpus, output)

    triage_path = output / "triage.json"
    assert triage_path.exists(), "triage.json not created"
    triage = json.loads(triage_path.read_text())

    # Top-level keys
    for key in ("ingested_at", "corpus_path", "domain", "total_files", "successful", "failed", "documents"):
        assert key in triage, f"Missing top-level key: {key}"

    assert triage["total_files"] >= 2, f"Expected >= 2 files, got {triage['total_files']}"
    assert triage["successful"] + triage["failed"] == triage["total_files"], (
        f"successful ({triage['successful']}) + failed ({triage['failed']}) != total ({triage['total_files']})"
    )


@pytest.mark.skipif(not HAS_INGEST, reason="ingest_documents not available")
def test_ingest_integration_document_metadata_fields(tmp_path):
    """Each document in triage.json has all D-08 metadata fields with correct types."""
    corpus = tmp_path / "corpus"
    hotel_dir = corpus / "Hotel"
    hotel_dir.mkdir(parents=True)
    shutil.copy(FIXTURES / "sample_contract_a.pdf", hotel_dir / "contract_a.pdf")

    output = tmp_path / "output"
    _result = ingest_corpus(corpus, output)

    triage = json.loads((output / "triage.json").read_text())
    assert len(triage["documents"]) >= 1, "Expected at least 1 document"

    d08_fields = {
        "doc_id", "filename", "file_path", "file_size_bytes", "page_count",
        "category", "parse_type", "text_length", "parse_errors",
        "extraction_readiness_score",
    }

    for doc in triage["documents"]:
        for field in d08_fields:
            assert field in doc, f"Missing D-08 field '{field}' in document {doc.get('doc_id', '???')}"

        assert isinstance(doc["doc_id"], str), f"doc_id not str: {type(doc['doc_id'])}"
        assert isinstance(doc["file_size_bytes"], int), f"file_size_bytes not int: {type(doc['file_size_bytes'])}"
        assert doc["file_size_bytes"] > 0, f"file_size_bytes should be > 0, got {doc['file_size_bytes']}"
        assert doc["category"] in {"hotel", "av", "uncategorized"}, f"Unexpected category: {doc['category']}"
        assert doc["parse_type"] in {"text", "scanned", "mixed", "failed"}, (
            f"Unexpected parse_type: {doc['parse_type']}"
        )
        score = doc["extraction_readiness_score"]
        assert isinstance(score, float) or isinstance(score, int), f"score not numeric: {type(score)}"
        assert 0.0 <= score <= 1.0, f"score out of range: {score}"


@pytest.mark.skipif(not HAS_INGEST, reason="ingest_documents not available")
def test_ingest_integration_error_handling(tmp_path):
    """Pipeline handles corrupt files gracefully: logs error, doesn't crash."""
    corpus = tmp_path / "corpus"
    sec_dir = corpus / "Security"
    sec_dir.mkdir(parents=True)
    # Write random bytes as corrupt PDF
    corrupt_file = sec_dir / "corrupt.pdf"
    corrupt_file.write_bytes(b"\x00\x01\x02\x03" * 100)

    output = tmp_path / "output"
    # Should not raise
    _result = ingest_corpus(corpus, output)

    triage = json.loads((output / "triage.json").read_text())
    assert triage["total_files"] >= 1, "Expected at least 1 file"

    # Find the corrupt document entry
    corrupt_docs = [d for d in triage["documents"] if "corrupt" in d.get("filename", "").lower()]
    assert len(corrupt_docs) >= 1, f"Expected corrupt.pdf entry, got docs: {[d['filename'] for d in triage['documents']]}"
    corrupt_doc = corrupt_docs[0]
    # Either parse_errors is set or parse_type is "failed"
    has_error = corrupt_doc.get("parse_errors") is not None or corrupt_doc.get("parse_type") == "failed"
    assert has_error, f"Expected error indication for corrupt file, got: {corrupt_doc}"


@pytest.mark.skipif(not HAS_INGEST, reason="ingest_documents not available")
def test_ingest_integration_empty_corpus(tmp_path):
    """Ingesting an empty directory produces triage.json with total_files=0."""
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    output = tmp_path / "output"

    _result = ingest_corpus(corpus, output)

    triage = json.loads((output / "triage.json").read_text())
    assert triage["total_files"] == 0, f"Expected 0 files, got {triage['total_files']}"
    assert triage["documents"] == [], f"Expected empty documents list, got {triage['documents']}"


@pytest.mark.skipif(not HAS_INGEST, reason="ingest_documents not available")
def test_ingest_integration_text_files_written(tmp_path):
    """After ingest_corpus, ingested/ dir exists with at least one .txt file."""
    output = tmp_path / "output"
    ingest_corpus(FIXTURES, output)

    ingested_dir = output / "ingested"
    assert ingested_dir.exists(), "ingested/ directory not created"
    txt_files = list(ingested_dir.glob("*.txt"))
    assert len(txt_files) >= 1, f"Expected >= 1 .txt file, got {len(txt_files)}"
    # Each txt file should have content
    for tf in txt_files:
        assert tf.stat().st_size > 0, f"Empty text file: {tf.name}"


@pytest.mark.skipif(not HAS_INGEST, reason="ingest_documents not available")
def test_ingest_integration_txt_content_matches(tmp_path):
    """Text file content in ingested/ matches parse_document output."""
    output = tmp_path / "output"
    ingest_corpus(FIXTURES, output)

    # Parse a known fixture directly
    fixture_file = FIXTURES / "sample_contract_a.pdf"
    expected_text = parse_document(fixture_file)
    assert isinstance(expected_text, str), f"parse_document failed: {expected_text}"

    # Find corresponding txt file
    doc_id = sanitize_doc_id(fixture_file.name)
    txt_path = output / "ingested" / f"{doc_id}.txt"
    assert txt_path.exists(), f"Expected {txt_path} to exist"

    actual_text = txt_path.read_text(encoding="utf-8")
    # Normalize whitespace for comparison (reader may produce trailing spaces)
    actual_lines = [line.rstrip() for line in actual_text.splitlines()]
    expected_lines = [line.rstrip() for line in expected_text.splitlines()]
    assert actual_lines == expected_lines, "Text file content does not match parse_document output"


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


# ---------------------------------------------------------------------------
# Phase 3 Wave 2: Graph Construction & Orchestration (UT-036+)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_SIFTKG, reason="sift-kg not installed")
def test_ut036_graph_build_contracts(tmp_path):
    """Graph builds from contract extraction JSON via sift-kg."""
    from run_sift import cmd_build
    import io
    import contextlib

    # Create a minimal contract extraction
    entities = [
        {"name": "Aramark", "entity_type": "PARTY", "confidence": 0.95,
         "attributes": {"role": "Caterer", "aliases": ["Contractor"], "legal_name": "Aramark Sports & Entertainment Services, LLC"}},
        {"name": "Hall A", "entity_type": "VENUE", "confidence": 0.9,
         "attributes": {"capacity": "5000", "location": "Pennsylvania Convention Center"}},
        {"name": "Catering for 500 guests", "entity_type": "SERVICE", "confidence": 0.85,
         "attributes": {"description": "Full catering service", "provider": "Aramark"}},
        {"name": "$45 per person lunch", "entity_type": "COST", "confidence": 0.9,
         "attributes": {"amount": 45.0, "currency": "USD", "unit": "per person", "raw_text": "$45 per person for lunch service"}},
        {"name": "Final headcount due Aug 1", "entity_type": "DEADLINE", "confidence": 0.88,
         "attributes": {"date": "2026-08-01", "what_is_due": "Final headcount", "raw_text": "Final headcount due by August 1, 2026"}},
    ]
    relations = [
        {"source_entity": "Aramark", "target_entity": "Catering for 500 guests",
         "relation_type": "PROVIDES", "confidence": 0.9,
         "attributes": {"source_contract": "test_contract", "section": "1.1"}},
        {"source_entity": "$45 per person lunch", "target_entity": "Catering for 500 guests",
         "relation_type": "COSTS", "confidence": 0.88},
    ]
    write_extraction("test_contract", str(tmp_path), entities, relations,
                     chunks_processed=3, domain_name="contract")

    # Build graph (capture stdout; label_communities may print before the result JSON)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        cmd_build(str(tmp_path), domain_name="contract")

    # Parse last JSON object from stdout (cmd_build result is the last line)
    output_lines = buf.getvalue().strip().split("\n")
    result = json.loads(output_lines[-1])
    assert result["entities"] >= 4, f"Expected >= 4 entities, got {result['entities']}"
    assert result["relations"] >= 1, f"Expected >= 1 relation, got {result['relations']}"
    assert (tmp_path / "graph_data.json").exists(), "graph_data.json not created"


@pytest.mark.skipif(not HAS_SIFTKG, reason="sift-kg not installed")
def test_ut037_graph_node_attributes(tmp_path):
    """Graph nodes carry domain-specific typed attributes (D-14, D-16)."""
    from run_sift import cmd_build
    import io
    import contextlib

    entities = [
        {"name": "Aramark", "entity_type": "PARTY", "confidence": 0.95,
         "attributes": {"role": "Caterer", "aliases": ["Contractor"]}},
        {"name": "$45 per person lunch", "entity_type": "COST", "confidence": 0.9,
         "attributes": {"amount": 45.0, "currency": "USD", "unit": "per person", "raw_text": "$45 per person for lunch service"}},
    ]
    relations = [
        {"source_entity": "$45 per person lunch", "target_entity": "Aramark",
         "relation_type": "COSTS", "confidence": 0.88},
    ]
    write_extraction("attr_test", str(tmp_path), entities, relations, domain_name="contract")

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        cmd_build(str(tmp_path), domain_name="contract")

    # Load graph and check attributes
    graph_data = json.loads((tmp_path / "graph_data.json").read_text())
    nodes = graph_data.get("nodes", graph_data.get("entities", []))
    # Find COST node
    cost_nodes = [n for n in nodes if n.get("entity_type") == "COST"]
    assert len(cost_nodes) >= 1, f"No COST nodes found in {len(nodes)} nodes"
    cost = cost_nodes[0]
    attrs = cost.get("attributes", cost)
    # COST must have amount and raw_text (per D-16)
    assert "amount" in str(attrs) or "45" in str(attrs), f"COST node missing amount: {attrs}"


@pytest.mark.skipif(not HAS_SIFTKG, reason="sift-kg not installed")
def test_ut038_visualization_renders(tmp_path):
    """Pyvis HTML visualization renders for contract graph (D-18)."""
    from run_sift import cmd_build, cmd_view
    import io
    import contextlib

    entities = [
        {"name": "Aramark", "entity_type": "PARTY", "confidence": 0.95},
        {"name": "Hall A", "entity_type": "VENUE", "confidence": 0.9},
    ]
    relations = [
        {"source_entity": "Aramark", "target_entity": "Hall A",
         "relation_type": "PROVIDES", "confidence": 0.85},
    ]
    write_extraction("viz_test", str(tmp_path), entities, relations, domain_name="contract")

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        cmd_build(str(tmp_path), domain_name="contract")

    # View should generate HTML
    try:
        cmd_view(str(tmp_path))
    except SystemExit:
        pass  # pyvis may try to open browser

    html_files = list(tmp_path.glob("*.html"))
    assert len(html_files) >= 1, f"No HTML visualization files generated in {tmp_path}"
    html_content = html_files[0].read_text()
    assert "vis-network" in html_content or "vis.js" in html_content or "<html" in html_content, \
        "HTML file does not appear to be a vis.js visualization"


# ========================================================================
# UT-039: Biomedical epistemic analysis backward compatibility
# ========================================================================
def test_ut039_biomedical_epistemic_backward_compat(tmp_path):
    """Biomedical epistemic analysis produces same output after refactor."""
    from label_epistemic import analyze_epistemic

    # Create minimal graph_data.json with biomedical-style links
    graph_data = {
        "metadata": {"domain": "drug-discovery"},
        "nodes": [
            {"id": "compound:sotorasib", "name": "sotorasib", "entity_type": "COMPOUND"},
            {"id": "gene:kras_g12c", "name": "KRAS G12C", "entity_type": "GENE"},
        ],
        "links": [
            {
                "relation_id": "rel_001",
                "source": "compound:sotorasib",
                "target": "gene:kras_g12c",
                "relation_type": "INHIBITS",
                "confidence": 0.95,
                "evidence": "Sotorasib inhibits KRAS G12C with high selectivity.",
                "source_document": "pmid_12345",
            },
            {
                "relation_id": "rel_002",
                "source": "compound:sotorasib",
                "target": "gene:kras_g12c",
                "relation_type": "MODULATES",
                "confidence": 0.6,
                "evidence": "Sotorasib may reduce downstream signaling through KRAS G12C.",
                "source_document": "pmid_67890",
            },
        ],
    }
    (tmp_path / "graph_data.json").write_text(json.dumps(graph_data, indent=2))

    # Call with no domain (should default to biomedical)
    result = analyze_epistemic(tmp_path)

    # Verify claims_layer.json was written
    claims_path = tmp_path / "claims_layer.json"
    assert claims_path.exists(), "claims_layer.json was not created"

    claims = json.loads(claims_path.read_text())
    assert "metadata" in claims, "claims_layer missing metadata"
    assert "summary" in claims, "claims_layer missing summary"
    assert "base_domain" in claims, "claims_layer missing base_domain"
    assert "super_domain" in claims, "claims_layer missing super_domain"

    # Verify graph_data.json links have epistemic_status field
    updated_graph = json.loads((tmp_path / "graph_data.json").read_text())
    for link in updated_graph["links"]:
        assert "epistemic_status" in link, f"Link {link.get('relation_id')} missing epistemic_status"

    # The hedging evidence ("may reduce") should classify as hypothesized
    rel_002 = [l for l in updated_graph["links"] if l["relation_id"] == "rel_002"][0]
    assert rel_002["epistemic_status"] == "hypothesized", \
        f"Expected 'hypothesized' for hedging evidence, got '{rel_002['epistemic_status']}'"


# ========================================================================
# UT-040: Cross-contract entity identification (XREF-01)
# ========================================================================
def test_ut040_cross_contract_entities():
    """Entities appearing in multiple contracts are identified (XREF-01)."""
    from epistemic_contract import find_cross_contract_entities
    nodes = [
        {"id": "party:aramark", "name": "Aramark", "entity_type": "PARTY",
         "source_documents": ["aramark_catering", "pcc_vendor_policy"]},
        {"id": "venue:hall_a", "name": "Hall A", "entity_type": "VENUE",
         "source_documents": ["pcc_license", "av_vendor_agreement", "aramark_catering"]},
        {"id": "cost:setup_fee", "name": "Setup Fee", "entity_type": "COST",
         "source_documents": ["av_vendor_agreement"]},  # Single contract -- not cross-contract
    ]
    result = find_cross_contract_entities(nodes)
    assert len(result) == 2, f"Expected 2 cross-contract entities, got {len(result)}"
    assert result[0]["entity_id"] == "venue:hall_a", "Hall A (3 contracts) should be first"
    assert result[0]["contract_count"] == 3
    assert result[1]["entity_id"] == "party:aramark"
    assert result[1]["contract_count"] == 2


# ========================================================================
# UT-042: Conflict rules load from domain.yaml
# ========================================================================
def test_ut042_conflict_rules_yaml():
    """Contract domain.yaml contains valid conflict_rules section (XREF-02)."""
    import yaml

    domain_path = PROJECT_ROOT / "skills" / "contract-extraction" / "domain.yaml"
    data = yaml.safe_load(domain_path.read_text())
    assert "conflict_rules" in data, "domain.yaml missing conflict_rules"
    rules = data["conflict_rules"]
    assert "exclusive_use" in rules
    assert "schedule_contradiction" in rules
    assert "term_contradiction" in rules
    assert "cost_budget_mismatch" in rules
    for name, rule in rules.items():
        assert "severity" in rule, f"Rule {name} missing severity"
        assert rule["severity"] in ("CRITICAL", "WARNING", "INFO"), f"Rule {name} invalid severity"
        assert "suggested_action_template" in rule, f"Rule {name} missing suggested_action_template"


# ========================================================================
# UT-045: Domain-aware dispatch
# ========================================================================
def test_ut045_domain_dispatch(tmp_path):
    """label_epistemic.py dispatches to correct module based on domain."""
    from label_epistemic import analyze_epistemic

    # Create graph_data.json with metadata.domain = "drug-discovery"
    graph_data = {
        "metadata": {"domain": "drug-discovery"},
        "nodes": [
            {"id": "compound:aspirin", "name": "aspirin", "entity_type": "COMPOUND"},
            {"id": "disease:headache", "name": "headache", "entity_type": "DISEASE"},
        ],
        "links": [
            {
                "relation_id": "rel_d01",
                "source": "compound:aspirin",
                "target": "disease:headache",
                "relation_type": "TREATS",
                "confidence": 0.92,
                "evidence": "Aspirin treats headache effectively.",
                "source_document": "pmid_99999",
            },
            {
                "relation_id": "rel_d02",
                "source": "compound:aspirin",
                "target": "disease:headache",
                "relation_type": "MAY_TREAT",
                "confidence": 0.55,
                "evidence": "Aspirin may reduce chronic headache frequency.",
                "source_document": "pmid_88888",
            },
        ],
    }
    (tmp_path / "graph_data.json").write_text(json.dumps(graph_data, indent=2))

    # Call analyze_epistemic -- should use biomedical path
    result = analyze_epistemic(tmp_path)

    # Verify claims_layer.json exists
    claims_path = tmp_path / "claims_layer.json"
    assert claims_path.exists(), "claims_layer.json was not created"

    # Check that links in graph_data.json have epistemic_status
    updated_graph = json.loads((tmp_path / "graph_data.json").read_text())
    for link in updated_graph["links"]:
        assert "epistemic_status" in link, f"Link {link.get('relation_id')} missing epistemic_status"

    # Contract domain should now dispatch to epistemic_contract module
    contract_graph = {
        "metadata": {"domain": "contract"},
        "nodes": [
            {"id": "party:test", "name": "Test Party", "entity_type": "PARTY",
             "confidence": 0.9, "attributes": {}},
        ],
        "links": [],
    }
    (tmp_path / "graph_data.json").write_text(json.dumps(contract_graph, indent=2))
    contract_result = analyze_epistemic(tmp_path, domain_name="contract")
    assert "super_domain" in contract_result, "Contract domain should return valid claims_layer"
    assert contract_result["super_domain"].get("domain") == "contract"


# ========================================================================
# UT-041: Conflict detection with 4 types (XREF-02)
# ========================================================================
def test_ut041_conflict_detection():
    """Four conflict types detected from graph data (XREF-02)."""
    from epistemic_contract import detect_conflicts
    nodes = [
        {"id": "clause:aramark_exclusive", "name": "Aramark Exclusivity", "entity_type": "CLAUSE",
         "attributes": {"clause_type": "exclusivity"}, "source_document": "aramark_catering"},
        {"id": "clause:dessert_scope", "name": "Dessert Vendor Scope", "entity_type": "CLAUSE",
         "attributes": {"clause_type": "exclusivity"}, "source_document": "dessert_vendor"},
        {"id": "venue:hall_a", "name": "Hall A", "entity_type": "VENUE",
         "attributes": {"room_or_space": "Hall A"}, "source_document": "pcc_license"},
        {"id": "deadline:headcount_a", "name": "Headcount Due", "entity_type": "DEADLINE",
         "attributes": {"what_is_due": "final headcount", "date": "2026-08-01"}, "source_document": "aramark_catering"},
        {"id": "deadline:headcount_b", "name": "Headcount Due AV", "entity_type": "DEADLINE",
         "attributes": {"what_is_due": "final headcount", "date": "2026-07-15"}, "source_document": "av_vendor"},
    ]
    links = [
        {"source": "clause:aramark_exclusive", "target": "venue:hall_a",
         "relation_type": "RESTRICTS", "source_document": "aramark_catering"},
        {"source": "clause:dessert_scope", "target": "venue:hall_a",
         "relation_type": "RESTRICTS", "source_document": "dessert_vendor"},
    ]
    rules = {
        "exclusive_use": {
            "entity_types": ["CLAUSE", "VENUE"],
            "match_on": ["attributes.room_or_space", "attributes.clause_type"],
            "match_value": "exclusivity",
            "severity": "CRITICAL",
            "suggested_action_template": "Review {source} against {conflict} for exclusive-use overlap in {space}",
        },
        "schedule_contradiction": {
            "entity_types": ["DEADLINE"],
            "match_on": ["attributes.what_is_due"],
            "compare_attribute": "attributes.date",
            "conflict_condition": "dates_conflict",
            "severity": "WARNING",
            "suggested_action_template": "Reconcile {entity_a} with {entity_b} -- dates conflict for {what_is_due}",
        },
    }
    conflicts = detect_conflicts(nodes, links, rules)
    assert len(conflicts) >= 1, f"Expected at least 1 conflict, got {len(conflicts)}"
    severities = [c["severity"] for c in conflicts]
    assert "CRITICAL" in severities or "WARNING" in severities, "Conflicts must have severity"
    for c in conflicts:
        assert "suggested_action" in c, f"Conflict {c['id']} missing suggested_action"
        assert "entities_involved" in c, f"Conflict {c['id']} missing entities_involved"


# ========================================================================
# UT-043: Coverage gap identification (XREF-03)
# ========================================================================
def test_ut043_coverage_gaps():
    """Coverage gaps identified between reference items and contract graph (XREF-03)."""
    from epistemic_contract import find_coverage_gaps
    ref_nodes = [
        {"id": "ref:security_plan", "name": "Security staffing plan for 5000 attendees",
         "entity_type": "PLANNING_ITEM", "source": "reference",
         "attributes": {"category": "requirement"}},
        {"id": "ref:catering_budget", "name": "Catering budget $150,000",
         "entity_type": "PLANNING_ITEM", "source": "reference",
         "attributes": {"category": "budget", "amount": "$150,000"}},
    ]
    contract_nodes = [
        {"id": "obligation:catering_service", "name": "Provide catering for event meals",
         "entity_type": "OBLIGATION", "attributes": {"action": "provide catering services"}},
        # No security-related obligation -- this should be a gap
    ]
    links = []
    gaps = find_coverage_gaps(ref_nodes, contract_nodes, links)
    assert len(gaps) >= 1, f"Expected at least 1 gap, got {len(gaps)}"
    gap_refs = [g["reference_entity"] for g in gaps]
    assert "ref:security_plan" in gap_refs, "Security plan gap should be detected"
    for g in gaps:
        assert "severity" in g
        assert "suggested_action" in g


# ========================================================================
# UT-044: Risk scoring with severity (XREF-04)
# ========================================================================
def test_ut044_risk_scoring():
    """Risks scored as CRITICAL, WARNING, or INFO with suggested actions (XREF-04)."""
    from epistemic_contract import score_risks
    conflicts = [
        {"id": "conflict:exclusive_use:001", "type": "exclusive_use", "severity": "CRITICAL",
         "description": "Exclusive-use conflict", "entities_involved": ["a", "b"],
         "contracts_involved": ["c1", "c2"], "suggested_action": "Review"},
    ]
    gaps = [
        {"id": "gap:001", "type": "coverage_gap", "severity": "WARNING",
         "description": "Missing coverage", "reference_entity": "ref:x",
         "suggested_action": "Add coverage"},
    ]
    risks = score_risks(conflicts, gaps)
    assert len(risks) >= 2, f"Expected at least 2 risks, got {len(risks)}"
    severities = {r["severity"] for r in risks}
    assert "CRITICAL" in severities, "Should have CRITICAL risks from exclusive-use conflict"
    assert "WARNING" in severities, "Should have WARNING risks from coverage gap"
    for r in risks:
        assert r["severity"] in ("CRITICAL", "WARNING", "INFO")
        assert "suggested_action" in r
        assert "source_type" in r


# ========================================================================
# UT-046: claims_layer.json contract schema (output format)
# ========================================================================
def test_ut046_claims_layer_schema(tmp_path):
    """Contract claims_layer.json has correct Super Domain structure."""
    from epistemic_contract import analyze_contract_epistemic
    # Create minimal contract graph_data.json
    graph_data = {
        "metadata": {"domain": "contract"},
        "nodes": [
            {"id": "party:aramark", "name": "Aramark", "entity_type": "PARTY",
             "confidence": 0.95, "attributes": {}},
            {"id": "obligation:catering", "name": "Provide catering", "entity_type": "OBLIGATION",
             "confidence": 0.9, "attributes": {"action": "provide catering"}},
        ],
        "links": [
            {"source": "party:aramark", "target": "obligation:catering",
             "relation_type": "OBLIGATES", "confidence": 0.9,
             "evidence": "Aramark shall provide catering", "source_document": "aramark_agreement"},
        ],
    }
    (tmp_path / "graph_data.json").write_text(json.dumps(graph_data, indent=2))
    result = analyze_contract_epistemic(tmp_path, graph_data)
    assert "metadata" in result
    assert "summary" in result
    assert "base_domain" in result
    assert "super_domain" in result
    assert result["super_domain"].get("domain") == "contract"
    assert "cross_contract_entities" in result["super_domain"]
    assert "conflicts" in result["super_domain"]
    assert "risks" in result["super_domain"]
    summary = result["summary"]
    assert "risks" in summary
    assert all(k in summary["risks"] for k in ("CRITICAL", "WARNING", "INFO"))
