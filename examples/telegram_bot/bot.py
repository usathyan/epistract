"""Epistract Telegram Bot -- reference implementation.

A domain-agnostic Telegram bot that loads any domain's graph data,
answers questions via LLM, and demonstrates the template pattern.

Usage:
    python -m examples.telegram_bot.bot --domain contracts --data ./output/ --token $BOT_TOKEN

Requires: python-telegram-bot>=22.0, httpx
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Template + Data (reuse workbench infrastructure per D-06)
# ---------------------------------------------------------------------------

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from examples.workbench.template_loader import load_template, auto_generate_starters  # noqa: E402
from examples.workbench.data_loader import WorkbenchData  # noqa: E402

logger = logging.getLogger(__name__)


def build_bot_system_prompt(data: WorkbenchData, template: dict) -> str:
    """Build system prompt for LLM -- reuses workbench pattern."""
    from examples.workbench.system_prompt import build_system_prompt

    return build_system_prompt(data, template)


def format_welcome_message(template: dict) -> str:
    """Format /start welcome message with domain title and starters."""
    title = template.get("title", "Knowledge Graph Explorer")
    starters = template.get("starter_questions", [])
    msg = f"Welcome to {title}!\n\n"
    if starters:
        msg += "Try asking:\n"
        for i, q in enumerate(starters[:5], 1):
            msg += f"{i}. {q}\n"
    else:
        msg += "Send any question about the knowledge graph.\n"
    msg += "\nType /help for more info."
    return msg


# ---------------------------------------------------------------------------
# Bot handlers (require python-telegram-bot)
# ---------------------------------------------------------------------------

try:
    from telegram import Update, BotCommand  # noqa: F401
    from telegram.ext import (
        Application,
        CommandHandler,
        MessageHandler,
        filters,
        ContextTypes,
    )

    HAS_TELEGRAM = True
except ImportError:
    HAS_TELEGRAM = False


if HAS_TELEGRAM:

    async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        template = context.bot_data["template"]
        await update.message.reply_text(format_welcome_message(template))

    async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        template = context.bot_data["template"]
        title = template.get("title", "Knowledge Graph Explorer")
        await update.message.reply_text(
            f"Send any question about the knowledge graph. "
            f"I'll answer using {title} data.\n\n"
            f"Commands:\n/start - Welcome message\n/help - This help text"
        )

    async def handle_message(
        update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle free-text messages -- query LLM with graph context."""
        import httpx

        template = context.bot_data["template"]
        data = context.bot_data["data"]
        question = update.message.text

        # Build system prompt with full KG context
        system = build_bot_system_prompt(data, template)

        # Resolve API config (same as workbench)
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            await update.message.reply_text(
                "No ANTHROPIC_API_KEY set. Cannot query LLM."
            )
            return

        # Send typing indicator
        await update.message.chat.send_action("typing")

        # Call Anthropic API (non-streaming for Telegram)
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": "claude-sonnet-4-20250514",
                        "max_tokens": 4096,
                        "system": system,
                        "messages": [{"role": "user", "content": question}],
                    },
                )
                if resp.status_code != 200:
                    await update.message.reply_text(
                        f"API error: {resp.status_code}"
                    )
                    return
                result = resp.json()
                text = result["content"][0]["text"]
                # Telegram max message length is 4096
                if len(text) > 4000:
                    text = text[:4000] + "\n\n... (truncated)"
                await update.message.reply_text(text)
        except Exception as e:
            logger.error("LLM request failed: %s", e)
            await update.message.reply_text(
                "LLM request failed. Verify your API key is configured and try again."
            )


def run_bot(token: str, domain: str | None, data_dir: Path):
    """Start the Telegram bot."""
    if not HAS_TELEGRAM:
        print("Error: python-telegram-bot not installed.")
        print("Install with: uv pip install 'python-telegram-bot>=22.0'")
        sys.exit(1)

    template = load_template(domain)
    data = WorkbenchData(data_dir)

    app = Application.builder().token(token).build()
    app.bot_data["template"] = template
    app.bot_data["data"] = data

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    logger.info("Starting bot with domain=%s, data=%s", domain, data_dir)
    app.run_polling()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Epistract Telegram Bot")
    parser.add_argument(
        "--domain", help="Domain name (e.g., contracts, drug-discovery)"
    )
    parser.add_argument(
        "--data", required=True, help="Path to extraction output directory"
    )
    parser.add_argument(
        "--token", help="Telegram bot token (or set TELEGRAM_BOT_TOKEN env)"
    )
    args = parser.parse_args()

    bot_token = args.token or os.environ.get("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        print("Error: Provide --token or set TELEGRAM_BOT_TOKEN env var")
        sys.exit(1)

    run_bot(bot_token, args.domain, Path(args.data))
