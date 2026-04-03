"""Chat API endpoint with LLM SSE streaming."""
from __future__ import annotations

import json
import os
from typing import AsyncGenerator

import httpx
from fastapi import APIRouter, Request
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from examples.workbench.system_prompt import build_system_prompt, get_matched_source_chunks

router = APIRouter(prefix="/api", tags=["chat"])


# ---------------------------------------------------------------------------
# Request model
# ---------------------------------------------------------------------------


class ChatRequest(BaseModel):
    """Chat request body."""

    question: str
    history: list[dict] = []  # [{"role": "user"|"assistant", "content": "..."}]


# ---------------------------------------------------------------------------
# API key resolution
# ---------------------------------------------------------------------------


def _resolve_api_config() -> tuple[str | None, str, str, str]:
    """Return (api_key, base_url, model, provider) from available env vars.

    Priority:
    1. ANTHROPIC_API_KEY -> direct Anthropic API (native format)
    2. OPENROUTER_API_KEY -> OpenRouter (OpenAI-compatible format)
    """
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    if anthropic_key:
        return anthropic_key, "https://api.anthropic.com/v1/messages", "claude-sonnet-4-20250514", "anthropic"

    openrouter_key = os.environ.get("OPENROUTER_API_KEY")
    if openrouter_key:
        return openrouter_key, "https://openrouter.ai/api/v1/chat/completions", "anthropic/claude-sonnet-4", "openrouter"

    return None, "", "", ""


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.post("/chat")
async def chat(request: Request, body: ChatRequest):
    """Stream an LLM response as SSE events."""
    api_key, base_url, model, provider = _resolve_api_config()
    if not api_key:
        return EventSourceResponse(
            _error_stream(
                "No API key found. Set ANTHROPIC_API_KEY or OPENROUTER_API_KEY."
            )
        )

    data = request.app.state.data

    # Build system prompt with full KG context
    system = build_system_prompt(data)

    # Add matched source chunks to the user's question context
    source_context = get_matched_source_chunks(data, body.question)
    user_content = body.question
    if source_context:
        user_content = f"{body.question}\n\n---\n{source_context}"

    # Build messages array with history (D-08: session only, last 10 turns max)
    messages = []
    recent_history = body.history[-10:] if len(body.history) > 10 else body.history
    for msg in recent_history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_content})

    if provider == "anthropic":
        return EventSourceResponse(
            _stream_anthropic(api_key, base_url, model, system, messages),
            media_type="text/event-stream",
        )
    else:
        return EventSourceResponse(
            _stream_openai_compat(api_key, base_url, model, system, messages),
            media_type="text/event-stream",
        )


async def _stream_anthropic(
    api_key: str, base_url: str, model: str, system: str, messages: list[dict]
) -> AsyncGenerator[dict, None]:
    """Stream via Anthropic's native API using httpx."""
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": model,
        "max_tokens": 4096,
        "system": system,
        "messages": messages,
        "stream": True,
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", base_url, json=payload, headers=headers) as resp:
                if resp.status_code != 200:
                    body = await resp.aread()
                    yield {"data": json.dumps({"type": "error", "content": f"API error {resp.status_code}: {body.decode()[:500]}"})}
                    yield {"data": json.dumps({"type": "done"})}
                    return

                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        event = json.loads(data_str)
                        if event.get("type") == "content_block_delta":
                            delta = event.get("delta", {})
                            text = delta.get("text", "")
                            if text:
                                yield {"data": json.dumps({"type": "text", "content": text})}
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        yield {"data": json.dumps({"type": "error", "content": str(e)})}

    yield {"data": json.dumps({"type": "done"})}


async def _stream_openai_compat(
    api_key: str, base_url: str, model: str, system: str, messages: list[dict]
) -> AsyncGenerator[dict, None]:
    """Stream via OpenAI-compatible API (OpenRouter) using httpx."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/epistract",
        "X-Title": "STA Contract Workbench",
    }
    # OpenAI format: system message goes in messages array
    oai_messages = [{"role": "system", "content": system}] + messages
    payload = {
        "model": model,
        "max_tokens": 4096,
        "messages": oai_messages,
        "stream": True,
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", base_url, json=payload, headers=headers) as resp:
                if resp.status_code != 200:
                    body = await resp.aread()
                    yield {"data": json.dumps({"type": "error", "content": f"API error {resp.status_code}: {body.decode()[:500]}"})}
                    yield {"data": json.dumps({"type": "done"})}
                    return

                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        event = json.loads(data_str)
                        choices = event.get("choices", [])
                        if choices:
                            delta = choices[0].get("delta", {})
                            text = delta.get("content", "")
                            if text:
                                yield {"data": json.dumps({"type": "text", "content": text})}
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        yield {"data": json.dumps({"type": "error", "content": str(e)})}

    yield {"data": json.dumps({"type": "done"})}


async def _error_stream(message: str) -> AsyncGenerator[dict, None]:
    """Stream an error message."""
    yield {"data": json.dumps({"type": "error", "content": message})}
    yield {"data": json.dumps({"type": "done"})}
