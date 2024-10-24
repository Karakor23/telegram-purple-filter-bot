import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes, ConversationHandler
from PIL import Image
import io

from config import load_config
from handlers import start, process_image, button_callback
from image_caption import add_caption
from logger import setup_logger

logger = setup_logger(__name__)

# Define conversation states
WAITING_FOR_IMAGE, WAITING_FOR_CAPTION = range(2)

async def caption_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Caption command received")
    await update.message.reply_text("Please send me an image to add a caption to.")
    return WAITING_FOR_IMAGE

async def receive_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Image received for captioning")
    if update.message.photo:
        file = await update.message.photo[-1].get_file()
    elif update.message.document:
        file = await update.message.document.get_file()
    else:
        await update.message.reply_text("Please send an image file.")
        return ConversationHandler.END

    image_bytes = await file.download_as_bytearray()
    context.user_data['image'] = Image.open(io.BytesIO(image_bytes))
    
    await update.message.reply_text("Great! Now send me the caption text you want to add to the image.")
    return WAITING_FOR_CAPTION

async def add_caption_to_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Caption text received")
    caption_text = update.message.text
    image = context.user_data['image']
    
    captioned_image = add_caption(image, caption_text)
    
    output = io.BytesIO()
    captioned_image.save(output, format='PNG')
    output.seek(0)
    
    await update.message.reply_photo(photo=output, caption="Here's your image with the caption!")
    return ConversationHandler.END

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
        
        # Caption conversation handler
        caption_conv_handler = ConversationHandler(
            entry_points=[CommandHandler("caption", caption_command)],
            states={
                WAITING_FOR_IMAGE: [MessageHandler(filters.PHOTO | filters.Document.IMAGE, receive_image)],
                WAITING_FOR_CAPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_caption_to_image)],
            },
            fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
        )
        application.add_handler(caption_conv_handler)
        
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
