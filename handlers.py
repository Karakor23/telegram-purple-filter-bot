import io
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ContextTypes
import telegram
from PIL import Image

from image_processor import apply_purple_black_tone, add_watermark
from logger import setup_logger

logger = setup_logger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    try:
        logger.info("Start command received")
        welcome_message = (
            "Welcome to the Purple Filter Market Dominance Bot! 🟣\n\n"
            "Send me a JPEG or PNG image and I'll apply a purple-black filter to it.\n"
            "You can adjust the intensity using the buttons that appear with the filtered image. \n"
            "Website: https://dominance.market/ \n"
            "https://x.com/MarketDomSol \n"
            "https://t.me/market_dominance"
        )
        await update.message.reply_text(welcome_message)
        logger.info("Start command handled successfully")
    except Exception as e:
        logger.error(f"Error in start command: {str(e)}")
        logger.exception("Full traceback:")
        await update.message.reply_text("An error occurred. Please try again later.")

async def process_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process the received image and apply the filter."""
    try:
        logger.info("Starting image processing")
        
        # Get the file information
        if not update.message.photo and update.message.document:
            file = update.message.document
            if not file.mime_type in ["image/jpeg", "image/png"]:
                await update.message.reply_text(
                    "Sorry, I can only process JPEG or PNG images. Please send a valid image file."
                )
                return
            photo_file = await context.bot.get_file(file.file_id)
        elif update.message.photo:
            photo = update.message.photo[-1]
            logger.info(f"Photo size: {photo.width}x{photo.height}")
            photo_file = await context.bot.get_file(photo.file_id)
        else:
            await update.message.reply_text(
                "Please send me a JPEG or PNG image to apply the purple filter."
            )
            return
        
        logger.info("Downloading image bytes")
        image_bytes = await photo_file.download_as_bytearray()
        logger.info(f"Downloaded {len(image_bytes)} bytes")
        
        logger.info("Opening image with PIL")
        image = Image.open(io.BytesIO(image_bytes))
        
        if image.format not in ['JPEG', 'PNG']:
            await update.message.reply_text(
                "Sorry, I can only process JPEG or PNG images. "
                "Please send an image in one of these formats."
            )
            return
            
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
        processed_image = apply_purple_black_tone(image)
        logger.info("Filter applied successfully")
        
        logger.info("Adding watermark")
        processed_image = add_watermark(processed_image)
        
        logger.info("Saving processed image")
        output = io.BytesIO()
        processed_image.save(output, format='JPEG')
        output.seek(0)
        logger.info("Image saved to bytes")
        
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
        
        logger.info("Storing image in context")
        context.user_data['original_image'] = image
        context.user_data['settings'] = {
            'purple': 1.0,
            'black': 1.0,
            'contrast': 1.0
        }
        
        logger.info("Sending processed image")
        await update.message.reply_photo(
            photo=output,
            reply_markup=reply_markup
        )
        logger.info("Image processing completed successfully")
        
    except Exception as e:
        logger.error(f"Error in process_image: {str(e)}")
        logger.exception("Full traceback:")
        await update.message.reply_text(
            "Sorry, there was an error processing your image. "
            "Please make sure you're sending a valid JPEG or PNG image and try again."
        )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button presses for adjusting filter intensities."""
    try:
        logger.info("Button callback received")
        query = update.callback_query
        await query.answer()
        
        logger.info("Getting current settings")
        settings = context.user_data.get('settings', {
            'purple': 1.0,
            'black': 1.0,
            'contrast': 1.0
        })
        
        old_settings = settings.copy()
        
        adjustment = 0.5
        logger.info(f"Processing button: {query.data}")
        if query.data == "purple_up":
            if settings['purple'] < 4.0:
                settings['purple'] = min(4.0, settings['purple'] + adjustment)
        elif query.data == "purple_down":
            if settings['purple'] > 0.0:
                settings['purple'] = max(0.0, settings['purple'] - adjustment)
        elif query.data == "black_up":
            if settings['black'] < 4.0:
                settings['black'] = min(4.0, settings['black'] + adjustment)
        elif query.data == "black_down":
            if settings['black'] > 0.0:
                settings['black'] = max(0.0, settings['black'] - adjustment)
        elif query.data == "contrast_up":
            if settings['contrast'] < 3.0:
                settings['contrast'] = min(3.0, settings['contrast'] + adjustment)
        elif query.data == "contrast_down":
            if settings['contrast'] > 0.0:
                settings['contrast'] = max(0.0, settings['contrast'] - adjustment)
        
        if settings == old_settings:
            logger.info("Settings unchanged, skipping update")
            await query.answer("Maximum/minimum value reached!")
            return
            
        logger.info(f"New settings: {settings}")
        context.user_data['settings'] = settings
        
        if 'original_image' not in context.user_data:
            logger.error("Original image not found in context")
            await query.message.reply_text("Sorry, I couldn't find the original image. Please send a new image.")
            return
            
        logger.info("Processing image with new settings")
        try:
            processed_image = apply_purple_black_tone(
                context.user_data['original_image'],
                settings['purple'],
                settings['black'],
                settings['contrast']
            )
            
            processed_image = add_watermark(processed_image)
            
            logger.info("Saving processed image")
            output = io.BytesIO()
            processed_image.save(output, format='JPEG')
            output.seek(0)
            
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
            
        except telegram.error.BadRequest as e:
            if "Message is not modified" in str(e):
                logger.info("Image unchanged, ignoring update")
                await query.answer("No change in image!")
            else:
                raise
            
    except Exception as e:
        logger.error(f"Error in button_callback: {str(e)}")
        logger.exception("Full traceback:")
        await query.message.reply_text(
            "Sorry, there was an error adjusting the image. Please try sending a new image."
        )
