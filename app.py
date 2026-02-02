"""
Telegram Bot that handles text messages, images, and documents.
Supports Python 3.8+
"""

import logging
import mimetypes
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from src.db import init_db_from_env
from src.graph.graph import graph
from src.schemas.state import WorkflowState
from src.tools.minio_storage import get_minio_client, upload_bytes

load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load bot token from environment variable
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]

compiled_graph = graph.compile()

def _extract_response_text(result: object) -> str | None:
    """Extract response_text from a graph result payload."""
    if isinstance(result, dict):
        return result.get("response_text")
    return getattr(result, "response_text", None)


# ==================== COMMAND HANDLERS ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    welcome_message = """
    Welcome to the Multi-Content Telegram Bot! 👋
    
    I can handle:
    • 📝 Text messages
    • 🖼️ Images (JPG, PNG, GIF, WebP)
    • 📄 Documents (PDF, TXT, DOCX, etc.)
    
    Just send me any of these and I'll process them for you!
    
    Commands:
    /start - Show this message
    /help - Get help
    /stats - View your activity stats
    """
    await update.message.reply_text(welcome_message)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = """
    How to use this bot:
    
    1. **Text Messages**: Send any text and I'll acknowledge it
    2. **Images**: Send photos and I'll tell you about them
    3. **Documents**: Send files and I'll download and process them
    
    You can send multiple items at once (images + captions, etc.)
    """
    await update.message.reply_text(help_text)


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user stats."""
    user_id = update.effective_user.id
    user_data = context.user_data
    
    text_count = user_data.get('text_count', 0)
    image_count = user_data.get('image_count', 0)
    document_count = user_data.get('document_count', 0)
    
    stats_message = f"""
    📊 Your Stats:
    
    Messages sent: {text_count}
    Images sent: {image_count}
    Documents sent: {document_count}
    Total items: {text_count + image_count + document_count}
    """
    await update.message.reply_text(stats_message)


# ==================== MESSAGE HANDLERS ====================

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text messages."""
    user = update.effective_user
    user_id = user.id
    text = update.message.text
    
    # Update stats
    context.user_data['text_count'] = context.user_data.get('text_count', 0) + 1
    
    # Log the message
    logger.info("Text from %s (%s): %s...", user.first_name or "User", user_id, text[:50])

    state = WorkflowState(
        user_input=text,
        telegram_user_id=str(user_id),
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
    )
    result = compiled_graph.invoke(state.model_dump())
    response_text = _extract_response_text(result) or "✅ Got it. Thanks!"
    await update.message.reply_text(response_text)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle photo/image messages."""
    user = update.effective_user
    
    # Update stats
    context.user_data['image_count'] = context.user_data.get('image_count', 0) + 1
    
    # Get the photo (get the largest size)
    photo = update.message.photo[-1]
    file_id = photo.file_id
    file_size = photo.file_size
    width = photo.width
    height = photo.height
    
    logger.info("Photo from %s: %sx%s, size: %s bytes", user.first_name or "User", width, height, file_size)
    
    # Get caption if provided
    caption = update.message.caption or "No caption"
    
    # Store file_id for later retrieval if needed
    context.user_data['last_photo_id'] = file_id

    try:
        file = await context.bot.get_file(file_id)
        file_bytes = await file.download_as_bytearray()
        file_path = getattr(file, "file_path", "") or ""
        suffix = os.path.splitext(file_path)[1] or ".jpg"
        content_type = getattr(file, "mime_type", None)
        if not content_type:
            content_type = mimetypes.guess_type(file_path)[0] or "image/jpeg"
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        object_name = f"telegram/{update.effective_user.id}/{timestamp}_{file_id}{suffix}"

        client, bucket = get_minio_client()
        upload_bytes(
            client,
            bucket,
            object_name,
            bytes(file_bytes),
            content_type,
            metadata={"file_id": file_id},
        )
        logger.info("Image uploaded to MinIO: %s/%s", bucket, object_name)
        uploaded_file_id = file_id
    except Exception as exc:
        logger.error("Failed to upload image to MinIO: %s", exc)
        uploaded_file_id = None

    state = WorkflowState(
        user_input=caption,
        telegram_user_id=str(user.id),
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        file_id=uploaded_file_id,
    )
    result = compiled_graph.invoke(state.model_dump())
    response_text = _extract_response_text(result) or "✅ Image received. Thanks!"
    await update.message.reply_text(response_text)

# ==================== ERROR HANDLER ====================

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    
    if update and isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            "❌ An error occurred. Please try again later."
        )


# ==================== MAIN ====================

def main() -> None:
    """Start the bot."""

    # Check if token is set
    if not TELEGRAM_BOT_TOKEN :
        print("❌ ERROR: Please set your BOT_TOKEN in the script!")
        print("Get your token from @BotFather on Telegram")
        return

    init_db_from_env()
    
    # Create the Application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats))

    # Register message handlers
    # Order matters: more specific filters should come first
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Register error handler
    application.add_error_handler(error_handler)

    # Start the Bot
    print("✅ Bot is running! Press Ctrl+C to stop.")
    print(f"📱 Search for @BotFather on Telegram to create a bot and get your token")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
