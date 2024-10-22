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

def apply_purple_black_tone(img, purple_intensity=1.0, black_intensity=1.0, contrast=1.0):
    """Apply the purple-black filter to an image."""
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

async def process_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process the received image and apply the filter."""
    try:
        # Get the photo file
        photo = update.message.photo[-1]  # Get the largest available photo
        photo_file = await context.bot.get_file(photo.file_id)
        
        # Download the image
        image_bytes = await photo_file.download_as_bytearray()
        image = Image.open(io.BytesIO(image_bytes))
        
        # Resize if the image is too large (Telegram has size limits)
        max_size = 1280
        if max(image.size) > max_size:
            ratio = max_size / max(image.size)
            new_size = tuple(int(dim * ratio) for dim in image.size)
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
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
        
        # Send the processed image with adjustment buttons
        await update.message.reply_photo(
            photo=output,
            reply_markup=reply_markup
        )
        
    except Exception as e:
        await update.message.reply_text(f"Sorry, there was an error processing your image: {str(e)}")

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
    
    try:
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
            
            # Send the updated image
            await query.message.edit_media(
                media=InputMediaPhoto(output),
                reply_markup=reply_markup
            )
    except Exception as e:
        await query.message.reply_text(f"Error updating image: {str(e)}")

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
