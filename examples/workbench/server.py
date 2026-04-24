"""Epistract Workbench - Domain-agnostic knowledge graph explorer."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from examples.workbench.api_chat import router as chat_router
from examples.workbench.api_graph import router as graph_router
from examples.workbench.api_sources import router as sources_router
from examples.workbench.data_loader import WorkbenchData
from examples.workbench.template_loader import (
    DOMAINS_DIR,
    load_template,
    resolve_domain,
)

STATIC_DIR = Path(__file__).parent / "static"


def create_app(output_dir: Path, domain: str | None = None) -> FastAPI:
    """Create and configure the FastAPI application.

    FIDL-06: Resolves the effective domain via resolve_domain (precedence:
    explicit arg > graph_data.json metadata.domain > None/fallback).
    """
    resolved_domain, _source = resolve_domain(Path(output_dir), domain)
    template = load_template(resolved_domain)
    app = FastAPI(title=template.get("title", "Knowledge Graph Explorer"))

    # CORS for local development (per D-07, localhost only)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Load data at startup
    app.state.data = WorkbenchData(output_dir)
    app.state.template = template

    # Store output_dir and domain name for later use
    app.state.output_dir = output_dir
    app.state._domain_name = resolved_domain  # FIDL-06: use resolved, not raw
    app.state._domain_source = _source  # FIDL-06: expose for debugging

    # Include API routers
    app.include_router(graph_router)
    app.include_router(sources_router)
    app.include_router(chat_router)

    # Mount static files (create dir if needed for dev)
    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/")
    async def root():
        index = STATIC_DIR / "index.html"
        if index.exists():
            return FileResponse(str(index))
        return {
            "message": template.get("title", "Knowledge Graph Explorer"),
            "status": "running",
            "static_dir": "not found - create examples/workbench/static/index.html",
        }

    @app.get("/api/template")
    async def get_template():
        return app.state.template

    @app.get("/api/dashboard")
    async def get_dashboard():
        """Return dashboard HTML content for the current domain.

        Two paths:
          1. If domains/<domain>/workbench/dashboard.html exists, serve it directly.
          2. Otherwise, auto-generate a summary from graph stats (entity counts
             by type, total nodes, total edges, top communities).
        """
        template = app.state.template
        domain = app.state._domain_name
        if domain:
            dashboard_html_path = DOMAINS_DIR / domain / "workbench" / "dashboard.html"
            if dashboard_html_path.exists():
                return {"html": dashboard_html_path.read_text(encoding="utf-8")}
        # Auto-generate from graph stats
        data = app.state.data
        nodes = data.get_nodes()
        edges = data.get_edges()
        entity_counts: dict[str, int] = {}
        for n in nodes:
            t = n.get("entity_type", "UNKNOWN")
            entity_counts[t] = entity_counts.get(t, 0) + 1
        # `template.get("dashboard")` may return None (Pydantic default) when
        # the domain template has no `dashboard:` block. `dict.get(k, default)`
        # only honors the default when the key is missing, not when the value
        # is None — so we explicitly coalesce.
        dashboard_block = template.get("dashboard") or {}
        title = dashboard_block.get(
            "title", template.get("title", "Knowledge Graph Summary")
        )
        subtitle = dashboard_block.get("subtitle", template.get("subtitle", ""))
        return {
            "html": None,
            "auto": True,
            "title": title,
            "subtitle": subtitle,
            "entity_counts": entity_counts,
            "total_nodes": len(nodes),
            "total_edges": len(edges),
        }

    @app.get("/api/health")
    async def health():
        import os

        data = app.state.data
        # Which LLM provider the chat panel will use on the next request.
        # Order mirrors api_chat._resolve_api_config(). AZURE_FOUNDRY_* and
        # ANTHROPIC_FOUNDRY_* are accepted as aliases.
        has_foundry = bool(
            os.environ.get("AZURE_FOUNDRY_API_KEY")
            or os.environ.get("ANTHROPIC_FOUNDRY_API_KEY")
        )
        if has_foundry:
            has_custom_base = bool(
                os.environ.get("AZURE_FOUNDRY_BASE_URL")
                or os.environ.get("ANTHROPIC_FOUNDRY_BASE_URL")
            )
            provider = "azure-foundry-custom" if has_custom_base else "azure-foundry"
        elif os.environ.get("ANTHROPIC_API_KEY"):
            provider = "anthropic"
        elif os.environ.get("OPENROUTER_API_KEY"):
            provider = "openrouter"
        else:
            provider = None
        return {
            "status": "ok",
            "output_dir": str(data.output_dir),
            "nodes": len(data.get_nodes()),
            "edges": len(data.get_edges()),
            "documents": len(data.documents),
            "has_claims": bool(data.claims_layer),
            "has_api_key": bool(
                has_foundry
                or os.environ.get("ANTHROPIC_API_KEY")
                or os.environ.get("OPENROUTER_API_KEY")
            ),
            "llm_provider": provider,
        }

    @app.get("/api/models")
    async def get_models():
        """Return the curated model list for the active LLM provider.

        Detection mirrors /api/health. We intentionally do NOT call
        api_chat._resolve_api_config() because that function raises
        RuntimeError when Foundry keys are set without a base URL or
        resource — which would break this endpoint on every page-load.
        Foundry returns a single-entry list (deployment name) so the
        frontend hides the selector (only one choice available).
        """
        import os

        from examples.workbench.api_chat import PROVIDER_MODELS

        has_foundry = bool(
            os.environ.get("AZURE_FOUNDRY_API_KEY")
            or os.environ.get("ANTHROPIC_FOUNDRY_API_KEY")
        )
        if has_foundry:
            deployment = (
                os.environ.get("AZURE_FOUNDRY_DEPLOYMENT")
                or os.environ.get("ANTHROPIC_FOUNDRY_DEPLOYMENT")
                or "claude-sonnet-4-6"
            )
            has_custom_base = bool(
                os.environ.get("AZURE_FOUNDRY_BASE_URL")
                or os.environ.get("ANTHROPIC_FOUNDRY_BASE_URL")
            )
            provider = "azure-foundry-custom" if has_custom_base else "azure-foundry"
            return {
                "provider": provider,
                "default_model": deployment,
                "models": [{"id": deployment, "label": deployment}],
            }
        if os.environ.get("ANTHROPIC_API_KEY"):
            models = PROVIDER_MODELS["anthropic"]
            return {
                "provider": "anthropic",
                "default_model": models[0]["id"],
                "models": models,
            }
        if os.environ.get("OPENROUTER_API_KEY"):
            models = PROVIDER_MODELS["openrouter"]
            return {
                "provider": "openrouter",
                "default_model": models[0]["id"],
                "models": models,
            }
        return {"provider": None, "default_model": None, "models": []}

    return app
