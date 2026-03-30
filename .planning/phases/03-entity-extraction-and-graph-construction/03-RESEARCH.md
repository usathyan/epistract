# Phase 3: Entity Extraction and Graph Construction - Research

**Researched:** 2026-03-29
**Domain:** LLM-driven contract entity extraction, entity resolution, knowledge graph construction
**Confidence:** HIGH

## Summary

Phase 3 builds the core extraction and graph construction pipeline for contract documents. The existing codebase already provides nearly everything needed: sift-kg 0.9.0 handles graph building with built-in entity deduplication (2-phase: deterministic normalization + SemHash fuzzy matching at 0.95 threshold), `build_extraction.py` writes extraction JSON, `run_sift.py` orchestrates build/view/export, and `agents/extractor.md` is already domain-aware. The contract domain schema (7 entity types, 7 relation types) and SKILL.md with full extraction guidance were completed in Phase 1.

The primary new work is: (1) a clause-aware chunking script that splits ingested text at section/clause boundaries, (2) orchestration to dispatch parallel extraction agents and merge chunk-level outputs per document, (3) contract-specific entity resolution enhancements (legal suffix stripping like "LLC", "Inc.", defined-term alias resolution), and (4) updating `label_communities.py` to handle contract entity types rather than only biomedical ones.

**Primary recommendation:** Build the chunker as `scripts/chunk_document.py`, add contract-specific normalization rules to a pre-processing step before sift-kg's built-in `prededup_entities`, and use the existing `run_sift.py build` + `label_communities.py` pipeline with minimal modifications for contract-aware community labeling.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Clause-aware chunking via a Python pre-processor script (e.g., `scripts/chunk_document.py`). Splits ingested text at section/clause boundaries (Article, Section, numbered clauses) to keep legal context intact.
- **D-02:** Fallback to fixed ~10K character chunks at paragraph boundaries when no clause structure is detected (e.g., free-form emails, XLS files).
- **D-03:** Chunk output stored as intermediate files (e.g., `ingested/<doc_id>_chunks/`) for debuggability and re-run without re-chunking.
- **D-04:** Parallel agent dispatch (4+ concurrent) -- one extraction agent per document, matching the existing pattern from `commands/ingest.md` Step 3.
- **D-05:** One merged extraction JSON per document (`extractions/<doc_id>.json`), matching existing `build_extraction.py` pattern.
- **D-06:** Full contract SKILL.md passed as context to each extraction agent (Phase 1 D-17 pattern).
- **D-07:** Cross-references between contract sections extracted as attributes (e.g., "per Section 4.2") and resolved during graph construction when all sections are available. No overlap or neighboring-section inclusion during chunking.
- **D-08:** Reuse existing `agents/extractor.md` -- it's already domain-aware. No new contract-specific agent needed.
- **D-09:** Pipeline is corpus-agnostic -- processes whatever documents exist in the corpus directory. Not hardcoded to any specific document count.
- **D-10:** Research-first approach -- phase researcher MUST investigate existing contract/legal ontologies (LKIF, FIBO, ContractML, etc.), open-source contract review tools, and established taxonomies for obligations, parties, and clauses. Scope: general contract analysis frameworks + event/venue contract examples.
- **D-11:** If research finds established ontologies, adapt their concepts into the existing domain.yaml format (Phase 1 pattern). Don't adopt external formats directly -- preserve the pluggable domain config system.
- **D-12:** SemHash fuzzy dedup as baseline implementation (case normalization, legal suffix stripping). Research findings inform upgrades to the resolution strategy.
- **D-13:** Extraction agents capture defined-term aliases during extraction -- e.g., when a contract says "hereinafter referred to as 'Contractor'", extract both the formal name AND the alias. Store as `aliases` attribute on PARTY entities.
- **D-14:** Structured typed attributes per entity type (COST, DEADLINE, PARTY, OBLIGATION, CLAUSE, SERVICE, VENUE -- detailed attribute schemas specified in CONTEXT.md).
- **D-15:** Clause-level provenance on all graph edges -- each relation stores the source contract, section/clause number.
- **D-16:** COST entities store both parsed numeric amounts and original contract text.
- **D-17:** Synthetic contract fixtures in `tests/fixtures/` for deterministic testing.
- **D-18:** Basic sift-kg visualization verified -- confirm pyvis HTML viewer renders contract graph with distinguishable entity types.

