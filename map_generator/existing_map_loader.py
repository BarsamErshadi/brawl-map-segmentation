import csv
import json
import os
import random
import numpy as np

# Paths to your resources
TILE_IMAGES_DIR = 'map_generator/tile_images'
BACKGROUNDS_DIR = 'map_generator/backgrounds'
MAPS_DIR = 'map_generator/maps'
OUTPUT_IMAGES_DIR = 'map_generator/output/maps'
CONFIG_FILE = 'map_generator/config.json'

# Ensure output directory exists
os.makedirs(OUTPUT_IMAGES_DIR, exist_ok=True)

# --- Optimizing the Char Map for faster lookups ---
# We convert the dict to a structure that's faster to query if needed,
# but strictly we just need the keys and values accessible.
TILE_CHAR_MAPPING = {
    'M': ['block_of_stone&grass', 'cactus', 'cubic_wall', 'blue_weights', 'yellow_metallic_box'],
    'X': ['yellow_wall'],
    'F': ['bush'],
    'B': ['cactus', 'bumper'],
    'D': ['red_pottery'],
    'I': ['invincible_wall'],
    'Y': ['wooden_box', 'yellow_wall', 'star_block'],
    'R': ['bush'],
    'C': ['wooden_barrel', 'blue_barrel'],
    'N': ['wooden_fence', 'metallic_fence'],
    'J': ['air'],
    'S': ['air'],
    '.': ["air"],
    '1': ['air'], '2': ['air'], '3': ['air'],
    '6': ['air'], '7': ['air'], '8': ['air'],
    'W': ['air'], 'L': ['air'], 'U': ['air'],
    'K': ['air'], 'O': ['air'], 'o': ['air'],
    'T': ['cactus', "potted_plant"],
}


def load_configuration():
    with open(CONFIG_FILE, 'r', encoding="utf-8") as f:
        return json.load(f)


def load_background_images(config):
    backgrounds = []
    config_bgs = set(config['backgrounds'].keys())

    # Listdir is fast, but set lookup is faster than list iteration
    for bg_file in os.listdir(BACKGROUNDS_DIR):
        if bg_file in config_bgs:
            backgrounds.append(bg_file)
    return backgrounds


