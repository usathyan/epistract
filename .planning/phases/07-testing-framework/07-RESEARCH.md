# Phase 7: Testing Framework - Research

**Researched:** 2026-04-03
**Domain:** Python test infrastructure (pytest), fixture-based testing, three-tier test architecture
**Confidence:** HIGH

## Summary

Phase 7 builds a comprehensive test suite across three tiers (unit, integration, E2E) for the epistract cross-domain KG framework. The existing codebase already has 46 unit tests in `tests/test_unit.py`, 32 provenance tests in `tests/test_kg_provenance.py`, and 13 workbench tests -- providing a strong foundation.

The primary work is: (1) reorganize existing tests into the three-tier structure with pytest markers, (2) convert the 32 KG provenance tests from live-server HTTP calls to fixture-based mocking, (3) add integration tests for core pipeline entry points (`run_sift.py`, `build_extraction.py`, `label_epistemic.py`, `label_communities.py`, `domain_resolver.py`), (4) add schema validation tests for agents and skills, (5) create an E2E pipeline test using pre-recorded extraction JSON, and (6) add cross-domain verification tests. No conftest.py exists yet -- this is the key infrastructure gap.

**Primary recommendation:** Create `tests/conftest.py` with shared fixtures (graph data loading, tmp output dirs, domain resolution), add `pyproject.toml` pytest config for marker registration and path setup, then reorganize tests into tiered files with marker-based selection via Makefile targets.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Three-tier test structure: Unit (fast, no external deps) -> Integration (needs sift-kg/RDKit but no servers) -> E2E (needs running workbench/LLM). Pytest markers (`@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.e2e`) control which tier runs.
- **D-02:** Makefile targets: `make test` = unit only, `make test-integration` = integration tier, `make test-all` = everything.
- **D-03:** KG provenance tests (32 existing) converted to fixture-based mocking -- load graph_data.json + claims_layer.json from fixtures, mock HTTP calls. Tests run offline and fast.
- **D-04:** Shared fixtures directory at `tests/fixtures/` with domain-labeled files (e.g., `sample_graph_data.json` for drug-discovery, `contract_graph_data.json` for contracts). Both domains share the same fixture loading pattern.
- **D-05:** E2E pipeline test (TEST-05) uses pre-recorded extraction JSON files as golden outputs. Pipeline runs graph-build -> epistemic -> export starting from pre-extracted data. No LLM calls -- deterministic and fast.
- **D-06:** Command coverage (TEST-02) defined as testing the underlying Python entry points that each `/epistract:*` command invokes. Every Python function a command would call (e.g., `run_sift.py build`, `run_sift.py export`, `build_extraction.py`, `label_epistemic.py`) runs without error against test fixtures.
- **D-07:** Agent coverage (TEST-04) uses Pydantic schema validation. Create DocumentExtraction Pydantic models and validate existing extraction JSON fixtures against the schema. Proves format correctness without invoking agents.
- **D-08:** Skill coverage (TEST-03) validates that domain YAML schemas load correctly and that extraction prompt templates produce valid output format.
- **D-09:** Local execution only for this phase. No GitHub Actions CI setup.
- **D-10:** Optional dependencies (RDKit, Biopython) handled with `pytest.mark.skipif` markers. Unit tier runs without optional deps. Integration tier requires sift-kg.

### Claude's Discretion
- Test file organization (single file vs multiple test files per tier)
- conftest.py fixture design and shared helpers
- Exact pytest marker names and grouping
- Whether to add `pyproject.toml` pytest config or keep Makefile-only
- Test naming convention (keep existing `test_ut{NNN}_` pattern or adopt new scheme)

