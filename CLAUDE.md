# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with this repository.

## Project Overview

**Enroute ReimburseMate** is a Telegram bot service designed to assist users with reimbursement workflows. The bot is powered by an AI workflow built with LangGraph and handles multiple input types including text, images, and documents.

## Tech Stack

- **Python 3.13+**
- **python-telegram-bot**: Async Telegram Bot API wrapper
- **LangGraph**: AI workflow orchestration (planned)
- **python-dotenv**: Environment variable management
- **uv**: Package manager

## Project Structure

```
├── app.py           # Main Telegram bot application with handlers
├── main.py          # Entry point (placeholder)
├── pyproject.toml   # Project dependencies and metadata
├── uv.lock          # Lock file for reproducible installs
├── .env             # Environment variables (not committed)
└── downloads/       # Downloaded files from users (created at runtime)
```

## Common Commands

### Setup & Installation
```bash
# Install dependencies
uv sync

# Create .env file with your bot token
echo "TELEGRAM_BOT_TOKEN=your_token_here" > .env
```

### Running the Bot
```bash
# Run the bot
uv run python app.py
```

## Architecture

### Message Handlers (app.py)

The bot uses async handlers for different content types:
- `handle_text()` - Text message processing
- `handle_photo()` - Image processing with metadata extraction
- `handle_document()` - Document handling with file download support
- `handle_video()` - Video file processing
- `handle_audio()` - Audio file processing
- `handle_voice()` - Voice message processing

### Command Handlers
- `/start` - Welcome message and bot capabilities
- `/help` - Usage instructions
- `/stats` - User activity statistics
- `/get_document` - Download last received document
- `/get_image` - Download last received image

### User State
User data is stored in `context.user_data` and tracks:
- Message counts by type (text, image, document)
- Last received file IDs for download commands

## Environment Variables

| Variable | Description |
|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather (required) |

## Development Guidelines

1. **Async/Await**: All handlers must be async functions
2. **Error Handling**: Use the centralized `error_handler()` for exceptions
3. **Logging**: Use the configured logger for all debug/info messages
4. **File Downloads**: Store in `downloads/` directory, create if not exists

## Telegram Bot Setup

1. Message @BotFather on Telegram with `/start`
2. Create a new bot with `/newbot`
3. Copy the token to your `.env` file
4. Access your bot via the provided t.me link

## Future Enhancements (LangGraph Integration)

The planned AI workflow will include:
- Receipt/invoice parsing from images
- Expense categorization
- Reimbursement form generation
- Multi-step approval workflows
