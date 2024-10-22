import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk, ImageEnhance, ImageDraw, ImageFont
import io
import os

class PurpleFilterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Purple-Black Filter Application with Captions")
        
        # Store the original image and processed image
        self.original_image = None
        self.current_processed_image = None
        self.photo_image = None
        
        # Create main frame
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create button to load image
        self.load_button = ttk.Button(self.main_frame, text="Load Image", command=self.load_image)
        self.load_button.grid(row=0, column=0, pady=5)
        
        # Create intensity sliders
        self.purple_intensity_var = tk.DoubleVar(value=1.0)
        self.black_intensity_var = tk.DoubleVar(value=1.0)
        self.contrast_var = tk.DoubleVar(value=1.0)
        
        # Purple intensity controls
        self.purple_label = ttk.Label(self.main_frame, text="Purple Intensity:")
        self.purple_label.grid(row=1, column=0, pady=2)
        self.purple_slider = ttk.Scale(
            self.main_frame,
            from_=0.0,
            to=4.0,
            orient=tk.HORIZONTAL,
            variable=self.purple_intensity_var,
            command=self.update_image
        )
        self.purple_slider.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=2)
        
        # Black intensity controls
        self.black_label = ttk.Label(self.main_frame, text="Black Intensity:")
        self.black_label.grid(row=3, column=0, pady=2)
        self.black_slider = ttk.Scale(
            self.main_frame,
            from_=0.0,
            to=4.0,
            orient=tk.HORIZONTAL,
            variable=self.black_intensity_var,
            command=self.update_image
        )
        self.black_slider.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=2)
        
        # Contrast controls
        self.contrast_label = ttk.Label(self.main_frame, text="Contrast:")
        self.contrast_label.grid(row=5, column=0, pady=2)
        self.contrast_slider = ttk.Scale(
            self.main_frame,
            from_=0.0,
            to=3.0,
            orient=tk.HORIZONTAL,
            variable=self.contrast_var,
            command=self.update_image
        )
        self.contrast_slider.grid(row=6, column=0, sticky=(tk.W, tk.E), pady=2)
        
        # Caption controls
        self.caption_frame = ttk.LabelFrame(self.main_frame, text="Caption Settings", padding="5")
        self.caption_frame.grid(row=7, column=0, pady=5, sticky=(tk.W, tk.E))
        
        # Caption text entry
        self.caption_var = tk.StringVar(value="Enter your caption")
        self.caption_entry = ttk.Entry(self.caption_frame, textvariable=self.caption_var, width=40)
        self.caption_entry.grid(row=0, column=0, columnspan=2, pady=5, sticky=(tk.W, tk.E))
        
        # Font size spinbox
        self.font_size_var = tk.IntVar(value=150)  # Increased default size
        self.font_size_label = ttk.Label(self.caption_frame, text="Font Size:")
        self.font_size_label.grid(row=1, column=0, pady=2)
        self.font_size_spinbox = ttk.Spinbox(
            self.caption_frame,
            from_=50,
            to=500,
            increment=10,
            textvariable=self.font_size_var,
            width=5,
            command=self.update_image
        )
        self.font_size_spinbox.grid(row=1, column=1, sticky=(tk.W), pady=2, padx=5)
        # Bind the spinbox to also update on keyboard input
        self.font_size_spinbox.bind('<Return>', self.update_image)
        self.font_size_spinbox.bind('<FocusOut>', self.update_image)
        
        # Outline thickness slider
        self.outline_var = tk.IntVar(value=3)  # Increased default thickness
        self.outline_label = ttk.Label(self.caption_frame, text="Outline Thickness:")
        self.outline_label.grid(row=2, column=0, pady=2)
        self.outline_slider = ttk.Scale(
            self.caption_frame,
            from_=1,
            to=8,  # Increased maximum thickness
            orient=tk.HORIZONTAL,
            variable=self.outline_var,
            command=self.update_image
        )
        self.outline_slider.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2)
        
        # Create canvas for image display
        self.canvas = tk.Canvas(self.main_frame, width=800, height=600)
        self.canvas.grid(row=8, column=0, pady=5)
        
        # Add label to show when no image is loaded
        self.canvas.create_text(
            400, 300,
            text="Please load an image",
            font=('Arial', 14)
        )
        
        # Bind caption entry to update
        self.caption_var.trace_add('write', self.update_image_wrapper)
        
    def update_image_wrapper(self, *args):
        self.update_image()

    def load_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.tiff")]
        )
        if file_path:
            self.original_image = Image.open(file_path)
            self.original_image.thumbnail((800, 600), Image.Resampling.LANCZOS)
            self.update_image()

    def apply_purple_black_tone(self, img, purple_intensity=1.0, black_intensity=1.0, contrast=1.0):
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

    def add_caption(self, img, text, font_size, outline_thickness):
        # Create a drawing object
        draw = ImageDraw.Draw(img)
        
        # Try to use Arial, fall back to default if not available
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()
        
        # Get text size
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Calculate position (centered at bottom)
        x = (img.width - text_width) // 2
        y = img.height - text_height - 40  # Increased padding from bottom
        
        # Draw thicker outline
        for offset_x in range(-outline_thickness, outline_thickness + 1):
            for offset_y in range(-outline_thickness, outline_thickness + 1):
                draw.text(
                    (x + offset_x, y + offset_y),
                    text,
                    font=font,
                    fill='black'
                )
        
        # Draw main text in bright purple/pink
        draw.text(
            (x, y),
            text,
            font=font,
            fill='#FF00FF'
        )
        
        return img

    def update_image(self, *args):
        if self.original_image:
            # Create a copy of the original image
            working_image = self.original_image.copy()
            
            # Apply filter
            processed_image = self.apply_purple_black_tone(
                working_image,
                self.purple_intensity_var.get(),
                self.black_intensity_var.get(),
                self.contrast_var.get()
            )
            
            # Add caption
            if self.caption_var.get().strip():
                processed_image = self.add_caption(
                    processed_image,
                    self.caption_var.get(),
                    self.font_size_var.get(),
                    self.outline_var.get()
                )
            
            # Convert to PhotoImage for display
            self.photo_image = ImageTk.PhotoImage(processed_image)
            
            # Update canvas
            self.canvas.delete("all")
            self.canvas.create_image(
                400, 300,
                image=self.photo_image,
                anchor=tk.CENTER
            )

if __name__ == "__main__":
    root = tk.Tk()
    app = PurpleFilterApp(root)
    root.mainloop()
