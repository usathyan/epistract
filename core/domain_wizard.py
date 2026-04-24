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
import re
import tempfile
import textwrap
import unicodedata

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

# Phase 16 FIDL-05 — Multi-excerpt Pass-1 schema discovery.
# D-01: head(EXCERPT_CHARS) + middle(EXCERPT_CHARS centered on len//2) + tail(EXCERPT_CHARS)
# D-02: conditional on length — docs with len > MULTI_EXCERPT_THRESHOLD use the 3-excerpt path;
# shorter docs are passed through as full text for backward-compatible prompt shape.
EXCERPT_CHARS = 4000
MULTI_EXCERPT_THRESHOLD = 12000


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


def _build_excerpts(
    doc_text: str,
    excerpt_chars: int = EXCERPT_CHARS,
) -> list[str]:
    """Return head / middle / tail excerpts for long documents.

    Phase 16 FIDL-05 multi-excerpt primitive. For documents short enough
    to fit under MULTI_EXCERPT_THRESHOLD, this returns the empty list —
    the caller passes full text to the LLM instead. For longer documents,
    returns exactly three `excerpt_chars`-long slices: the first `excerpt_chars`
    chars (head), a slice centered on `len(doc_text) // 2` of width
    `excerpt_chars` (middle, D-03), and the last `excerpt_chars` chars (tail).

    Args:
        doc_text: Full document text.
        excerpt_chars: Width of each excerpt slice. Defaults to EXCERPT_CHARS (4000).

    Returns:
        Empty list if `len(doc_text) <= MULTI_EXCERPT_THRESHOLD`.
        Otherwise a 3-element list: [head_slice, middle_slice, tail_slice].
    """
    if len(doc_text) <= MULTI_EXCERPT_THRESHOLD:
        return []

    half = excerpt_chars // 2
    mid_center = len(doc_text) // 2
    m0 = mid_center - half
    m1 = mid_center + half

    head = doc_text[:excerpt_chars]
    middle = doc_text[m0:m1]
    tail = doc_text[-excerpt_chars:]
    return [head, middle, tail]


