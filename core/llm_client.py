"""Synchronous LLM client with provider auto-detection.

Uses the same provider priority as `examples/workbench/api_chat._resolve_api_config()`
(Azure Foundry → Anthropic direct → OpenRouter), but returns a sync call path for
pipeline scripts like `core/label_epistemic.py`.

The two implementations are deliberately independent: `examples/` is the consumer
layer and depends on core's *output*, not its code (see CLAUDE.md §Layers). They are
NOT a shared abstraction, and an earlier docstring claiming this module "mirrors"
that one was wrong — the OpenRouter defaults had silently diverged. If you change a
default here, change it there too; the model constants below are named so a grep for
`DEFAULT_` finds both call sites.

Callers should import `resolve_api_config()` + `call_llm()` and handle the
`LLMConfigError` / `LLMCallError` exceptions they raise.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Model defaults
# ---------------------------------------------------------------------------
# Keep in sync with PROVIDER_MODELS and the defaults in
# examples/workbench/api_chat.py. See the module docstring for why these are
# duplicated rather than shared.
DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-5"
DEFAULT_OPENROUTER_MODEL = "anthropic/claude-sonnet-4.6"

# Foundry is a deployment NAME registered in Azure AI Studio, not an Anthropic
# model id — it is whatever the operator called their deployment. Changing this
# default would break every existing install whose Azure deployment is named
# `claude-sonnet-4-6`, so it is intentionally left alone. Operators point it at
# a newer model with AZURE_FOUNDRY_DEPLOYMENT.
DEFAULT_FOUNDRY_DEPLOYMENT = "claude-sonnet-4-6"


class LLMConfigError(RuntimeError):
    """Raised when credentials are set but incomplete (e.g., Foundry key without endpoint)."""


class LLMCallError(RuntimeError):
    """Raised when the LLM call itself fails."""


@dataclass(frozen=True)
class LLMConfig:
    api_key: str
    base_url: str  # For anthropic-native: full /v1/messages URL. For OpenRouter: /v1 base.
    model: str
    provider: str  # "anthropic" | "openrouter"


def _ensure_messages_suffix(url: str) -> str:
    """For anthropic-native gateways: ensure URL ends with /v1/messages."""
    url = url.rstrip("/")
    if url.endswith("/v1/messages"):
        return url
    if url.endswith("/v1"):
        return url + "/messages"
    return url + "/v1/messages"


def resolve_api_config() -> LLMConfig | None:
    """Return configured LLMConfig, or None when no credentials are present.

    Priority: Azure Foundry (Azure AI Foundry or custom Anthropic gateway) →
    Anthropic direct → OpenRouter. Raises LLMConfigError when Foundry key is
    set but endpoint config is missing (never silently falls through).
    """
    foundry_key = os.environ.get("AZURE_FOUNDRY_API_KEY") or os.environ.get(
        "ANTHROPIC_FOUNDRY_API_KEY"
    )
    if foundry_key:
        custom_base = (
            os.environ.get("AZURE_FOUNDRY_BASE_URL")
            or os.environ.get("ANTHROPIC_FOUNDRY_BASE_URL")
            or ""
        ).strip()
        resource = os.environ.get("AZURE_FOUNDRY_RESOURCE", "").strip()
        deployment = (
            os.environ.get("AZURE_FOUNDRY_DEPLOYMENT")
            or os.environ.get("ANTHROPIC_FOUNDRY_DEPLOYMENT")
            or DEFAULT_FOUNDRY_DEPLOYMENT
        )
        if custom_base:
            base_url = _ensure_messages_suffix(custom_base)
        elif resource:
            base_url = (
                f"https://{resource}.services.ai.azure.com/anthropic/v1/messages"
            )
        else:
            raise LLMConfigError(
                "Foundry API key is set but neither AZURE_FOUNDRY_BASE_URL "
                "(or ANTHROPIC_FOUNDRY_BASE_URL) nor AZURE_FOUNDRY_RESOURCE "
                "is configured. Set one and retry, or unset the key to fall "
                "back to ANTHROPIC_API_KEY / OPENROUTER_API_KEY."
            )
        return LLMConfig(foundry_key, base_url, deployment, "anthropic")

    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    if anthropic_key:
        return LLMConfig(
            anthropic_key,
            "https://api.anthropic.com/v1/messages",
            DEFAULT_ANTHROPIC_MODEL,
            "anthropic",
        )

    openrouter_key = os.environ.get("OPENROUTER_API_KEY")
    if openrouter_key:
        return LLMConfig(
            openrouter_key,
            "https://openrouter.ai/api/v1",
            os.environ.get("OPENROUTER_MODEL", DEFAULT_OPENROUTER_MODEL),
            "openrouter",
        )

    return None


def call_llm(
    system: str,
    user: str,
    *,
    config: LLMConfig | None = None,
    max_tokens: int = 4096,
    temperature: float = 0.3,
    effort: str | None = None,
    timeout: float = 120.0,
) -> str:
    """Make a single synchronous LLM call and return the assistant text.

    Args:
        system: System prompt (domain persona + graph context).
        user: User message (the narrator task).
        config: Optional pre-resolved config. If None, calls resolve_api_config().
        max_tokens: Output token cap. On current Anthropic models this budget is
            shared with thinking tokens, so leave headroom above the expected
            answer length or the response truncates mid-output.
        temperature: OpenRouter path only — see below. 0.0 = deterministic,
            0.3 = light variation (default).
        effort: Anthropic path only. One of "low" | "medium" | "high" | "xhigh"
            | "max", sent as output_config.effort. This is the current control
            for reasoning depth and token spend; it is the replacement for
            temperature on the Anthropic-native path.
        timeout: Request timeout in seconds.

    Note on `temperature`:
        Current Anthropic models (Opus 5, Sonnet 5, Opus 4.8, Opus 4.7) removed
        temperature/top_p/top_k and reject them with HTTP 400, so the
        Anthropic-native path does NOT send it. It is still honoured on the
        OpenRouter path, which is OpenAI-compatible and may route to non-Anthropic
        models where the parameter is meaningful. Callers wanting deterministic
        behaviour on Anthropic should pass effort="low" and tighten the prompt.

    Returns:
        Assistant-generated text (already stripped of markdown fences).

    Raises:
        LLMConfigError: credentials missing or incomplete.
        LLMCallError: network/API failure; wraps the underlying exception.
    """
    if config is None:
        config = resolve_api_config()
    if config is None:
        raise LLMConfigError(
            "No API key found. Set one of: AZURE_FOUNDRY_API_KEY (with "
            "AZURE_FOUNDRY_BASE_URL or AZURE_FOUNDRY_RESOURCE); "
            "ANTHROPIC_API_KEY; OPENROUTER_API_KEY."
        )

    if config.provider == "anthropic":
        return _call_anthropic(config, system, user, max_tokens, effort, timeout)
    return _call_openrouter(config, system, user, max_tokens, temperature, timeout)


def _call_anthropic(
    config: LLMConfig,
    system: str,
    user: str,
    max_tokens: int,
    effort: str | None,
    timeout: float,
) -> str:
    """Call Anthropic-native endpoint (direct API or Foundry gateway) via httpx.

    Deliberately does NOT send `temperature`. Opus 5, Sonnet 5, Opus 4.8 and
    Opus 4.7 removed temperature/top_p/top_k and reject a non-default value with
    HTTP 400 — sending it would break every call on a current model. Omitting the
    parameter is accepted by older models too, so this is safe across the board.
    Reasoning depth is controlled by `effort` instead.
    """
    try:
        import httpx
    except ImportError as e:
        raise LLMCallError("httpx is required for anthropic provider") from e

    headers = {
        "x-api-key": config.api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload: dict = {
        "model": config.model,
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }
    if effort:
        payload["output_config"] = {"effort": effort}
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(config.base_url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError as e:
        raise LLMCallError(f"Anthropic API error: {e}") from e
    except ValueError as e:  # JSON decode
        raise LLMCallError(f"Anthropic API returned non-JSON: {e}") from e

    # Anthropic returns content as list of blocks
    blocks = data.get("content") or []
    parts = [b.get("text", "") for b in blocks if b.get("type") == "text"]
    return _strip_fences("".join(parts))


def _call_openrouter(
    config: LLMConfig,
    system: str,
    user: str,
    max_tokens: int,
    temperature: float,
    timeout: float,
) -> str:
    """Call OpenRouter via the openai SDK (OpenAI-compatible)."""
    try:
        from openai import OpenAI
    except ImportError as e:
        raise LLMCallError(
            "openai SDK is required for openrouter provider. "
            "Install: uv pip install openai"
        ) from e

    client = OpenAI(api_key=config.api_key, base_url=config.base_url, timeout=timeout)
    try:
        resp = client.chat.completions.create(
            model=config.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
    except Exception as e:  # noqa: BLE001 - openai raises many shapes; all become LLMCallError
        raise LLMCallError(f"OpenRouter API error: {e}") from e

    content = (resp.choices[0].message.content or "") if resp.choices else ""
    return _strip_fences(content)


def _strip_fences(text: str) -> str:
    """Strip leading/trailing ```markdown...``` fences if present."""
    import re

    text = (text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```\s*$", "", text)
    return text.strip()
