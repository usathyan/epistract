#!/usr/bin/env python3
"""Domain creation wizard for epistract knowledge graph framework.

Analyzes sample documents via multi-pass LLM analysis to propose a domain
schema, then generates a complete domain package (domain.yaml, SKILL.md,
epistemic.py, references/) ready for the standard pipeline.

Usage:
    from core.domain_wizard import analyze_documents, generate_domain_package

    # Step 1: Analyze documents and get schema proposal
    proposal = analyze_documents(doc_paths, domain_description)

    # Step 2: Generate the full domain package
    result = generate_domain_package(domain_name, proposal, output_dir)
"""

from __future__ import annotations

import ast
import importlib.util
import json
import tempfile
import textwrap

import yaml

from pathlib import Path

from core.domain_resolver import DOMAINS_DIR, DOMAIN_ALIASES, list_domains

# Optional sift-kg reader — used to extract text from binary formats (PDF, DOCX, etc.).
# Matches the guard pattern at core/ingest_documents.py:20-25.
try:
    from sift_kg.ingest.reader import read_document

    HAS_SIFT_READER = True
except ImportError:
    HAS_SIFT_READER = False


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MIN_SAMPLE_DOCS = 2
MAX_ENTITY_TYPES = 15
MAX_RELATION_TYPES = 20


# ---------------------------------------------------------------------------
# Document reading
# ---------------------------------------------------------------------------


def read_sample_documents(doc_paths: list[Path]) -> list[dict]:
    """Read sample documents for wizard analysis.

    Uses sift_kg.ingest.reader.read_document when available so PDFs, DOCX,
    and other binary formats produce extracted text rather than raw bytes.
    Falls back to plain-text read for .txt files when sift-kg is absent.
    Binary formats without sift-kg are skipped (not silently read as garbage).

    Args:
        doc_paths: List of paths to sample documents.

    Returns:
        List of dicts with keys: path, text, char_count.

    Raises:
        ValueError: If fewer than MIN_SAMPLE_DOCS readable documents.
    """
    results: list[dict] = []
    for p in doc_paths:
        p = Path(p)
        text: str | None = None

        if HAS_SIFT_READER:
            try:
                raw = read_document(p)
                text = raw if isinstance(raw, str) else str(raw)
            except Exception:
                # Mirrors core/ingest_documents.py parse_document:
                # skip unreadable docs; caller enforces MIN_SAMPLE_DOCS.
                continue
        elif p.suffix.lower() == ".txt":
            try:
                text = p.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
        else:
            # No sift-kg and not a plain-text file: skip rather than
            # silently read binary bytes (Bug 3 — FIDL-01).
            continue

        if text is None:
            continue

        results.append(
            {
                "path": str(p),
                "text": text,
                "char_count": len(text),
            }
        )

    if len(results) < MIN_SAMPLE_DOCS:
        raise ValueError(
            f"Need at least {MIN_SAMPLE_DOCS} readable documents, got {len(results)}. "
            "Recommend providing 3-5 representative samples for best results."
        )

    return results


# ---------------------------------------------------------------------------
# Prompt builders (Pass 1, 2, 3 + epistemic)
# ---------------------------------------------------------------------------


def build_schema_discovery_prompt(doc_text: str, domain_description: str) -> str:
    """Build Pass 1 prompt: discover entity and relation types from a single document.

    Args:
        doc_text: Full text of the sample document.
        domain_description: User-provided description of the domain.

    Returns:
        Prompt string for LLM schema discovery.
    """
    return textwrap.dedent(f"""\
        You are an expert knowledge graph schema designer.

        **Domain description:** {domain_description}

        **Task:** Analyze the following document and identify candidate entity types
        and relation types for building a knowledge graph in this domain.

        **Document text:**
        {doc_text[:8000]}

        **Instructions:**
        - Propose 5-15 entity types and 5-20 relation types.
        - Merge similar concepts into one type.
        - Use SCREAMING_SNAKE_CASE for type names (e.g., PARTY, OBLIGATION).
        - Each entity type needs a name, description, and 2-3 examples from the text.
        - Each relation type needs a name, description, source_type, and target_type.

        **Output format (JSON):**
        ```json
        {{
          "entity_types": [
            {{"name": "TYPE_NAME", "description": "...", "examples": ["..."]}}
          ],
          "relation_types": [
            {{"name": "REL_NAME", "description": "...", "source_type": "...", "target_type": "..."}}
          ]
        }}
        ```

        Return ONLY the JSON object, no commentary.
    """)


