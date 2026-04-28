import os
import shutil
import random

# Define the source directories for maps and labels
src_image_dir = 'map_generator/output/images'      # Directory where the map images are generated
src_label_dir = 'map_generator/output/labels'    # Directory where label files are generated

# Define the destination directories for train/validation sets
dst_image_dir_train = 'dataset/images/train/'
dst_image_dir_val = 'dataset/images/val/'
dst_label_dir_train = 'dataset/labels/train/'
dst_label_dir_val = 'dataset/labels/val/'

# Create the destination directories if they don't exist
os.makedirs(dst_image_dir_train, exist_ok=True)
os.makedirs(dst_image_dir_val, exist_ok=True)
os.makedirs(dst_label_dir_train, exist_ok=True)
os.makedirs(dst_label_dir_val, exist_ok=True)

# List all the map files and corresponding labels
map_files = sorted([f for f in os.listdir(src_image_dir) if f.endswith('.png') and not f.endswith('_mask.png')])
label_files = sorted([f for f in os.listdir(src_label_dir) if f.endswith('.txt')])

# Ensure that map and label files match
assert len(map_files) == len(label_files), "Mismatch between number of maps and labels."

# Split into train/val (e.g., 80% train, 20% val)
combined = list(zip(map_files, label_files))
random.shuffle(combined)
split_ratio = 0.8
split_index = int(len(combined) * split_ratio)
train_set = combined[:split_index]
val_set = combined[split_index:]

# Function to move images and labels
def move_files(dataset, image_src, label_src, image_dest, label_dest):
    for map_file, label_file in dataset:
        # Copy the map image
        shutil.move(os.path.join(image_src, map_file), os.path.join(image_dest, map_file))

        # Copy the label file
        shutil.move(os.path.join(label_src, label_file), os.path.join(label_dest, label_file))

# Move the files for train and validation sets
move_files(train_set, src_image_dir, src_label_dir, dst_image_dir_train, dst_label_dir_train)
move_files(val_set, src_image_dir, src_label_dir, dst_image_dir_val, dst_label_dir_val)

print("Images and labels have been organized into train and val sets.")
