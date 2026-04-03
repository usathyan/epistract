#!/usr/bin/env python3
"""Schema validation and domain skill coverage tests.

Covers TEST-03 (skill coverage) and TEST-04 (agent coverage via Pydantic).
Run: python -m pytest tests/test_schemas.py -m unit -v
"""
import json

import pytest
import yaml
from pydantic import BaseModel, ValidationError

from conftest import FIXTURES_DIR, PROJECT_ROOT

# ---------------------------------------------------------------------------
# Pydantic models for DocumentExtraction validation (D-07)
# ---------------------------------------------------------------------------


class ExtractedEntity(BaseModel):
    name: str
    entity_type: str
    confidence: float
    context: str = ""


class ExtractedRelation(BaseModel):
    source_entity: str
    target_entity: str
    relation_type: str
    confidence: float
    evidence: str = ""


class DocumentExtraction(BaseModel):
    document_id: str
    entities: list[ExtractedEntity]
    relations: list[ExtractedRelation]
    extracted_at: str
    domain_name: str
    chunks_processed: int = 1
    document_path: str = ""
    cost_usd: float = 0.0
    model_used: str = ""
    chunk_size: int = 10000
    error: str | None = None


# ---------------------------------------------------------------------------
# Domain paths
# ---------------------------------------------------------------------------
DRUG_DISCOVERY_YAML = PROJECT_ROOT / "domains" / "drug-discovery" / "domain.yaml"
CONTRACTS_YAML = PROJECT_ROOT / "domains" / "contracts" / "domain.yaml"
DRUG_DISCOVERY_SKILL = PROJECT_ROOT / "domains" / "drug-discovery" / "SKILL.md"
CONTRACTS_SKILL = PROJECT_ROOT / "domains" / "contracts" / "SKILL.md"

# Valid drug-discovery entity types
DRUG_DISCOVERY_ENTITY_TYPES = {
    "COMPOUND",
    "GENE",
    "PROTEIN",
    "DISEASE",
    "MECHANISM_OF_ACTION",
    "CLINICAL_TRIAL",
    "PATHWAY",
    "BIOMARKER",
    "ADVERSE_EVENT",
    "ORGANIZATION",
    "PUBLICATION",
    "REGULATORY_ACTION",
    "PHENOTYPE",
    "METABOLITE",
    "CELL_OR_TISSUE",
    "PROTEIN_DOMAIN",
    "SEQUENCE_VARIANT",
}


# ========================================================================
# TEST-04: Agent coverage via Pydantic DocumentExtraction validation
# ========================================================================


@pytest.mark.unit
def test_extraction_schema_drug_discovery():
    """Load drug extraction fixture and validate with DocumentExtraction model."""
    data = json.loads((FIXTURES_DIR / "sample_extraction_drug.json").read_text())
    result = DocumentExtraction(**data)
    assert len(result.entities) >= 3, f"Expected >= 3 entities, got {len(result.entities)}"
    assert result.domain_name == "drug-discovery"


@pytest.mark.unit
def test_extraction_schema_contracts():
    """Load contract extraction fixture and validate with DocumentExtraction model."""
    data = json.loads((FIXTURES_DIR / "sample_extraction_contract.json").read_text())
    result = DocumentExtraction(**data)
    assert result.domain_name == "contracts"
    assert len(result.entities) >= 2


@pytest.mark.unit
def test_extraction_schema_rejects_invalid():
    """DocumentExtraction rejects dict missing required document_id field."""
    invalid_data = {
        "entities": [],
        "relations": [],
        "extracted_at": "2026-01-01T00:00:00Z",
        "domain_name": "test",
    }
    with pytest.raises(ValidationError):
        DocumentExtraction(**invalid_data)


@pytest.mark.unit
def test_extraction_entity_types_valid():
    """All entity types in drug extraction fixture are valid drug-discovery types."""
    data = json.loads((FIXTURES_DIR / "sample_extraction_drug.json").read_text())
    result = DocumentExtraction(**data)
    for entity in result.entities:
        assert entity.entity_type in DRUG_DISCOVERY_ENTITY_TYPES, (
            f"Unknown entity type: {entity.entity_type}"
        )