def build_consolidation_prompt(candidates: list[dict], domain_description: str) -> str:
    """Build Pass 2 prompt: consolidate candidates across documents.

    Args:
        candidates: List of Pass 1 results from multiple documents.
        domain_description: User-provided description of the domain.

    Returns:
        Prompt string for LLM cross-document consolidation.
    """
    candidates_json = json.dumps(candidates, indent=2)
    return textwrap.dedent(f"""\
        You are an expert knowledge graph schema designer performing cross-document
        consolidation.

        **Domain description:** {domain_description}

        **Task:** You have entity and relation type candidates extracted from multiple
        documents. Consolidate them:
        1. Deduplicate synonyms (e.g., PERSON and INDIVIDUAL -> PARTY).
        2. Pick canonical SCREAMING_SNAKE_CASE names.
        3. Write clear descriptions for each type.
        4. Remove overly specific types; keep general, reusable ones.
        5. Aim for 5-{MAX_ENTITY_TYPES} entity types, 5-{MAX_RELATION_TYPES} relation types.

        **Candidates from all documents:**
        {candidates_json}

        **Output format (JSON):**
        ```json
        {{
          "entity_types": [
            {{"name": "TYPE_NAME", "description": "...", "examples": ["..."]}}
          ],
          "relation_types": [
            {{"name": "REL_NAME", "description": "...", "source_type": "...", "target_type": "..."}}
          ]
        }}
        ```

        Return ONLY the JSON object, no commentary.
    """)


def build_final_schema_prompt(consolidated: dict, domain_description: str) -> str:
    """Build Pass 3 prompt: finalize schema with validated relations.

    Args:
        consolidated: Consolidated schema from Pass 2.
        domain_description: User-provided description of the domain.

    Returns:
        Prompt string for final schema validation.
    """
    consolidated_json = json.dumps(consolidated, indent=2)
    return textwrap.dedent(f"""\
        You are an expert knowledge graph schema designer performing final validation.

        **Domain description:** {domain_description}

        **Task:** Finalize the consolidated schema below:
        1. Verify each relation references valid entity types from the list.
        2. Remove any relations whose source_type or target_type is missing.
        3. Write final descriptions (clear, concise, one sentence each).
        4. Output in domain.yaml-compatible dict format.

        **Consolidated schema:**
        {consolidated_json}

        **Output format (JSON):**
        ```json
        {{
          "entity_types": {{
            "TYPE_NAME": {{"description": "..."}},
          }},
          "relation_types": {{
            "REL_NAME": {{"description": "..."}},
          }}
        }}
        ```

        Return ONLY the JSON object, no commentary.
    """)


def build_epistemic_prompt(
    entity_types: dict,
    relation_types: dict,
    domain_description: str,
    sample_excerpts: list[str],
) -> str:
    """Build prompt for LLM to generate domain-specific epistemic parameters.

    Args:
        entity_types: Dict of entity type name -> {description}.
        relation_types: Dict of relation type name -> {description}.
        domain_description: User-provided description of the domain.
        sample_excerpts: Short excerpts from sample documents for context.

    Returns:
        Prompt string for epistemic parameter generation.
    """
    types_json = json.dumps(
        {"entity_types": entity_types, "relation_types": relation_types},
        indent=2,
    )
    excerpts_text = "\n---\n".join(sample_excerpts[:3])
    return textwrap.dedent(f"""\
        You are an expert in epistemic analysis for knowledge graphs.

        **Domain description:** {domain_description}

        **Schema:**
        {types_json}

        **Sample document excerpts:**
        {excerpts_text}

        **Task:** Generate domain-specific epistemic analysis parameters:

        1. **contradiction_pairs**: Pairs of terms that indicate contradictions in this
           domain (e.g., ["exclusive", "non-exclusive"], ["mandatory", "optional"]).

        2. **gap_target_types**: Entity types where coverage gaps are important to detect,
           with a list of expected entity types that should appear.
           Example: {{"coverage": ["PARTY", "DEADLINE"]}}

        3. **confidence_thresholds**: Confidence score thresholds for this domain.
           Example: {{"high": 0.9, "medium": 0.7, "low": 0.5}}

        **Output format (JSON):**
        ```json
        {{
          "contradiction_pairs": [["term_a", "term_b"]],
          "gap_target_types": {{"coverage": ["TYPE_A"]}},
          "confidence_thresholds": {{"high": 0.9, "medium": 0.7, "low": 0.5}}
        }}
        ```

        Return ONLY the JSON object, no commentary.
    """)


