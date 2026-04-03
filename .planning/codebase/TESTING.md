# Testing Patterns

**Analysis Date:** 2026-03-29

## Test Framework

**Runner:**
- pytest 7.0+ (specified in test imports)
- Config: Makefile target `make test` runs `python -m pytest tests/test_unit.py -v`
- No `pytest.ini` or `pyproject.toml` — uses pytest defaults

**Assertion Library:**
- pytest's native assertions (no special library)
- Format: `assert condition, f"Descriptive message with {context}"`

**Run Commands:**
```bash
make test              # Run all unit tests (verbose mode)
python -m pytest tests/test_unit.py -v
python -m pytest tests/test_unit.py::test_ut001_domain_loads  # Single test
```

**Coverage:**
- Not currently enforced (no coverage config found)
- No coverage targets in Makefile

## Test File Organization

**Location:**
- Single test file at `tests/test_unit.py`
- Tests are co-located with validation scripts they test, but centralized via imports
- Validation scripts in `skills/drug-discovery-extraction/validation-scripts/`
- Scripts in `scripts/`

**Naming Convention:**
- Test functions: `test_ut{NNN}_{description}` (e.g., `test_ut001_domain_loads`)
- Mapped to external TEST_REQUIREMENTS.md document (UT-001 through UT-014)
- 14 total test cases covering core functionality

**File Structure:**
```
tests/
├── test_unit.py          # Main test file with 14 unit tests
└── corpora/              # Test data directories for scenarios (not unit tests)
    ├── 01_*
    ├── 02_*
    └── 06_glp1_landscape/  # Scenario test data
```

## Test Structure

**Setup Pattern:**
- Conditional imports with availability flags (lines 26-56 in test_unit.py)
- Skip decorators for optional dependencies
- Path setup for local imports:
  ```python
  PROJECT_ROOT = Path(__file__).parent.parent
  VALIDATION_SCRIPTS = PROJECT_ROOT / "skills" / "drug-discovery-extraction" / "validation-scripts"
  SCRIPTS = PROJECT_ROOT / "scripts"
  sys.path.insert(0, str(VALIDATION_SCRIPTS))
  sys.path.insert(0, str(SCRIPTS))
  ```

**Test Fixture Pattern:**
- No pytest fixtures used (tests are functional/integration style)
- Create temp data inline for each test:
  ```python
  with tempfile.TemporaryDirectory() as tmpdir:
      # Write extraction or run command
      path = write_extraction("test_doc", tmpdir, entities, relations)
      assert Path(path).exists()
  ```

**Section Organization:**
- Each test preceded by comment block (72 dashes):
  ```python
  # ========================================================================
  # UT-001: Domain YAML Loads Successfully
  # ========================================================================
  ```
- Docstring describes test purpose and assertion
- Imports grouped by availability at top

**Assertion Pattern:**
- Always include context message: `assert condition, f"Expected X, got {actual}"`
- Check for specific values first, then structure
- Example from test_ut002 (lines 74-78):
  ```python
  text = "The aspirin structure is SMILES: CC(=O)Oc1ccccc1C(=O)O which is well known."
  results = scan_text(text)
  smiles_matches = [r for r in results if "SMILES" in r["pattern_type"]]
  assert len(smiles_matches) >= 1, f"Expected SMILES match, got: {results}"
  assert "CC(=O)Oc1ccccc1C(=O)O" in smiles_matches[0]["value"]
  ```

## Mocking

**Framework:** `unittest.mock` (imported at line 11)

**When to Mock:**
- Used selectively to avoid import side effects (test_ut008, line 156):
  ```python
  import validate_smiles as vs_mod
  orig_available = vs_mod.RDKIT_AVAILABLE
  try:
      vs_mod.RDKIT_AVAILABLE = False
      result = vs_mod.validate_smiles("CC(=O)Oc1ccccc1C(=O)O")
      assert result["valid"] is None
  finally:
      vs_mod.RDKIT_AVAILABLE = orig_available
  ```

**Pattern - Subprocess for Isolation:**
- For tests that need true import isolation, use subprocess (test_ut014, line 305-309):
  ```python
  import subprocess
  result = subprocess.run(
      [sys.executable, str(SCRIPTS / "validate_molecules.py"), tmpdir],
      capture_output=True,
      text=True,
  )
  ```

## Test Types

**Unit Tests - Validation Functions:**
- UT-002 through UT-011: Test individual validation and pattern-scanning functions
- Scope: Single function with known input → assert expected output
- Example (UT-002): `scan_text()` with SMILES text returns pattern match
- Example (UT-006): `validate_smiles()` with valid SMILES returns molecular properties

**Unit Tests - JSON Serialization:**
- UT-012: `write_extraction()` produces valid sift-kg DocumentExtraction JSON
- Checks fields: `document_id`, `entities`, `relations`, `extracted_at`, `domain_name`
- Validates JSON is parseable: `json.loads(Path(path).read_text())`

**Integration Tests - Graph Building:**
- UT-013: Create test extractions → run sift-kg build → verify graph output
- Scope: Full pipeline with real sift-kg API
- Requires sift-kg library (skipped if not installed)
- Verifies: `graph_data.json` created and contains entities

