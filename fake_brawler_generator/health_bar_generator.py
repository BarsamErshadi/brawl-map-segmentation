from PIL import Image, ImageDraw, ImageFont


def generate_health_bar_image(
        image_width=104,
        image_height=21,
        background_color=(56, 47, 95, 255),  # Outline color
        thirds_colors=((255, 15, 9, 255), (251, 227, 16, 255), (72, 227, 53, 255)),  # Bar colors
        thirds_shining_colors=((169, 240, 148, 255), (255, 240, 44, 255), (255, 15, 9, 255)),  # Shining colors
        value=0.5,
        font_name="fake_brawler_generator/LilitaOne-Regular.ttf",
        font_size=21,  # Font size for the health text
        health_amount=1284,
        force_first_color=False
):
    health_amount = health_amount
    # Load the font
    font = ImageFont.truetype(font_name, font_size)

    # Calculate the height of the text
    sample_text = str(health_amount)
    text_bbox = font.getbbox(sample_text)
    text_height = text_bbox[3] - text_bbox[1]
    text_width = text_bbox[2] - text_bbox[0]
    text_top_height = text_height // 2 - 1

    # Calculate the total image height needed
    total_image_height = image_height + text_top_height + 1
    total_image_width = max(image_width, text_width + 1)
    # Calculate the health text
    health_text = f"{health_amount}"

    text_x = (image_width - text_width) / 2

    # Create an image with transparency (RGBA mode)
    img = Image.new('RGBA', (total_image_width, total_image_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw the rounded rectangle background (the bar outline)
    outline_radius = 10
    draw.rounded_rectangle(
        [0, text_top_height, image_width - 1, image_height + text_top_height],
        radius=outline_radius,
        fill=background_color
    )

    if force_first_color:
        main_color = thirds_colors[2]
        shining_color = thirds_shining_colors[0]
    else:
        # Determine the color of the main filled section based on the value
        if value < 1 / 3:
            main_color = thirds_colors[0]
            shining_color = thirds_shining_colors[2]
        elif value < 2 / 3:
            main_color = thirds_colors[1]
            shining_color = thirds_shining_colors[1]
        else:
            main_color = thirds_colors[2]
            shining_color = thirds_shining_colors[0]

    # Draw the filled portion of the bar
    filled_width = int(image_width * value)
    fill_radius = outline_radius - 2
    if filled_width > 4:
        draw.rounded_rectangle(
            [2, text_top_height + 2, filled_width - 2, image_height - 2 + text_top_height],
            radius=fill_radius,
            fill=main_color
        )

        # Calculate the shining region
        shining_top = 5 + text_top_height
        shining_bottom = (image_height // 2) - 1 + text_top_height
        if shining_bottom > shining_top:
            shining_left = 3
            shining_right = filled_width - 2
            shining_width = shining_right - shining_left
            shining_height = shining_bottom - shining_top + 1
            if shining_width > 0:
                # Create a separate image for the shining shape
                shining_img = Image.new('RGBA', (shining_width, shining_height), (0, 0, 0, 0))
                draw_shining = ImageDraw.Draw(shining_img)

                # Define the radius for the top corners
                top_corners_radius = min(fill_radius, shining_height)

                # Draw a rounded rectangle for the shining region
                draw_shining.rounded_rectangle(
                    [0, 0, shining_width - 1, shining_height - 1],
                    radius=top_corners_radius,
                    fill=shining_color
                )

                # Flatten the bottom
                draw_shining.rectangle(
                    [0, top_corners_radius, shining_width, shining_height],
                    fill=shining_color
                )

                # Paste the shining region onto the main bar
                img.alpha_composite(shining_img, (shining_left, shining_top))

    # Draw the shadow with multiple layers
    shadow_color = (0, 0, 0, 128)  # Black color
    shadow_offsets = [
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1), (0, 1),
        (1, -1), (1, 0), (1, 1),
        (0, 2),  # Additional down offset for the stronger bottom shadow
        (-1, 2), (1, 2)  # Diagonal down offsets
    ]
    for dx, dy in shadow_offsets:
        draw.text((text_x + dx, dy + 1), health_text, font=font, fill=shadow_color, anchor="lt")

    # Draw the text on the image
    text_color = (255, 255, 255, 255)  # White color
    draw.text((text_x, 1), health_text, font=font, fill=text_color, anchor="lt")

    return img


if __name__ == "__main__":
    generate_health_bar_image(value=0.25, health_amount=1284).save("healthbar.png")
