import json
import os
import random
from concurrent.futures import ProcessPoolExecutor, as_completed
from functools import partial
from math import tan, radians

# Dependencies to install: pip install opencv-python numpy Pillow tqdm numba
import cv2
import numpy as np
from PIL import Image
from tqdm import tqdm
from numba import njit

# Assuming these local modules exist as in your original script
import map_generator.existing_map_loader as existing_map_loader
from fake_brawler_generator import extractor

# --- Configuration & Paths ---
TILE_IMAGES_DIR = 'map_generator/tile_images'
BACKGROUND_IMAGES_DIR = 'map_generator/backgrounds'
OUTPUT_IMAGES_DIR = 'map_generator/output/images'
OUTPUT_LABELS_DIR = 'map_generator/output/labels'
CONFIG_FILE = 'map_generator/config.json'
CENTERED_TILES = ["wooden_fence", "blue_post"]
DISABLED_TILES = []

os.makedirs(OUTPUT_IMAGES_DIR, exist_ok=True)
os.makedirs(OUTPUT_LABELS_DIR, exist_ok=True)


# --- Loading and Asset Preparation Functions ---

def load_configuration():
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
    return config


def prepare_image_asset(image):
    """
    Helper to return a tuple of (PIL_Image, Numpy_Alpha_Channel).
    """
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    alpha_arr = np.array(image)[:, :, 3].astype(np.uint8)
    return image, alpha_arr


def load_tile_images(config):
    tile_images = {}
    tile_labels = {}

    # --- CLASS MAPPING ---
    # 0 = wall (consolidated class)
    # 1 = bush (separate class)
    # ---------------------

    sorted_tile_types = sorted([t for t in config['tiles'] if t != "air" and t not in DISABLED_TILES])

    for tile_type in sorted_tile_types:
        tile_info = config['tiles'][tile_type]
        tile_images[tile_type] = {}

        # Assign simplified class ID
        if tile_type == "bush":
            tile_labels[tile_type] = 1
        else:
            tile_labels[tile_type] = 0

        target_dimension = tile_info.get('target_dimension')
        dimension_type = tile_info.get('dimension_type', 'width')
        tile_type_dir = os.path.join(TILE_IMAGES_DIR, tile_type)

        if tile_info['connectable']:
            tile_images[tile_type]['connected'] = {}
            for variant in tile_info['connected_variants']:
                variant_dir = os.path.join(tile_type_dir, 'connected', variant)
                if os.path.isdir(variant_dir):
                    tile_images[tile_type]['connected'][variant] = []
                    num_variations = tile_info['variations_per_variant']
                    for i in range(1, num_variations + 1):
                        image_path = os.path.join(variant_dir, f'variation{i}.png')
                        if os.path.isfile(image_path):
                            img = Image.open(image_path).convert('RGBA')
                            img = resize_tile(img, target_dimension, dimension_type)
                            tile_images[tile_type]['connected'][variant].append(prepare_image_asset(img))
        else:
            tile_images[tile_type]['default'] = []
            default_dir = os.path.join(tile_type_dir, 'default')
            if os.path.isdir(default_dir):
                num_variations = tile_info['variations']
                for i in range(1, num_variations + 1):
                    image_path = os.path.join(default_dir, f'variation{i}.png')
                    if os.path.isfile(image_path):
                        img = Image.open(image_path).convert('RGBA')
                        img = resize_tile(img, target_dimension, dimension_type)
                        tile_images[tile_type]['default'].append(prepare_image_asset(img))

    return tile_images, tile_labels


def resize_tile(tile_image, target_dimension, dimension_type='width'):
    if not target_dimension: return tile_image
    original_width, original_height = tile_image.size
    scale_ratio = target_dimension / (original_width if dimension_type == 'width' else original_height)
    new_width = int(original_width * scale_ratio)
    new_height = int(original_height * scale_ratio)
    return tile_image.resize((new_width, new_height), Image.LANCZOS)