### Claude's Discretion
- Validation strategy for extraction quality (schema validation, confidence thresholds, LLM review)
- Internal design of the clause-aware chunker (regex patterns for section detection, handling edge cases)
- Exact attribute schemas beyond the types specified above
- SemHash configuration parameters (similarity thresholds, normalization rules)
- How to structure the merged extraction when combining chunk-level outputs

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| EXTR-01 | System extracts contract entities (parties, obligations, deadlines, costs, clauses, services) from ingested documents using domain-configured prompts | Existing `agents/extractor.md` + contract `SKILL.md` provide the extraction framework. New `chunk_document.py` splits text at clause boundaries. `build_extraction.py` writes merged output. |
| EXTR-02 | Entity resolution deduplicates variant references to the same real-world entity | sift-kg `prededup_entities` provides 2-phase dedup (deterministic + SemHash). Contract-specific pre-processing (legal suffix stripping, alias resolution) augments this. |
| GRPH-01 | Extracted entities and relations are assembled into a NetworkX knowledge graph using the existing sift-kg pipeline | `run_sift.py build` calls `sift_kg.run_build()` which loads extractions, runs `prededup_entities`, builds graph, detects communities. Direct reuse. |
| GRPH-02 | Graph nodes carry domain-specific attributes (obligation deadlines, cost amounts, clause references) | `ExtractedEntity.attributes` field (dict) passes through to graph nodes. Domain.yaml entity types with `extraction_hints` guide attribute capture. Typed attribute schemas (D-14) enforced via extraction prompt. |

</phase_requirements>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| sift-kg | 0.9.0 | Graph building, entity resolution, community detection, visualization | Already installed; `run_build()` handles full pipeline including `prededup_entities` with SemHash |
| NetworkX | 3.4.2 | Graph data structure (MultiDiGraph) | Already installed; used by sift-kg internally |
| SemHash | 0.4.1 | Fuzzy entity name deduplication | Already installed (sift-kg dependency); `prededup_entities` uses it at 0.95 threshold |
| Pydantic | 2.11.7 | DocumentExtraction model validation | Already installed; `ExtractedEntity` / `ExtractedRelation` models |
| pyvis | 0.3.2 | Interactive HTML graph visualization | Already installed; sift-kg's `run_view()` generates HTML |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| inflect | (installed) | Singularization for entity name normalization | Used by sift-kg `prededup_entities` internally |
| Unidecode | (installed) | Unicode normalization for entity names | Used by sift-kg `_normalize_name` and `_make_entity_id` |
| Rich | (installed) | Terminal progress bars for batch processing | Chunking and extraction progress display |
| PyYAML | (installed) | Domain schema loading | `build_extraction.py` reads domain.yaml for domain_name |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| SemHash dedup | LLM-based entity resolution | SemHash is faster and deterministic; LLM is more accurate for complex aliases but costly and non-deterministic. Start with SemHash, upgrade later if needed. |
| regex clause detection | NLP-based section parser (e.g., docling) | Regex is simpler, sufficient for well-structured contracts. NLP adds dependency for marginal gain on structured legal text. |
| pyvis HTML viewer | D3.js custom dashboard | pyvis is sufficient for Phase 3 verification. Custom dashboard is Phase 5 scope. |

**Installation:** No new packages needed. All dependencies are already installed.

## Legal Ontology Research (D-10)

### Findings

Research into existing contract/legal ontologies found several frameworks, but none warrant direct adoption:

**LKIF (Legal Knowledge Interchange Format)**
- OWL-based ontology for legal concepts (norms, actions, roles, places)
- Too abstract for contract extraction -- models legal reasoning, not contract data structures
- Concepts like "Norm", "Obligation", "Permission" align with our OBLIGATION/CLAUSE split
- **Verdict:** Conceptual alignment validates our entity type choices, but LKIF's OWL format is not adoptable into domain.yaml
- Confidence: MEDIUM (reviewed GitHub repo and CEUR paper)

