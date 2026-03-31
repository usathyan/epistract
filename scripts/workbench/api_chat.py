"""Chat API endpoint with Claude Sonnet SSE streaming."""
from __future__ import annotations

import json
import os
from typing import AsyncGenerator

from fastapi import APIRouter, Request
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from scripts.workbench.system_prompt import build_system_prompt, get_matched_source_chunks

router = APIRouter(prefix="/api", tags=["chat"])

# ---------------------------------------------------------------------------
# Check for Anthropic SDK
# ---------------------------------------------------------------------------
try:
    from anthropic import AsyncAnthropic

    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


# ---------------------------------------------------------------------------
# Request model
# ---------------------------------------------------------------------------


class ChatRequest(BaseModel):
    """Chat request body."""

    question: str
    history: list[dict] = []  # [{"role": "user"|"assistant", "content": "..."}]


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.post("/chat")
async def chat(request: Request, body: ChatRequest):
    """Stream a Claude response as SSE events.

    Per D-03: Uses claude-sonnet-4-20250514.
    Per D-08: Session-only history (frontend manages, sends in request).
    Per D-09: Full KG context in system prompt + matched source chunks.
    """
    if not HAS_ANTHROPIC:
        return EventSourceResponse(
            _error_stream(
                "anthropic SDK not installed. Run: uv pip install anthropic"
            )
        )

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return EventSourceResponse(
            _error_stream("ANTHROPIC_API_KEY environment variable not set")
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
    # Include last 10 messages from history to stay within token limits
    recent_history = body.history[-10:] if len(body.history) > 10 else body.history
    for msg in recent_history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_content})

    return EventSourceResponse(
        _stream_response(api_key, system, messages),
        media_type="text/event-stream",
    )


async def _stream_response(
    api_key: str, system: str, messages: list[dict]
) -> AsyncGenerator[dict, None]:
    """Stream Claude response as SSE data events."""
    client = AsyncAnthropic(api_key=api_key)

    try:
        async with client.messages.stream(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=system,
            messages=messages,
        ) as stream:
            async for text in stream.text_stream:
                yield {"data": json.dumps({"type": "text", "content": text})}
    except Exception as e:
        yield {"data": json.dumps({"type": "error", "content": str(e)})}

    yield {"data": json.dumps({"type": "done"})}


async def _error_stream(message: str) -> AsyncGenerator[dict, None]:
    """Stream an error message."""
    yield {"data": json.dumps({"type": "error", "content": message})}
    yield {"data": json.dumps({"type": "done"})}