def load_background_images(config):
    return [bg_file for bg_file in os.listdir(BACKGROUND_IMAGES_DIR) if bg_file in config['backgrounds']]


def tilt_image(image, angle):
    width, height = image.size
    m = tan(radians(angle))
    xshift = abs(m) * height
    new_width = int(width + xshift)
    image = image.transform((new_width, height), Image.AFFINE, (1, m, -xshift if m > 0 else 0, 0, 1, 0),
                            resample=Image.BICUBIC)
    return image


@njit(fastmath=True)
def fast_draw_on_id_map(id_map, alpha_channel, pos_x, pos_y, instance_id):
    mask_h, mask_w = alpha_channel.shape
    map_h, map_w = id_map.shape
    x1 = max(0, pos_x)
    y1 = max(0, pos_y)
    x2 = min(map_w, pos_x + mask_w)
    y2 = min(map_h, pos_y + mask_h)

    if x1 >= x2 or y1 >= y2: return

    mask_x_start = x1 - pos_x
    mask_y_start = y1 - pos_y
    threshold = 128 if instance_id == 0 else 0

    for i in range(y2 - y1):
        for j in range(x2 - x1):
            alpha_val = alpha_channel[mask_y_start + i, mask_x_start + j]
            if alpha_val > threshold:
                id_map[y1 + i, x1 + j] = instance_id


def generate_segmentation_labels(id_map, instance_id_to_class_id, instance_bounds, image_width, image_height):
    label_lines = []

    for instance_id, class_id in instance_id_to_class_id.items():
        if instance_id == 0 or instance_id not in instance_bounds: continue

        bx, by, bw, bh = instance_bounds[instance_id]
        pad = 2
        roi_x1 = max(0, bx - pad)
        roi_y1 = max(0, by - pad)
        roi_x2 = min(image_width, bx + bw + pad)
        roi_y2 = min(image_height, by + bh + pad)

        roi_id_map = id_map[roi_y1:roi_y2, roi_x1:roi_x2]
        binary_mask = (roi_id_map == instance_id).astype(np.uint8)

        if not np.any(binary_mask): continue

        contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            if len(contour) < 3: continue
            epsilon = 0.001 * cv2.arcLength(contour, True)
            approx_contour = cv2.approxPolyDP(contour, epsilon, True)
            if len(approx_contour) < 3: continue

            points = approx_contour.flatten().astype(float)
            points[0::2] += roi_x1
            points[1::2] += roi_y1
            points[0::2] /= image_width
            points[1::2] /= image_height
            np.clip(points, 0, 1, out=points)

            points_str = " ".join([f"{p:.6f}" for p in points])
            label_lines.append(f"{class_id} {points_str}")

    return label_lines


def get_connected_variant(grid, x, y, tile_type):
    grid_width, grid_height = len(grid[0]), len(grid)
    connections = {
        'top': y > 0 and grid[y - 1][x] == tile_type,
        'bottom': y < grid_height - 1 and grid[y + 1][x] == tile_type,
        'left': x > 0 and grid[y][x - 1] == tile_type,
        'right': x < grid_width - 1 and grid[y][x + 1] == tile_type,
    }
    sides = sorted([side for side, connected in connections.items() if connected])
    count = len(sides)
    if count == 0: return 'isolated'
    if count == 1: return f"edge_{sides[0]}"
    if count == 2:
        if 'bottom' in sides and 'top' in sides: return 'side_vertical'
        if 'left' in sides and 'right' in sides: return 'side_horizontal'
        return f"corner_{sides[0][0]}{sides[1][0]}"
    if count == 3: return f"three_{'_'.join(sides)}"
    return 'center'


def calculate_tile_position(x, y, origin_x, origin_y, x_offset_x, x_offset_y, y_offset_x_tile, y_offset_y):
    pos_x = origin_x + x * x_offset_x + y * y_offset_x_tile
    pos_y = origin_y + x * x_offset_y + y * y_offset_y
    return int(pos_x), int(pos_y)


