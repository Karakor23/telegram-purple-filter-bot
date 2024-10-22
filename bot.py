import os
import io
from PIL import Image, ImageEnhance
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get token from environment variable
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    raise ValueError("No TELEGRAM_BOT_TOKEN found in environment variables")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    welcome_message = ("Welcome to the Purple Filter Bot! 🟣\n\n"
                      "Send me any image and I'll apply a purple-black filter to it.\n"
                      "You can adjust the intensity using the buttons that appear with the filtered image.")
    await update.message.reply_text(welcome_message)

[... rest of your code remains the same until button_callback function ...]

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button presses for adjusting filter intensities."""
    query = update.callback_query
    await query.answer()
    
    # Get current settings
    settings = context.user_data.get('settings', {
        'purple': 1.0,
        'black': 1.0,
        'contrast': 1.0
    })
    
    # Adjust settings based on button press
    adjustment = 0.5
    if query.data == "purple_up":
        settings['purple'] = min(4.0, settings['purple'] + adjustment)
    elif query.data == "purple_down":
        settings['purple'] = max(0.0, settings['purple'] - adjustment)
    elif query.data == "black_up":
        settings['black'] = min(4.0, settings['black'] + adjustment)
    elif query.data == "black_down":
        settings['black'] = max(0.0, settings['black'] - adjustment)
    elif query.data == "contrast_up":
        settings['contrast'] = min(3.0, settings['contrast'] + adjustment)
    elif query.data == "contrast_down":
        settings['contrast'] = max(0.0, settings['contrast'] - adjustment)
    
    # Update stored settings
    context.user_data['settings'] = settings
    
    # Process image with new settings
    if 'original_image' in context.user_data:
        processed_image = apply_purple_black_tone(
            context.user_data['original_image'],
            settings['purple'],
            settings['black'],
            settings['contrast']
        )
        
        # Save the processed image to bytes
        output = io.BytesIO()
        processed_image.save(output, format='JPEG')
        output.seek(0)
        
        # Update the image with the same buttons
        keyboard = [
            [
                InlineKeyboardButton("↑ Purple", callback_data="purple_up"),
                InlineKeyboardButton("↓ Purple", callback_data="purple_down")
            ],
            [
                InlineKeyboardButton("↑ Black", callback_data="black_up"),
                InlineKeyboardButton("↓ Black", callback_data="black_down")
            ],
            [
                InlineKeyboardButton("↑ Contrast", callback_data="contrast_up"),
                InlineKeyboardButton("↓ Contrast", callback_data="contrast_down")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_media(
            media=InputMediaPhoto(output),
            reply_markup=reply_markup
        )

def main():
    """Start the bot."""
    try:
        # Create the Application
        application = Application.builder().token(TOKEN).build()

        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.PHOTO, process_image))
        application.add_handler(CallbackQueryHandler(button_callback))

        # Start the Bot
        print("Bot is starting...")
        application.run_polling()
        
    except Exception as e:
        print(f"Error starting bot: {e}")
        raise

if __name__ == '__main__':
    main()