# ---------------------------------------------------------------------------
# Domain collision check
# ---------------------------------------------------------------------------


def check_domain_exists(domain_name: str) -> bool:
    """Check if a domain name already exists or is aliased.

    Args:
        domain_name: Domain name to check.

    Returns:
        True if domain exists or is a known alias.
    """
    # Check aliases
    if domain_name in DOMAIN_ALIASES:
        return True

    # Check existing domains
    existing = list_domains()
    return domain_name in existing


# ---------------------------------------------------------------------------
# Artifact generators
# ---------------------------------------------------------------------------


def generate_domain_yaml(
    domain_name: str,
    description: str,
    system_context: str,
    entity_types: dict,
    relation_types: dict,
) -> str:
    """Generate domain.yaml content as YAML string.

    Args:
        domain_name: Human-readable domain name (e.g., "Real Estate Leases").
        description: Multi-line domain description.
        system_context: System prompt for LLM extraction context.
        entity_types: Dict of entity type name -> {description}.
        relation_types: Dict of relation type name -> {description}.

    Returns:
        YAML string ready to write to domain.yaml.
    """
    schema = {
        "name": domain_name,
        "version": "1.0.0",
        "description": description,
        "system_context": system_context,
        "entity_types": entity_types,
        "relation_types": relation_types,
    }
    return yaml.safe_dump(
        schema,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
    )


def generate_skill_md(
    domain_name: str,
    system_context: str,
    entity_types: dict,
    relation_types: dict,
    extraction_guidelines: str,
) -> str:
    """Generate SKILL.md content as markdown string.

    Args:
        domain_name: Human-readable domain name.
        system_context: System prompt paragraph.
        entity_types: Dict of entity type name -> {description}.
        relation_types: Dict of relation type name -> {description}.
        extraction_guidelines: Numbered guidelines for extraction agents.

    Returns:
        Markdown string ready to write to SKILL.md.
    """
    lines: list[str] = []
    lines.append(f"# {domain_name} Domain\n")
    lines.append(f"{system_context}\n")

    # Entity Types table
    lines.append("## Entity Types\n")
    lines.append("| Type | Description |")
    lines.append("|------|-------------|")
    for name, info in entity_types.items():
        desc = info.get("description", "") if isinstance(info, dict) else str(info)
        lines.append(f"| {name} | {desc} |")
    lines.append("")

    # Relation Types table
    lines.append("## Relation Types\n")
    lines.append("| Type | Description |")
    lines.append("|------|-------------|")
    for name, info in relation_types.items():
        desc = info.get("description", "") if isinstance(info, dict) else str(info)
        lines.append(f"| {name} | {desc} |")
    lines.append("")

    # Extraction Guidelines
    lines.append("## Extraction Guidelines\n")
    lines.append(extraction_guidelines)
    lines.append("")

    return "\n".join(lines)


