---
phase: 21
slug: clinicaltrials-pubchem-domain
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-17
---

# Phase 21 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `tests/test_unit.py` (existing) |
| **Quick run command** | `python -m pytest tests/test_unit.py -k "clinicaltrials" -v` |
| **Full suite command** | `python -m pytest tests/test_unit.py -v` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_unit.py -k "clinicaltrials" -v`
- **After every plan wave:** Run `python -m pytest tests/test_unit.py -v`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 21-01-01 | 01 | 1 | CTDM-01 | — | N/A | unit | `pytest -k "test_clinicaltrials_domain_yaml"` | ❌ W0 | ⬜ pending |
| 21-01-02 | 01 | 1 | CTDM-02 | — | N/A | unit | `pytest -k "test_clinicaltrials_skill"` | ❌ W0 | ⬜ pending |
| 21-01-03 | 01 | 1 | CTDM-03 | — | N/A | unit | `pytest -k "test_clinicaltrials_epistemic"` | ❌ W0 | ⬜ pending |
| 21-02-01 | 02 | 2 | CTDM-04 | — | API errors non-fatal | unit | `pytest -k "test_clinicaltrials_enrichment_ct"` | ❌ W0 | ⬜ pending |
| 21-02-02 | 02 | 2 | CTDM-05 | — | API errors non-fatal | unit | `pytest -k "test_clinicaltrials_enrichment_pubchem"` | ❌ W0 | ⬜ pending |
| 21-02-03 | 02 | 2 | CTDM-06 | — | --enrich optional | unit | `pytest -k "test_clinicaltrials_enrichment_report"` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/test_unit.py` — add stubs for CTDM-01 through CTDM-06 (domain loading, enrichment API calls with mocks, report generation)
- [x] `tests/fixtures/clinicaltrials/` — sample CT protocol document fixture, mock ClinicalTrials.gov API response, mock PubChem PUG REST response

*Wave 0 installs test stubs; actual passing tests come in subsequent waves.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Live ClinicalTrials.gov API enrichment returns correct trial metadata | CTDM-04 | Requires live network, real NCT IDs | Run `/epistract:ingest --domain clinicaltrials --enrich` on a document containing NCT IDs; verify `_enrichment_report.json` shows >0 trials enriched |
| Live PubChem enrichment returns ConnectivitySMILES for known compounds | CTDM-05 | Requires live network | Run `/epistract:ingest --domain clinicaltrials --enrich` on a document with known compound names (ibuprofen, remdesivir); verify `_enrichment_report.json` shows compounds enriched with SMILES |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** approved — Wave 0 tests landed in Plan 21-00 on 2026-04-18
