import os
import json
from PIL import Image, ImageDraw
from math import tan, radians

TILE_IMAGES_DIR = 'tile_images'
BACKGROUND_IMAGES_DIR = 'backgrounds'
OUTPUT_IMAGES_DIR = 'output/background_overlays'
CONFIG_FILE = 'config.json'

os.makedirs(OUTPUT_IMAGES_DIR, exist_ok=True)

def load_configuration():
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
    return config

def tilt_image(image, angle):
    width, height = image.size
    m = tan(radians(angle))
    xshift = abs(m) * height
    new_width = int(width + xshift)
    new_height = height
    image = image.transform(
        (new_width, new_height),
        Image.AFFINE,
        (1, m, -xshift if m > 0 else 0, 0, 1, 0),
        resample=Image.BICUBIC,
        fillcolor=None
    )
    return image

def compute_grid_size(bg_settings):
    origin_x = bg_settings.get('origin_x', 0)
    origin_y = bg_settings.get('origin_y', 0)
    x_offset_x = bg_settings.get('x_offset_x', 1)
    y_offset_y = bg_settings.get('y_offset_y', 1)

    non_placeable_margins = bg_settings.get('non_placeable_margins', {})
    right_margin = non_placeable_margins.get('right', 0)
    bottom_margin = non_placeable_margins.get('bottom', 0)

    map_width = bg_settings['map_width']
    map_height = bg_settings['map_height']

    placeable_width = map_width - origin_x - right_margin
    placeable_height = map_height - origin_y - bottom_margin

    grid_width = max(1, int(placeable_width // x_offset_x))
    grid_height = max(1, int(placeable_height // y_offset_y))

    return grid_width, grid_height

def create_overlay_image(bg_filename, bg_settings):
    bg_path = os.path.join(BACKGROUND_IMAGES_DIR, bg_filename)
    background = Image.open(bg_path).convert('RGBA')

    background_alpha = 150
    background = Image.blend(Image.new("RGBA", background.size, (0,0,0,0)), background, background_alpha/255)


    overlay_image = Image.new('RGBA', background.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay_image)

    map_width = bg_settings['map_width']
    map_height = bg_settings['map_height']
    non_placeable_margins = bg_settings['non_placeable_margins']

    origin_x = bg_settings.get('origin_x', non_placeable_margins['left'])
    origin_y = bg_settings.get('origin_y', non_placeable_margins['top'])
    x_offset_x = bg_settings.get('x_offset_x', 0)
    x_offset_y = bg_settings.get('x_offset_y', 0)
    y_offset_y = bg_settings.get('y_offset_y', 0)

    tilt_angle_left = bg_settings.get('tilt_angle_left', 0)
    tilt_angle_right = bg_settings.get('tilt_angle_right', 0)
    y_offset_x_left = bg_settings.get('y_offset_x_left', 0)
    y_offset_x_right = bg_settings.get('y_offset_x_right', 0)

    grid_width, grid_height = compute_grid_size(bg_settings)
    grid_center = (grid_width - 1) / 2 if grid_width > 1 else 0

    for y in range(grid_height):
        for x in range(grid_width):
            if grid_width > 1:
                if x <= grid_center:
                    interp_factor = x / grid_center if grid_center != 0 else 0
                    tilt_angle_tile = tilt_angle_left + (0 - tilt_angle_left) * interp_factor
                    y_offset_x_tile = y_offset_x_left + (0 - y_offset_x_left) * interp_factor
                else:
                    interp_factor = (x - grid_center) / grid_center if grid_center != 0 else 0
                    tilt_angle_tile = 0 + (tilt_angle_right - 0) * interp_factor
                    y_offset_x_tile = 0 + (y_offset_x_right - 0) * interp_factor
            else:
                tilt_angle_tile = 0
                y_offset_x_tile = 0

            tile_img = Image.new('RGBA', (50, 50), (255, 0, 0, 128))
            tile_img_tilted = tilt_image(tile_img, tilt_angle_tile)

            pos_x, pos_y = (
                origin_x + x * x_offset_x + y * y_offset_x_tile,
                origin_y + x * x_offset_y + y * y_offset_y
            )
            overlay_image.alpha_composite(tile_img_tilted, dest=(int(pos_x), int(pos_y)))

    background.alpha_composite(overlay_image) # place on top
    return background


def main():
    config = load_configuration()
    for bg_filename, bg_settings in config['backgrounds'].items():
        overlay_image = create_overlay_image(bg_filename, bg_settings)
        overlay_image.save(os.path.join(OUTPUT_IMAGES_DIR, f"{bg_filename}_overlay.png"))

if __name__ == '__main__':
    main()