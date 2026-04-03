# Phase 7: Testing Framework - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-03
**Phase:** 07-testing-framework
**Areas discussed:** Test scope & tiers, Test data strategy, Command & skill testing, CI & execution

---

## Test Scope & Tiers

### Test Tier Structure

| Option | Description | Selected |
|--------|-------------|----------|
| Three tiers (Recommended) | Unit → Integration → E2E with pytest markers and Makefile targets | ✓ |
| Two tiers | Fast (unit+integration) → Live. Simpler but less granular | |
| Single suite with skips | Current pattern, one file, skipif decorators. No tier control | |

**User's choice:** Three tiers
**Notes:** `make test` = unit only, `make test-integration` = integration, `make test-all` = everything

### Provenance Tests

| Option | Description | Selected |
|--------|-------------|----------|
| Fixture-based mock (Recommended) | Load graph/claims from fixtures, mock HTTP. Offline and fast | ✓ |
| Live server required | Keep as-is, hit localhost:8000. @pytest.mark.live | |
| Docker-based | Spin up workbench in Docker for test runs | |

**User's choice:** Fixture-based mock
**Notes:** Validates tracing logic without needing a live server

---

## Test Data Strategy

### Fixture Organization

| Option | Description | Selected |
|--------|-------------|----------|
| Shared fixtures dir (Recommended) | tests/fixtures/ with domain-labeled files | ✓ |
| Domain-scoped fixtures | tests/fixtures/drug-discovery/ and tests/fixtures/contracts/ | |
| Inline fixtures | Generate fixture data in conftest.py factory functions | |

**User's choice:** Shared fixtures dir
**Notes:** Both domains share the same fixture loading pattern

### E2E LLM Handling

| Option | Description | Selected |
|--------|-------------|----------|
| Pre-recorded extractions (Recommended) | Saved extraction JSON as golden outputs. No LLM calls | ✓ |
| Live LLM with tiny corpus | Actually call Claude. Costs money, non-deterministic | |
| Mock LLM responses | Intercept LLM calls, return canned JSON | |

**User's choice:** Pre-recorded extractions
**Notes:** Pipeline runs graph-build → epistemic → export from pre-extracted data

---

## Command & Skill Testing

### Command Coverage Definition

| Option | Description | Selected |
|--------|-------------|----------|
| Test underlying Python (Recommended) | Test Python entry points each command invokes | ✓ |
| Script-level integration | Bash scripts invoking python core/run_sift.py directly | |
| Smoke test via Claude Code | Manual test protocol, document pass/fail | |

**User's choice:** Test underlying Python
**Notes:** Command coverage = every Python function a command would invoke runs without error

### Agent Coverage

| Option | Description | Selected |
|--------|-------------|----------|
| Schema validation on fixtures (Recommended) | Pydantic models validate extraction JSON format | ✓ |
| Golden output comparison | Structure comparison against known-good files | |
| Live agent test | Run extractor via Claude API. Requires API key | |

**User's choice:** Schema validation on fixtures
**Notes:** Proves format correctness without invoking agents

---

## CI & Execution

### CI Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Local only for now (Recommended) | Focus on test suite quality. CI is future scope | ✓ |
| Basic GitHub Actions | Minimal CI: install deps, run unit tests on push | |
| Full CI matrix | Python 3.11/3.12/3.13 matrix with optional dep variants | |

**User's choice:** Local only
**Notes:** Avoids scope creep into CI config, secrets management

### Optional Dependencies

| Option | Description | Selected |
|--------|-------------|----------|
| Skip with markers (Recommended) | Current skipif pattern. Unit tier always succeeds | ✓ |
| Require all for integration | Forces full install for integration tier | |
| Separate test groups | pytest groups: core, rdkit, biopython, siftkg | |

**User's choice:** Skip with markers
**Notes:** `make test` always succeeds regardless of installed optional deps

---

## Claude's Discretion

- Test file organization (single vs multiple files per tier)
- conftest.py design and shared helpers
- Exact pytest marker names
- pyproject.toml pytest config vs Makefile-only
- Test naming convention

## Deferred Ideas

- GitHub Actions CI setup
- Test coverage reporting
- Docker-based test environment
- Live LLM integration tests
