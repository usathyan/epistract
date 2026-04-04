"""Template discovery and loading for the Epistract Workbench.

Loads domain-specific workbench templates from domains/*/workbench/template.yaml.
Falls back to generic defaults when no domain template exists.

Self-contained: imports only PyYAML, pathlib, os (no imports from core/).
"""
from __future__ import annotations

import os
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
