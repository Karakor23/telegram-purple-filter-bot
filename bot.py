import logging
import sys
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

from config import load_config
from handlers import start, process_image, button_callback
from logger import setup_logger

logger = setup_logger(__name__)

async def caption_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Caption command received")
    await update.message.reply_text("OK from caption command")
    logger.info("Caption command response sent")

def main():
    """Start the bot."""
    try:
        logger.info("Starting bot initialization")
        config = load_config()
        
        # Create the Application
        application = Application.builder().token(config.TOKEN).build()

        # Add handlers
        logger.info("Adding handlers")
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("caption", caption_command))
        application.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, process_image))
        application.add_handler(CallbackQueryHandler(button_callback))
        
        # Start the Bot
        logger.info("Bot is starting...")
        application.run_polling()
        
    except Exception as e:
        logger.error(f"Critical error starting bot: {e}")
        logger.exception("Full traceback:")
        raise

if __name__ == '__main__':
    main()