def compute_grid_size(bg_settings):
    origin_x = bg_settings.get('origin_x', 0)
    origin_y = bg_settings.get('origin_y', 0)
    x_offset_x = bg_settings.get('x_offset_x', 1)
    y_offset_y = bg_settings.get('y_offset_y', 1)
    margins = bg_settings.get('non_placeable_margins', {})
    map_width, map_height = bg_settings['map_width'], bg_settings['map_height']
    placeable_width = map_width - origin_x - margins.get('right', 0)
    placeable_height = map_height - origin_y - margins.get('bottom', 0)
    grid_width = max(1, int(placeable_width / x_offset_x)) if x_offset_x > 0 else 1
    grid_height = max(1, int(placeable_height / y_offset_y)) if y_offset_y > 0 else 1
    return grid_width, grid_height


def place_tiles(
        map_image, id_map, instance_id_to_class_id, instance_bounds, instance_id_counter, grid, tile_images,
        tile_labels, config,
        origin_x, origin_y, x_offset_x, x_offset_y, y_offset_y,
        tilt_angle_left, tilt_angle_right, y_offset_x_left, y_offset_x_right
):
    grid_width, grid_height = len(grid[0]), len(grid)
    grid_center = (grid_width - 1) / 2.0
    tilted_tile_cache = {}

    for y in range(grid_height):
        for x in range(grid_width):
            tile_type = grid[y][x]
            if tile_type == "air" or tile_type not in tile_images: continue

            tile_info = config['tiles'][tile_type]
            if tile_info['connectable']:
                variant = get_connected_variant(grid, x, y, tile_type)
                variations = tile_images[tile_type]['connected'].get(variant, tile_images[tile_type]['connected'].get(
                    'isolated'))
            else:
                variations = tile_images[tile_type].get('default')

            if not variations: continue
            tile_img_asset, tile_alpha_asset = random.choice(variations)

            if grid_width > 1 and grid_center > 0:
                if x <= grid_center:
                    interp = x / grid_center
                    tilt_angle = tilt_angle_left + (0 - tilt_angle_left) * interp
                    y_offset_x_calc = y_offset_x_left + (0 - y_offset_x_left) * interp
                else:
                    interp = (x - grid_center) / grid_center
                    tilt_angle = 0 + (tilt_angle_right - 0) * interp
                    y_offset_x_calc = 0 + (y_offset_x_right - 0) * interp
            else:
                tilt_angle, y_offset_x_calc = 0, 0

            cache_key = (id(tile_img_asset), tilt_angle)

            if cache_key not in tilted_tile_cache:
                tilted_img = tilt_image(tile_img_asset, tilt_angle)
                tilted_alpha = np.array(tilted_img)[:, :, 3].astype(np.uint8)
                tilted_tile_cache[cache_key] = (tilted_img, tilted_alpha)

            final_tile_img, final_tile_alpha = tilted_tile_cache[cache_key]

            pos_x, pos_y = calculate_tile_position(x, y, origin_x, origin_y, x_offset_x, x_offset_y, y_offset_x_calc,
                                                   y_offset_y)

            w, h = final_tile_img.size
            if tile_type in CENTERED_TILES:
                pos_x -= (w - x_offset_x) // 2
                pos_y -= (h - y_offset_y) // 2

            map_image.alpha_composite(final_tile_img, dest=(pos_x, pos_y))

            instance_id_counter += 1
            instance_id_to_class_id[instance_id_counter] = tile_labels[tile_type]
            instance_bounds[instance_id_counter] = (pos_x, pos_y, w, h)

            fast_draw_on_id_map(id_map, final_tile_alpha, pos_x, pos_y, instance_id_counter)

    return instance_id_counter


def generate_map_grid(grid_width, grid_height, tile_types, tile_probabilities, config):
    air_prob = config['tiles']['air']['placement_probability']
    return [
        random.choices(tile_types + ["air"], weights=tile_probabilities + [air_prob], k=int(grid_width))
        for _ in range(int(grid_height))
    ]