**FIBO (Financial Industry Business Ontology)**
- EDMC standard for financial instruments and contracts
- `fibo/FND/Agreements/Contracts/` ontology defines Contract, MutualContractualAgreement, ContractParty
- Too financial-domain-specific (derivatives, securities) for event contracts
- **Verdict:** Validates PARTY as an entity type; concept of "ContractParty" with roles aligns with our PARTY + role attribute
- Confidence: MEDIUM (reviewed EDMC spec viewer)

**Accord Project**
- Open-source smart legal contracts framework
- Focuses on executable contract clauses (Cicero engine), not extraction
- Template model (TemplateMark) structures clauses as executable code
- **Verdict:** Not applicable to our extraction use case
- Confidence: HIGH (reviewed project docs)

**Open Contracts**
- Open-source contract labeling/analysis tool
- PDF-first approach (works with original document, not plain text)
- Uses annotation-based ML, not LLM extraction
- **Verdict:** Different approach; not directly reusable but validates our entity type taxonomy
- Confidence: MEDIUM (reviewed GitHub)

### Recommendation (D-11)

The existing domain.yaml is well-aligned with established legal ontologies. No changes needed:
- PARTY maps to LKIF "Legal Role" and FIBO "ContractParty"
- OBLIGATION maps to LKIF "Obligation" (deontic norm with "shall/must")
- CLAUSE maps to LKIF "Norm" (legal rule/condition)
- The OBLIGATION vs CLAUSE disambiguation in SKILL.md correctly follows LKIF's distinction between deontic norms (obligations) and constitutive norms (clauses/definitions)

**No ontology adoption needed.** The Phase 1 domain.yaml already captures the right abstractions.

## Architecture Patterns

### Recommended Project Structure

```
scripts/
  chunk_document.py       # NEW: Clause-aware chunking
  build_extraction.py     # EXISTING: Writes extraction JSON (no changes)
  run_sift.py             # EXISTING: Graph build/view/export (no changes)
  label_communities.py    # MODIFY: Add contract entity type support
  ingest_documents.py     # EXISTING: Document ingestion (no changes)
  entity_resolution.py    # NEW: Contract-specific pre-processing for entity resolution
tests/
  test_unit.py            # EXTEND: Add Phase 3 tests (UT-030+)
  fixtures/               # EXTEND: Add synthetic contract text fixtures
```

### Pattern 1: Clause-Aware Chunking

**What:** Split ingested text at section/clause boundaries for context-preserving extraction.
**When to use:** When processing structured legal documents with Article/Section/Clause structure.

```python
# scripts/chunk_document.py
import re
from pathlib import Path

# Regex patterns for section headers (ordered by specificity)
SECTION_PATTERNS = [
    re.compile(r"^(ARTICLE\s+[IVXLCDM\d]+)", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^(Section\s+\d+[\.\d]*)", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^(\d+\.\d+[\.\d]*\s+[A-Z])", re.MULTILINE),
    re.compile(r"^([A-Z][A-Z\s]{3,}:?\s*$)", re.MULTILINE),  # ALL CAPS headers
]

MAX_CHUNK_SIZE = 10000
MIN_CHUNK_SIZE = 500

def chunk_document(text: str, doc_id: str) -> list[dict]:
    """Split text at clause boundaries. Falls back to paragraph-based ~10K chunks."""
    # Try clause-aware splitting first
    sections = _split_at_sections(text)
    if len(sections) > 1:
        return _merge_small_sections(sections, doc_id)
    # Fallback: paragraph-based fixed-size chunks
    return _split_fixed(text, doc_id, MAX_CHUNK_SIZE)
```

### Pattern 2: Contract Entity Resolution Pre-Processing

**What:** Normalize legal entity names before sift-kg's built-in dedup runs.
**When to use:** After extraction, before `run_sift.py build`.

```python
# scripts/entity_resolution.py
LEGAL_SUFFIXES = [
    "llc", "l.l.c.", "inc", "inc.", "incorporated",
    "corp", "corp.", "corporation", "co.", "company",
    "ltd", "ltd.", "limited", "lp", "l.p.",
    "llp", "l.l.p.", "pllc", "p.l.l.c.",
    "authority", "assn", "association",
]

DEFINED_TERM_PATTERN = re.compile(
    r'(?:hereinafter|hereafter|referred to as|known as)\s+["\']([^"\']+)["\']',
    re.IGNORECASE,
)

def normalize_party_name(name: str) -> str:
    """Strip legal suffixes and normalize party names."""
    normalized = name.strip()
    lower = normalized.lower()
    for suffix in LEGAL_SUFFIXES:
        if lower.endswith(suffix):
            normalized = normalized[: -len(suffix)].rstrip(" ,.")
            break
    return normalized.strip()
```

