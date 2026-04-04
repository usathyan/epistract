"""Tests for the Telegram bot reference implementation.

Tests pure functions only -- does NOT require python-telegram-bot installed.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Ensure project root is on sys.path for imports
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------------------
# Test: bot module imports without error (telegram lib not required)
# ---------------------------------------------------------------------------

def test_bot_module_imports():
    """Bot module should import without python-telegram-bot installed."""
    from examples.telegram_bot.bot import format_welcome_message, build_bot_system_prompt
    assert callable(format_welcome_message)
    assert callable(build_bot_system_prompt)


# ---------------------------------------------------------------------------
# Test: format_welcome_message with contracts template
# ---------------------------------------------------------------------------

def test_format_welcome_with_starters():
    """Welcome message should include title and numbered starter questions."""
    from examples.telegram_bot.bot import format_welcome_message

    template = {
        "title": "Sample Contract Analysis Workbench",
        "starter_questions": [
            "What are the top cross-contract conflicts?",
            "Walk me through every deadline",
        ],
    }
    msg = format_welcome_message(template)

    assert "STA" in msg, "Welcome should contain template title"
    assert "1." in msg, "Welcome should have numbered questions"
    assert "2." in msg, "Welcome should have second numbered question"
    assert "conflicts" in msg.lower(), "Welcome should contain starter question text"


def test_format_welcome_empty_starters():
    """With no starters, welcome should show generic prompt."""
    from examples.telegram_bot.bot import format_welcome_message

    template = {"title": "Test KG", "starter_questions": []}
    msg = format_welcome_message(template)

    assert "Send any question" in msg, "Empty starters should show generic prompt"
    assert "Test KG" in msg, "Welcome should still contain title"


def test_format_welcome_no_title():
    """With no title, welcome should use default."""
    from examples.telegram_bot.bot import format_welcome_message

    msg = format_welcome_message({})
    assert "Knowledge Graph Explorer" in msg, "Should use default title"


# ---------------------------------------------------------------------------
# Test: build_bot_system_prompt contains persona
# ---------------------------------------------------------------------------

def test_bot_template_system_prompt():
    """System prompt should contain the template persona."""
    from examples.telegram_bot.bot import build_bot_system_prompt

    # Create a mock WorkbenchData
    mock_data = MagicMock()
    mock_data.graph_data = {"nodes": [], "edges": []}
    mock_data.claims_layer = {}
    mock_data.communities = {}
    mock_data.documents = []

    template = {
        "persona": "You are the Contract Guru who knows everything about vendor agreements.",
        "title": "Contract Analysis",
    }
    prompt = build_bot_system_prompt(mock_data, template)

    assert "Contract Guru" in prompt, "System prompt should contain persona text"
    assert isinstance(prompt, str), "System prompt should be a string"
