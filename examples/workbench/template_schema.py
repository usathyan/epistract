"""Pydantic models for workbench template configuration.

Defines the schema for domain-specific workbench templates loaded from
domains/*/workbench/template.yaml files.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class DashboardConfig(BaseModel):
    """Dashboard panel configuration."""

    title: str = "Knowledge Graph Summary"
    subtitle: str = ""


class WorkbenchTemplate(BaseModel):
    """Domain-specific workbench template configuration.

    Loaded from domains/{domain}/workbench/template.yaml.
    All fields have sensible defaults for generic (domain-agnostic) use.
    """

    title: str = "Knowledge Graph Explorer"
    subtitle: str = "Explore entities and relationships"
    persona: str = (
        "You are a knowledge graph analyst. "
        "Answer questions using the graph data provided."
    )
    placeholder: str = "Ask a question about the knowledge graph..."
    loading_message: str = "Analyzing"
    starter_questions: list[str] = Field(default_factory=list)
    entity_colors: dict[str, str] = Field(default_factory=dict)
    dashboard: DashboardConfig | None = None
