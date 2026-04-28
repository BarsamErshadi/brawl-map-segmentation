import random
import time

from PIL import Image, ImageDraw, ImageFont

def generate_username_image(
    text="Username",
    font_path="fake_brawler_generator/LilitaOne-Regular.ttf",  # Path to a valid .ttf font file
    font_size=30,
    text_color=(72, 227, 53, 255),  # Color of the text
    shadow_color=(0, 0, 0),  # Base color for the shadow
    shadow_top_thin=1,  # Max thickness at the top
    shadow_bottom_thick=3,  # Max thickness at the bottom
    shadow_opacity_min=100,  # Minimum opacity for the shadow (at the top)
    shadow_opacity_max=255,  # Maximum opacity for the shadow (at the bottom)
):
    """
    Generates an image with text, customizable font, and a shadow effect.

    Parameters:
        text (str): The text to display.
        font_path (str): Path to the .ttf font file.
        font_size (int): Font size for the text.
        text_color (tuple): RGBA color for the text.
        shadow_color (tuple): RGB base color for the shadow.
        shadow_top_thin (int): Shadow thickness at the top.
        shadow_bottom_thick (int): Shadow thickness at the bottom.
        shadow_opacity_min (int): Minimum opacity for the shadow (at the top).
        shadow_opacity_max (int): Maximum opacity for the shadow (at the bottom).

    Returns:
        None
    """
    # Load font
    font = ImageFont.truetype(font_path, font_size)

    # Calculate text size using getbbox
    left, top, right, bottom = font.getbbox(text)
    text_width = right - left
    text_height = bottom - top

    # Create a new image with transparent background
    image_width = text_width
    image_height = text_height
    img = Image.new("RGBA", (image_width, image_height+5), (0, 0, 0, 0))

    # Create a drawing context
    draw = ImageDraw.Draw(img)

    # Total height for the shadow gradient
    shadow_height = shadow_bottom_thick - shadow_top_thin + 1

    # Draw the shadow
    for y_offset in range(-shadow_top_thin, shadow_bottom_thick + 1):
        # Calculate normalized position in the gradient (0 to 1)
        normalized_position = (y_offset - (-shadow_top_thin)) / shadow_height

        # Interpolate opacity smoothly between min and max
        current_opacity = int(
            shadow_opacity_min + (shadow_opacity_max - shadow_opacity_min) * normalized_position
        )

        # Clamp opacity to valid range
        current_opacity = max(0, min(255, current_opacity))

        # Create the shadow color with dynamic opacity
        shadow_fill = shadow_color + (current_opacity,)

        # Determine shadow thickness for the current offset
        shadow_thickness = shadow_top_thin if y_offset <= 0 else shadow_bottom_thick

        for x_offset in range(-shadow_thickness, shadow_thickness + 1):
            draw.text(
                (x_offset, y_offset),
                text,
                font=font,
                fill=shadow_fill,
                anchor="lt"
            )

    # Draw the main text
    draw.text(
        (0, 0),
        text,
        font=font,
        fill=text_color,
        anchor="lt"
    )

    return img
