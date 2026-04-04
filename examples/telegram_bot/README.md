# Epistract Telegram Bot

Reference implementation of a Telegram bot that queries any domain's knowledge graph via LLM.

## Prerequisites

- Python 3.11+
- `python-telegram-bot` >= 22.0
- Extraction output directory (from running the epistract pipeline)
- Telegram Bot Token (from @BotFather)
- Anthropic API key

## Setup

1. Install the bot dependency:
   ```bash
   uv pip install "python-telegram-bot>=22.0"
   ```

2. Create a bot via Telegram's @BotFather and get the token.

3. Set environment variables:
   ```bash
   export TELEGRAM_BOT_TOKEN="your-bot-token"
   export ANTHROPIC_API_KEY="your-api-key"
   ```

4. Run the bot:
   ```bash
   python -m examples.telegram_bot.bot --domain contracts --data ./output/
   ```

## Usage

- `/start` - Welcome message with domain-specific starter questions
- `/help` - Usage instructions
- Free text - Ask any question about the knowledge graph

## How It Works

The bot reuses the workbench template system (`domains/<name>/workbench/template.yaml`)
for persona, starter questions, and domain identity. It loads graph data via the same
`WorkbenchData` loader used by the web workbench.

One template system, two consumers (web workbench + Telegram bot) per D-06.
