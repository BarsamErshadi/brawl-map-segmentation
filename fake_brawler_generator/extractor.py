import os
import random
import time

from PIL import Image

from fake_brawler_generator.ammo_bar_generator import generate_ammo_bar_image
from fake_brawler_generator.base_brawler_generator import create_base_brawler_image
from fake_brawler_generator.health_bar_generator import generate_health_bar_image
from fake_brawler_generator.username_generator import generate_username_image


# 1. Create your base "combined_image" with green circle, brawler, and ammo bar


def create_fake_player_image(brawler_path, ammo_amount, health_amount, health_percentage, username, have_gadget_icon=False, gear_amount=False, have_hypercharge_icon=False, force_first_color=False):
    # ammobar just above the brawler image

    bottom_half = -47
    if have_gadget_icon:
        bottom_half -= 8
    elif have_hypercharge_icon:
        bottom_half -= 3
    elif gear_amount == 2:
        bottom_half -= 4
    elif gear_amount == 1:
        bottom_half -= 1
    ammo_bar_offset = - 86 + bottom_half

    base_brawler_image = create_base_brawler_image(brawler_path, have_gadget_icon=have_gadget_icon, gear_amount=gear_amount, have_hypercharge_icon=have_hypercharge_icon, color="green")

    ammo_bar_image = generate_ammo_bar_image(value=ammo_amount)
    health_bar_image = generate_health_bar_image(value=health_percentage, health_amount=health_amount, force_first_color=force_first_color)

    username_image = generate_username_image(username)

    base_width = max(base_brawler_image.width, ammo_bar_image.width, health_bar_image.width, username_image.width)
    base_height = ammo_bar_image.height + abs(ammo_bar_offset) + health_bar_image.height + username_image.height

    # paste the base brawler image at the bottom of the canvas
    base_brawler_x = (base_width - base_brawler_image.width) // 2
    base_brawler_y = base_height - base_brawler_image.height

    ammo_bar_x = (base_width - ammo_bar_image.width) // 2
    ammo_bar_y = base_height - ammo_bar_image.height + ammo_bar_offset

    # health bar just above the ammo bar
    health_bar_x = (base_width - health_bar_image.width) // 2
    health_bar_y = ammo_bar_y - health_bar_image.height

    # username just above the health bar
    username_x = (base_width - username_image.width) // 2
    username_y = health_bar_y - username_image.height

    combined_img = Image.new("RGBA", (base_width, base_height), (0, 0, 0, 0))
    combined_img.paste(base_brawler_image, (base_brawler_x, base_brawler_y), base_brawler_image)
    combined_img.paste(ammo_bar_image, (ammo_bar_x, ammo_bar_y), ammo_bar_image)
    combined_img.paste(health_bar_image, (health_bar_x, health_bar_y), health_bar_image)
    combined_img.paste(username_image, (username_x, username_y), username_image)

    return combined_img

def create_fake_ally_image(brawler_path, health_amount, health_percentage, username, have_gadget_icon=False, gear_amount=False, have_hypercharge_icon=False, force_first_color=False):
    bottom_half = -47
    if have_gadget_icon:
        bottom_half -= 8
    elif have_hypercharge_icon:
        bottom_half -= 3
    elif gear_amount == 2:
        bottom_half -= 4
    elif gear_amount == 1:
        bottom_half -= 1
    ammo_bar_offset = - 86 + bottom_half

    base_brawler_image = create_base_brawler_image(brawler_path, have_gadget_icon=have_gadget_icon, gear_amount=gear_amount, have_hypercharge_icon=have_hypercharge_icon, color="blue")

    ammo_bar_image = generate_ammo_bar_image(value=2.3)

    health_bar_image = generate_health_bar_image(value=health_percentage, health_amount=health_amount, thirds_colors=((255, 15, 9, 255), (251, 227, 16, 255), (0, 224, 255, 255)), thirds_shining_colors=((0, 255, 255, 255), (255, 240, 44, 255), (255, 15, 9, 255)), force_first_color=force_first_color)

    username_image = generate_username_image(username, text_color=(129, 254, 251, 255))

    base_width = max(base_brawler_image.width, ammo_bar_image.width, health_bar_image.width, username_image.width)
    base_height = abs(ammo_bar_offset) + ammo_bar_image.height + health_bar_image.height + username_image.height

    # paste the base brawler image at the bottom of the canvas
    base_brawler_x = (base_width - base_brawler_image.width) // 2
    base_brawler_y = base_height - base_brawler_image.height

    ammo_bar_y = base_height - ammo_bar_image.height + ammo_bar_offset

    # health bar just above the ammo bar
    health_bar_x = (base_width - health_bar_image.width) // 2
    health_bar_y = ammo_bar_y - health_bar_image.height

    # username just above the health bar
    username_x = (base_width - username_image.width) // 2
    username_y = health_bar_y - username_image.height

    combined_img = Image.new("RGBA", (base_width, base_height), (0, 0, 0, 0))
    combined_img.paste(base_brawler_image, (base_brawler_x, base_brawler_y), base_brawler_image)
    combined_img.paste(health_bar_image, (health_bar_x, health_bar_y), health_bar_image)
    combined_img.paste(username_image, (username_x, username_y), username_image)

    return combined_img

