# Sample Markdown Document

This is a minimal markdown fixture used by Phase 15 FT-013 to prove that
`discover_corpus` picks up `.md` files after the FIDL-04 delegation to
sift-kg's Kreuzberg extractor.

## Section

Markdown was one of the extensions silently excluded by the pre-Phase-15
`SUPPORTED_EXTENSIONS` hardcoded allowlist (only 9 extensions survived
that filter; `.md` was not among them). After Plan 15-01, `.md` is one of
the >=28 text-class extensions resolved at runtime from
`KreuzbergExtractor.supported_extensions()`.

## Assertions This Fixture Enables

- FT-013: this file is discovered by `discover_corpus`.
- FT-013: this file parses to text containing the phrase "Phase 15 FT-013".
- FT-013: the resulting `triage.json` lists this file with
  `parse_type == "text"` and an empty `warnings[]` list.
