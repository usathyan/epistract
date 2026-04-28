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

# ---------------------------------------------------------------------------
# OpenRouter live model cache (module-level — survives across requests)
# ---------------------------------------------------------------------------
_or_models_cache: dict = {"data": None, "fetched_at": 0.0}
_OR_CACHE_TTL = 3600  # seconds — OpenRouter adds ~27 models / month
_OPENROUTER_DEFAULT_MODEL = "anthropic/claude-sonnet-4"

# Mapping of OpenRouter id prefix -> category label for optgroup rendering.
# The tilde prefix used on "latest" aliases (e.g. ~anthropic/) is stripped
# before lookup. Unknown prefixes fall into "Other".
CATEGORY_MAP: dict[str, str] = {
    "anthropic": "Claude (Anthropic)",
    "openai": "GPT / O-series (OpenAI)",
    "google": "Gemini / Gemma (Google)",
    "meta-llama": "Llama (Meta)",
    "mistralai": "Mistral",
    "deepseek": "DeepSeek",
    "qwen": "Qwen (Alibaba)",
    "x-ai": "Grok (xAI)",
    "nvidia": "Nvidia",
    "cohere": "Cohere",
    "amazon": "Amazon",
    "perplexity": "Perplexity",
}


def _filter_and_group_or_models(raw: list[dict]) -> list[dict]:
    """Filter OpenRouter models to text-output only and attach group/cost fields.

    Exclusions (in order):
      - architecture.output_modalities != ["text"]  (drops image/audio generators)
      - id startswith "openrouter/"                  (router meta-models)
      - expiration_date set and < today               (expired models)
      - float(pricing.prompt) < 0                     (variable-price routers)

    Returns new dicts with fields: id, label, group, input_cost, output_cost,
    context_length, free. Defensive parsing tolerates missing/None fields —
    never raise from this function.
    """
    from datetime import date

    today = date.today().isoformat()
    result: list[dict] = []
    for m in raw:
        arch = m.get("architecture", {}) or {}
        if arch.get("output_modalities") != ["text"]:
            continue
        model_id = m.get("id", "") or ""
        if model_id.startswith("openrouter/"):
            continue
        exp = m.get("expiration_date")
        if exp and exp < today:
            continue
        pricing = m.get("pricing", {}) or {}
        try:
            prompt_price = float(pricing.get("prompt", "0") or "0")
        except (ValueError, TypeError):
            prompt_price = 0.0
        if prompt_price < 0:
            continue
        try:
            completion_price = float(pricing.get("completion", "0") or "0")
        except (ValueError, TypeError):
            completion_price = 0.0
        # Strip leading '~' (latest-alias prefix) before lookup.
        prefix = model_id.split("/")[0].lstrip("~")
        group = CATEGORY_MAP.get(prefix, "Other")
        name = m.get("name", model_id) or model_id
        label_name = name.split(": ", 1)[1] if ": " in name else name
        is_free = prompt_price == 0.0
        input_cost_per_million = round(prompt_price * 1_000_000, 4)
        output_cost_per_million = round(completion_price * 1_000_000, 4)
        cost_label = "free" if is_free else f"${input_cost_per_million:.2f}/M"
        result.append(
            {
                "id": model_id,
                "label": f"{label_name} ({cost_label})",
                "group": group,
                "input_cost": 0.0 if is_free else input_cost_per_million,
                "output_cost": 0.0 if is_free else output_cost_per_million,
                "context_length": m.get("context_length", 0) or 0,
                "free": is_free,
            }
        )
    return result