def generate_epistemic_py(
    domain_slug: str,
    entity_types: dict,
    contradiction_pairs: list[tuple[str, str]],
    gap_target_types: dict,
    confidence_thresholds: dict,
) -> str:
    """Generate epistemic.py as Python source code string.

    Args:
        domain_slug: Domain name with hyphens replaced by underscores.
        entity_types: Dict of entity type name -> {description}.
        contradiction_pairs: Pairs of terms indicating contradictions.
        gap_target_types: Entity types for coverage gap detection.
        confidence_thresholds: Confidence score thresholds.

    Returns:
        Python source code string for epistemic.py.
    """
    entity_type_names = list(entity_types.keys())
    pairs_repr = repr(contradiction_pairs)
    gaps_repr = repr(gap_target_types)
    high = confidence_thresholds.get("high", 0.9)
    medium = confidence_thresholds.get("medium", 0.7)
    low = confidence_thresholds.get("low", 0.5)

    code = textwrap.dedent(f'''\
        #!/usr/bin/env python3
        """Epistemic analysis for {domain_slug} domain.

        Generated by the epistract domain wizard.
        Performs contradiction detection, confidence calibration,
        gap analysis, and cross-document linking.
        """

        from __future__ import annotations

        from collections import defaultdict
        from pathlib import Path


        # ---------------------------------------------------------------------------
        # Domain-specific parameters
        # ---------------------------------------------------------------------------

        _CONTRADICTION_PAIRS = {pairs_repr}
        _GAP_TARGET_TYPES = {gaps_repr}
        _CONFIDENCE_HIGH = {high}
        _CONFIDENCE_MEDIUM = {medium}
        _CONFIDENCE_LOW = {low}
        _ENTITY_TYPES = {repr(entity_type_names)}


        def analyze_{domain_slug}_epistemic(
            output_dir: Path,
            graph_data: dict,
        ) -> dict:
            """Analyze epistemic status of {domain_slug} knowledge graph.

            Args:
                output_dir: Directory containing graph outputs.
                graph_data: Parsed graph_data.json with nodes and links.

            Returns:
                Dict with keys: metadata, summary, base_domain, super_domain.
            """
            nodes = graph_data.get("nodes", [])
            links = graph_data.get("links", [])

            # --- Contradiction detection ---
            conflicts: list[dict] = []
            for pair in _CONTRADICTION_PAIRS:
                if len(pair) != 2:
                    continue
                term_a, term_b = pair[0].lower(), pair[1].lower()
                for link in links:
                    evidence = str(link.get("evidence", "")).lower()
                    if term_a in evidence and term_b in evidence:
                        conflicts.append({{
                            "type": "contradiction",
                            "terms": [pair[0], pair[1]],
                            "relation": link.get("id", ""),
                            "evidence": link.get("evidence", ""),
                        }})

            # --- Confidence calibration ---
            asserted_count = 0
            hypothesized_count = 0
            unverified_count = 0

            for link in links:
                confidence = link.get("confidence", 0.5)
                if confidence >= _CONFIDENCE_HIGH:
                    link["epistemic_status"] = "asserted"
                    asserted_count += 1
                elif confidence >= _CONFIDENCE_MEDIUM:
                    link["epistemic_status"] = "hypothesized"
                    hypothesized_count += 1
                else:
                    link["epistemic_status"] = "unverified"
                    unverified_count += 1

            # --- Gap analysis ---
            gaps: list[dict] = []
            node_types = defaultdict(int)
            for node in nodes:
                node_types[node.get("entity_type", "")] += 1

            for gap_category, expected_types in _GAP_TARGET_TYPES.items():
                for expected in expected_types:
                    if node_types.get(expected, 0) == 0:
                        gaps.append({{
                            "category": gap_category,
                            "missing_type": expected,
                            "description": f"No {{expected}} entities found in graph",
                        }})

            # --- Cross-document linking ---
            doc_entities: dict[str, set] = defaultdict(set)
            for node in nodes:
                for doc in node.get("source_documents", []):
                    doc_entities[node.get("name", "")].add(doc)
            cross_doc_entities = [
                {{"name": name, "document_count": len(docs)}}
                for name, docs in doc_entities.items()
                if len(docs) > 1
            ]

            # --- Build claims_layer ---
            claims_layer = {{
                "metadata": {{
                    "domain": "{domain_slug}",
                    "description": "Epistemic analysis for {domain_slug} domain",
                    "generated_from": str(output_dir / "graph_data.json"),
                    "total_relations": len(links),
                }},
                "summary": {{
                    "conflicts_found": len(conflicts),
                    "gaps_found": len(gaps),
                    "cross_document_entities": len(cross_doc_entities),
                    "epistemic_status_counts": {{
                        "asserted": asserted_count,
                        "hypothesized": hypothesized_count,
                        "unverified": unverified_count,
                    }},
                }},
                "base_domain": {{
                    "description": "Factual {domain_slug} knowledge graph relations",
                    "relation_count": asserted_count,
                }},
                "super_domain": {{
                    "domain": "{domain_slug}",
                    "description": "Epistemic layer -- conflicts, gaps, cross-document linking",
                    "conflicts": conflicts,
                    "coverage_gaps": gaps,
                    "cross_document_entities": cross_doc_entities,
                }},
            }}

            return claims_layer
    ''')
    return code