def build_schema_discovery_prompt(doc_text: str, domain_description: str) -> str:
    """Build Pass 1 prompt: discover entity and relation types from a single document.

    For documents longer than MULTI_EXCERPT_THRESHOLD, sends three explicit excerpts
    (head / middle / tail) with `[EXCERPT N/3 — chars X to Y]` markers so the LLM
    does not infer false contiguity between disjoint slices (D-04). The preface
    sentence is spelled out per D-05. For shorter documents, sends the full text
    under the original singular `**Document text:**` header (backward-compatible
    prompt shape; D-02).

    Args:
        doc_text: Full text of the sample document.
        domain_description: User-provided description of the domain.

    Returns:
        Prompt string for LLM schema discovery.
    """
    excerpts = _build_excerpts(doc_text)

    if excerpts:
        head, middle, tail = excerpts
        mid_center = len(doc_text) // 2
        half = EXCERPT_CHARS // 2
        m0 = mid_center - half
        m1 = mid_center + half
        tail_start = len(doc_text) - EXCERPT_CHARS
        tail_end = len(doc_text)
        body = textwrap.dedent(f"""\
            **Document excerpts:**
            The following are three excerpts from a larger document. Treat them as non-contiguous samples of the same document, not as a single continuous passage.

            [EXCERPT 1/3 — chars 0 to {EXCERPT_CHARS} (head)]
            {head}

            [EXCERPT 2/3 — chars {m0} to {m1} (middle)]
            {middle}

            [EXCERPT 3/3 — chars {tail_start} to {tail_end} (tail)]
            {tail}
            """)
    else:
        body = textwrap.dedent(f"""\
            **Document text:**
            {doc_text}
            """)

    return textwrap.dedent(f"""\
        You are an expert knowledge graph schema designer.

        **Domain description:** {domain_description}

        **Task:** Analyze the following document and identify candidate entity types
        and relation types for building a knowledge graph in this domain.

        {body}
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
    community_label_anchors: list[str] | None = None,
) -> str:
    """Generate domain.yaml content as YAML string.

    Args:
        domain_name: Human-readable domain name (e.g., "Real Estate Leases").
        description: Multi-line domain description.
        system_context: System prompt for LLM extraction context.
        entity_types: Dict of entity type name -> {description}.
        relation_types: Dict of relation type name -> {description}.
        community_label_anchors: Optional ordered list of entity type names used
            as label anchors for community detection output. When provided, emitted
            as the last top-level key in domain.yaml. Omitted when None.

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
    if community_label_anchors is not None:
        schema["community_label_anchors"] = community_label_anchors
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


        # ------------------------------------------------------------------
        # CUSTOM_RULES -- domain-specific epistemic rules (FIDL-07 opt-in)
        # ------------------------------------------------------------------
        # Each rule is a callable with signature:
        #     rule(nodes: list[dict], links: list[dict], context: dict) -> list[dict]
        # where context = {{"output_dir", "graph_data", "domain_name"}}.
        # Rule failures are isolated (one exception logs status='error' but
        # does NOT abort the phase). Findings merge into
        # claims_layer["super_domain"]["custom_findings"][rule.__name__].
        # See docs/known-limitations.md (Per-Domain Extensibility, FIDL-07)
        # for the full contract. Example:
        #
        #     def my_rule(nodes, links, context):
        #         return [{{"rule_name": "my_rule", "type": "example",
        #                   "severity": "INFO", "description": "x",
        #                   "evidence": {{}}}}]
        #     CUSTOM_RULES.append(my_rule)

        CUSTOM_RULES: list = []
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
# FIDL-08 — Slug + workbench template helpers (Phase 19 Plan 19-01)
# ---------------------------------------------------------------------------

# 12-color vis.js-friendly palette cycled by entity_type alphabetical order
# when emitting workbench/template.yaml (D-04). Locked order — UT-052 asserts
# indices 0, 1, 2 explicitly; any reorder is a breaking change requiring a
# test update.
DEFAULT_ENTITY_COLORS = [
    "#97c2fc",
    "#ffa07a",
    "#90ee90",
    "#f1c40f",
    "#e74c3c",
    "#9b59b6",
    "#1abc9c",
    "#e67e22",
    "#34495e",
    "#fd79a8",
    "#636e72",
    "#00b894",
]


def generate_slug(name: str) -> str:
    """Produce a safe directory name from a human-readable domain name.

    Rules (D-01):
        1. NFKD-normalize and strip non-ASCII chars (accents, CJK, etc.).
        2. Lowercase.
        3. Replace every run of non-[a-z0-9] with a single '-'.
        4. Strip leading/trailing '-'.
        5. Collapse any residual '--+' to a single '-'.

    Raises:
        ValueError: If the final slug is empty OR contains '--' (defense in
            depth — the regex should prevent '--' but the assertion catches
            any future regex drift).

    Examples:
        >>> generate_slug("Q&A Analysis (v2)")
        'q-a-analysis-v2'
        >>> generate_slug("  Hello World  ")
        'hello-world'
        >>> generate_slug("drug-discovery")  # existing-domain invariant
        'drug-discovery'
    """
    # (1) + (2) NFKD + ASCII strip + lowercase
    ascii_value = (
        unicodedata.normalize("NFKD", name)
        .encode("ascii", "ignore")
        .decode("ascii")
        .lower()
    )
    # (3) Non-alnum runs → single '-'
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_value)
    # (4) Strip leading/trailing hyphens
    slug = slug.strip("-")
    # (5) Defensive: collapse '--+' (the regex above should already prevent
    # these, but a belt-and-suspenders pass guards against future regex drift)
    slug = re.sub(r"-+", "-", slug)
    # Post-condition: reject empty or malformed
    if not slug or "--" in slug:
        raise ValueError(f"Cannot derive slug from: {name!r}")
    return slug


