from PIL import Image, ImageEnhance, ImageDraw, ImageFont
from logger import setup_logger

logger = setup_logger(__name__)

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

def add_watermark(image):
    """Add a black bar with text at the bottom of the image."""
    try:
        bar_height = 40
        new_width = image.width
        new_height = image.height + bar_height
        
        new_image = Image.new('RGB', (new_width, new_height), 'black')
        new_image.paste(image, (0, 0))
        
        draw = ImageDraw.Draw(new_image)
        font = ImageFont.load_default()
        text = "X:@MarketDomSol TG:market_dominance"
        
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (new_width - text_width) // 2
        y = image.height + (bar_height - text_height) // 2
        
        draw.text((x, y), text, fill='white', font=font)
        
        return new_image
    except Exception as e:
        logger.error(f"Error adding watermark: {str(e)}")
        return image  # Return original image if watermark fails