# ========================================================================
# TEST-03: Skill coverage via domain YAML validation
# ========================================================================


@pytest.mark.unit
def test_drug_discovery_domain_yaml_loads():
    """Drug-discovery domain.yaml loads and has 17 entity types and 30 relation types."""
    data = yaml.safe_load(DRUG_DISCOVERY_YAML.read_text())
    assert data["name"] is not None
    assert len(data["entity_types"]) == 17, f"Expected 17, got {len(data['entity_types'])}"
    assert len(data["relation_types"]) == 30, f"Expected 30, got {len(data['relation_types'])}"


@pytest.mark.unit
def test_contracts_domain_yaml_loads():
    """Contracts domain.yaml loads and has 9 entity types and 9 relation types."""
    data = yaml.safe_load(CONTRACTS_YAML.read_text())
    assert data["name"] is not None
    assert len(data["entity_types"]) == 9, f"Expected 9, got {len(data['entity_types'])}"
    assert len(data["relation_types"]) == 9, f"Expected 9, got {len(data['relation_types'])}"


@pytest.mark.unit
def test_drug_discovery_skill_md_exists():
    """Drug-discovery SKILL.md exists and is non-trivial (> 100 bytes)."""
    assert DRUG_DISCOVERY_SKILL.exists(), f"Missing: {DRUG_DISCOVERY_SKILL}"
    assert DRUG_DISCOVERY_SKILL.stat().st_size > 100, "SKILL.md is too small"


@pytest.mark.unit
def test_contracts_skill_md_exists():
    """Contracts SKILL.md exists and is non-trivial (> 100 bytes)."""
    assert CONTRACTS_SKILL.exists(), f"Missing: {CONTRACTS_SKILL}"
    assert CONTRACTS_SKILL.stat().st_size > 100, "SKILL.md is too small"


@pytest.mark.unit
def test_domain_yaml_entity_types_have_required_fields():
    """Every entity type in both domain YAMLs has name and description."""
    for yaml_path in [DRUG_DISCOVERY_YAML, CONTRACTS_YAML]:
        data = yaml.safe_load(yaml_path.read_text())
        entity_types = data["entity_types"]

        if isinstance(entity_types, dict):
            # Drug-discovery format: {TYPE_NAME: {description: ..., ...}}
            for type_name, type_def in entity_types.items():
                assert isinstance(type_name, str), f"Entity type key must be str: {type_name}"
                assert "description" in type_def, (
                    f"Entity type {type_name} in {yaml_path.name} missing 'description'"
                )
        elif isinstance(entity_types, list):
            # Contracts format: [{name: ..., description: ...}, ...]
            for entry in entity_types:
                assert "name" in entry, (
                    f"Entity type entry in {yaml_path.name} missing 'name': {entry}"
                )
                assert "description" in entry, (
                    f"Entity type {entry.get('name', '?')} in {yaml_path.name} missing 'description'"
                )


@pytest.mark.unit
def test_domain_yaml_relation_types_have_required_fields():
    """Every relation type in both domain YAMLs has name/key and description."""
    for yaml_path in [DRUG_DISCOVERY_YAML, CONTRACTS_YAML]:
        data = yaml.safe_load(yaml_path.read_text())
        relation_types = data["relation_types"]

        if isinstance(relation_types, dict):
            # Drug-discovery format: {TYPE_NAME: {description: ..., ...}}
            for type_name, type_def in relation_types.items():
                assert isinstance(type_name, str), f"Relation type key must be str: {type_name}"
                assert "description" in type_def, (
                    f"Relation type {type_name} in {yaml_path.name} missing 'description'"
                )
        elif isinstance(relation_types, list):
            # Contracts format: [{name: ..., description: ...}, ...]
            for entry in relation_types:
                assert "name" in entry, (
                    f"Relation type entry in {yaml_path.name} missing 'name': {entry}"
                )
                assert "description" in entry, (
                    f"Relation type {entry.get('name', '?')} in {yaml_path.name} missing 'description'"
                )
