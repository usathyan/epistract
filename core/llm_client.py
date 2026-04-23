"""Synchronous LLM client with provider auto-detection.

Mirrors `examples/workbench/api_chat._resolve_api_config()` provider priority
(Azure Foundry → Anthropic direct → OpenRouter) but returns a sync call path
for use from pipeline scripts like `core/label_epistemic.py`.

Callers should import `resolve_api_config()` + `call_llm()` and handle the
`LLMConfigError` / `LLMCallError` exceptions they raise.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


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
            or "claude-sonnet-4-6"
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
            "claude-sonnet-4-20250514",
            "anthropic",
        )

    openrouter_key = os.environ.get("OPENROUTER_API_KEY")
    if openrouter_key:
        return LLMConfig(
            openrouter_key,
            "https://openrouter.ai/api/v1",
            "anthropic/claude-sonnet-4.6",
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
    timeout: float = 120.0,
) -> str:
    """Make a single synchronous LLM call and return the assistant text.

    Args:
        system: System prompt (domain persona + graph context).
        user: User message (the narrator task).
        config: Optional pre-resolved config. If None, calls resolve_api_config().
        max_tokens: Output token cap. Narratives fit comfortably in 4096.
        temperature: 0.0 = deterministic, 0.3 = light variation (default).
        timeout: Request timeout in seconds.

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
        return _call_anthropic(config, system, user, max_tokens, temperature, timeout)
    return _call_openrouter(config, system, user, max_tokens, temperature, timeout)


def _call_anthropic(
    config: LLMConfig,
    system: str,
    user: str,
    max_tokens: int,
    temperature: float,
    timeout: float,
) -> str:
    """Call Anthropic-native endpoint (direct API or Foundry gateway) via httpx."""
    try:
        import httpx
    except ImportError as e:
        raise LLMCallError("httpx is required for anthropic provider") from e

    headers = {
        "x-api-key": config.api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": config.model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }
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
