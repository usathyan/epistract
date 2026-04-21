# Phase 17 Deferred Items

## Pre-existing test failures (out of scope)

### `tests/test_workbench.py::test_schema_expansion`

**Status:** Pre-existing failure on HEAD (verified via `git stash && pytest` during Plan 17-01 execution).

**Root cause:** Test looks for `skills/contract-extraction/domain.yaml` — path no longer exists after Phase 6 repo reorganization (domains moved to `domains/contracts/domain.yaml`). Test's `if not schema_path.exists(): pytest.skip(...)` guard FAILS to skip because the test is running from the repo root where `skills/contract-extraction/domain.yaml` is checked relatively — but the `pytest.skip` branch never fires because the assertion is reached.

Actually: the `skip` DOES fire on fresh clones, but this machine has the legacy schema at that path (or the assertion wording is misleading). Regardless: the assertion-failure is pre-existing and unrelated to FIDL-06.

**Why not fixed in 17-01:** Out of Phase 17 scope. Plan 17-01 is a metadata-propagation change — does not touch contract domain schemas, test infrastructure, or skill paths. Fixing this test would require either deleting it (it refers to a Phase-6-era `skills/` path that no longer matches the `domains/` reorg) or updating the schema to include COMMITTEE/PERSON/EVENT/STAGE/ROOM entity types — neither action is on FIDL-06's critical path.

**Recommendation:** Delete `test_schema_expansion` in a quick cleanup PR, or update it to point at `domains/contracts/domain.yaml` with entity-type assertions aligned to the actual current schema (PARTY, CONTRACT, OBLIGATION, ...). Filed for a future quick task.
