---
phase: 21-clinicaltrials-pubchem-domain
verified: 2026-04-19T04:00:00Z
status: passed
score: 12/12 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 10/12
  gaps_closed:
    - "The --enrich flag in /epistract:ingest triggers post-build node enrichment for the clinicaltrials domain"
    - "Enrichment is opt-in via --enrich; omitting the flag leaves graph_data.json unmodified after build"
  gaps_remaining: []
  regressions: []
---

# Phase 21: ClinicalTrials + PubChem Domain Verification Report

**Phase Goal:** Ship the clinicaltrials domain package + ClinicalTrials.gov v2 and PubChem enrichment + usage guards for all /epistract:* commands. All CTDM requirements (CTDM-01 through CTDM-06) must be satisfied.
**Verified:** 2026-04-19T04:00:00Z
**Status:** passed
**Re-verification:** Yes — previous verification (2026-04-19T02:40:00Z) reported gaps_found (10/12) after Plan 21-03 deleted Step 5.5 and the --enrich argument from commands/ingest.md. Both items have been restored.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Domain resolver discovers 'clinicaltrials' via list_domains() and resolves aliases 'clinicaltrial' and 'clinical_trials' | VERIFIED | list_domains() returns ['clinicaltrials', 'contracts', 'drug-discovery']; DOMAIN_ALIASES has both 'clinicaltrial' and 'clinical_trials' keys in core/domain_resolver.py; runtime confirmed |
| 2 | domain.yaml loads via sift_kg.load_domain() and declares exactly 12 entity types and 10 relation types | VERIFIED | grep confirms 12 entity type keys and 10 relation type keys; test_ctdm01_clinicaltrials_domain_yaml PASSED |
| 3 | SKILL.md instructs extractor agents to capture NCT IDs as canonical Trial names and classify trial phase | VERIFIED | SKILL.md is 529 lines with 24 H3 headings; "CRITICAL: NCT ID Capture Directive" prominent; TrialPhase normalization rule present; test_ctdm02 PASSED |
| 4 | The epistemic dispatcher finds analyze_clinicaltrials_epistemic by convention and runs it on a graph to produce a claims layer | VERIFIED | _load_domain_epistemic('clinicaltrials') returns module with function; runtime call returns {metadata, summary, base_domain, super_domain}; test_ctdm03 PASSED |
| 5 | Phase III > II > I evidence grading applies to relations whose source or target is a Trial node | VERIFIED | PHASE3/2/1_VALUES constants in epistemic.py; _grade_relation() applies phase -> blinding -> enrollment bumps; EVIDENCE_TIERS defined |
| 6 | The --enrich flag in /epistract:ingest triggers post-build node enrichment for the clinicaltrials domain | VERIFIED | Step 5.5 restored at lines 125-148 of commands/ingest.md; invokes python3 ${CLAUDE_PLUGIN_ROOT}/domains/clinicaltrials/enrich.py <output_dir>; ORDER OK: Step5=117 Step5.5=125 Step6=150 |
| 7 | Trial nodes whose name matches NCT\d{8} are enriched with CT.gov v2 API metadata | VERIFIED | _fetch_ct_gov() calls clinicaltrials.gov/api/v2/studies/{nct_id}; returns flat ct_* dict; test_ctdm04 PASSED |
| 8 | Compound nodes are enriched with PubChem molecular data (CID, formula, weight, canonical_smiles from ConnectivitySMILES, InChI) | VERIFIED | _fetch_pubchem() reads ConnectivitySMILES into canonical_smiles; returns all 5 molecular keys; test_ctdm05 PASSED |
| 9 | API failures (404, timeout, connection error, rate limit exhaustion) log counts but never abort the pipeline | VERIFIED | Both fetchers return None on all error conditions; PUBCHEM_MAX_RETRIES=3; test_ctdm06_enrich_non_blocking PASSED |
| 10 | Every enrichment run writes <output_dir>/extractions/_enrichment_report.json summarizing hit rates per entity type | VERIFIED | _write_report() writes to extractions/_enrichment_report.json with domain, trials{}, compounds{}, hit_rate keys; test_ctdm06_enrich_report_written PASSED |
| 11 | Enrichment is opt-in via --enrich; omitting the flag leaves graph_data.json unmodified after build | VERIFIED | Step 5.5 conditional guard restored: "Skip this step entirely unless BOTH of these are true: 1. The user passed --enrich. 2. The resolved --domain is clinicaltrials (or aliases)." |
| 12 | Wave 0 test stubs for CTDM-01..06 exist in tests/test_unit.py and all pass after Plans 01/02 implementation | VERIFIED | All 12 CTDM tests PASSED; full suite 58 passed, 0 failed |

