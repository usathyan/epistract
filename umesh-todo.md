# V2 Scenario Validation — Manual TODO

## Prerequisites

- Claude Code with epistract plugin installed
- `ANTHROPIC_API_KEY` set (or equivalent for your LLM provider)
- `/epistract:setup` already run

## The 6 Drug Discovery Scenarios

Each lives in `tests/corpora/` with `docs/` (input) and `output/` (V1 results):

| # | Directory | Topic | Docs |
|---|-----------|-------|------|
| S1 | `01_picalm_alzheimers` | PICALM/Alzheimer's | 15 |
| S2 | `02_kras_g12c_landscape` | KRAS G12C | 16 |
| S3 | `03_rare_disease` | Rare Disease | 15 |
| S4 | `04_immunooncology` | Immuno-Oncology | 16 |
| S5 | `05_cardiovascular` | Cardiovascular | 15 |
| S6 | `06_glp1_landscape` | GLP-1 | 34 |

## For each scenario (S1-S6):

```bash
# Example for S1 — repeat for S2-S6, changing paths
/epistract:ingest --domain drug-discovery --input tests/corpora/01_picalm_alzheimers/docs/
/epistract:build
/epistract:epistemic
/epistract:validate
/epistract:view
```

Output lands in `./epistract-output/` by default. To preserve V1 output, use `--output tests/corpora/01_picalm_alzheimers/output-v2/`.

## Contracts (optional — needs STA data)

```bash
/epistract:ingest --domain contracts --input ./sample-contracts/
/epistract:build --domain contracts
/epistract:epistemic --domain contracts
/epistract:view
```

## After all runs — validate against V1 baselines

```bash
python tests/regression/run_regression.py --baselines tests/baselines/v1/ --output-dir tests/corpora/
```

Expected: all 6 drug discovery scenarios show **PASS** (>=80% of V1 counts).

## Save V2 baselines (once validation passes)

```bash
python tests/regression/run_regression.py --update-baselines
make regression  # verify V2 baselines
```

## Resume GSD execution

After completing the above, resume phase 11:

```bash
/gsd:execute-phase 11
```

This will pick up from plan 11-03 (Task 1 checkpoint). Respond with:
- `"validated"` — all scenarios passed
- `"validated-no-contracts"` — drug discovery passed, no STA data

Plan 11-04 (git squash + PR + v2.0.0 tag) runs after 11-03 completes.
