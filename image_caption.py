from PIL import Image, ImageDraw, ImageFont
import os
from logger import setup_logger

logger = setup_logger(__name__)

def add_caption(image, caption_text, position='bottom'):
    """Add a caption to the image."""
    try:
        draw = ImageDraw.Draw(image)
        
        # Use Impact font
        font_path = os.path.join(os.path.dirname(__file__), 'impact.ttf')
        if not os.path.exists(font_path):
            logger.warning("Impact font not found. Using default font.")
            font = ImageFont.load_default()
        else:
            font_size = int(image.width * 0.1)  # Adjust font size based on image width
            font = ImageFont.truetype(font_path, font_size)

        # Calculate text size
        text_width, text_height = draw.textsize(caption_text, font=font)

        # Calculate position
        padding = 10
        x = (image.width - text_width) // 2
        if position == 'top':
            y = padding
        else:  # bottom
            y = image.height - text_height - padding

        # Draw text outline
        outline_color = 'black'
        for adj in range(-3, 4):
            draw.text((x+adj, y), caption_text, font=font, fill=outline_color)
            draw.text((x, y+adj), caption_text, font=font, fill=outline_color)

        # Draw text
        draw.text((x, y), caption_text, font=font, fill='white')

        return image
    except Exception as e:
        logger.error(f"Error adding caption: {str(e)}")
        return image  # Return original image if caption fails
