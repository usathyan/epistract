"""Template discovery and loading for the Epistract Workbench.

Loads domain-specific workbench templates from domains/*/workbench/template.yaml.
Falls back to generic defaults when no domain template exists.

Self-contained: imports only PyYAML, pathlib, os (no imports from core/).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import yaml

from examples.workbench.template_schema import WorkbenchTemplate

# ---------------------------------------------------------------------------
# Domain directory resolution
# ---------------------------------------------------------------------------

DOMAINS_DIR = Path(
    os.environ.get(
        "CLAUDE_PLUGIN_ROOT",
        str(Path(__file__).resolve().parent.parent.parent),
    )
) / "domains"

# ---------------------------------------------------------------------------
# Generic fallback template (all WorkbenchTemplate defaults)
# ---------------------------------------------------------------------------

GENERIC_TEMPLATE: dict = WorkbenchTemplate().model_dump()


def load_template(domain_name: str | None = None) -> dict:
    """Load a domain-specific workbench template.

    Args:
        domain_name: Domain directory name (e.g., "contracts", "drug-discovery").
                     If None or template not found, returns generic defaults.

    Returns:
        Plain dict with all template fields, merged with defaults.
    """
    if not domain_name:
        return dict(GENERIC_TEMPLATE)

    template_path = DOMAINS_DIR / domain_name / "workbench" / "template.yaml"
    if not template_path.exists():
        return dict(GENERIC_TEMPLATE)

    try:
        raw = yaml.safe_load(template_path.read_text())
        if not isinstance(raw, dict):
            return dict(GENERIC_TEMPLATE)
        # Validate and merge with defaults via Pydantic
        model = WorkbenchTemplate(**raw)
        return model.model_dump()
    except Exception:
        return dict(GENERIC_TEMPLATE)


def resolve_domain(
    output_dir: Path,
    explicit_domain: str | None,
) -> tuple[str | None, str]:
    """Resolve the effective domain for a workbench session.

    Precedence (D-03, D-07, D-09 — explicit beats implicit):
      1. `explicit_domain` arg is non-None → ("<arg>", "explicit")
      2. `<output_dir>/graph_data.json` has `metadata.domain` set (non-None) →
         ("<metadata>", "metadata")
      3. Otherwise → (None, "fallback") + a visible stderr warning when
         graph_data.json exists but metadata.domain is missing (D-08 legacy).

    Args:
        output_dir: Directory containing graph_data.json.
        explicit_domain: The value passed via --domain flag (or None).

    Returns:
        Tuple of (resolved_domain, source) where `source` is one of
        "explicit", "metadata", or "fallback". Callers pass resolved_domain
        to load_template().
    """
    if explicit_domain:
        return explicit_domain, "explicit"

    graph_path = Path(output_dir) / "graph_data.json"
    if not graph_path.exists():
        # Launcher already emits a "Warning: No graph_data.json found" for
        # this case; don't double-warn.
        return None, "fallback"

    try:
        graph_json = json.loads(graph_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        print(
            f"Warning: could not parse {graph_path}; domain defaults to generic",
            file=sys.stderr,
        )
        return None, "fallback"

    metadata = graph_json.get("metadata") or {}
    domain_from_meta = metadata.get("domain")
    if domain_from_meta:
        return domain_from_meta, "metadata"

    # Legacy graph (pre-Phase-17) — no domain in metadata.
    print(
        f"Warning: {graph_path} has no metadata.domain field; "
        "domain defaults to generic. Rebuild the graph with "
        "`/epistract:ingest --domain <name>` to get a domain-aware workbench.",
        file=sys.stderr,
    )
    return None, "fallback"


def auto_generate_starters(entity_types: list[str]) -> list[str]:
    """Generate starter questions from entity type names.

    Args:
        entity_types: List of entity type strings (e.g., ["COMPOUND", "GENE"]).

    Returns:
        List of 3-4 starter questions, or single fallback if no types given.
    """
    if not entity_types:
        return ["What are the main entities in this knowledge graph?"]

    # Lowercase for natural language
    types_lower = [t.lower().replace("_", " ") for t in entity_types]
    first = types_lower[0]

    questions = [
        f"What are all the {first} entities and their relationships?",
        "What conflicts or gaps exist in the data?",
        "Show me the most connected entities across all types",
    ]

    if len(types_lower) >= 2:
        second = types_lower[1]
        questions.append(
            f"How do {first} entities relate to {second} entities?"
        )

    return questions
