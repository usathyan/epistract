# Coding Conventions

**Analysis Date:** 2026-03-29

## Language & Tooling

**Primary Language:** Python 3.11+

**Code Formatting:**
- Tool: `ruff format`
- Commands: `ruff format scripts/ tests/` in Makefile
- No explicit `.ruff.toml` found — uses ruff defaults

**Linting:**
- Tool: `ruff check`
- Command: `ruff check scripts/ tests/` in Makefile
- Enforces standard Python conventions

## Naming Patterns

**Module/File Names:**
- Descriptive snake_case: `validate_smiles.py`, `scan_patterns.py`, `build_extraction.py`
- Scripts in `scripts/` prefix with action verb: `run_sift.py`, `label_communities.py`, `label_epistemic.py`
- Validation scripts in `skills/drug-discovery-extraction/validation-scripts/`

**Function Names:**
- snake_case throughout
- Descriptive: `write_extraction()`, `validate_smiles()`, `scan_text()`, `detect_type()`
- Private functions prefixed with single underscore: `_normalize_fields()`, `_import_sift()`, `_generate_label()`, `_clean_name()`
- Commands in sift wrapper use prefix: `cmd_build()`, `cmd_view()`, `cmd_export()`, `cmd_info()`, `cmd_search()`

**Variable Names:**
- snake_case: `output_dir`, `entity_type`, `pattern_type`, `doc_id`, `smiles`
- Type hints used throughout: `entities: list[dict]`, `text: str`, `pattern: re.Pattern`
- Acronyms expanded in longer forms: `RDKIT_AVAILABLE`, `BIOPYTHON_AVAILABLE`, `HAS_SIFTKG`

**Constants:**
- SCREAMING_SNAKE_CASE: `PATTERNS`, `DNA_CHARS`, `RNA_CHARS`, `PROTEIN_CHARS`, `HEDGING_PATTERNS`, `PATENT_PATTERN`
- Pattern definitions: `PATTERNS: list[tuple[str, re.Pattern, str]]`
- Availability flags: `HAS_SIFTKG`, `HAS_RDKIT`, `HAS_BIOPYTHON`, `RDKIT_AVAILABLE`, `BIOPYTHON_AVAILABLE`

**Type Names:**
- Classes rarely used; dicts preferred for structured data
- Type hints with Union/Optional: `seq_type: str | None`, `domain_path: str | None`
- Generics: `list[dict]`, `dict[str, str]`, `tuple[str, re.Pattern, str]`

## Import Organization

**Order:**
1. Standard library: `import json`, `import sys`, `from pathlib import Path`, `from datetime import datetime, timezone`
2. Third-party: `import pytest`, `from rdkit import Chem`, `from Bio.Seq import Seq`
3. Local/project: `from scan_patterns import scan_text`, `from build_extraction import write_extraction`

**Path Construction:**
- Use `pathlib.Path` throughout: `Path(file_path)`, `Path(__file__).parent`, `Path(output_dir) / "subdir" / "file.json"`
- Avoid os.path — always Path

**Conditional Imports:**
- Wrap optional dependencies in try/except at module level
- Set availability flags: `HAS_RDKIT = True`
- Pattern in `validate_molecules.py` (line 30-48):
  ```python
  try:
      from validate_smiles import validate_smiles
      HAS_RDKIT = True
  except ImportError:
      HAS_RDKIT = False
      validate_smiles = None  # type: ignore[assignment]
  ```

**Path Insertion for Local Modules:**
```python
VALIDATION_SCRIPTS = PROJECT_ROOT / "skills" / "drug-discovery-extraction" / "validation-scripts"
sys.path.insert(0, str(VALIDATION_SCRIPTS))
```

## Code Style

**Docstrings:**
- Function: Triple-quoted block with description, Args, Returns
- Module: Triple-quoted at top with usage examples
- Example from `validate_smiles.py`:
  ```python
  """RDKit-based SMILES validation and molecular property calculation.

  Usage:
      Single:  python validate_smiles.py "CC(=O)Oc1ccccc1C(=O)O"
      Batch:   echo '["CC(=O)O", "invalid"]' | python validate_smiles.py --batch
  """
  ```

**Line Width:**
- Appears to be ~90-100 chars (not strictly enforced)
- Ruff will apply default formatting

