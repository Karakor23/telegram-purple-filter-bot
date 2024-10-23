from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from logger import setup_logger

logger = setup_logger(__name__)

async def caption_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Respond to the /caption command."""
    try:
        logger.info("Caption command received")
        await update.message.reply_text("OK")
        logger.info("Caption command handled successfully")
    except Exception as e:
        logger.error(f"Error in caption command: {str(e)}")
        logger.exception("Full traceback:")
        await update.message.reply_text("An error occurred. Please try again later.")

def setup_caption_handler(application):
    """Add the caption command handler to the application."""
    application.add_handler(CommandHandler("caption", caption_command))
    logger.info("Caption command handler set up")
