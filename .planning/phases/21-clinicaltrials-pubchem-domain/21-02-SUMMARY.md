---
phase: 21-clinicaltrials-pubchem-domain
plan: "02"
subsystem: domains/clinicaltrials
tags: [enrichment, clinicaltrials, pubchem, api-integration, wave-3]
dependency_graph:
  requires: [21-00, 21-01]
  provides: [enrich_graph, _fetch_ct_gov, _fetch_pubchem, _extract_nct_id, --enrich-flag]
  affects: [commands/ingest.md, domains/clinicaltrials/enrich.py]
tech_stack:
  added: [requests, requests.utils.quote, exponential-backoff]
  patterns: [non-blocking-enrichment, graceful-degradation, module-level-mock-target]
key_files:
  created:
    - domains/clinicaltrials/enrich.py
  modified:
    - commands/ingest.md
decisions:
  - "_fetch_pubchem reads ConnectivitySMILES response key (not CanonicalSMILES) — PubChem API quirk documented in 21-RESEARCH.md Pitfall 2"
  - "enrich_graph falls back to raw JSON node iteration when sift-kg is unavailable (ImportError guard)"
  - "_write_report wrapped in try/except OSError so nonexistent output_dir prints zero report instead of crashing"
  - "module-level `import requests` (not `from requests import ...`) required so unittest.mock.patch.object(enrich.requests, 'get') intercepts calls"
metrics:
  duration: 3min
  completed: "2026-04-18"
  tasks_completed: 2
  files_created: 1
  files_modified: 1
---

# Phase 21 Plan 02: ClinicalTrials.gov + PubChem Enrichment Summary

**One-liner:** Post-build graph enrichment for the clinicaltrials domain — CT.gov v2 Trial metadata and PubChem molecular data patched onto graph nodes via non-blocking API calls with exponential backoff.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create domains/clinicaltrials/enrich.py | 76b4bd7 | domains/clinicaltrials/enrich.py |
| 2 | Wire --enrich flag into commands/ingest.md (Step 5.5) | b621e16 | commands/ingest.md |

## What Was Built

### Task 1: domains/clinicaltrials/enrich.py (285 lines)

Public API:
- `_extract_nct_id(text)` — regex `NCT\d{8}` extracts NCT ID from any string, returns None if absent
- `_fetch_ct_gov(nct_id)` — CT.gov v2 `/api/v2/studies/{nctId}` with 15s timeout; returns flat dict with `ct_overall_status`, `ct_phase`, `ct_enrollment`, `ct_start_date`, `ct_completion_date`, `ct_brief_title`; returns None on 404 or any RequestException
- `_fetch_pubchem(compound_name)` — PubChem PUG REST with `requests.utils.quote` URL sanitization, 30s timeout, 3x exponential backoff on 429; reads `ConnectivitySMILES` key (not `CanonicalSMILES`) into `canonical_smiles`; returns None on 404 or retry exhaustion
- `enrich_graph(output_dir, domain)` — loads `graph_data.json` via `sift_kg.KnowledgeGraph.load()`, iterates nodes, patches Trial + Compound nodes, saves, writes `<output_dir>/extractions/_enrichment_report.json`

Security mitigations applied per threat model:
- T-21-02-01: `requests.utils.quote(compound_name)` prevents URL injection
- T-21-02-02: `NCT_PATTERN = re.compile(r"NCT\d{8}")` constrains CT.gov URL inputs
- T-21-02-03: `PUBCHEM_MAX_RETRIES = 3` caps retry loop
- T-21-02-04: `CTGOV_TIMEOUT = 15`, `PUBCHEM_TIMEOUT = 30` on every request
- T-21-02-07: `_write_report` wrapped in OSError guard; CLI smoke test prints zero report on nonexistent dir

### Task 2: commands/ingest.md edits

- Added `--enrich` argument documentation to Arguments block (clinicaltrials domain scope only)
- Inserted new `### Step 5.5: Enrich Knowledge Graph` section between Step 5 (build) and Step 6 (view)
- Step 5.5 invokes `python3 ${CLAUDE_PLUGIN_ROOT}/domains/clinicaltrials/enrich.py <output_dir>` only when both `--enrich` and `--domain clinicaltrials` (or aliases) are present
- Step 5.5 explicitly states non-blocking behavior — pipeline continues to Step 6 on failure
- Updated Step 7 to include enrichment hit rates from `_enrichment_report.json`

## Verification Results

```
python3 -m pytest tests/test_unit.py -k "test_ctdm04 or test_ctdm05 or test_ctdm06" -v
6 passed, 52 deselected in 3.45s

python3 -m pytest tests/test_unit.py -v
56 passed, 2 skipped in 20.01s  (no regressions)

python3 domains/clinicaltrials/enrich.py /nonexistent/dir
→ prints zero-count JSON report, exits 0 (graceful absence-of-graph handling)
```

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] _write_report crashed on nonexistent output_dir**
- **Found during:** Task 1 smoke test (`python3 domains/clinicaltrials/enrich.py /nonexistent/dir`)
- **Issue:** `_write_report` called `extractions_dir.mkdir(parents=True, exist_ok=True)` which raised `PermissionError` when the parent dir didn't exist on the root filesystem
- **Fix:** Wrapped `_write_report` body in `try/except OSError: return None` so the function degrades gracefully
- **Files modified:** domains/clinicaltrials/enrich.py
- **Commit:** 76b4bd7 (included in Task 1 commit)

## Known Stubs

None — all enrichment functions are fully wired to live APIs (mocked in tests via `patch.object`).

## Threat Flags

None — all new network surface (CT.gov, PubChem) was pre-identified in the plan's threat model and mitigated.

## Self-Check: PASSED

- [x] `domains/clinicaltrials/enrich.py` exists: FOUND
- [x] `wc -l domains/clinicaltrials/enrich.py` = 285 (>= 180)
- [x] commit 76b4bd7 exists: FOUND
- [x] commit b621e16 exists: FOUND
- [x] All 6 CTDM-04/05/06 tests green
- [x] Full suite 56 passed, 2 skipped, 0 failed
