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

# Domain resolution imports
from domain_resolver import (
    resolve_domain,
    list_domains,
    get_domain_skill_md,
    get_validation_scripts_dir,
    validate_domain_cross_refs,
)

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

        # Run build (uses domain name, not path)
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
# Domain Resolution Tests (Phase 1: DCFG-01, DCFG-04)
# ---------------------------------------------------------------------------


def test_resolve_domain_default():
    """DCFG-04: resolve_domain(None) returns drug-discovery domain path."""
    path = resolve_domain(None)
    assert path.exists(), f"Default domain path does not exist: {path}"
    assert path.name == "domain.yaml"
    assert "drug-discovery-extraction" in str(path)


def test_resolve_domain_explicit_drug_discovery():
    """DCFG-04: resolve_domain('drug-discovery') returns same as default."""
    path = resolve_domain("drug-discovery")
    default_path = resolve_domain(None)
    assert path == default_path, f"Explicit != default: {path} vs {default_path}"


def test_resolve_domain_nonexistent():
    """DCFG-01: resolve_domain('nonexistent') raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError, match="not found"):
        resolve_domain("nonexistent")


def test_resolve_domain_validates_package(tmp_path):
    """DCFG-01/D-03: Domain missing SKILL.md raises FileNotFoundError."""
    # Create a domain dir with only domain.yaml (missing SKILL.md and references/)
    fake_skills = tmp_path / "skills"
    fake_domain = fake_skills / "fake-extraction"
    fake_domain.mkdir(parents=True)
    (fake_domain / "domain.yaml").write_text("name: Fake\nversion: '1.0'\n")
    # Temporarily patch SKILLS_DIR
    import domain_resolver

    original = domain_resolver.SKILLS_DIR
    domain_resolver.SKILLS_DIR = fake_skills
    try:
        with pytest.raises(FileNotFoundError, match="SKILL.md"):
            resolve_domain("fake")
    finally:
        domain_resolver.SKILLS_DIR = original


def test_list_domains():
    """DCFG-01/D-06: list_domains() discovers drug-discovery domain."""
    domains = list_domains()
    assert len(domains) >= 1, "Should find at least drug-discovery domain"
    names = [d["name"] for d in domains]
    assert "drug-discovery" in names, f"drug-discovery not in {names}"
    # Each domain has required keys
    for d in domains:
        assert "name" in d
        assert "description" in d
        assert "version" in d


def test_get_domain_skill_md():
    """DCFG-01: get_domain_skill_md returns SKILL.md content."""
    content = get_domain_skill_md("drug-discovery")
    assert len(content) > 100, "SKILL.md should have substantial content"
    assert "drug discovery" in content.lower() or "Drug Discovery" in content


def test_get_validation_scripts_dir_biomedical():
    """DCFG-01/D-18: Biomedical domain has validation-scripts/."""
    vs_dir = get_validation_scripts_dir("drug-discovery")
    assert vs_dir is not None, "Biomedical domain should have validation-scripts"
    assert vs_dir.is_dir()


def test_validate_cross_refs_biomedical():
    """DCFG-01/D-04: Biomedical domain has valid cross-references."""
    domain_path = resolve_domain("drug-discovery")
    errors = validate_domain_cross_refs(domain_path)
    assert errors == [], f"Biomedical domain has cross-ref errors: {errors}"


# ---------------------------------------------------------------------------
# Contract Domain Integration Tests (Phase 1: DCFG-02, DCFG-03, DCFG-04)
# ---------------------------------------------------------------------------


def test_contract_domain_resolves():
    """DCFG-01: resolve_domain('contract') returns contract domain path."""
    path = resolve_domain("contract")
    assert path.exists(), f"Contract domain path does not exist: {path}"
    assert "contract-extraction" in str(path)


@pytest.mark.skipif(not HAS_SIFTKG, reason="sift-kg not installed")
def test_contract_domain_loads():
    """DCFG-02: sift-kg load_domain() loads contract domain.yaml."""
    from sift_kg import load_domain as sift_load

    domain_path = resolve_domain("contract")
    domain = sift_load(domain_path=domain_path)
    assert domain.name == "Contract Analysis"


def test_contract_domain_schema():
    """DCFG-02: Contract domain has 7 entity types and 7 relation types."""
    import yaml

    domain_path = resolve_domain("contract")
    with open(domain_path) as f:
        data = yaml.safe_load(f)
    et = set(data["entity_types"].keys())
    expected_et = {"PARTY", "OBLIGATION", "DEADLINE", "COST", "CLAUSE", "SERVICE", "VENUE"}
    assert et == expected_et, f"Entity types mismatch: {et}"
    rt = set(data["relation_types"].keys())
    expected_rt = {"OBLIGATES", "CONFLICTS_WITH", "DEPENDS_ON", "COSTS", "PROVIDES", "RESTRICTS", "RELATED_TO"}
    assert rt == expected_rt, f"Relation types mismatch: {rt}"


def test_contract_cross_refs():
    """DCFG-02/D-04: Contract domain relation types reference valid entity types."""
    domain_path = resolve_domain("contract")
    errors = validate_domain_cross_refs(domain_path)
    assert errors == [], f"Contract domain cross-ref errors: {errors}"


def test_contract_skill_md():
    """DCFG-03: Contract SKILL.md exists with extraction guidance."""
    content = get_domain_skill_md("contract")
    assert "PARTY" in content, "SKILL.md missing PARTY entity type"
    assert "OBLIGATION" in content, "SKILL.md missing OBLIGATION entity type"
    assert "entity_type" in content, "SKILL.md missing entity_type field guidance"


def test_contract_no_validation_scripts():
    """DCFG-03/D-18: Contract domain has no validation-scripts."""
    vs_dir = get_validation_scripts_dir("contract")
    assert vs_dir is None, f"Contract domain should not have validation-scripts: {vs_dir}"


def test_contract_domain_package_complete():
    """DCFG-03/D-03: Contract domain has all required files."""
    contract_dir = PROJECT_ROOT / "skills" / "contract-extraction"
    assert (contract_dir / "domain.yaml").exists(), "Missing domain.yaml"
    assert (contract_dir / "SKILL.md").exists(), "Missing SKILL.md"
    assert (contract_dir / "references").is_dir(), "Missing references/"
    assert (contract_dir / "references" / "entity-types.md").exists(), "Missing entity-types.md"
    assert (contract_dir / "references" / "relation-types.md").exists(), "Missing relation-types.md"


def test_list_domains_includes_contract():
    """DCFG-01/D-06: list_domains() discovers contract domain."""
    domains = list_domains()
    names = [d["name"] for d in domains]
    assert "contract" in names, f"Contract not in discovered domains: {names}"
    assert "drug-discovery" in names, f"Drug-discovery not in discovered domains: {names}"


@pytest.mark.skipif(not HAS_SIFTKG, reason="sift-kg not installed")
def test_biomedical_domain_still_loads():
    """DCFG-04: Existing biomedical domain loads unchanged."""
    from sift_kg import load_domain as sift_load

    domain_path = resolve_domain(None)
    domain = sift_load(domain_path=domain_path)
    assert domain.name == "Drug Discovery"
