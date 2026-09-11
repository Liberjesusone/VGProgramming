"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

Game settings: input bindings, the sizes everything else is measured
against, and the loaded textures, tilesets and fonts.
"""

import pathlib

import pygame

from gale import input_handler
from gale import tilemap

# ------------------------------------------------------------
# input
# ------------------------------------------------------------
#input_handler.InputHandler.set_keyboard_action(input_handler.KEY_ESCAPE, "quit")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_RETURN, "confirm")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_KP_ENTER, "confirm")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_w, "move_up")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_s, "move_down")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_a, "move_left")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_d, "move_right")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_F1, "debug")

TITLE = "Light Spirits"

BASE_DIR = pathlib.Path(__file__).parent

# ------------------------------------------------------------
# sizes
# ------------------------------------------------------------
# The window is three times the virtual surface, so every pixel of art
# lands on an exact 3x3 block of screen pixels and nothing is ever
# resampled. 640x360 also doubles cleanly to 1280x720 for a smaller
# window while developing.
VIRTUAL_WIDTH = 640
VIRTUAL_HEIGHT = 360

WINDOW_WIDTH = 1536
WINDOW_HEIGHT = 790

TILE_SIZE = 32

# The player is two tiles tall. That is not an arbitrary pick: it makes
# the screen 11.25 tiles high, so the player occupies 2/11 of the screen.
PLAYER_WIDTH = 28
PLAYER_HEIGHT = 64


def to_virtual(position) -> tuple[int, int]:
    """ Window pixels to virtual surface pixels.

    gale.Game draws on the virtual surface and stretches it over the
    whole window, but pygame reports the mouse in window pixels, so any
    hit test or aim direction has to undo that stretch first.
    """
    x, y = position
    return (x * VIRTUAL_WIDTH / WINDOW_WIDTH, y * VIRTUAL_HEIGHT / WINDOW_HEIGHT)


# ------------------------------------------------------------
# floors
# ------------------------------------------------------------
# Each source texture was one continuous seamless image; tools/build_assets.py
# turned it into a BLOCK_TILES x BLOCK_TILES grid of tiles that still line up
# against each other. Laying a material down means repeating that grid, which
# is why Level indexes it with row % BLOCK_TILES and col % BLOCK_TILES rather
# than picking tiles at random: two tiles that were not neighbours in the
# source do not join cleanly.
BLOCK_TILES = 8
TILES_PER_MATERIAL = BLOCK_TILES * BLOCK_TILES

FLOOR_MATERIALS = [
    "weathered_cracked_stone_slabs",
    "damp_mossy_cobblestone",
    "wet_dark_packed_earth_with_small_pebbles",
    "rotten_wooden_planks",
    "grey_ash_and_fine_gravel",
]

PROP_NAMES = [
    "broken_stone_pillar",
    "dead_leafless_tree",
    "mossy_boulder",
    "rusted_iron_brazier",
    "stone_sarcophagus",
]


def _graphic(*parts: str) -> pygame.Surface:
    return pygame.image.load(BASE_DIR.joinpath("assets", "graphics", *parts))


# Add to the TEXTURES the floor- ones
TEXTURES = {
    f"floor-{name}": _graphic("tilesets", f"floor_{name}.png")
    for name in FLOOR_MATERIALS
}
# Add to the TEXTURES the prop- ones
TEXTURES.update(
    {f"prop-{name}": _graphic("props", f"{name}.png") for name in PROP_NAMES}
)

# Gid 0 is reserved by Tiled to mean "empty", so the first material starts
# at 1 and each one after it claims the next block of TILES_PER_MATERIAL.
FLOOR_TILESETS = {
    name: tilemap.Tileset(
        TEXTURES[f"floor-{name}"],
        TILE_SIZE,
        TILE_SIZE,
        first_gid=1 + index * TILES_PER_MATERIAL,
    )
    for index, name in enumerate(FLOOR_MATERIALS)
}

FLOOR_FIRST_GID = {
    name: tileset.first_gid for name, tileset in FLOOR_TILESETS.items()
}

FONTS = {
    "small": pygame.font.Font(None, 18),
    "medium": pygame.font.Font(None, 28),
    "large": pygame.font.Font(None, 64),
}

COLOR_BACKGROUND = (12, 12, 16)
COLOR_TEXT = (222, 218, 208)
COLOR_DIM = (140, 136, 128)
COLOR_ACCENT = (198, 158, 92)