def generate_workbench_template(
    domain_slug: str,
    entity_types: dict,
    persona_override: str | None = None,
) -> str:
    """Emit a Pydantic-valid workbench/template.yaml for a new domain (D-04).

    The ``persona`` field serves DUAL purposes — single source of truth:
      1. Workbench chat system prompt (reactive: fires on user questions).
      2. ``core.label_epistemic`` automatic narrator (proactive: fires after
         ``/epistract:epistemic`` runs, produces epistemic_narrative.md).

    Callers who want a custom-tailored persona can supply ``persona_override``
    — typically elicited from the user during ``/epistract:domain`` interactive
    wizard, or synthesized by the wizard LLM from the domain description. When
    omitted, an analyst-shaped template is used with the domain slug substituted
    in — richer than a one-liner, weaker than a hand-crafted persona, and
    immediately usable.

    Produces a complete override (not a partial) — every field of
    ``examples.workbench.template_schema.WorkbenchTemplate`` is populated so
    downstream consumers never fall back to defaults. Colors assigned
    deterministically by sorting entity_types keys alphabetically and cycling
    through ``DEFAULT_ENTITY_COLORS`` via modulo (D-04 + D-16).

    Args:
        domain_slug: The normalized slug (from generate_slug) — used to seed
            stub title/subtitle/persona text.
        entity_types: Mapping of entity-type name -> {description: ...}.
            Insertion order is NOT honored — keys are sorted alphabetically
            before palette assignment to guarantee determinism (UT-052 gate).
        persona_override: Optional full persona paragraph(s). When provided,
            used verbatim. When None, falls back to the default analyst
            template below.

    Returns:
        YAML string (from yaml.safe_dump, sort_keys=False) ready to write to
        ``domains/<slug>/workbench/template.yaml``.
    """
    pretty_name = domain_slug.replace("-", " ").replace("_", " ").title()
    pretty_lower = pretty_name.lower()
    sorted_entity_types = sorted(entity_types.keys())
    entity_colors = {
        entity_type: DEFAULT_ENTITY_COLORS[i % len(DEFAULT_ENTITY_COLORS)]
        for i, entity_type in enumerate(sorted_entity_types)
    }

    default_persona = textwrap.dedent(f"""\
        You are a senior {pretty_lower} analyst. You have reviewed the corpus
        summarized below and built a knowledge graph of the entities and
        relationships defined in this domain's schema.

        Your role is to ANALYZE, not just retrieve. When answering questions or
        producing a briefing:

        EPISTEMIC STATUS IS PART OF THE ANSWER.
        The graph annotates each relation with a status: asserted (stated with
        definitive / quantitative evidence), prophetic (forward-looking language
        such as "is expected to" / "may be prepared by"; claims not yet
        demonstrated), hypothesized (hedged wording like "suggests" / "may" /
        "appears to"), speculative (single-source conjecture), negative
        (explicit absence of effect), and contested (same relation with
        conflicting confidence across sources). Call out status whenever it
        changes interpretation.

        SYNTHESIZE ACROSS DOCUMENTS. Note convergence and divergence. Group
        related claims into named clusters. Don't repeat raw counts — interpret
        them.

        SURFACE GAPS. Silence is a finding. If the graph is missing something a
        domain analyst would expect, say so explicitly.

        CITATION DISCIPLINE. Every factual claim must reference its source
        document(s) by ID. When sources disagree, show both sides.

        FORMAT. Markdown tables for cross-entity comparisons, bullet lists for
        summaries, inline code for entity names, block quotes for verbatim
        source evidence.

        TONE. Direct and precise. Hedge only when the evidence is hedged.
        Never fabricate — if a question is outside the graph's coverage, say
        so and explain what data would close the gap.
        """)

    data = {
        "title": f"{pretty_name} Knowledge Graph Explorer",
        "subtitle": f"Explore {pretty_lower} entities and relationships",
        "persona": persona_override.strip() if (persona_override and persona_override.strip()) else default_persona.strip(),
        "placeholder": "Ask a question about the knowledge graph...",
        "loading_message": "Analyzing",
        "starter_questions": [],
        "entity_colors": entity_colors,
        "dashboard": {
            "title": f"{pretty_name} Knowledge Graph Summary",
            "subtitle": "",
        },
        "analysis_patterns": {
            "cross_references_heading": "CROSS-DOMAIN REFERENCES",
            "appears_in_phrase": "appears in",
        },
    }
    return yaml.safe_dump(data, sort_keys=False, default_flow_style=False, allow_unicode=True)


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
    *,
    workbench_yaml: str | None = None,
) -> Path:
    """Write all domain package files to the domains directory.

    Args:
        domain_name: Directory name for the domain (e.g., "real-estate").
        domain_yaml: Content for domain.yaml.
        skill_md: Content for SKILL.md.
        epistemic_py: Content for epistemic.py.
        entity_types_md: Content for references/entity-types.md.
        relation_types_md: Content for references/relation-types.md.
        workbench_yaml: Optional content for workbench/template.yaml
            (FIDL-08 D-05). When None, no workbench/ dir is created — existing
            callers are byte-identical. When provided, creates
            `domain_dir/workbench/` and writes `template.yaml`.

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

    if workbench_yaml is not None:
        workbench_dir = domain_dir / "workbench"
        workbench_dir.mkdir(parents=True, exist_ok=True)
        (workbench_dir / "template.yaml").write_text(workbench_yaml)

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
    persona: str | None = None,
    community_label_anchors: list[str] | None = None,
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
        persona: Optional custom workbench/narrator persona paragraph. When
            None, ``generate_workbench_template`` emits an analyst-shaped
            default template with the domain slug substituted — richer than
            a one-liner and immediately usable, but users are encouraged to
            hand-tailor for best narrator output. Persona serves BOTH the
            workbench chat prompt (reactive) and the ``/epistract:epistemic``
            narrator (proactive, writes ``epistemic_narrative.md``).

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
        community_label_anchors=community_label_anchors,
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

    # Write package (FIDL-08 D-02 + D-06 — slug via generate_slug, workbench template auto-emit)
    dir_name = generate_slug(domain_name)
    workbench_yaml = generate_workbench_template(
        dir_name, entity_types, persona_override=persona,
    )
    domain_dir = write_domain_package(
        dir_name, domain_yaml, skill_md, epistemic_py,
        entity_types_md, relation_types_md,
        workbench_yaml=workbench_yaml,
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
            str(domain_dir / "workbench" / "template.yaml"),
        ],
    }


# ---------------------------------------------------------------------------
# FIDL-08 Phase 19 Plan 19-02 — --schema bypass (D-09, D-10, D-11)
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """Wizard CLI entry point supporting the --schema bypass.

    Usage:
        python -m core.domain_wizard --schema <file.json> --name <slug>

    The --schema flag skips the 3-pass LLM discovery entirely (D-11) and
    generates a domain package directly from the user-supplied JSON schema.
    --name is required (D-10) since there is no sample corpus to derive a
    name from.

    The interactive wizard flow (sample-document analysis) is NOT invoked
    here — it is orchestrated by the Claude command agent in
    commands/domain.md, which calls analyze_documents() and
    generate_domain_package() directly.

    Args:
        argv: Optional list of CLI args (excluding program name). When None,
              defaults to sys.argv[1:]. Tests pass an explicit list for
              deterministic invocation.

    Returns:
        Exit code: 0 on success, non-zero on error.
    """
    import sys as _sys
    argv = argv if argv is not None else _sys.argv[1:]

    if "--schema" not in argv:
        print(
            "Usage: python -m core.domain_wizard --schema <file.json> --name <slug>\n"
            "       (Interactive wizard flow is invoked via /epistract:domain.)",
            file=_sys.stderr,
        )
        return 1

    # Parse --schema <file>
    try:
        schema_path = argv[argv.index("--schema") + 1]
    except IndexError:
        print("Error: --schema requires a file path argument", file=_sys.stderr)
        return 1

    # Parse --name <slug> (D-10 required)
    if "--name" not in argv:
        print(
            "Error: --schema requires --name <slug> (no sample corpus to derive a name from)",
            file=_sys.stderr,
        )
        return 1
    try:
        domain_name = argv[argv.index("--name") + 1]
    except IndexError:
        print("Error: --name requires a slug argument", file=_sys.stderr)
        return 1

    # Load + validate schema (D-09)
    try:
        schema = json.loads(Path(schema_path).read_text())
    except (OSError, json.JSONDecodeError) as e:
        print(f"Error: cannot load schema file {schema_path}: {e}", file=_sys.stderr)
        return 1

    for required_key in ("entity_types", "relation_types"):
        if required_key not in schema or not isinstance(schema[required_key], dict):
            print(
                f"Error: schema file missing required key '{required_key}' "
                f"(required: entity_types, relation_types — must be dicts)",
                file=_sys.stderr,
            )
            return 1

    # Defaults for optional keys
    description = schema.get("description", "")
    system_context = schema.get("system_context", "Domain extraction pipeline")
    extraction_guidelines = schema.get("extraction_guidelines", "Follow domain schema.")
    contradiction_pairs = schema.get("contradiction_pairs", [])
    gap_target_types = schema.get("gap_target_types", {})
    confidence_thresholds = schema.get("confidence_thresholds", {
        "high": 0.9, "medium": 0.7, "low": 0.5,
    })
    # Persona: optional; surfaces in workbench chat AND epistemic narrator.
    # When absent, generate_workbench_template falls back to the analyst-shaped
    # default with the domain slug substituted.
    persona = schema.get("persona")
    # community_label_anchors: optional list of entity types used to anchor
    # community labels (domain-aware labeling).  Must be read here so that
    # --schema bypass callers can supply anchors without going through the
    # interactive wizard.
    community_label_anchors = schema.get("community_label_anchors") or None

    # D-11: bypass the 3-pass LLM discovery — call generate_domain_package directly.
    # Mirror commands/domain.md:140 slug convention (hyphens → underscores for function names).
    domain_slug = domain_name.replace("-", "_")
    result = generate_domain_package(
        domain_name=domain_name,
        domain_slug=domain_slug,
        description=description,
        system_context=system_context,
        entity_types=schema["entity_types"],
        relation_types=schema["relation_types"],
        extraction_guidelines=extraction_guidelines,
        contradiction_pairs=contradiction_pairs,
        gap_target_types=gap_target_types,
        confidence_thresholds=confidence_thresholds,
        persona=persona,
        community_label_anchors=community_label_anchors,
    )

    print(f"Domain package created at: {result['domain_dir']}")
    print("Files written:")
    for f in result["files_written"]:
        print(f"  - {f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