def compute_grid_size(bg_settings):
    origin_x = bg_settings.get('origin_x', 0)
    origin_y = bg_settings.get('origin_y', 0)
    x_offset_x = bg_settings.get('x_offset_x', 1)
    y_offset_y = bg_settings.get('y_offset_y', 1)

    margins = bg_settings.get('non_placeable_margins', {})
    placeable_width = bg_settings['map_width'] - origin_x - margins.get('right', 0)
    placeable_height = bg_settings['map_height'] - origin_y - margins.get('bottom', 0)

    grid_width = max(1, int(placeable_width // x_offset_x))
    grid_height = max(1, int(placeable_height // y_offset_y))
    return grid_width, grid_height


def process_maps_in_csv_fast(csv_filename):
    """
    Reads the CSV file into memory and parses it into NumPy character arrays.
    Optimized for speed by avoiding row-by-row CSV parsing logic where possible.
    """
    maps = []

    with open(os.path.join(MAPS_DIR, csv_filename), 'r', encoding="utf-8") as f:
        lines = f.readlines()

    current_map_data = []
    current_map_name = None

    for line in lines:
        line = line.strip()
        if not line: continue

        # Fast check for map header (start of a new block)
        # Assuming standard CSV format where first cell is non-empty for names
        if not line.startswith(','):
            parts = line.split(',')
            first_cell = parts[0].replace('"', '')

            if first_cell:
                # Save previous map
                if current_map_name and current_map_data:
                    if current_map_name.startswith("Laserball_"):
                        maps.append(create_numpy_grid(current_map_data))

                current_map_name = first_cell
                current_map_data = []
                continue

        # This is a data row
        # Remove CSV artifacts fast
        clean_line = line.replace('"', '').replace(',', '')
        if clean_line:
            current_map_data.append(list(clean_line))

    # Add last map
    if current_map_name and current_map_data:
        if current_map_name.startswith("Laserball_"):
            maps.append(create_numpy_grid(current_map_data))

    return maps


def create_numpy_grid(data_list):
    """
    Converts list of lists to a NumPy character array.
    Handles jagged arrays by padding with 'air' ('.') to the max width.
    """
    if not data_list:
        return np.array([])

    max_len = max(len(row) for row in data_list)
    # Create a fixed size array filled with '.' (air)
    padded_grid = np.full((len(data_list), max_len), '.', dtype='<U1')

    for i, row in enumerate(data_list):
        # Fill in the actual data
        length = len(row)
        padded_grid[i, :length] = row

    return padded_grid


def vectorize_map_slice(grid_slice):
    """
    Takes a numpy character grid (the slice) and replaces chars with tile names.
    Uses vectorization to replace all 'M's at once, all 'X's at once, etc.
    """
    # Create an output array of objects (strings)
    # We init with 'air'
    output_grid = np.full(grid_slice.shape, 'air', dtype=object)

    # Find unique characters present in this specific slice
    unique_chars = np.unique(grid_slice)

    for char in unique_chars:
        # Get the potential tiles for this character
        possible_tiles = TILE_CHAR_MAPPING.get(char, ['air'])

        # Pick ONE random tile to represent this character for this entire slice
        # (This matches your original logic: char_to_tile_mapping is built per slice)
        chosen_tile = random.choice(possible_tiles)

        # Boolean masking: Update all positions where grid_slice == char at once
        # This is vastly faster than iterating x,y
        mask = (grid_slice == char)
        output_grid[mask] = chosen_tile

    return output_grid.tolist()


def main():
    # 1. Locate Map File
    csv_files = [f for f in os.listdir(MAPS_DIR) if f.endswith('.csv')]
    if not csv_files:
        print("No CSV files found in maps directory.")
        return []

    # 2. Load all maps into RAM as NumPy arrays
    all_maps = process_maps_in_csv_fast(csv_files[0])
    if not all_maps:
        print("Warning: No valid maps found in CSV.")
        return []

    config = load_configuration()
    background_files = load_background_images(config)

    # 3. Group backgrounds by their Grid Height
    # This prevents processing the same map 50 times if 50 backgrounds share the same height.
    bgs_by_height = {}
    for bg_filename in background_files:
        bg_settings = config['backgrounds'][bg_filename]
        _, grid_height = compute_grid_size(bg_settings)

        if grid_height not in bgs_by_height:
            bgs_by_height[grid_height] = []
        bgs_by_height[grid_height].append(bg_filename)

    final_grids = []

    # 4. Process maps per height requirement
    for grid_height, bg_list in bgs_by_height.items():

        # Create the grids for this specific height
        grids_for_this_height = []

        for map_arr in all_maps:
            map_h, map_w = map_arr.shape

            if map_h >= grid_height:
                # Slice the map (Sliding Window)
                # Vectorized approach: Iterate start indices
                for i in range(map_h - grid_height + 1):
                    # Extract slice (View)
                    map_slice = map_arr[i: i + grid_height, :]
                    # Convert chars to tile names
                    converted_grid = vectorize_map_slice(map_slice)
                    grids_for_this_height.append(converted_grid)
            else:
                # Pad the map
                pad_amount = grid_height - map_h
                # Create padding of air
                padding = np.full((pad_amount, map_w), '.', dtype='<U1')
                # Stack
                padded_map = np.vstack((map_arr, padding))

                converted_grid = vectorize_map_slice(padded_map)
                grids_for_this_height.append(converted_grid)

        # 5. Assign these generated grids to ALL backgrounds that need this height
        # This duplicates the reference, not the data, so it's memory efficient-ish
        # but saves massive CPU time.
        for bg_filename in bg_list:
            for g in grids_for_this_height:
                final_grids.append((g, bg_filename))

    return final_grids


if __name__ == "__main__":
    # For testing
    main()