**Comments:**
- Single-line comments with `#` for clarification
- Block separators with comment lines (79 dashes):
  ```python
  # ---------------------------------------------------------------------------
  # Availability flags
  # ---------------------------------------------------------------------------
  ```
- Inline comments explain patterns or heuristics (e.g., line 82-83 in `scan_patterns.py`)

**Spacing:**
- 2 blank lines between top-level functions/sections
- 1 blank line between methods within section
- Horizontal rule comments divide major sections

## Error Handling

**Pattern - Graceful Degradation:**
- Optional libraries fail at import, not runtime
- Functions return error dict instead of raising
- Example from `validate_smiles.py` (line 29-33):
  ```python
  if not RDKIT_AVAILABLE:
      return {
          "valid": None,
          "error": "RDKit not installed. Run: uv pip install rdkit",
      }
  ```

**Pattern - Validation Results:**
- All validation functions return dict with consistent structure:
  - `"valid": True|False|None` — validation result
  - `"error": str` — error message if validation failed
  - Additional fields: properties, descriptors, etc.
- Example from `validate_sequences.py` (line 106-120):
  ```python
  if not chars <= DNA_CHARS:
      invalid = chars - DNA_CHARS
      return {"valid": False, "error": f"Invalid DNA characters: {sorted(invalid)}"}
  ```

**Pattern - User-Friendly Import Errors:**
- Wrapper functions catch ImportError and provide help text
- Example from `run_sift.py` (line 17-28):
  ```python
  def _import_sift(names: list[str]):
      try:
          import sift_kg
      except ImportError:
          print("Error: sift-kg is not installed.\nRun /epistract-setup or: uv pip install sift-kg", file=sys.stderr)
          sys.exit(1)
  ```

**Pattern - Field Normalization:**
- LLM outputs may use non-standard field names
- Normalize before processing: `_normalize_fields()` in `build_extraction.py` (line 13-24)
  ```python
  for e in entities:
      if "type" in e and "entity_type" not in e:
          e["entity_type"] = e.pop("type")
  ```

## JSON & Data Structures

**JSON Output:**
- Indented with 2 spaces: `json.dumps(data, indent=2)`
- Always use `indent=2` for readability
- ISO format for timestamps: `datetime.now(timezone.utc).isoformat()`

**Data Shape Patterns:**
- Entities: `{"name": str, "entity_type": str, "confidence": float, "context": str}`
- Relations: `{"source_entity": str, "target_entity": str, "relation_type": str, "confidence": float, "evidence": str}`
- Extractions: `{"document_id": str, "entities": list, "relations": list, "extracted_at": str, "domain_name": str}`

**List Comprehensions & Filtering:**
- Preferred over loops for clarity
- Example from `label_communities.py` (line 38-39):
  ```python
  genes = [m["name"] for m in members if m.get("entity_type") == "GENE"]
  ```

## Regex Patterns

**Pattern Definition Style:**
- Define at module level as list/dict of tuples with metadata
- Compile with flags: `re.compile(pattern, re.IGNORECASE)`
- Example from `label_epistemic.py`:
  ```python
  HEDGING_PATTERNS = [
      (re.compile(r"\b(suggests?|suggested)\b", re.I), "hypothesized"),
  ]
  PATENT_PATTERN = re.compile(r"^patent", re.I)
  ```

## CLI/Main Pattern

**Entry Point:**
```python
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)  # Print module docstring
        sys.exit(1)
    # Parse args manually, call functions
```

**Argument Parsing:**
- Manual `sys.argv` parsing (no argparse in main scripts)
- Check for flags: `if "--json" in sys.argv`
- Get next arg: `sys.argv[sys.argv.index("--flag") + 1]`

## Type Hints

**Modern Python (3.10+):**
- Use `|` for Union: `str | None` (not `Optional[str]`)
- Use `from __future__ import annotations` for forward references
- Example from `validate_sequences.py`:
  ```python
  from __future__ import annotations
  def validate_sequence(seq: str, seq_type: str | None = None) -> dict:
  ```

**Return Type Consistency:**
- Functions returning validation results always return `dict`
- Functions with side effects return `str` (file path) or `None`
- Type hints on all function signatures

## Testing Conventions (see TESTING.md for detail)

- Tests are in `/tests/test_unit.py`
- Use `pytest` with conditional skip decorators
- Assertions with descriptive messages: `assert condition, f"Expected X, got {actual}"`

---

*Convention analysis: 2026-03-29*
