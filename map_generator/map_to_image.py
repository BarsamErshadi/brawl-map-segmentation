import os
import json
import random
import csv
import time

from PIL import Image
from math import tan, radians
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial
from tqdm import tqdm


# Paths to your resources
TILE_IMAGES_DIR = 'tile_images'  # Replace with the actual path
BACKGROUNDS_DIR = 'backgrounds'  # Replace with the actual path
MAPS_DIR = 'maps'  # Directory containing your CSV map files
OUTPUT_IMAGES_DIR = 'output/maps'  # Directory to save generated maps
CONFIG_FILE = 'config.json'  # Configuration file

# Ensure output directory exists
os.makedirs(OUTPUT_IMAGES_DIR, exist_ok=True)

# Load configuration
def load_configuration():
    with open(CONFIG_FILE, 'r', encoding="utf-8") as f:
        config = json.load(f)
    return config

# Load tile images
def load_tile_images(config):
    tile_images = {}
    for tile_type, tile_info in config['tiles'].items():
        if tile_type == "air":
            continue  # Skip loading "air" as it has no actual tile image
        tile_images[tile_type] = {}

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
                        image_filename = f'variation{i}.png'
                        image_path = os.path.join(variant_dir, image_filename)
                        if os.path.isfile(image_path):
                            tile_image = Image.open(image_path).convert('RGBA')
                            tile_image = resize_tile(tile_image, target_dimension, dimension_type)
                            tile_images[tile_type]['connected'][variant].append(tile_image)
                        else:
                            print(f"Warning: File {image_path} does not exist.")
                else:
                    print(f"Warning: Variant directory {variant_dir} does not exist for tile type {tile_type}")
        else:
            tile_images[tile_type]['default'] = []
            default_dir = os.path.join(tile_type_dir, 'default')
            if os.path.isdir(default_dir):
                num_variations = tile_info['variations']
                for i in range(1, num_variations + 1):
                    image_filename = f'variation{i}.png'
                    image_path = os.path.join(default_dir, image_filename)
                    if os.path.isfile(image_path):
                        tile_image = Image.open(image_path).convert('RGBA')
                        tile_image = resize_tile(tile_image, target_dimension, dimension_type)
                        tile_images[tile_type]['default'].append(tile_image)
                    else:
                        print(f"Warning: File {image_path} does not exist.")
            else:
                print(f"Warning: Default directory {default_dir} does not exist for tile type {tile_type}")
    return tile_images

# Resize tile images
def resize_tile(tile_image, target_dimension, dimension_type='width'):
    original_width, original_height = tile_image.size
    if dimension_type == 'width':
        scale_ratio = target_dimension / original_width
    else:
        scale_ratio = target_dimension / original_height

    new_width = int(original_width * scale_ratio)
    new_height = int(original_height * scale_ratio)

    tile_image = tile_image.resize((new_width, new_height), Image.LANCZOS)
    return tile_image

# Tilt image for perspective effect
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

# Calculate tile position
def calculate_tile_position(x, y, origin_x, origin_y, x_offset_x, x_offset_y, y_offset_x_tile, y_offset_y):
    pos_x = origin_x + x * x_offset_x + y * y_offset_x_tile
    pos_y = origin_y + x * x_offset_y + y * y_offset_y
    return int(pos_x), int(pos_y)

# Get connected variant for connectable tiles
def get_connected_variant(grid, x, y, tile_type):
    grid_width = len(grid[0])
    grid_height = len(grid)
    connections = {
        'top': y > 0 and grid[y - 1][x] == tile_type,
        'bottom': y < grid_height - 1 and grid[y + 1][x] == tile_type,
        'left': x > 0 and grid[y][x - 1] == tile_type,
        'right': x < grid_width - 1 and grid[y][x + 1] == tile_type,
    }
    connected_sides = [side for side, connected in connections.items() if connected]
    num_connections = len(connected_sides)
    if num_connections == 0:
        return 'isolated'
    elif num_connections == 1:
        return f"edge_{connected_sides[0]}"
    elif num_connections == 2:
        if {'top', 'bottom'}.issubset(connected_sides):
            return 'side_vertical'
        elif {'left', 'right'}.issubset(connected_sides):
            return 'side_horizontal'
        elif 'top' in connected_sides and 'left' in connected_sides:
            return 'corner_tl'
        elif 'top' in connected_sides and 'right' in connected_sides:
            return 'corner_tr'
        elif 'bottom' in connected_sides and 'left' in connected_sides:
            return 'corner_bl'
        elif 'bottom' in connected_sides and 'right' in connected_sides:
            return 'corner_br'
        else:
            return f"two_{'_'.join(sorted(connected_sides))}"
    elif num_connections == 3:
        return f"three_{'_'.join(sorted(connected_sides))}"
    elif num_connections == 4:
        return 'center'
    return 'isolated'