**Integration Tests - Full Validation Orchestrator:**
- UT-014: Create extraction → run subprocess script → verify results output
- Scope: Pattern scanning → validation → JSON results generation
- Verifies: `validation/results.json` exists with statistics

**Dependency Tests:**
- UT-001: sift-kg domain YAML loads with correct schema (17 entity types, 30 relation types)

## Conditional Test Execution

**Skip Decorators:**
```python
@pytest.mark.skipif(not HAS_SIFTKG, reason="sift-kg not installed")
def test_ut001_domain_loads():
    ...

@pytest.mark.skipif(not HAS_RDKIT, reason="RDKit not installed")
def test_ut006_validate_smiles_valid():
    ...

@pytest.mark.skipif(not HAS_BIOPYTHON, reason="Biopython not installed")
def test_ut009_validate_dna():
    ...
```

**Availability Flags (set at module import):**
- Lines 26-56 in test_unit.py
- Three binary flags: `HAS_SIFTKG`, `HAS_RDKIT`, `HAS_BIOPYTHON`
- Set before any test definitions
- Allows running tests with partial environments (minimal setup) or full setup

## Test Data & Fixtures

**Inline Test Data:**
- No separate fixtures file; data created inline in each test
- SMILES examples: `"CC(=O)Oc1ccccc1C(=O)O"` (aspirin), `"not_a_smiles"`
- NCT example: `"NCT04303780"`
- DNA example: `"ATCGATCGATCGATCG"`
- CAS example: `"2252403-56-6"`

**Entity/Relation Test Fixtures (for JSON writing):**
- Defined locally in test_ut012 (lines 203-219):
  ```python
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
  ```

**Domain YAML Reference:**
- Path: `skills/drug-discovery-extraction/domain.yaml`
- Defined once in module globals (line 19):
  ```python
  DOMAIN_YAML = PROJECT_ROOT / "skills" / "drug-discovery-extraction" / "domain.yaml"
  ```
- Used by UT-001 and UT-013

## Test Coverage

**Current State:**
- 14 total tests
- Coverage areas:
  - Domain schema loading (1 test)
  - Pattern scanning (4 tests)
  - SMILES validation (3 tests)
  - Sequence validation (3 tests)
  - JSON serialization (1 test)
  - Graph building (1 test)
  - Full pipeline/validation orchestrator (1 test)

**Not Tested (gaps):**
- Epistemic labeling (`label_epistemic.py`) — no test
- Community labeling (`label_communities.py`) — no test
- Individual command functions in `run_sift.py` (`cmd_view`, `cmd_export`, `cmd_info`, `cmd_search`) — not tested
- Error cases in pattern scanning (overlapping spans, edge cases) — minimal coverage
- Contradiction detection logic in epistemic labeling — no test

**Risk Areas (low test coverage):**
- `label_epistemic.py` (80+ lines of hedging patterns and contradiction logic)
- `label_communities.py` (100+ lines of labeling heuristics)
- Extraction enrichment in `validate_molecules.py` (graph mutation logic)

## Common Testing Patterns

**Checking List of Results (filtering approach):**
```python
def test_ut002_scan_smiles():
    results = scan_text(text)
    smiles_matches = [r for r in results if "SMILES" in r["pattern_type"]]
    assert len(smiles_matches) >= 1, f"Expected SMILES match, got: {results}"
    assert "CC(=O)Oc1ccccc1C(=O)O" in smiles_matches[0]["value"]
```

**Checking Dictionary Fields:**
```python
def test_ut006_validate_smiles_valid():
    result = validate_smiles("CC(=O)Oc1ccccc1C(=O)O")
    assert result["valid"] is True
    assert "molecular_weight" in result
    assert 170 < result["molecular_weight"] < 190  # Range check
```

**JSON File Existence & Parsing:**
```python
with tempfile.TemporaryDirectory() as tmpdir:
    path = write_extraction("test_doc", tmpdir, entities, relations)
    assert Path(path).exists()

    data = json.loads(Path(path).read_text())
    assert data["document_id"] == "test_doc"
    assert isinstance(data["entities"], list)
```

**Type Checking in Validation:**
```python
assert detect_type("ATCGATCG") == "DNA"
assert detect_type("AUGCUAGC") == "RNA"
assert detect_type("MTEYKLVVV") == "protein"
```

**Temporary Directory for File I/O:**
- All file I/O tests use `tempfile.TemporaryDirectory()`
- Ensures tests are isolated and don't pollute filesystem
- Pattern: `with tempfile.TemporaryDirectory() as tmpdir: ...`

## Running Tests Locally

```bash
# Install dependencies
make setup              # Or: make setup-all for RDKit/Biopython

# Run all tests
make test

# Run with minimal setup (core tests only)
python -m pytest tests/test_unit.py::test_ut002_scan_smiles -v
python -m pytest tests/test_unit.py::test_ut003_scan_nct -v
python -m pytest tests/test_unit.py::test_ut011_detect_type -v

# Run with optional dependencies
uv pip install rdkit-pypi biopython sift-kg
make test
```

---

*Testing analysis: 2026-03-29*
