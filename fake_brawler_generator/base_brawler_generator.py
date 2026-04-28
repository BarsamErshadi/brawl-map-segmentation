from PIL import Image


def max_crop_image(image):
    pixels = image.load()

    # Get image size
    width, height = image.size

    # Find the bounding box
    left, top, right, bottom = width, height, 0, 0

    for x in range(width):
        for y in range(height):
            r, g, b, a = pixels[x, y]
            if a != 0:  # Check if pixel is non-empty (alpha > 0)
                left = min(left, x)
                top = min(top, y)
                right = max(right, x)
                bottom = max(bottom, y)

    # Crop the image to the bounding box
    cropped_image = image.crop((left, top, right + 1, bottom + 1))
    return cropped_image


def create_base_brawler_image(brawler_path, gear_amount: int = 0, have_gadget_icon=False, have_hypercharge_icon=False, color="green"):
    if color == "green":
        circle_path = "fake_brawler_generator/asset_images/green_circle.png"
        gadget_icon_path = "fake_brawler_generator/asset_images/gadget_icon.png"
        gear_icon_path = "fake_brawler_generator/asset_images/gear_icon.png"
        two_gears_icon_path = "fake_brawler_generator/asset_images/two_gears_icon.png"
        hypercharge_icon_path = "fake_brawler_generator/asset_images/hypercharge_icon.png"
    elif color == "blue":
        circle_path = "fake_brawler_generator/asset_images/blue_circle.png"
        gadget_icon_path = "fake_brawler_generator/asset_images/blue_gadget_icon.png"
        gear_icon_path = "fake_brawler_generator/asset_images/blue_gear_icon.png"
        two_gears_icon_path = "fake_brawler_generator/asset_images/blue_two_gears_icon.png"
        hypercharge_icon_path = "fake_brawler_generator/asset_images/blue_hypercharge_icon.png"
    elif color == "red":
        circle_path = "fake_brawler_generator/asset_images/red_circle.png"
        gadget_icon_path = "fake_brawler_generator/asset_images/red_gadget_icon.png"
        gear_icon_path = "fake_brawler_generator/asset_images/red_gear_icon.png"
        two_gears_icon_path = "fake_brawler_generator/asset_images/red_two_gears_icon.png"
        hypercharge_icon_path = "fake_brawler_generator/asset_images/red_hypercharge_icon.png"
    else:
        raise ValueError("Invalid circle color")


    circle = Image.open(circle_path).convert("RGBA")
    brawler_image = Image.open(brawler_path).convert("RGBA")

    # Make the canvas big enough for circle or brawler (whichever is larger)
    base_width = max(circle.width, brawler_image.width)
    base_height = max(circle.height, brawler_image.height)
    combined_img = Image.new("RGBA", (base_width, base_height), (0, 0, 0, 0))

    # Center the circle
    circle_offset = (
        (base_width - circle.width) // 2,
        base_height - circle.height
    )
    combined_img.paste(circle, circle_offset, circle)

    if gear_amount or have_hypercharge_icon or have_gadget_icon:
        #add 20 pixels down to the existing combined_img canva size
        _ = Image.new("RGBA", (base_width, base_height+20), (0, 0, 0, 0))
        _.paste(combined_img, (0, 0))
        combined_img = _

    #put gadget
    if have_gadget_icon:
        gadget_icon = Image.open(gadget_icon_path).convert("RGBA")
        gadget_offset = (
            circle_offset[0] + circle.width//2 - gadget_icon.width//2,
            base_height - gadget_icon.height//2 - 5
        )
        combined_img.paste(gadget_icon, gadget_offset, gadget_icon)

    #put hyperchage
    if have_hypercharge_icon:
        hypercharge_icon = Image.open(hypercharge_icon_path).convert("RGBA")
        hypercharge_offset = (
            circle_offset[0] + circle.width//2 - hypercharge_icon.width//2 + 32,
            base_height - hypercharge_icon.height//2 - 10
        )
        combined_img.paste(hypercharge_icon, hypercharge_offset, hypercharge_icon)

    #put gear
    if gear_amount:
        if gear_amount == 1:
            gear_icon = Image.open(gear_icon_path).convert("RGBA")
        elif gear_amount == 2:
            gear_icon = Image.open(two_gears_icon_path).convert("RGBA")
        else:
            raise ValueError("Invalid gear amount")
        gear_offset = (
            circle_offset[0] + circle.width//2 - gear_icon.width//2 - 32,
            base_height - gear_icon.height//2 - 10
        )
        combined_img.paste(gear_icon, gear_offset, gear_icon)


    # Center the brawler
    brawler_offset = (
        (base_width - brawler_image.width) // 2,
        circle_offset[1] + (circle.height - brawler_image.height) // 2
    )
    combined_img.paste(brawler_image, brawler_offset, brawler_image)

    cropped_image = max_crop_image(combined_img)

    return cropped_image


if __name__ == "__main__":
    brawler_path = "skin_seg_3/barley/221.png"

    # 2. Create the base brawler image with circle behind it.
    combined_image = create_base_brawler_image(brawler_path)

    combined_image.save("base_brawler.png")