# Load background images
def load_background_images(config):
    backgrounds = []
    for bg_file in os.listdir(BACKGROUNDS_DIR):
        if bg_file in config['backgrounds']:
            backgrounds.append(bg_file)
        else:
            print(f"Warning: Background {bg_file} does not have a corresponding configuration in config.json")
    return backgrounds

# Updated mapping from characters to tile types based on your CSV data
tile_char_mapping = {
    'M': ['block_of_stone&grass', 'cactus'],   # Blocking1
    'X': ['cubic_wall', 'yellow_wall'],        # Blocking2
    'F': ['yellow_wall'],                      # Blocking3
    'B': ['cactus'],                           # Blocking4
    'D': ['red_pottery'],                      # DecoDestructible
    'I': ['invincible_wall'],                  # Indestructible
    'Y': ['wooden_box'],                       # RespawningForest
    'R': ['bush'],                             # Forest
    'C': ['wooden_barrel'],                    # BlockingDestroyableWithWeapon
    'N': ['wooden_fence'],                     # Fence
    'J': ['air'],                        # InvisibleIndestructible
    'S': ['blue_barrel'],                      # Snow
    'JJ': ['blue_post'],
    # Any other characters will map to 'air' by default
}

CENTERED_TILES = ["wooden_fence", "blue_post"]

def compute_grid_size(bg_settings):
    """
    Compute grid_width and grid_height based on background settings.
    """
    origin_x = bg_settings.get('origin_x', 0)
    origin_y = bg_settings.get('origin_y', 0)
    x_offset_x = bg_settings.get('x_offset_x', 1)  # Prevent division by zero
    y_offset_y = bg_settings.get('y_offset_y', 1)  # Prevent division by zero

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

