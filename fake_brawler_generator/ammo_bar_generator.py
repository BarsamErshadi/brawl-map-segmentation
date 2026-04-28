from PIL import Image, ImageDraw


def generate_ammo_bar_image(
        image_width=102,
        image_height=14,
        bar_outline_color=(34, 41, 65, 255),  # Outline color
        fill_color=(233, 103, 22, 255),  # Color for fully filled sections
        other_color=(111, 139, 182, 255),  # Color for partially filled sections
        empty_color=(200, 200, 200, 255),  # Inner color for empty sections
        fill_color_shining=(240, 148, 92, 255),  # Shining effect color
        value=1.1,  # Ammo value
        total_sections=3,
        corner_radius=10,
):
    """
    Generates a horizontal ammo bar image with shining effect on fully filled sections.
    """
    if value < 0:
        value = 0.0
    if value > total_sections:
        value = float(total_sections)

    section_width_float = float(image_width) / total_sections

    # Clamp corner radius to avoid overlaps
    corner_radius = min(corner_radius, image_height // 2, int(section_width_float) // 2)

    img = Image.new('RGBA', (image_width, image_height + 1), (0, 0, 0, 0))
    draw_main = ImageDraw.Draw(img)

    full_sections = int(value)
    partial_fill = value - full_sections
    partial_fill = max(0.0, min(1.0, partial_fill))

    for i in range(total_sections):
        left = int(round(i * section_width_float))
        right = int(round((i + 1) * section_width_float))

        draw_main.rounded_rectangle(
            [left, 0, right, image_height],
            radius=corner_radius,
            fill=empty_color,
            outline=None
        )

    for i in range(total_sections):
        section_left = int(round(i * section_width_float))
        section_right = int(round((i + 1) * section_width_float))
        section_width = section_right - section_left

        if i < full_sections:
            draw_main.rounded_rectangle(
                [section_left, 0, section_right, image_height],
                radius=corner_radius,
                fill=fill_color,
                outline=None
            )

            # Add shining effect on top half
            shining_height_top = +2  # 1 pixel further up
            shining_height_bottom = (image_height // 2)  # 2 pixels further down
            shining_left = section_left + 2  # 2 less on the left
            shining_right = section_right - 2  # 2 less on the right

            draw_main.rounded_rectangle(
                [shining_left, shining_height_top, shining_right, shining_height_bottom],
                fill=fill_color_shining,
                outline=None, radius=1
            )
        elif i == full_sections and partial_fill > 0.0:
            section_img = Image.new('RGBA', (section_width, image_height), (0, 0, 0, 0))
            section_draw = ImageDraw.Draw(section_img)

            section_draw.rounded_rectangle(
                [0, 0, section_width, image_height],
                radius=corner_radius,
                fill=other_color,
                outline=None
            )

            fill_w = int(round(section_width * partial_fill))
            mask_img = Image.new('L', (section_width, image_height), 0)
            mask_draw = ImageDraw.Draw(mask_img)

            if fill_w > 0:
                mask_draw.rectangle([0, 0, fill_w, image_height], fill=255)

            img.paste(section_img, (section_left, 0), mask_img)

    for i in range(total_sections):
        left = int(round(i * section_width_float))
        right = int(round((i + 1) * section_width_float))
        draw_main.rounded_rectangle(
            [left, 0, right, image_height],
            radius=corner_radius,
            fill=None,
            outline=bar_outline_color
        )

    return img


# Example usage
if __name__ == "__main__":
    generate_ammo_bar_image(
        value=2.3,
        total_sections=3
    ).save("ammobar.png")
