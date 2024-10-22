import os
import io
import logging
import sys
import traceback
from PIL import Image, ImageEnhance
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from dotenv import load_dotenv

# Set up logging with more detailed format
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def get_token():
    """Get token with detailed logging."""
    # Try different methods to get the token
    token = None
    logger.info("Attempting to get token...")
    
    # Method 1: Direct environment variable
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if token:
        logger.info("Token found in os.environ")
        return token
        
    # Method 2: Through dotenv
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if token:
        logger.info("Token found through dotenv")
        return token
    
    # Debug information
    logger.error("Token not found. Available environment variables:")
    for key in os.environ:
        logger.error(f"- {key}")
    
    raise ValueError("No TELEGRAM_BOT_TOKEN found in environment variables")

# Get token
try:
    TOKEN = get_token()
    logger.info("Successfully loaded token")
except Exception as e:
    logger.error(f"Error loading token: {str(e)}")
    raise

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    try:
        logger.info("Start command received")
        welcome_message = ("Welcome to the Purple Filter Bot! 🟣\n\n"
                        "Send me any image and I'll apply a purple-black filter to it.\n"
                        "You can adjust the intensity using the buttons that appear with the filtered image.")
        await update.message.reply_text(welcome_message)
        logger.info("Start command handled successfully")
    except Exception as e:
        logger.error(f"Error in start command: {str(e)}")
        logger.exception("Full traceback:")
        await update.message.reply_text("An error occurred. Please try again later.")

def apply_purple_black_tone(img, purple_intensity=1.0, black_intensity=1.0, contrast=1.0):
    """Apply the purple-black filter to an image."""
    try:
        logger.info(f"Applying filter with settings - purple: {purple_intensity}, black: {black_intensity}, contrast: {contrast}")
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
        
        logger.info("Splitting channels")
        r, g, b = img.split()
        
        logger.info("Processing channels")
        r = r.point(lambda i: adjust_channel(i, 0.3, 0.2))
        g = g.point(lambda i: adjust_channel(i, -0.3, 0.3))
        b = b.point(lambda i: adjust_channel(i, 0.3, 0.3))
        
        logger.info("Merging channels")
        return Image.merge('RGB', (r, g, b))
    except Exception as e:
        logger.error(f"Error in apply_purple_black_tone: {str(e)}")
        logger.exception("Full traceback:")
        raise

async def process_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process the received image and apply the filter."""
    try:
        logger.info("Starting image processing")
        
        # Get the photo file
        logger.info("Getting photo file")
        photo = update.message.photo[-1]
        logger.info(f"Photo size: {photo.width}x{photo.height}")
        
        logger.info("Getting file from Telegram")
        photo_file = await context.bot.get_file(photo.file_id)
        
        logger.info("Downloading image bytes")
        # Download the image
        image_bytes = await photo_file.download_as_bytearray()
        logger.info(f"Downloaded {len(image_bytes)} bytes")
        
        logger.info("Opening image with PIL")
        image = Image.open(io.BytesIO(image_bytes))
        logger.info(f"Original image size: {image.size}")
        
        # Resize if the image is too large
        max_size = 1280
        if max(image.size) > max_size:
            logger.info("Resizing image")
            ratio = max_size / max(image.size)
            new_size = tuple(int(dim * ratio) for dim in image.size)
            image = image.resize(new_size, Image.Resampling.LANCZOS)
            logger.info(f"New image size: {image.size}")
        
        logger.info("Applying purple filter")
        # Apply filter with default values
        processed_image = apply_purple_black_tone(image)
        logger.info("Filter applied successfully")
        
        # Save the processed image to bytes
        logger.info("Saving processed image")
        output = io.BytesIO()
        processed_image.save(output, format='JPEG')
        output.seek(0)
        logger.info("Image saved to bytes")
        
        # Create intensity adjustment buttons
        logger.info("Creating keyboard markup")
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
        logger.info("Storing image in context")
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
        logger.exception("Full traceback:")
        await update.message.reply_text(
            "Sorry, there was an error processing your image. Please try again with a different image or contact support if the problem persists."
        )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button presses for adjusting filter intensities."""
    try:
        logger.info("Button callback received")
        query = update.callback_query
        await query.answer()
        
        # Get current settings
        logger.info("Getting current settings")
        settings = context.user_data.get('settings', {
            'purple': 1.0,
            'black': 1.0,
            'contrast': 1.0
        })
        
        # Adjust settings based on button press
        adjustment = 0.5
        logger.info(f"Processing button: {query.data}")
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
        
        logger.info(f"New settings: {settings}")
        # Update stored settings
        context.user_data['settings'] = settings
        
        if 'original_image' not in context.user_data:
            logger.error("Original image not found in context")
            await query.message.reply_text("Sorry, I couldn't find the original image. Please send a new image.")
            return
            
        logger.info("Processing image with new settings")
        # Process image with new settings
        processed_image = apply_purple_black_tone(
            context.user_data['original_image'],
            settings['purple'],
            settings['black'],
            settings['contrast']
        )
        
        # Save the processed image to bytes
        logger.info("Saving processed image")
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
        
        logger.info("Updating message with new image")
        await query.message.edit_media(
            media=InputMediaPhoto(output),
            reply_markup=reply_markup
        )
        logger.info("Button callback completed successfully")
        
    except Exception as e:
        logger.error(f"Error in button_callback: {str(e)}")
        logger.exception("Full traceback:")
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
        logger.info("Adding handlers")
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.PHOTO, process_image))
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
