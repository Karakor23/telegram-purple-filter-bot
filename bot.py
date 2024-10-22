import os
import io
import logging
from PIL import Image, ImageEnhance
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get token from environment variable
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    logger.error("No TELEGRAM_BOT_TOKEN found in environment variables")
    raise ValueError("No TELEGRAM_BOT_TOKEN found in environment variables")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    try:
        welcome_message = ("Welcome to the Purple Filter Bot! 🟣\n\n"
                        "Send me any image and I'll apply a purple-black filter to it.\n"
                        "You can adjust the intensity using the buttons that appear with the filtered image.")
        await update.message.reply_text(welcome_message)
    except Exception as e:
        logger.error(f"Error in start command: {str(e)}")
        await update.message.reply_text("An error occurred. Please try again later.")

def apply_purple_black_tone(img, purple_intensity=1.0, black_intensity=1.0, contrast=1.0):
    """Apply the purple-black filter to an image."""
    try:
        img = img.convert('RGB')
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(contrast)
        
        def adjust_channel(pixel, purple_factor, black_factor):
            purple_value = min(int(pixel * (1.0 + (purple_intensity * purple_factor))), 255)
            black_threshold = 128
            if pixel < black_threshold:
                black_value = int(pixel * (1.0 - (black_intensity * black_factor)))
            else:
                black_value = pixel
            return min(purple_value, black_value)
        
        r, g, b = img.split()
        
        r = r.point(lambda i: adjust_channel(i, 0.3, 0.2))
        g = g.point(lambda i: adjust_channel(i, -0.3, 0.3))
        b = b.point(lambda i: adjust_channel(i, 0.3, 0.3))
        
        return Image.merge('RGB', (r, g, b))
    except Exception as e:
        logger.error(f"Error in apply_purple_black_tone: {str(e)}")
        raise

async def process_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process the received image and apply the filter."""
    try:
        logger.info("Starting image processing")
        
        # Get the photo file
        photo = update.message.photo[-1]
        photo_file = await context.bot.get_file(photo.file_id)
        
        logger.info("Downloading image")
        # Download the image
        image_bytes = await photo_file.download_as_bytearray()
        image = Image.open(io.BytesIO(image_bytes))
        
        # Resize if the image is too large
        max_size = 1280
        if max(image.size) > max_size:
            ratio = max_size / max(image.size)
            new_size = tuple(int(dim * ratio) for dim in image.size)
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        logger.info("Applying filter")
        # Apply filter with default values
        processed_image = apply_purple_black_tone(image)
        
        # Save the processed image to bytes
        output = io.BytesIO()
        processed_image.save(output, format='JPEG')
        output.seek(0)
        
        # Create intensity adjustment buttons
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
        
        # Store original image and current settings in context
        context.user_data['original_image'] = image
        context.user_data['settings'] = {
            'purple': 1.0,
            'black': 1.0,
            'contrast': 1.0
        }
        
        logger.info("Sending processed image")
        # Send the processed image with adjustment buttons
        await update.message.reply_photo(
            photo=output,
            reply_markup=reply_markup
        )
        logger.info("Image processing completed successfully")
        
    except Exception as e:
        logger.error(f"Error in process_image: {str(e)}")
        await update.message.reply_text(
            "Sorry, there was an error processing your image. Please try again with a different image or contact support if the problem persists."
        )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button presses for adjusting filter intensities."""
    try:
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
        
        if 'original_image' not in context.user_data:
            await query.message.reply_text("Sorry, I couldn't find the original image. Please send a new image.")
            return
            
        # Process image with new settings
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
        
    except Exception as e:
        logger.error(f"Error in button_callback: {str(e)}")
        await query.message.reply_text(
            "Sorry, there was an error adjusting the image. Please try sending a new image."
        )

def main():
    """Start the bot."""
    try:
        logger.info("Starting bot initialization")
        # Create the Application
        application = Application.builder().token(TOKEN).build()

        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.PHOTO, process_image))
        application.add_handler(CallbackQueryHandler(button_callback))

        # Start the Bot
        logger.info("Bot is starting...")
        application.run_polling()
        
    except Exception as e:
        logger.error(f"Critical error starting bot: {e}")
        raise

if __name__ == '__main__':
    main()