def process_maps_in_csv(csv_filename):
    """
    Reads the CSV file and returns a list of maps (map_name, map_data).
    """
    maps = []
    with open(os.path.join(MAPS_DIR, csv_filename), 'r', encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = [row for row in reader if row]

    current_map_name = None
    current_map_data = []

    for row in rows:
        # Detect new map by checking if the first cell is not empty and doesn't start with ','
        first_cell = row[0]
        if first_cell and not first_cell.startswith(','):
            # Save the previous map
            if current_map_name and current_map_data:
                if current_map_name.startswith("Laserball"):
                    maps.append((current_map_name, current_map_data))
            # Start a new map
            current_map_name = first_cell.replace('"', '')
            current_map_data = []
        else:
            # Continue collecting map data
            # Remove leading commas and quotes
            line = ''.join(cell for cell in row)

            line.replace('",', '')
            line.replace(',"', '')
            if line:
                current_map_data.append(list(line))

    # Add the last map
    if current_map_name and current_map_data:
        if current_map_name.startswith("Laserball"):
            maps.append((current_map_name, current_map_data))

    return maps

def process_single_map(
    map_name, map_data, config, tile_images, background_files
):
    print(map_data)
    i = 0
    # Map characters to tile types
    grid = []
    for row in map_data:
        i+= 1
        grid_row = []
        for char in row:
            tile_type_list = tile_char_mapping.get(char, ['air'])  # Default to ['air'] if not found
            tile_type = random.choice(tile_type_list)
            grid_row.append(tile_type)
        grid.append(grid_row)
    print(grid)
    print()
    if not grid or not grid[0]:
        print(f"Warning: Grid is empty for map {map_name}")
        return

    # For each background, generate the map image
    for bg_filename in background_files:

        bg_settings = config['backgrounds'][bg_filename]
        bg_path = os.path.join(BACKGROUNDS_DIR, bg_filename)
        background = Image.open(bg_path).convert('RGBA')
        map_image = background.copy()

        origin_x = bg_settings.get('origin_x', 0)
        origin_y = bg_settings.get('origin_y', 0)
        x_offset_x = bg_settings.get('x_offset_x', 1)
        x_offset_y = bg_settings.get('x_offset_y', 0)
        y_offset_y = bg_settings.get('y_offset_y', 1)

        tilt_angle_left = bg_settings.get('tilt_angle_left', 0)
        tilt_angle_right = bg_settings.get('tilt_angle_right', 0)
        y_offset_x_left = bg_settings.get('y_offset_x_left', 0)
        y_offset_x_right = bg_settings.get('y_offset_x_right', 0)

        non_placeable_margins = bg_settings.get('non_placeable_margins', {})
        grid_width_limit, grid_height_limit = compute_grid_size(bg_settings)

        # Adjust grid size if necessary
        resized_grid = grid

        # Adjust grid height
        if len(grid) > grid_height_limit:
            start_row = random.randint(0, len(grid) - grid_height_limit)
            resized_grid = grid[start_row:start_row + grid_height_limit]


        # Place tiles on the map
        place_tiles_on_map(
            map_image, resized_grid, tile_images, config,
            origin_x, origin_y, x_offset_x, x_offset_y, y_offset_y,
            tilt_angle_left, tilt_angle_right, y_offset_x_left, y_offset_x_right,
            non_placeable_margins
        )

        # Save the map image
        base_filename = f"{map_name}_{bg_filename}"
        output_path = os.path.join(OUTPUT_IMAGES_DIR, f"{base_filename}.png")
        map_image.convert('RGB').save(output_path)

# Function to place tiles on the map image
def place_tiles_on_map(
    map_image, grid, tile_images, config,
    origin_x, origin_y, x_offset_x, x_offset_y, y_offset_y,
    tilt_angle_left, tilt_angle_right, y_offset_x_left, y_offset_x_right,
    non_placeable_margins
):
    if not grid or not grid[0]:
        print("Warning: Empty grid passed to place_tiles_on_map.")
        return

    grid_width = len(grid[0])
    grid_height = len(grid)
    grid_center = (grid_width - 1) / 2 if grid_width > 1 else 0
    tilted_tile_cache = {}
    variant = None
    for y in range(grid_height):
        for x in range(grid_width):
            tile_type = grid[y][x]
            if tile_type == "air":
                continue  # Skip empty tiles
            if tile_type in tile_images:
                tile_info = config['tiles'][tile_type]
                if tile_info['connectable']:
                    variant = get_connected_variant(grid, x, y, tile_type)
                    if variant in tile_images[tile_type]['connected']:
                        variations = tile_images[tile_type]['connected'][variant]
                    else:
                        variant = 'isolated'
                        variations = tile_images[tile_type]['connected'].get(variant, [])
                        if not variations:
                            continue
                    tile_img = random.choice(variations)
                else:
                    tile_img = random.choice(tile_images[tile_type]['default'])

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

                cache_key = (tile_type, variant, tilt_angle_tile)
                if cache_key in tilted_tile_cache:
                    tile_img_tilted = tilted_tile_cache[cache_key]
                else:
                    tile_img_tilted = tilt_image(tile_img, tilt_angle_tile)
                    tilted_tile_cache[cache_key] = tile_img_tilted

                actual_tile_width, actual_tile_height = tile_img_tilted.size
                pos_x, pos_y = calculate_tile_position(
                    x, y, origin_x, origin_y, x_offset_x, x_offset_y, y_offset_x_tile, y_offset_y
                )
                if tile_type in CENTERED_TILES:
                    pos_x_center = pos_x - (actual_tile_width // 2) + (x_offset_x // 2)
                    pos_y_center = pos_y - (actual_tile_height // 2) + (y_offset_y // 2)
                    pos_x, pos_y = int(pos_x_center), int(pos_y_center)

                map_image.alpha_composite(tile_img_tilted, dest=(int(pos_x), int(pos_y)))

def main():
    config = load_configuration()
    tile_images = load_tile_images(config)
    background_files = load_background_images(config)
    map_files = [f for f in os.listdir(MAPS_DIR) if f.endswith('.csv')]

    # Collect all maps to process
    all_maps = []
    for csv_filename in map_files:
        maps_in_csv = process_maps_in_csv(csv_filename)
        all_maps.extend(maps_in_csv)

    # Filter maps to only those starting with "Laserball"
    #hahaha
    all_maps = [(map_name, map_data) for map_name, map_data in all_maps if map_name.startswith("Laserball_")]
    process_map_partial = partial(
        process_single_map,
        config=config,
        tile_images=tile_images,
        background_files=background_files
    )

    max_workers = os.cpu_count() or 8

    print(f"Starting map generation with {max_workers} parallel workers...")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(process_map_partial, map_name, map_data)
            for map_name, map_data in all_maps
        ]

        for future in tqdm(as_completed(futures), total=len(futures), desc="Generating Maps"):
            try:
                future.result()
            except Exception as e:
                print(f"Error generating map: {e}")

    print(f"Generated maps for {len(all_maps)} maps.")

if __name__ == '__main__':
    main()
