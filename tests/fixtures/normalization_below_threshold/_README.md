# Phase 13 --fail-threshold Abort Fixture

10 files total: 2 recoverable + 8 unrecoverable.
Post-normalize pass rate: 2/10 = 0.20, below the default --fail-threshold 0.95.
Pipeline MUST abort with clear error before run_sift.py build is invoked.

Unrecoverable failure modes:
- bad_01: empty object (no required fields)
- bad_02: entities is not a list
- bad_03: entity missing name
- bad_04: entity missing both type AND entity_type (normalization cannot rescue)
- bad_05: malformed JSON (unparseable)
- bad_06: relation missing source_entity
- bad_07: relation missing target_entity
- bad_08: confidence 5.0 (out of range [0.0, 1.0])