### Deferred Ideas (OUT OF SCOPE)
- GitHub Actions CI setup -- future phase after test suite is stable
- Test coverage reporting (coverage.py) -- not in scope, no coverage targets defined
- Docker-based test environment
- Live LLM integration tests -- too expensive/non-deterministic
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TEST-01 | V1 regression suite -- every V1 capability has automated tests against reorganized codebase | Existing 46 unit tests cover V1 capabilities; need verification they pass against Phase 6 reorganized paths (core/, domains/) |
| TEST-02 | Command coverage -- every `/epistract:*` command has integration test | 10 commands map to Python entry points in core/run_sift.py, core/build_extraction.py, core/label_epistemic.py, core/label_communities.py, domains/*/validate_molecules.py |
| TEST-03 | Skill coverage -- every skill produces correct output format | 2 domain YAML schemas (drug-discovery: 17 entity types + 30 relation types, contracts: 9 entity + 9 relation), SKILL.md files exist for both |
| TEST-04 | Agent coverage -- extractor/validator produce valid DocumentExtraction JSON | Pydantic model for DocumentExtraction schema, validate against fixture extraction JSONs |
| TEST-05 | E2E pipeline test -- install through export lifecycle | Pre-recorded extraction JSONs in fixtures, pipeline: build_extraction -> run_sift build -> label_communities -> label_epistemic -> run_sift export |
| TEST-06 | KG provenance regression -- 32 existing tests pass | test_kg_provenance.py currently uses live HTTP requests; needs conversion to fixture-based with mocked requests |
| TEST-07 | Cross-domain verification -- both domains produce valid graphs through same pipeline | domain_resolver.py resolves both "drug-discovery" and "contracts"; build_extraction.py and run_sift.py accept --domain flag |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | 8.2.1 | Test runner and framework | Already installed and used by project |
| pydantic | >=2.5 | Schema validation for DocumentExtraction models (TEST-04) | Already a project dependency |
| pyyaml | >=6.0 | YAML schema loading for skill tests (TEST-03) | Already a project dependency |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| unittest.mock | stdlib | Mock HTTP calls in provenance tests | TEST-06 conversion |
| tempfile | stdlib | Temporary directories for integration tests | All tiers |
| shutil | stdlib | Copy fixtures to temp dirs | Integration/E2E setup |
| json | stdlib | Load/validate JSON fixtures | All fixture operations |
| pathlib | stdlib | Path operations (project convention) | Everywhere |

### No New Dependencies Needed
All test infrastructure uses pytest (already installed) plus stdlib modules. Pydantic is already a project dependency for DocumentExtraction validation. No `pip install` needed for the test framework itself.

## Architecture Patterns

### Recommended Test Structure
```
tests/
├── conftest.py              # Shared fixtures, path setup, markers
├── fixtures/
│   ├── sample_graph_data.json         # Drug-discovery graph (existing)
│   ├── sample_claims_layer.json       # Drug-discovery claims (existing)
│   ├── sample_communities.json        # Drug-discovery communities (existing)
│   ├── sample_ingested/               # Ingested text files (existing)
│   ├── sample_contract_a.pdf          # Contract fixtures (existing)
│   ├── sample_contract_b.pdf          # Contract fixtures (existing)
│   ├── contract_graph_data.json       # NEW: Contract domain graph fixture
│   ├── contract_claims_layer.json     # NEW: Contract domain claims fixture
│   ├── sample_extraction_drug.json    # NEW: Pre-recorded drug extraction for E2E
│   └── sample_extraction_contract.json # NEW: Pre-recorded contract extraction for E2E
├── test_unit.py             # Unit tier: fast, no external deps (existing, expanded)
├── test_integration.py      # Integration tier: needs sift-kg
├── test_e2e.py              # E2E tier: full pipeline
├── test_kg_provenance.py    # Provenance tests (converted to fixture-based)
└── test_workbench.py        # Workbench tests (existing, in examples/)
```

### Pattern 1: conftest.py with Shared Fixtures
**What:** Central fixture file providing graph data, output dirs, domain resolution, and path setup
**When to use:** Every test file imports from conftest automatically

```python
# tests/conftest.py
import json
import shutil
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
FIXTURES_DIR = Path(__file__).parent / "fixtures"

# Path setup for project imports (no installed package)
sys.path.insert(0, str(PROJECT_ROOT / "core"))
sys.path.insert(0, str(PROJECT_ROOT / "domains" / "drug-discovery" / "validation"))
sys.path.insert(0, str(PROJECT_ROOT / "domains" / "drug-discovery"))
sys.path.insert(0, str(PROJECT_ROOT / "domains" / "contracts"))

# Availability flags
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


@pytest.fixture
def fixtures_dir():
    return FIXTURES_DIR


@pytest.fixture
def sample_graph_data():
    return json.loads((FIXTURES_DIR / "sample_graph_data.json").read_text())


@pytest.fixture
def sample_claims_layer():
    return json.loads((FIXTURES_DIR / "sample_claims_layer.json").read_text())


@pytest.fixture
def sample_output_dir(tmp_path):
    """Temp dir pre-populated with graph data, claims, communities."""
    for name in ["sample_graph_data.json", "sample_claims_layer.json", "sample_communities.json"]:
        src = FIXTURES_DIR / name
        if src.exists():
            target_name = name.replace("sample_", "").replace("graph_data", "graph_data")
            shutil.copy(src, tmp_path / name.replace("sample_", ""))
    ingested = tmp_path / "ingested"
    ingested.mkdir(exist_ok=True)
    for txt in (FIXTURES_DIR / "sample_ingested").glob("*.txt"):
        shutil.copy(txt, ingested / txt.name)
    return tmp_path
```

### Pattern 2: Pytest Marker Registration in pyproject.toml
**What:** Register custom markers to avoid warnings; configure test discovery
**When to use:** Project-wide pytest configuration

```toml
# pyproject.toml (new file, minimal)
[tool.pytest.ini_options]
markers = [
    "unit: Fast tests with no external dependencies",
    "integration: Tests requiring sift-kg and optional libs",
    "e2e: End-to-end pipeline tests",
]
testpaths = ["tests"]
```

### Pattern 3: Provenance Test Conversion (TEST-06)
**What:** Replace live HTTP calls with fixture-loaded data and mocked responses
**When to use:** Converting test_kg_provenance.py from server-dependent to offline

```python
# Before (live server):
@pytest.fixture(scope="module")
def graph_data():
    resp = requests.get(f"{BASE_URL}/api/graph", timeout=10)
    return resp.json()

# After (fixture-based):
@pytest.fixture(scope="module")
def graph_data():
    return json.loads((FIXTURES_DIR / "sample_graph_data.json").read_text())

# Chat responses mocked with pre-recorded answers
@pytest.fixture
def mock_chat_response():
    return "Pennsylvania Convention Center Authority is the licensor..."
```

### Pattern 4: Pydantic DocumentExtraction Schema (TEST-04)
**What:** Define Pydantic models matching the extraction JSON format, validate fixtures
**When to use:** Agent coverage testing

```python
from pydantic import BaseModel

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
```

### Anti-Patterns to Avoid
- **sys.path manipulation in every test file:** Move to conftest.py once, all tests inherit.
- **Tests dependent on live servers:** The 32 provenance tests currently need a running workbench. Convert to fixture-based.
- **Hardcoded fixture paths:** Use `FIXTURES_DIR` constant from conftest, not inline paths.
- **Mixing tiers in one file:** Unit tests should NEVER import sift-kg. Keep tier boundaries clean.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JSON schema validation | Custom dict-checking logic | Pydantic BaseModel | Handles nested validation, type coercion, clear error messages |
| Test fixture loading | Inline file reads in each test | conftest.py fixtures | DRY, consistent across tiers, automatic cleanup |
| Temporary directories | Manual mkdir/cleanup | pytest `tmp_path` fixture | Auto-cleanup, unique per test, built into pytest |
| HTTP mocking | Custom mock server | `unittest.mock.patch` on `requests.get/post` | Stdlib, well-understood, no new dependency |
| YAML validation | Manual key checking | `yaml.safe_load` + assert on structure | Already used throughout project |

## Common Pitfalls

### Pitfall 1: sys.path Conflicts Between Test Files
**What goes wrong:** Multiple test files manipulate `sys.path` differently, causing import resolution to depend on test execution order.
**Why it happens:** The project has no installable package (no pyproject.toml with package config). Tests use `sys.path.insert` to find modules.
**How to avoid:** Centralize ALL path manipulation in `conftest.py`. Remove `sys.path` lines from individual test files.
**Warning signs:** Tests pass individually but fail when run together.

### Pitfall 2: Provenance Test Conversion Losing Coverage
**What goes wrong:** Converting 32 provenance tests to fixture-based changes what they actually test -- they no longer verify the workbench API layer.
**Why it happens:** The original tests verify chat->graph->source tracing through a live API. Mocking removes the API verification.
**How to avoid:** Accept the scope change. The converted tests verify graph tracing logic (node lookup, edge traversal, entity matching). API testing is deferred to a future phase with the workbench.
**Warning signs:** Tests pass but don't exercise `find_node()`, `find_edges_between()` graph traversal functions.

### Pitfall 3: sift-kg Import Side Effects
**What goes wrong:** Unit tests that `import sift_kg` trigger heavy initialization (model loading, etc.) making the unit tier slow.
**Why it happens:** `sift_kg.load_domain()` and `sift_kg.KnowledgeGraph` are needed for integration tests but should never run in unit tier.
**How to avoid:** Unit tests must NEVER import sift-kg. Use `pytest.mark.skipif(not HAS_SIFTKG)` on integration tests. The existing UT-001 test already uses this pattern correctly.
**Warning signs:** `make test` (unit only) takes > 5 seconds.

### Pitfall 4: Missing Contract Domain Fixtures
**What goes wrong:** Contract domain tests fail because `contract_graph_data.json` fixture doesn't exist yet.
**Why it happens:** Existing fixtures are drug-discovery focused. The cross-domain test (TEST-07) needs contract domain graph data.
**How to avoid:** Create `contract_graph_data.json` and `contract_claims_layer.json` fixtures during Wave 0 setup. Use the contract entity/relation types from `domains/contracts/domain.yaml` (9 entity types, 9 relation types).
**Warning signs:** TEST-07 cannot run.

### Pitfall 5: build_extraction.py Requires Domain Resolution
**What goes wrong:** `write_extraction()` calls `resolve_domain()` which reads from `domains/` directory. If tests run from a different working directory, the path resolution breaks.
**Why it happens:** `domain_resolver.py` uses `Path(__file__).parent.parent / "domains"` which is relative to the source file location, not CWD. This should work, but test isolation can interfere.
**How to avoid:** Verify that `core/domain_resolver.py` `DOMAINS_DIR` resolves correctly in test context. The path is `Path(__file__).parent.parent / "domains"` which uses the source file's location, so it should be stable.
**Warning signs:** `FileNotFoundError: Domain 'drug-discovery' not found`.

## Code Examples

### Command Entry Point Mapping (TEST-02)
Each `/epistract:*` command maps to a Python function to test:

| Command | Entry Point | Test Strategy |
|---------|------------|---------------|
| `/epistract:setup` | `scripts/setup.sh` | Skip (shell script, not Python testable) |
| `/epistract:ingest` | `core/ingest_documents.py` | Integration: parse sample docs |
| `/epistract:build` | `core/run_sift.py cmd_build()` | Integration: build from fixture extractions |
| `/epistract:query` | `core/run_sift.py cmd_search()` | Integration: search fixture graph |
| `/epistract:export` | `core/run_sift.py cmd_export()` | Integration: export fixture graph |
| `/epistract:view` | `core/run_sift.py cmd_view()` | Skip (opens browser, visual) |
| `/epistract:validate` | `domains/drug-discovery/validate_molecules.py` | Unit: pattern scan + validation |
| `/epistract:epistemic` | `core/label_epistemic.py analyze_epistemic()` | Integration: analyze fixture graph |
| `/epistract:ask` | Workbench chat API | Skip (needs running server) |
| `/epistract:dashboard` | Workbench web server | Skip (needs running server) |

Testable commands: 7 of 10. The 3 skipped (setup, view, ask/dashboard) require shell execution or running servers.

### E2E Pipeline Test Pattern (TEST-05)
```python
@pytest.mark.e2e
def test_e2e_pipeline(tmp_path):
    """Full lifecycle: extraction JSON -> graph build -> epistemic -> export."""
    # 1. Write pre-recorded extraction to output dir
    extraction = load_fixture("sample_extraction_drug.json")
    (tmp_path / "extractions").mkdir()
    (tmp_path / "extractions" / "test_doc.json").write_text(json.dumps(extraction))

    # 2. Build graph from extraction
    cmd_build(str(tmp_path), domain_name="drug-discovery")
    assert (tmp_path / "graph_data.json").exists()

    # 3. Label communities
    label_communities(tmp_path)
    assert (tmp_path / "communities.json").exists()

    # 4. Analyze epistemic layer
    result = analyze_epistemic(tmp_path)
    assert (tmp_path / "claims_layer.json").exists()

    # 5. Export
    cmd_export(str(tmp_path), "json")
    # Verify export file exists
```

### Cross-Domain Verification Pattern (TEST-07)
```python
@pytest.mark.integration
def test_cross_domain_both_produce_valid_graphs(tmp_path):
    """Both drug-discovery and contracts domains produce valid graphs through same pipeline."""
    for domain_name in ["drug-discovery", "contracts"]:
        domain_dir = tmp_path / domain_name
        domain_dir.mkdir()
        # Load domain-specific extraction fixture
        extraction = load_fixture(f"sample_extraction_{domain_name.replace('-', '_')}.json")
        (domain_dir / "extractions").mkdir()
        (domain_dir / "extractions" / "test.json").write_text(json.dumps(extraction))
        # Build through same entry point
        cmd_build(str(domain_dir), domain_name=domain_name)
        graph = json.loads((domain_dir / "graph_data.json").read_text())
        assert len(graph["nodes"]) > 0
        assert "metadata" in graph
```

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.2.1 |
| Config file | none -- see Wave 0 (create pyproject.toml) |
| Quick run command | `python -m pytest tests/test_unit.py -m unit -v` |
| Full suite command | `python -m pytest tests/ -v` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TEST-01 | V1 regression (46 existing tests pass) | unit | `python -m pytest tests/test_unit.py -m unit -v` | Existing (needs markers) |
| TEST-02 | Command coverage (7 entry points) | integration | `python -m pytest tests/test_integration.py -m integration -v` | Wave 0 |
| TEST-03 | Skill/domain YAML loads + validates | unit | `python -m pytest tests/test_unit.py -k "domain_yaml or skill" -v` | Partially existing (UT-001, UT-042) |
| TEST-04 | Agent output schema validation | unit | `python -m pytest tests/test_unit.py -k "extraction_schema" -v` | Wave 0 |
| TEST-05 | E2E pipeline lifecycle | e2e | `python -m pytest tests/test_e2e.py -m e2e -v` | Wave 0 |
| TEST-06 | KG provenance (32 tests fixture-based) | integration | `python -m pytest tests/test_kg_provenance.py -m integration -v` | Existing (needs conversion) |
| TEST-07 | Cross-domain verification | integration | `python -m pytest tests/test_integration.py -k "cross_domain" -v` | Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/test_unit.py -m unit -v --tb=short`
- **Per wave merge:** `python -m pytest tests/ -v --tb=short`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/conftest.py` -- shared fixtures, path setup, availability flags
- [ ] `pyproject.toml` -- pytest marker registration, testpaths config
- [ ] `tests/test_integration.py` -- integration tier test file
- [ ] `tests/test_e2e.py` -- E2E tier test file
- [ ] `tests/fixtures/contract_graph_data.json` -- contract domain graph fixture
- [ ] `tests/fixtures/contract_claims_layer.json` -- contract domain claims fixture
- [ ] `tests/fixtures/sample_extraction_drug.json` -- pre-recorded drug extraction for E2E
- [ ] `tests/fixtures/sample_extraction_contract.json` -- pre-recorded contract extraction for E2E
- [ ] Makefile update -- add `test-integration` and `test-all` targets

## Project Constraints (from CLAUDE.md)

- **Package management:** `uv` for Python (not pip directly)
- **Testing:** `pytest` (confirmed, already in use)
- **Linting:** `ruff check` and `ruff format`
- **Python:** 3.11+, type hints with `|` union syntax
- **Paths:** Always use `pathlib.Path`, never `os.path`
- **Imports:** Wrap optional dependencies in try/except, set availability flags
- **Assertions:** Use f-string descriptive messages
- **JSON:** `indent=2` for all JSON output
- **Naming:** snake_case throughout, test IDs with UT-NNN pattern
- **Makefile:** Must have standard targets (help, install, test, lint, format, clean)

## Sources

### Primary (HIGH confidence)
- Codebase analysis: `tests/test_unit.py` (46 tests, 1118 lines), `tests/test_kg_provenance.py` (32 tests, 472 lines), `tests/test_workbench.py` (13 tests, 260 lines)
- Codebase analysis: `core/` directory (10 Python modules), `domains/` directory (2 domains), `commands/` directory (10 commands)
- Codebase analysis: `tests/fixtures/` (9 fixture files + 4 ingested text files)
- CONTEXT.md: 10 locked decisions (D-01 through D-10)
- `Makefile`: Current `test` target runs only `tests/test_unit.py`

### Secondary (MEDIUM confidence)
- pytest 8.2.1 documentation for markers, conftest patterns, marker registration

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all tools already in project, no new dependencies
- Architecture: HIGH -- clear existing patterns to extend, well-documented decisions
- Pitfalls: HIGH -- identified from actual code analysis (sys.path issues, sift-kg imports, missing fixtures)

**Research date:** 2026-04-03
**Valid until:** 2026-05-03 (stable -- test infrastructure doesn't change fast)