def place_noise_objects(map_image, id_map, config, bg_settings, goast_post_images, goal_posts_placement_probability):
    noise_objects = []

    if (player_img := extractor.create_random_fake_player()):
        noise_objects.append(prepare_image_asset(player_img))
    for _ in range(random.randint(0, 3)):
        if (enemy_img := extractor.create_random_fake_other(extractor.create_fake_enemy_image)):
            noise_objects.append(prepare_image_asset(enemy_img))
    for _ in range(random.randint(0, 2)):
        if (ally_img := extractor.create_random_fake_other(extractor.create_fake_ally_image)):
            noise_objects.append(prepare_image_asset(ally_img))

    if goast_post_images and random.random() < goal_posts_placement_probability:
        noise_objects.append(random.choice(goast_post_images))

    margins = bg_settings.get('non_placeable_margins', {})
    origin_x = bg_settings.get('origin_x', margins.get('left', 0))
    origin_y = bg_settings.get('origin_y', margins.get('top', 0))
    map_width, map_height = map_image.size

    for obj_img, obj_alpha in noise_objects:
        bw, bh = obj_img.size
        max_x = map_width - margins.get('right', 0) - bw
        max_y = map_height - margins.get('bottom', 0) - bh

        if origin_x >= max_x or origin_y >= max_y: continue

        rand_x = random.randint(origin_x, max_x)
        rand_y = random.randint(origin_y, max_y)

        # 1. VISUALS: Draw the player/noise on the image (RGB)
        map_image.alpha_composite(obj_img, dest=(rand_x, rand_y))

        # 2. LABELS (OCCLUSION FIX):
        # We deliberately DO NOT draw on the id_map here.
        # This means the mask for the wall/bush underneath remains intact.
        # fast_draw_on_id_map(id_map, obj_alpha, rand_x, rand_y, 0)


def process_single_map(map_index, is_existing, data, config, tile_images, tile_labels, background_files, tile_types,
                       tile_probabilities, goast_post_images, goal_posts_placement_probability):
    random.seed()

    if is_existing:
        grid, bg_filename = data
        base_filename = f'map_real_{map_index}'
    else:
        bg_filename = random.choice(background_files)
        base_filename = f'map_{map_index}'

    bg_settings = config['backgrounds'][bg_filename]
    background = Image.open(os.path.join(BACKGROUND_IMAGES_DIR, bg_filename)).convert('RGBA')
    map_image = background.copy()
    map_width, map_height = map_image.size

    id_map = np.zeros((map_height, map_width), dtype=np.uint16)
    instance_id_counter = 0
    instance_id_to_class_id = {}
    instance_bounds = {}

    origin_x, origin_y = bg_settings.get('origin_x', 0), bg_settings.get('origin_y', 0)
    x_offset_x, x_offset_y, y_offset_y = bg_settings.get('x_offset_x', 0), bg_settings.get('x_offset_y',
                                                                                           0), bg_settings.get(
        'y_offset_y', 0)
    tilt_angle_left, tilt_angle_right = bg_settings.get('tilt_angle_left', 0), bg_settings.get('tilt_angle_right', 0)
    y_offset_x_left, y_offset_x_right = bg_settings.get('y_offset_x_left', 0), bg_settings.get('y_offset_x_right', 0)

    if not is_existing:
        grid_width, grid_height = compute_grid_size(bg_settings)
        grid = generate_map_grid(grid_width, grid_height, tile_types, tile_probabilities, config)

    # 1. Place tiles
    instance_id_counter = place_tiles(
        map_image, id_map, instance_id_to_class_id, instance_bounds, instance_id_counter,
        grid, tile_images, tile_labels, config,
        origin_x, origin_y, x_offset_x, x_offset_y, y_offset_y,
        tilt_angle_left, tilt_angle_right, y_offset_x_left, y_offset_x_right
    )

    # 2. Place noise (With Occlusion Fix)
    place_noise_objects(map_image, id_map, config, bg_settings, goast_post_images, goal_posts_placement_probability)

    # 3. Generate labels
    label_lines = generate_segmentation_labels(id_map, instance_id_to_class_id, instance_bounds, map_width, map_height)

    # 4. Save
    map_filename = f'{base_filename}.png'
    map_image.convert('RGB').save(os.path.join(OUTPUT_IMAGES_DIR, map_filename))

    label_filename = f'{base_filename}.txt'
    with open(os.path.join(OUTPUT_LABELS_DIR, label_filename), 'w') as f:
        f.write('\n'.join(label_lines))

    return map_filename, label_filename