### Pattern 3: Chunk-Level Extraction Merge

**What:** Combine chunk-level extraction outputs into one document-level extraction JSON.
**When to use:** After all chunks of a document are extracted.

```python
def merge_chunk_extractions(chunks: list[dict], doc_id: str) -> dict:
    """Merge chunk-level extractions into one document extraction."""
    all_entities = []
    all_relations = []
    seen_entities = set()  # (name, entity_type) dedup within document

    for chunk in chunks:
        for entity in chunk.get("entities", []):
            key = (entity["name"].lower(), entity["entity_type"])
            if key not in seen_entities:
                all_entities.append(entity)
                seen_entities.add(key)
            else:
                # Update confidence to max across chunks
                for existing in all_entities:
                    if (existing["name"].lower(), existing["entity_type"]) == key:
                        existing["confidence"] = max(
                            existing["confidence"], entity["confidence"]
                        )
                        break
        all_relations.extend(chunk.get("relations", []))

    return {
        "entities": all_entities,
        "relations": all_relations,
        "chunks_processed": len(chunks),
    }
```

### Anti-Patterns to Avoid
- **Hand-rolling entity dedup from scratch:** sift-kg's `prededup_entities` already does 2-phase dedup (deterministic + SemHash). Add contract-specific normalization as a pre-processing step, don't replace the existing pipeline.
- **Chunking with overlap:** D-07 explicitly says no overlap or neighboring-section inclusion. Cross-references are captured as attributes and resolved at graph construction time.
- **Creating a new extraction agent:** D-08 says reuse `agents/extractor.md`. It's already domain-aware and reads SKILL.md.
- **Hardcoding entity counts or document names:** D-09 says pipeline is corpus-agnostic.
- **Storing chunk text in extraction JSON:** Chunks are intermediate files (D-03) stored in `ingested/<doc_id>_chunks/`, not embedded in extraction output.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Entity dedup | Custom fuzzy matching | sift-kg `prededup_entities` (deterministic + SemHash) | Already handles case normalization, singularization, Unicode normalization, and fuzzy matching. Tested across 6 biomedical scenarios. |
| Graph construction | Manual NetworkX graph building | `sift_kg.run_build()` via `run_sift.py build` | Handles extraction loading, entity resolution, relation type normalization, postprocessing, community detection, and review flagging. |
| Community detection | Custom clustering | sift-kg Louvain community detection | Built into `run_build()`, saves `communities.json` automatically. |
| Graph visualization | Custom D3.js/HTML | pyvis via `run_sift.py view` | Generates interactive HTML viewer. Phase 5 handles dashboard. |
| DocumentExtraction schema | Custom JSON validation | Pydantic `DocumentExtraction` model | sift-kg validates entity_type, relation_type, confidence, etc. automatically. |
| Section header detection (complex) | NLP sentence parser | Regex patterns | Contract sections follow predictable patterns (Article, Section, numbered clauses). Regex is sufficient and deterministic. |

**Key insight:** sift-kg already handles the graph construction pipeline end-to-end. Phase 3's new code is primarily: (1) clause-aware chunking, (2) contract-specific name normalization, and (3) orchestrating extraction agent dispatch. Everything else is reuse.

## Common Pitfalls

### Pitfall 1: Entity Name Mismatch in Relations
**What goes wrong:** Extraction agent writes `source_entity: "Aramark"` but the entity was extracted as `name: "Aramark Sports & Entertainment Services, LLC"`. sift-kg can't resolve the relation endpoint.
**Why it happens:** LLM uses abbreviated names in relation source/target fields.
**How to avoid:** SKILL.md already instructs "source_entity / target_entity: The `name` field of a previously extracted entity. Must match exactly." Emphasize this in chunker context. Also, sift-kg's `_resolve_entity_name` does fuzzy matching on endpoints.
**Warning signs:** High `relations_skipped` count in build output.