def generate_reference_docs(
    entity_types: dict,
    relation_types: dict,
) -> tuple[str, str]:
    """Generate reference markdown docs for entity and relation types.

    Args:
        entity_types: Dict of entity type name -> {description}.
        relation_types: Dict of relation type name -> {description}.

    Returns:
        Tuple of (entity_types_md, relation_types_md).
    """
    # Entity types doc
    entity_lines: list[str] = ["# Domain Entity Types\n"]
    for name, info in entity_types.items():
        desc = info.get("description", "") if isinstance(info, dict) else str(info)
        entity_lines.append(f"## {name}")
        entity_lines.append(f"{desc}\n")
    entity_md = "\n".join(entity_lines)

    # Relation types doc
    relation_lines: list[str] = ["# Domain Relation Types\n"]
    for name, info in relation_types.items():
        desc = info.get("description", "") if isinstance(info, dict) else str(info)
        relation_lines.append(f"## {name}")
        relation_lines.append(f"{desc}\n")
    relation_md = "\n".join(relation_lines)

    return entity_md, relation_md


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_generated_epistemic(code: str, domain_slug: str) -> dict:
    """Validate generated epistemic.py code.

    Checks:
        1. Syntax via ast.parse
        2. Importability via importlib
        3. Function existence
        4. Dry-run with empty graph data

    Args:
        code: Python source code string.
        domain_slug: Domain slug for function name lookup.

    Returns:
        {"valid": True} or {"valid": False, "error": "..."}.
    """
    # 1. Syntax check
    try:
        ast.parse(code)
    except SyntaxError as e:
        return {"valid": False, "error": f"SyntaxError: {e}"}

    # 2-4. Import, function check, dry-run
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False,
        ) as tmp:
            tmp.write(code)
            tmp_path = Path(tmp.name)

        spec = importlib.util.spec_from_file_location(
            f"_wizard_validate_{domain_slug}", str(tmp_path),
        )
        if spec is None or spec.loader is None:
            return {"valid": False, "error": "Could not create module spec"}

        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        func_name = f"analyze_{domain_slug}_epistemic"
        if not hasattr(mod, func_name):
            return {
                "valid": False,
                "error": f"Function '{func_name}' not found in module",
            }

        func = getattr(mod, func_name)
        result = func(
            output_dir=Path("/tmp"),
            graph_data={"nodes": [], "links": []},
        )

        required_keys = {"metadata", "summary", "base_domain", "super_domain"}
        missing = required_keys - set(result.keys())
        if missing:
            return {
                "valid": False,
                "error": f"Return dict missing keys: {missing}",
            }

        return {"valid": True}

    except Exception as e:
        return {"valid": False, "error": f"{type(e).__name__}: {e}"}

    finally:
        if tmp_path and tmp_path.exists():
            tmp_path.unlink()


# ---------------------------------------------------------------------------
# Package writer
# ---------------------------------------------------------------------------


