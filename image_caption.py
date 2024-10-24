from PIL import Image, ImageDraw, ImageFont
import os
from logger import setup_logger

logger = setup_logger(__name__)

def get_font_size(image_width, text, font_path, max_width_ratio=0.9):
    """Find the largest font size that fits the text within the image width."""
    font_size = 1
    font = ImageFont.truetype(font_path, font_size)
    text_width = font.getsize(text)[0]
    max_width = int(image_width * max_width_ratio)

    while text_width < max_width:
        font_size += 1
        font = ImageFont.truetype(font_path, font_size)
        text_width = font.getsize(text)[0]

    return font_size - 1

def add_caption(image, caption_text, position='bottom'):
    """Add a caption to the image."""
    try:
        draw = ImageDraw.Draw(image)
        
        # Use Impact font
        font_path = os.path.join(os.path.dirname(__file__), 'impact.ttf')
        if not os.path.exists(font_path):
            logger.warning("Impact font not found. Using default font.")
            font = ImageFont.load_default()
            font_size = 40  # Default size
        else:
            font_size = get_font_size(image.width, caption_text, font_path)
            font = ImageFont.truetype(font_path, font_size)

        # Calculate text size
        text_width, text_height = draw.textsize(caption_text, font=font)

        # Calculate position
        x = (image.width - text_width) // 2
        if position == 'top':
            y = int(image.height * 0.1)  # 10% from the top
        else:  # bottom
            y = int(image.height * 0.9) - text_height  # 10% from the bottom

        # Draw text outline
        outline_color = 'black'
        outline_width = max(1, font_size // 15)  # Adjust outline width based on font size
        for adj in range(-outline_width, outline_width + 1):
            draw.text((x+adj, y), caption_text, font=font, fill=outline_color)
            draw.text((x, y+adj), caption_text, font=font, fill=outline_color)

        # Draw text
        draw.text((x, y), caption_text, font=font, fill='white')

        return image
    except Exception as e:
        logger.error(f"Error adding caption: {str(e)}")
        logger.exception("Full traceback:")
        return image  # Return original image if caption fails