### Pitfall 2: Chunk Size Too Large for LLM Context
**What goes wrong:** A single contract section exceeds the chunk target size, causing the LLM to miss entities in the middle.
**Why it happens:** Some contract sections (especially exhibits, schedules) can be very long.
**How to avoid:** After clause-aware splitting, apply a secondary split on oversized sections at paragraph boundaries. Log when this happens for debugging.
**Warning signs:** Long sections producing fewer entities per character than shorter ones.

### Pitfall 3: Legal Suffix Stripping Breaks Entity Identity
**What goes wrong:** Stripping "Authority" from "Pennsylvania Convention Center Authority" creates incorrect entity name.
**Why it happens:** "Authority" is both a legal suffix and part of the entity's proper name.
**How to avoid:** Only strip suffixes when they appear after a comma or as the last word following a clear legal entity name pattern. Maintain a short allowlist of known entity names from the domain context (PCC Authority, etc.).
**Warning signs:** Entity names that look truncated or wrong after normalization.

### Pitfall 4: Duplicate Entities from Multi-Chunk Extraction
**What goes wrong:** Same party extracted from chunks 1, 3, and 7 of the same document creates 3 entities.
**Why it happens:** Each chunk is extracted independently.
**How to avoid:** Merge chunk extractions within a document (dedup by lowercase name + entity_type) before writing to `extractions/<doc_id>.json`. Then sift-kg's cross-document dedup handles inter-document duplicates.
**Warning signs:** Entity counts much higher than expected for the number of contracts.

### Pitfall 5: Community Labeling Fails for Contract Entities
**What goes wrong:** `label_communities.py` produces generic "Entity1 / Entity2 / Entity3" labels because it only has biomedical entity type priority logic.
**Why it happens:** Current code prioritizes GENE, PROTEIN, PATHWAY etc. -- none of which exist in contract domain.
**How to avoid:** Add contract entity types to the priority map and labeling heuristics. PARTY and VENUE should anchor community labels for contracts.
**Warning signs:** All community labels are generic fallback format.

## Code Examples

### Clause-Aware Chunker Interface

```python
# scripts/chunk_document.py
# Source: Project pattern from ingest_documents.py
"""Clause-aware document chunker for contract text.

Usage:
    python chunk_document.py <doc_id> <output_dir>
    python chunk_document.py <doc_id> <output_dir> --max-size 10000
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

MAX_CHUNK_SIZE = 10000
MIN_CHUNK_SIZE = 500

def chunk_document(text: str, doc_id: str, max_size: int = MAX_CHUNK_SIZE) -> list[dict]:
    """Split document text into chunks at clause boundaries.

    Args:
        text: Full document text from ingested/<doc_id>.txt
        doc_id: Document identifier.
        max_size: Maximum chunk size in characters.

    Returns:
        List of chunk dicts with keys: chunk_id, text, section_header, char_offset.
    """
    ...

if __name__ == "__main__":
    # CLI: reads ingested/<doc_id>.txt, writes ingested/<doc_id>_chunks/
    ...
```

### Contract-Specific Entity Pre-Processing

```python
# scripts/entity_resolution.py
# Source: Project pattern from build_extraction.py
"""Pre-process extraction JSON files for contract entity resolution.

Runs BEFORE sift-kg build to normalize legal entity names and resolve aliases.
Modifies extraction files in-place.

Usage:
    python entity_resolution.py <output_dir>
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

def preprocess_extractions(output_dir: Path) -> dict:
    """Pre-process all extraction files for contract entity resolution.

    Returns:
        Stats dict with counts of normalizations performed.
    """
    ...
```

### Extending build_extraction.py for Chunk Merging

```python
# Addition to build_extraction.py (or separate merge function)
def merge_chunk_extractions(
    chunks: list[dict], doc_id: str, output_dir: str, domain_name: str | None = None
) -> str:
    """Merge chunk-level extractions and write single document extraction.

    Args:
        chunks: List of chunk extraction dicts (each has entities + relations).
        doc_id: Document identifier.
        output_dir: Output directory.
        domain_name: Domain name for resolution.

    Returns:
        Path to written extraction JSON.
    """
    merged = _merge_entities_and_relations(chunks)
    return write_extraction(
        doc_id, output_dir,
        merged["entities"], merged["relations"],
        chunks_processed=len(chunks),
        domain_name=domain_name,
    )
```