def main():
    config = load_configuration()

    tile_images, tile_labels = load_tile_images(config)
    print("Detected Tile Classes (Internal Mapping):", tile_labels)

    yaml_path = 'map_generator/data.yaml'
    with open(yaml_path, 'w') as f:
        f.write(f"path: ..\dataset \n")
        f.write("train: images/train # relative to path\n")
        f.write("val: images/val   # using same for train/val\n\n")
        f.write("names:\n")
        f.write("  0: wall\n")
        f.write("  1: bush\n")
    print(f"Generated {yaml_path} for training.")

    tile_types = list(tile_labels.keys())
    tile_probabilities = [config['tiles'][t]['placement_probability'] for t in tile_types]
    total_prob = sum(tile_probabilities)
    tile_probabilities = [p / total_prob for p in tile_probabilities] if total_prob > 0 else []

    background_files = load_background_images(config)

    goal_posts_paths = ["map_generator/misc_images/goal_posts_1.png", "map_generator/misc_images/goal_posts_2.png",
                        "map_generator/misc_images/goal_posts_3.png", "map_generator/misc_images/full_goals.png",
                        "map_generator/misc_images/full_goals_hflip.png",
                        "map_generator/misc_images/full_goals_vflip.png",
                        "map_generator/misc_images/full_goals_vhflip.png"]

    goast_post_images = []
    for p in goal_posts_paths:
        if os.path.exists(p):
            img = Image.open(p).convert('RGBA')
            goast_post_images.append(prepare_image_asset(img))

    goal_posts_placement_probability = config['map_settings'].get('posts_on_maps_amount', 0)
    num_maps_to_generate = config['map_settings'].get('num_maps_to_generate', 1000)
    max_workers = os.cpu_count() - 1

    if num_maps_to_generate > 0:
        print(f"Generating {num_maps_to_generate} random maps...")
        process_map_partial = partial(
            process_single_map, is_existing=False, data=None, config=config, tile_images=tile_images,
            tile_labels=tile_labels, background_files=background_files, tile_types=tile_types,
            tile_probabilities=tile_probabilities, goast_post_images=goast_post_images,
            goal_posts_placement_probability=goal_posts_placement_probability
        )
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(process_map_partial, i) for i in range(num_maps_to_generate)]
            for future in tqdm(as_completed(futures), total=num_maps_to_generate, desc="Generating Random Maps"):
                try:
                    future.result()
                except Exception as e:
                    print(f"Error generating map: {e}")
                    import traceback
                    traceback.print_exc()

    if config['map_settings'].get('generate_existing_maps', False):
        resized_grids = existing_map_loader.main()
        num_existing_maps = len(resized_grids)
        if num_existing_maps > 0:
            print(f"Generating {num_existing_maps} maps from existing grids...")
            process_existing_map_partial = partial(
                process_single_map, is_existing=True, config=config, tile_images=tile_images,
                tile_labels=tile_labels, background_files=background_files, tile_types=tile_types,
                tile_probabilities=tile_probabilities, goast_post_images=goast_post_images,
                goal_posts_placement_probability=goal_posts_placement_probability
            )
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(process_existing_map_partial, i, data=grid_data) for i, grid_data in
                           enumerate(resized_grids)]
                for future in tqdm(as_completed(futures), total=num_existing_maps, desc="Generating Existing Maps"):
                    try:
                        future.result()
                    except Exception as e:
                        print(f"Error generating existing map: {e}")

    print("\nDataset generation complete.")


if __name__ == '__main__':
    main()