def write_domain_package(
    domain_name: str,
    domain_yaml: str,
    skill_md: str,
    epistemic_py: str,
    entity_types_md: str,
    relation_types_md: str,
) -> Path:
    """Write all domain package files to the domains directory.

    Args:
        domain_name: Directory name for the domain (e.g., "real-estate").
        domain_yaml: Content for domain.yaml.
        skill_md: Content for SKILL.md.
        epistemic_py: Content for epistemic.py.
        entity_types_md: Content for references/entity-types.md.
        relation_types_md: Content for references/relation-types.md.

    Returns:
        Path to the created domain directory.
    """
    domain_dir = DOMAINS_DIR / domain_name
    refs_dir = domain_dir / "references"

    domain_dir.mkdir(parents=True, exist_ok=True)
    refs_dir.mkdir(parents=True, exist_ok=True)

    (domain_dir / "domain.yaml").write_text(domain_yaml)
    (domain_dir / "SKILL.md").write_text(skill_md)
    (domain_dir / "epistemic.py").write_text(epistemic_py)
    (domain_dir / "__init__.py").write_text("")
    (refs_dir / "entity-types.md").write_text(entity_types_md)
    (refs_dir / "relation-types.md").write_text(relation_types_md)

    return domain_dir


# ---------------------------------------------------------------------------
# High-level orchestration
# ---------------------------------------------------------------------------


def analyze_documents(
    doc_paths: list[Path],
    domain_description: str,
) -> dict:
    """Analyze sample documents and return a schema proposal.

    This is the entry point for the wizard's analysis phase. It reads documents
    and builds prompts for multi-pass LLM analysis. The actual LLM calls are
    performed by the caller (e.g., the /epistract:domain command agent).

    Args:
        doc_paths: Paths to sample documents.
        domain_description: User-provided domain description.

    Returns:
        Dict with keys: documents, prompts (containing discovery, consolidation
        prompt builders), domain_description.
    """
    docs = read_sample_documents(doc_paths)

    discovery_prompts = [
        build_schema_discovery_prompt(doc["text"], domain_description)
        for doc in docs
    ]

    return {
        "documents": docs,
        "discovery_prompts": discovery_prompts,
        "domain_description": domain_description,
    }


def generate_domain_package(
    domain_name: str,
    domain_slug: str,
    description: str,
    system_context: str,
    entity_types: dict,
    relation_types: dict,
    extraction_guidelines: str,
    contradiction_pairs: list[tuple[str, str]] | None = None,
    gap_target_types: dict | None = None,
    confidence_thresholds: dict | None = None,
) -> dict:
    """Generate and write a complete domain package.

    Args:
        domain_name: Human-readable domain name.
        domain_slug: Snake_case slug for function naming.
        description: Domain description for domain.yaml.
        system_context: System prompt for extraction agents.
        entity_types: Dict of entity type name -> {description}.
        relation_types: Dict of relation type name -> {description}.
        extraction_guidelines: Numbered guidelines for extraction.
        contradiction_pairs: Optional epistemic contradiction pairs.
        gap_target_types: Optional gap detection targets.
        confidence_thresholds: Optional confidence thresholds.

    Returns:
        Dict with keys: domain_dir, validation_result, files_written.
    """
    contradiction_pairs = contradiction_pairs or []
    gap_target_types = gap_target_types or {}
    confidence_thresholds = confidence_thresholds or {
        "high": 0.9,
        "medium": 0.7,
        "low": 0.5,
    }

    # Generate all artifacts
    domain_yaml = generate_domain_yaml(
        domain_name, description, system_context, entity_types, relation_types,
    )
    skill_md = generate_skill_md(
        domain_name, system_context, entity_types, relation_types,
        extraction_guidelines,
    )
    epistemic_py = generate_epistemic_py(
        domain_slug, entity_types, contradiction_pairs,
        gap_target_types, confidence_thresholds,
    )
    entity_types_md, relation_types_md = generate_reference_docs(
        entity_types, relation_types,
    )

    # Validate epistemic before writing
    validation = validate_generated_epistemic(epistemic_py, domain_slug)

    # Write package
    dir_name = domain_name.lower().replace(" ", "-")
    domain_dir = write_domain_package(
        dir_name, domain_yaml, skill_md, epistemic_py,
        entity_types_md, relation_types_md,
    )

    return {
        "domain_dir": str(domain_dir),
        "validation_result": validation,
        "files_written": [
            str(domain_dir / "domain.yaml"),
            str(domain_dir / "SKILL.md"),
            str(domain_dir / "epistemic.py"),
            str(domain_dir / "__init__.py"),
            str(domain_dir / "references" / "entity-types.md"),
            str(domain_dir / "references" / "relation-types.md"),
        ],
    }