### Test Fixture: Synthetic Contract Text

```python
# For tests/fixtures/ -- a small synthetic contract text file
SAMPLE_CONTRACT_TEXT = """
AGREEMENT FOR EVENT SERVICES

This Agreement ("Agreement") is entered into as of January 15, 2026,
between Pennsylvania Convention Center Authority ("PCC Authority" or
"Licensor") and Aramark Sports & Entertainment Services, LLC
("Caterer" or "Contractor").

ARTICLE I: SERVICES

Section 1.1 Catering Services. Caterer shall provide all food and
beverage services for the event scheduled for September 4-6, 2026
("Event").

Section 1.2 Exclusive Rights. Caterer shall have exclusive rights to
provide food and beverage services during the Event. No outside food
vendors shall be permitted without prior written consent.

ARTICLE II: COMPENSATION

Section 2.1 Base Rate. Client shall pay Caterer $45.00 per person
for lunch service and $65.00 per person for dinner service.

Section 2.2 Payment Terms. Payment shall be due within thirty (30)
days of invoice receipt.

ARTICLE III: TERM AND TERMINATION

Section 3.1 Effective Date. This Agreement shall be effective as of
the date first written above.

Section 3.2 Cancellation. In the event of cancellation less than
thirty (30) days prior to the Event, a cancellation fee of $5,000
shall apply.
"""
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Rule-based NER for contracts | LLM extraction with domain prompts | 2024-2025 | Higher recall, handles diverse formatting, no training data needed |
| Custom entity resolution | SemHash (Model2Vec) fuzzy matching | sift-kg 0.9.0 | Fast, deterministic baseline; 2-phase approach (normalize + fuzzy) |
| Manual community labeling | Louvain detection + heuristic labeling | sift-kg 0.9.0 | Automatic community detection and labeling |

**Deprecated/outdated:**
- spaCy-based NER for contract extraction: Requires labeled training data, limited entity types. LLM extraction with domain prompts is more flexible.
- Manual entity resolution spreadsheets: Replaced by automated SemHash-based dedup.

## Open Questions

1. **SemHash threshold for legal entities**
   - What we know: Default 0.95 threshold works well for biomedical entities. Legal entity names may need a lower threshold (e.g., 0.90) because of abbreviation patterns ("PCC" vs "Pennsylvania Convention Center").
   - What's unclear: Whether 0.95 or a lower threshold produces better results for contract entity names.
   - Recommendation: Start with 0.95 (sift-kg default), evaluate on test fixtures, adjust if needed. The contract-specific pre-processing (legal suffix stripping, alias resolution) should handle most cases before SemHash runs.

2. **Large contract handling (12-31 MB PDFs)**
   - What we know: Some PDFs are 12-31 MB. Text extraction completed in Phase 2 (ingested text files exist).
   - What's unclear: Whether these produce very large text files that need special chunking strategies.
   - Recommendation: The clause-aware chunker with max 10K chunk size handles this naturally. Log chunk counts per document to verify coverage.

3. **Extraction quality validation strategy (Claude's Discretion)**
   - What we know: sift-kg validates against DocumentExtraction schema (Pydantic). Domain.yaml constrains entity_type and relation_type to valid values.
   - What's unclear: Whether additional validation (confidence thresholds, mandatory attributes) is needed.
   - Recommendation: Schema validation (Pydantic) + confidence threshold filtering (drop entities below 0.5) + entity count sanity check (warn if document produces fewer than 3 entities). Keep it simple.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (already configured) |
| Config file | none (uses defaults, per existing pattern) |
| Quick run command | `python -m pytest tests/test_unit.py -v -k "ut03"` |
| Full suite command | `python -m pytest tests/test_unit.py -v` |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| EXTR-01 | Clause-aware chunking splits text at section boundaries | unit | `python -m pytest tests/test_unit.py::test_ut030_chunk_document_clause_split -x` | Wave 0 |
| EXTR-01 | Fallback chunking for unstructured text | unit | `python -m pytest tests/test_unit.py::test_ut031_chunk_document_fallback -x` | Wave 0 |
| EXTR-01 | Extraction JSON produced from chunked document | integration | `python -m pytest tests/test_unit.py::test_ut032_extraction_from_chunks -x` | Wave 0 |
| EXTR-02 | Legal suffix normalization | unit | `python -m pytest tests/test_unit.py::test_ut033_legal_suffix_stripping -x` | Wave 0 |
| EXTR-02 | Defined-term alias resolution | unit | `python -m pytest tests/test_unit.py::test_ut034_alias_resolution -x` | Wave 0 |
| EXTR-02 | sift-kg dedup merges variant party names | integration | `python -m pytest tests/test_unit.py::test_ut035_entity_dedup_integration -x` | Wave 0 |
| GRPH-01 | Graph builds from contract extractions | integration | `python -m pytest tests/test_unit.py::test_ut036_graph_build_contracts -x` | Wave 0 |
| GRPH-02 | Graph nodes carry typed attributes | unit | `python -m pytest tests/test_unit.py::test_ut037_graph_node_attributes -x` | Wave 0 |
| GRPH-02 | Visualization renders with contract entity types | smoke | `python -m pytest tests/test_unit.py::test_ut038_visualization_renders -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/test_unit.py -v -k "ut03" -x`
- **Per wave merge:** `python -m pytest tests/test_unit.py -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_unit.py` -- Add UT-030 through UT-038 test functions
- [ ] `tests/fixtures/sample_contract_text.txt` -- Synthetic contract text with known entities for deterministic testing
- [ ] `tests/fixtures/sample_contract_unstructured.txt` -- Free-form text (no section headers) for fallback chunking test

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| sift-kg | Graph building, entity resolution | Yes | 0.9.0 | -- |
| NetworkX | Graph data structure | Yes | 3.4.2 | -- |
| SemHash | Fuzzy entity dedup | Yes | 0.4.1 | -- |
| Pydantic | Extraction schema validation | Yes | 2.11.7 | -- |
| pyvis | Graph visualization | Yes | 0.3.2 | -- |
| inflect | Name singularization | Yes | (installed) | -- |
| Unidecode | Unicode normalization | Yes | (installed) | -- |
| Rich | Progress bars | Yes | (installed) | -- |
| Python | Runtime | Yes | 3.11+ | -- |

**Missing dependencies with no fallback:** None
**Missing dependencies with fallback:** None

## Sources

### Primary (HIGH confidence)
- sift-kg 0.9.0 source inspection -- `run_build()`, `build_graph()`, `prededup_entities()`, `_normalize_name()`, `_make_entity_id()` (direct source code inspection via Python inspect module)
- `skills/contract-extraction/domain.yaml` -- 7 entity types, 7 relation types (project file)
- `skills/contract-extraction/SKILL.md` -- Full extraction guidance with naming standards, disambiguation rules (project file)
- `agents/extractor.md` -- Domain-aware extraction agent (project file)
- `scripts/build_extraction.py` -- Extraction JSON writer with field normalization (project file)
- `scripts/run_sift.py` -- sift-kg wrapper with build/view/export (project file)
- `scripts/label_communities.py` -- Community labeling with biomedical entity priorities (project file)

### Secondary (MEDIUM confidence)
- [LKIF Core Ontology](https://github.com/RinkeHoekstra/lkif-core) -- Legal Knowledge Interchange Format concepts
- [FIBO Contracts Ontology](https://spec.edmcouncil.org/fibo/ontology/FND/Agreements/Contracts/) -- Financial contract modeling
- [Accord Project](https://accordproject.org/) -- Smart legal contracts framework
- [Open Contracts](https://opensource.legal/projects/OpenContracts) -- Open-source contract analysis tool

### Tertiary (LOW confidence)
- WebSearch on legal entity resolution patterns -- community consensus on legal suffix stripping and name normalization (needs validation against actual contract data)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- All libraries already installed and verified via Python import and version check
- Architecture: HIGH -- Patterns follow existing codebase conventions verified by reading source code
- Pitfalls: MEDIUM -- Based on experience with similar extraction pipelines; actual pitfalls will depend on real contract data
- Legal ontology research: MEDIUM -- Reviewed 4 frameworks, concluded existing domain.yaml is well-aligned

**Research date:** 2026-03-29
**Valid until:** 2026-04-28 (stable stack, no version changes expected)