def create_fake_enemy_image(brawler_path, health_amount, health_percentage, username, have_gadget_icon=False, gear_amount=False, have_hypercharge_icon=False, force_first_color=False):
    bottom_half = -47
    if have_gadget_icon:
        bottom_half -= 8
    elif have_hypercharge_icon:
        bottom_half -= 3
    elif gear_amount == 2:
        bottom_half -= 4
    elif gear_amount == 1:
        bottom_half -= 1
    ammo_bar_offset = - 86 + bottom_half

    base_brawler_image = create_base_brawler_image(brawler_path, have_gadget_icon=have_gadget_icon,gear_amount=gear_amount,have_hypercharge_icon=have_hypercharge_icon, color="red")

    ammo_bar_image = generate_ammo_bar_image(value=2.3)

    health_bar_image = generate_health_bar_image(value=health_percentage, health_amount=health_amount, thirds_colors=((255, 15, 9, 255), (251, 227, 16, 255), (233, 22, 47, 255)), thirds_shining_colors=((224, 110, 126, 255), (255, 240, 44, 255), (255, 15, 9, 255)), force_first_color=force_first_color)

    username_image = generate_username_image(username, text_color=(251, 172, 170, 255))

    base_width = max(base_brawler_image.width, ammo_bar_image.width, health_bar_image.width, username_image.width)
    base_height = abs(ammo_bar_offset)+ ammo_bar_image.height + health_bar_image.height + username_image.height

    # paste the base brawler image at the bottom of the canvas
    base_brawler_x = (base_width - base_brawler_image.width) // 2
    base_brawler_y = base_height - base_brawler_image.height

    ammo_bar_y = base_height - ammo_bar_image.height + ammo_bar_offset

    # health bar just above the ammo bar
    health_bar_x = (base_width - health_bar_image.width) // 2
    health_bar_y = ammo_bar_y - health_bar_image.height

    # username just above the health bar
    username_x = (base_width - username_image.width) // 2
    username_y = health_bar_y - username_image.height

    combined_img = Image.new("RGBA", (base_width, base_height), (0, 0, 0, 0))
    combined_img.paste(base_brawler_image, (base_brawler_x, base_brawler_y), base_brawler_image)
    combined_img.paste(health_bar_image, (health_bar_x, health_bar_y), health_bar_image)
    combined_img.paste(username_image, (username_x, username_y), username_image)

    return combined_img

def get_random_username():
    length = random.randint(0, 15)
    username = ""
    for i in range(length):
        username += random.choice("abcdefghijklmnopqrstuvwxyz123456789._-/\\\"'!@#$%^&*()_+[]{}|;:,.<>?")
    return username

SKINS_DIR = "fake_brawler_generator/skin_seg_3"


def skins_available():
    # Character cutouts aren't committed; without them, maps are generated without character distractors.
    return os.path.isdir(SKINS_DIR) and len(os.listdir(SKINS_DIR)) > 0


def create_random_fake_player():
    if not skins_available():
        return None
    have_gadget_icon = random.choice([True, False])
    gear_amount = random.choice([0, 1, 2])
    have_hypercharge_icon = random.choice([True, False])
    max_health = random.randint(3000, 15000)
    #health percentage is between 0 and 1
    health_percentage = random.random()
    health_amount = int(health_percentage*max_health)
    force_first_color = random.choice([True, False])
    #ammo amount is between 0 and 3
    ammo_amount = round(random.random()*3, 3)
    username = get_random_username()
    #get random folder in skin_seg_3
    all_sub_folders = os.listdir("fake_brawler_generator/skin_seg_3")
    random_folder = random.choice(all_sub_folders)
    random_file = random.choice(os.listdir(f"fake_brawler_generator/skin_seg_3/{random_folder}"))
    full_path = f"fake_brawler_generator/skin_seg_3/{random_folder}/{random_file}"
    return create_fake_player_image(full_path, ammo_amount, health_amount, health_percentage, username, have_gadget_icon=have_gadget_icon, gear_amount=gear_amount, have_hypercharge_icon=have_hypercharge_icon, force_first_color=force_first_color)

def create_random_fake_other(func):
    if not skins_available():
        return None
    have_gadget_icon = random.choice([True, False])
    gear_amount = random.choice([0, 1, 2])
    have_hypercharge_icon = random.choice([True, False])
    max_health = random.randint(3000, 15000)
    #health percentage is between 0 and 1
    health_percentage = random.random()
    health_amount = int(health_percentage*max_health)
    force_first_color = random.choice([True, False])
    username = get_random_username()
    #get random folder in skin_seg_3/skin_seg_3
    all_sub_folders = os.listdir("fake_brawler_generator/skin_seg_3")
    random_folder = random.choice(all_sub_folders)
    random_file = random.choice(os.listdir(f"fake_brawler_generator/skin_seg_3/{random_folder}"))
    full_path = f"fake_brawler_generator/skin_seg_3/{random_folder}/{random_file}"
    return func(full_path, health_amount, health_percentage, username, have_gadget_icon=have_gadget_icon, gear_amount=gear_amount, have_hypercharge_icon=have_hypercharge_icon, force_first_color=force_first_color)


if __name__ == "__main__":
    for i in range(1, 101):
        print(i, end=" ")
        final_image = create_random_fake_other(create_fake_enemy_image)
        final_image.save(f"temp/new{i}.png")