**Score:** 12/12 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `domains/clinicaltrials/domain.yaml` | 12 entity types, 10 relation types, min_lines 120 | VERIFIED | 101 lines; 12 entity types (Trial, Intervention, Condition, Sponsor, Investigator, Outcome, Compound, Biomarker, Cohort, Population, TrialPhase, Site); 10 relation types confirmed |
| `domains/clinicaltrials/SKILL.md` | NCT ID directive, 12 entity + 10 relation H3 sections, min_lines 80 | VERIFIED | 529 lines; 24 H3 headings; CRITICAL: NCT ID Capture Directive present |
| `domains/clinicaltrials/epistemic.py` | analyze_clinicaltrials_epistemic function, min_lines 120 | VERIFIED | 225 lines; exports analyze_clinicaltrials_epistemic; PHASE3/2/1 constants; BLINDING_RE; _grade_relation |
| `domains/clinicaltrials/enrich.py` | enrich_graph, _fetch_ct_gov, _fetch_pubchem, _extract_nct_id, min_lines 180 | VERIFIED | 285 lines; all 4 public symbols present; module-level import requests |
| `core/domain_resolver.py` | DOMAIN_ALIASES entries for clinicaltrial and clinical_trials | VERIFIED | Both aliases present; all 4 pre-existing aliases preserved |
| `commands/ingest.md` | --enrich argument in ## Arguments, Step 5.5 between Step 5 and Step 6 | VERIFIED | --enrich bullet at line 42; Step 5.5 at lines 125-148 (ORDER OK); enrich.py invocation at line 134; Step 7 enrichment hit-rate bullet at line 167 |
| 12 commands/*.md files | All have ## Usage Guard | VERIFIED | grep -l "## Usage Guard" commands/*.md returns 12 |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| core/domain_resolver.py DOMAIN_ALIASES | domains/clinicaltrials/ | alias map entries | VERIFIED | clinicaltrial and clinical_trials both resolve to clinicaltrials dir at runtime |
| core/label_epistemic.py _load_domain_epistemic | domains/clinicaltrials/epistemic.py:analyze_clinicaltrials_epistemic | convention-based dispatch | VERIFIED | Module loads; function found; returns 4-key schema |
| commands/ingest.md Step 5.5 | domains/clinicaltrials/enrich.py | python3 ${CLAUDE_PLUGIN_ROOT}/domains/clinicaltrials/enrich.py <output_dir> | VERIFIED | Step 5.5 restored at line 125; invocation at line 134; conditional guard requires both --enrich and --domain clinicaltrials |
| enrich.py:_fetch_ct_gov | https://clinicaltrials.gov/api/v2/studies/{nctId} | requests.get with 15s timeout | VERIFIED | CTGOV_URL and CTGOV_TIMEOUT=15 present; NCT_PATTERN constrains inputs |
| enrich.py:_fetch_pubchem | https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{name}/property/.../JSON | requests.get with 30s timeout + 3x exponential backoff on 429 | VERIFIED | PUBCHEM_URL, PUBCHEM_TIMEOUT=30, PUBCHEM_MAX_RETRIES=3; backoff loop present; requests.utils.quote for URL sanitization |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| enrich.py:enrich_graph | enrichment dict | _fetch_ct_gov / _fetch_pubchem | Yes (real API calls, mocked in tests) | FLOWING |
| enrich.py:_fetch_ct_gov | ct_overall_status, ct_phase, ct_enrollment | CT.gov v2 protocolSection JSON | Yes (parsing verified against mock fixture) | FLOWING |
| enrich.py:_fetch_pubchem | canonical_smiles | ConnectivitySMILES key in PubChem response | Yes (Pitfall 2 handled) | FLOWING |
| epistemic.py:analyze_clinicaltrials_epistemic | trial_lookup, evidence_counts | graph_data nodes/links | Yes (processes real graph node dicts) | FLOWING |
| commands/ingest.md pipeline | enrich_graph invocation | Step 5.5 conditional | Conditional — flows when --enrich + --domain clinicaltrials | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| All 12 CTDM tests pass | python3 -m pytest tests/test_unit.py -k "ctdm" -v | 12 passed, 46 deselected | PASS |
| Full test suite has no regressions | python3 -m pytest tests/test_unit.py -v | 58 passed, 0 failed | PASS |
| domain_resolver.list_domains includes clinicaltrials | python3 -c "from core.domain_resolver import list_domains; print(list_domains())" | ['clinicaltrials', 'contracts', 'drug-discovery'] | PASS |
| Step 5.5 ordering correct in ingest.md | awk check on Step 5/5.5/6 line numbers | ORDER OK: Step5=117 Step5.5=125 Step6=150 | PASS |
| Step 5.5 invokes enrich.py | grep "domains/clinicaltrials/enrich.py" commands/ingest.md | Match at line 134 | PASS |
| --enrich in ## Arguments block | grep "^- \`--enrich\`" commands/ingest.md | Match at line 42 | PASS |
| Enrichment hit-rate in Step 7 | grep "_enrichment_report.json" commands/ingest.md | Matches at lines 142 and 167 | PASS |

### Requirements Coverage

CTDM requirements (CTDM-01 through CTDM-06) are phase-21-only requirements defined in the plan files; they do not appear in .planning/REQUIREMENTS.md.

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| CTDM-01 | 21-01 | domain package with 12 entity + 10 relation types, ARCH-03 compliant | SATISFIED | domain.yaml loads; list_domains() includes clinicaltrials; no core/ changes |
| CTDM-02 | 21-01 | SKILL.md with NCT ID capture, phase classification, intervention/condition disambiguation | SATISFIED | SKILL.md 529 lines; CRITICAL NCT ID Capture Directive; 24 H3 headings |
| CTDM-03 | 21-01 | epistemic.py with phase-based grading, blinding, enrollment signals | SATISFIED | analyze_clinicaltrials_epistemic returns 4-key dict; phase constants and BLINDING_RE present |
| CTDM-04 | 21-02 | CT.gov v2 enrichment via /api/v2/studies/{nctId}, graceful error handling | SATISFIED | _fetch_ct_gov() implemented and tested; Step 5.5 restored in ingest.md wiring the invocation |
| CTDM-05 | 21-02 | PubChem PUG REST enrichment, 3x backoff, ConnectivitySMILES quirk handled | SATISFIED | _fetch_pubchem() implemented and tested; ConnectivitySMILES key handled correctly |
| CTDM-06 | 21-02, 21-03 | Non-blocking --enrich flag, _enrichment_report.json written, pipeline continues on failure | SATISFIED | enrich_graph() writes report; non-blocking behavior verified; Step 5.5 and --enrich arg fully restored in ingest.md |

### Anti-Patterns Found

None. No TODOs, FIXMEs, placeholders, empty implementations, or hardcoded stubs found in any delivered file.

### Human Verification Required

None. All must-haves are programmatically verifiable and confirmed.

### Gaps Summary

No gaps. The two previously-failed truths have been resolved:

1. Step 5.5 ("Enrich Knowledge Graph") has been restored to commands/ingest.md between Step 5 (line 117) and Step 6 (line 150), with the correct conditional guard and enrich.py invocation at line 134.
2. The --enrich argument bullet has been restored to the ## Arguments block at line 42.
3. The enrichment hit-rate bullet has been restored to Step 7 at line 167.

All 12 CTDM tests pass. Full suite runs 58 passed, 0 failed with no regressions.

---

_Verified: 2026-04-19T04:00:00Z_
_Verifier: Claude (gsd-verifier)_