async def _check_or_model_health(
    models: list[dict],
    client: "httpx.AsyncClient",  # noqa: F821
) -> list[dict]:
    """Parallel health check using the OpenRouter endpoints API.

    For ALL models: exclude if endpoints array is empty (no active providers).
    For free-tier models additionally: exclude if uptime signals indicate degraded service.

    Three-value verdict per model:
      "ok"           — healthy or no data to judge against
      "no_endpoints" — empty endpoints array (exclude ALL models)
      "low_uptime"   — below thresholds (exclude FREE models only)

    Thresholds:
      - uptime_last_5m >= 70%  -> INCLUDE (recent data, healthy)
      - uptime_last_5m <  70%  -> EXCLUDE free; keep paid
      - uptime_last_5m null AND uptime_last_1d >= 80%  -> INCLUDE
      - uptime_last_5m null AND uptime_last_1d <  80%  -> EXCLUDE free; keep paid
      - both null           -> INCLUDE (fail open: no data)
      - Any network error   -> INCLUDE (fail open per-task)
    """
    import asyncio

    async def fetch_health(model_id: str) -> tuple[str, str]:
        url = f"https://openrouter.ai/api/v1/models/{model_id}/endpoints"
        try:
            resp = await client.get(url, timeout=5.0)
            data = resp.json().get("data") or {}
            endpoints = data.get("endpoints") or []
            if not endpoints:
                return model_id, "no_endpoints"
            uptimes_5m = [
                e["uptime_last_5m"]
                for e in endpoints
                if e.get("uptime_last_5m") is not None
            ]
            uptimes_1d = [
                e["uptime_last_1d"]
                for e in endpoints
                if e.get("uptime_last_1d") is not None
            ]
            best_5m = max(uptimes_5m) if uptimes_5m else None
            best_1d = max(uptimes_1d) if uptimes_1d else None
            if best_5m is not None:
                return model_id, "ok" if best_5m >= 70.0 else "low_uptime"
            if best_1d is not None:
                return model_id, "ok" if best_1d >= 80.0 else "low_uptime"
            return model_id, "ok"
        except Exception:
            return model_id, "ok"

    tasks = [fetch_health(m["id"]) for m in models]
    results: dict[str, str] = dict(await asyncio.gather(*tasks))

    filtered: list[dict] = []
    for m in models:
        verdict = results.get(m["id"], "ok")
        if verdict == "no_endpoints":
            continue
        if verdict == "low_uptime" and m.get("free"):
            continue
        filtered.append(m)
    return filtered


async def _fetch_or_models() -> list[dict]:
    """Fetch and cache the OpenRouter text-output model list.

    TTL: _OR_CACHE_TTL seconds. On network error, returns cached data if
    any, else static PROVIDER_MODELS['openrouter'] (Plan 03 fallback).
    """
    import time

    import httpx

    from examples.workbench.api_chat import PROVIDER_MODELS

    now = time.time()
    if _or_models_cache["data"] is not None and (
        now - _or_models_cache["fetched_at"] < _OR_CACHE_TTL
    ):
        return _or_models_cache["data"]
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get("https://openrouter.ai/api/v1/models")
            resp.raise_for_status()
            raw = resp.json().get("data", []) or []
        models = _filter_and_group_or_models(raw)
        # Plan 05: filter out operationally-broken models via parallel /endpoints probe.
        # Separate AsyncClient with a connection-pool cap; fail-open at the gather level.
        try:
            async with httpx.AsyncClient(
                timeout=10.0, limits=httpx.Limits(max_connections=50)
            ) as health_client:
                models = await _check_or_model_health(models, health_client)
        except Exception:
            pass  # fail-open: keep the pre-health-check filtered list
        _or_models_cache["data"] = models
        _or_models_cache["fetched_at"] = now
        return models
    except Exception:
        if _or_models_cache["data"] is not None:
            return _or_models_cache["data"]
        return PROVIDER_MODELS["openrouter"]


# Localhost-only CORS allowlist (VUL-07 / SEC-05). The workbench is a developer tool;
# any cross-origin request from outside localhost is refused. Add additional ports here
# if the workbench is started on a non-default bind. The wildcard "*" is intentionally
# NOT used — see RESEARCH section "VUL-07 — CORS Wildcard".
LOCALHOST_ORIGINS: list[str] = [
    "http://localhost:8501",
    "http://127.0.0.1:8501",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]


def create_app(output_dir: Path, domain: str | None = None) -> FastAPI:
    """Create and configure the FastAPI application.

    FIDL-06: Resolves the effective domain via resolve_domain (precedence:
    explicit arg > graph_data.json metadata.domain > None/fallback).
    """
    resolved_domain, _source = resolve_domain(Path(output_dir), domain)
    template = load_template(resolved_domain)
    app = FastAPI(title=template.get("title", "Knowledge Graph Explorer"))

    # CORS for local development (per D-07, localhost only). Wildcard "*" was
    # replaced with an explicit allowlist — see VUL-07 / SEC-05 in
    # .planning/phases/08-workbench-security-hardening/08-RESEARCH.md.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=LOCALHOST_ORIGINS,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
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
            models = await _fetch_or_models()
            default = _OPENROUTER_DEFAULT_MODEL
            if not any(m.get("id") == default for m in models):
                default = models[0]["id"] if models else _OPENROUTER_DEFAULT_MODEL
            return {
                "provider": "openrouter",
                "default_model": default,
                "models": models,
            }
        return {"provider": None, "default_model": None, "models": []}

    return app
