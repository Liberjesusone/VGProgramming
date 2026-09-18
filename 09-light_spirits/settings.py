"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

Game settings: input bindings, the sizes everything else is measured
against, and the loaded textures, tilesets and fonts.
"""

import json
import pathlib
from typing import Dict

import pygame

from gale import input_handler
from gale import tilemap
from actions import (
    ATTACK,
    CONFIRM,
    DEBUG,
    DEBUG_BOSS,
    HEAL,
    MOVE_DOWN,
    MOVE_LEFT,
    MOVE_RIGHT,
    MOVE_UP,
    QUIT,
    ROLL,
    SWITCH_WEAPON,
)


# ------------------------------------------------------------
# Input
# ------------------------------------------------------------
#input_handler.InputHandler.set_keyboard_action(input_handler.KEY_ESCAPE, QUIT) # We will use another method in pause mode to quit
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_RETURN, CONFIRM)
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_KP_ENTER, CONFIRM)
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_w, MOVE_UP)
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_s, MOVE_DOWN)
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_a, MOVE_LEFT)
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_d, MOVE_RIGHT)
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_F1, DEBUG)
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_F2, DEBUG_BOSS)
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_q, SWITCH_WEAPON)
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_SPACE, ROLL)
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_r, HEAL)

""" The sword: held to charge, released to swing. No motion binding is
registered here on purpose, an action bound with InputHandler is
delivered to whichever state is on top of the stack, and a motion event
carries no .pressed/.released the way every on_input in this project
expects, so the first mouse twitch over any other screen would crash it.
Aiming is polled every frame in Player._update_aim instead. """
input_handler.InputHandler.set_mouse_click_action(input_handler.MOUSE_BUTTON_1, ATTACK)

TITLE = "Light Spirits"

BASE_DIR = pathlib.Path(__file__).parent


# ------------------------------------------------------------
# sizes
# ------------------------------------------------------------
""" The window is three times the virtual surface, so every pixel of art
lands on an exact 3x3 block of screen pixels and nothing is ever
resampled. 640x360 also doubles cleanly to 1280x720 for a smaller
window while developing. """
VIRTUAL_WIDTH = 640
VIRTUAL_HEIGHT = 360

""" Read from the real desktop instead of a hand-picked constant, so the
window (see LightSpirits.__init__, which opens it borderless at
exactly this size) always fills whatever screen the game runs on.

The same reasoning behind, e.g., a 1920x1080 monitor and a 15.6" laptop
under Windows' own DPI scaling both work with no per-machine tuning.
pygame.display.Info() must run after gale.game's own pygame.init()
(see that module) and before any pygame.display.set_mode() call, or it
reports the already-set window's size instead of the desktop's. """
_desktop = pygame.display.Info()
WINDOW_WIDTH = _desktop.current_w
WINDOW_HEIGHT = _desktop.current_h

TILE_SIZE = 32

""" The player is two tiles tall. That is not an arbitrary pick: it makes
the screen 11.25 tiles high, so the player occupies 2/11 of the screen.
Every character sprite (see tools/build_assets.py) is scaled to this
height at build time; there is no PLAYER_WIDTH constant to match it,
since the sprite's own width already varies by facing direction (a bow
held out to the side reads wider than one held behind the body),
Player.width reads it straight off whichever sprite is showing. """
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
# Names of files
# ------------------------------------------------------------
""" Each source texture was one continuous seamless image; tools/build_assets.py
turned it into a BLOCK_TILES x BLOCK_TILES grid of tiles that still line up
against each other. Laying a material down means repeating that grid, which
is why Level indexes it with row % BLOCK_TILES and col % BLOCK_TILES rather
than picking tiles at random: two tiles that were not neighbours in the
source do not join cleanly. """
BLOCK_TILES = 8
TILES_PER_MATERIAL = BLOCK_TILES * BLOCK_TILES

FLOOR_MATERIALS = [
    "weathered_cracked_stone_slabs",
    "damp_mossy_cobblestone",
    "wet_dark_packed_earth_with_small_pebbles",
    "rotten_wooden_planks",
    "grey_ash_and_fine_gravel",
]

""" Every direction a character sprite can face. "left" is never its own
generated image (see tools/build_assets.py): it is "right" mirrored at
build time, but the key exists here like the other three so nothing
reading TEXTURES has to know that. """
PLAYER_DIRECTIONS = ("down", "up", "left", "right")


# ------------------------------------------------------------
# Tilesets
# ------------------------------------------------------------
""" Every texture in the game lives in a handful of tilesets, one per
category, built by tools/build_assets.py: a PNG plus a JSON index naming
the exact rect of every region inside it. The same PNGs are what Tiled
paints the map with.

TILESETS[tileset][region] is every region, sliced once here at startup.
TEXTURES below keeps the keys the rest of the game has always used, so
nothing outside this file knows the art ever came from a tileset. """
TILESETS_DIR = BASE_DIR / "assets" / "tilesets"

TILESET_NAMES = (
    "floors", "walls", "fences", "forest", "rocks", "cliffs",
    "player", "enemies", "bosses", "props", "decor", "bonfire", "hud",
)


def _load_tileset(name: str) -> Dict[str, pygame.Surface]:
    """ Loads the tileset image, gets the json "regions" property
    and iterates for all the regions names and 4 coords to create
    the subimages of the tilesets; to create all the tiles"""
    image_path = TILESETS_DIR / f"{name}.png"

    if not image_path.exists():
        return {}

    image = pygame.image.load(image_path)

    with open(TILESETS_DIR / f"{name}.json", encoding="utf-8") as index:
        regions = json.load(index)["regions"]

    return {region: image.subsurface(pygame.Rect(rect)) for region, rect in regions.items()}

# For every tileset name, we load its dict. with the pose name and image
TILESETS = {name: _load_tileset(name) for name in TILESET_NAMES}


# ------------------------------------------------------------
# Placeholder for images that hasn't been created yet
# ------------------------------------------------------------
def _placeholder_character(label: str, width: int, height: int) -> pygame.Surface:
    """ Stand-in for a character pose that has not been generated yet. While 
    its own art was still being drawn: the game stays fully playable and 
    every pose is visibly testable in the meantime, and the moment 
    tools/build_assets.py adds the real pose to its tileset, _character_graphic
    below picks it up on its own, nothing else in the project has to change. """
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    box = surface.get_rect()
    pygame.draw.rect(surface, (90, 70, 110, 210), box, border_radius=6)
    pygame.draw.rect(surface, (230, 210, 140, 255), box, 2, border_radius=6)

    font = pygame.font.Font(None, 14)
    for i, word in enumerate(label.split("-")):
        text = font.render(word, True, (255, 255, 255))
        surface.blit(text, text.get_rect(center=(width // 2, height // 2 + i * 12 - 6)))

    return surface


""" How big a placeholder pose reads as, in the absence of a real image to
measure, close enough to the real character's own proportions
(settings.PLAYER_HEIGHT tall) that nothing downstream notices which
kind of surface it actually got. """
_PLACEHOLDER_CHARACTER_SIZE = (40, 64)


def _character_graphic(
    tileset: str, region: str, label: str, size: tuple = _PLACEHOLDER_CHARACTER_SIZE
) -> pygame.Surface:
    """ A character pose from its tileset if it has been generated, and a
    placeholder of the given size while it has not been. Floors and props
    read their tilesets directly instead, since that art is finished and a
    missing region there should keep failing loudly. """
    surface = TILESETS[tileset].get(region)
    return surface if surface is not None else _placeholder_character(label, *size)


# ------------------------------------------------------------
# Floor
# ------------------------------------------------------------
TEXTURES = {
    f"floor-{name}": TILESETS["floors"][f"floor_{name}"]
    for name in FLOOR_MATERIALS
}

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


# ------------------------------------------------------------
# Props
# ------------------------------------------------------------
TEXTURES.update(
    {f"prop-{name}": image for name, image in TILESETS["props"].items()}
)


# ------------------------------------------------------------
# Player
# ------------------------------------------------------------
""" Every other pose the player can be in: walking, and each weapon's own
idle/charge1/charge2/attack. (settings key prefix, source file prefix)
pairs, most of these are still being generated a piece at a time (see
tools/build_assets.py), so _character_graphic is what keeps the game
booting and fully playable in the meantime, placeholder poses and all. """
CHARACTER_POSE_SETS = [
    ("sword-idle", "archer_sword_idle"),
    ("sword-walk", "archer_sword_walk"),
    ("sword-charge1", "archer_sword_charge1"),
    ("sword-charge2", "archer_sword_charge2"),
    ("sword-attack", "archer_sword_attack"),
    ("bow-idle", "archer_bow_idle"),
    ("bow-walk", "archer_bow_walk"),
    ("bow-charge1", "archer_bow_charge1"),
    ("bow-charge2", "archer_bow_charge2"),
    ("bow-release", "archer_bow_release"),
    # The dodge roll, unlike every pose above, doesn't have a weapon
    ("roll1", "archer_roll1"),
    ("roll2", "archer_roll2"),
    ("roll3", "archer_roll3"),
]

# Load to Textures the player ones
for _key_prefix, _file_prefix in CHARACTER_POSE_SETS:
    TEXTURES.update(
        {
            f"player-{_key_prefix}-{direction}": _character_graphic(
                "player", f"{_file_prefix}_{direction}", f"{_key_prefix}-{direction}"
            )
            for direction in PLAYER_DIRECTIONS
        }
    )


# ------------------------------------------------------------
# Enemies
# ------------------------------------------------------------
""" Every enemy has the same five poses, one per stage of its single
attack plus walking, in the same four directions as the player. The size
is the placeholder's while no art exists, and the height the real sprite
sheet is scaled to by tools/build_assets.py once it does. """
ENEMY_POSES = ("idle", "walk", "charge1", "charge2", "attack")

ENEMY_SPRITE_SIZES = {
    "zombie": (32, 64),
    "witch": (64, 64),
    "golem": (64, 96),
}

for _kind, _size in ENEMY_SPRITE_SIZES.items():
    TEXTURES.update(
        {
            f"enemy-{_kind}-{pose}-{direction}": _character_graphic(
                "enemies", f"enemy_{_kind}_{pose}_{direction}", f"{_kind}-{pose}-{direction}", _size
            )
            for pose in ENEMY_POSES
            for direction in PLAYER_DIRECTIONS
        }
    )


# ------------------------------------------------------------
# Fonts
# ------------------------------------------------------------
FONTS = {
    "small": pygame.font.Font(None, 18),
    "medium": pygame.font.Font(None, 28),
    "large": pygame.font.Font(None, 64),
}


# ------------------------------------------------------------
# Sounds
# ------------------------------------------------------------
""" Two kinds of audio, kept in two folders:

assets/sounds holds short effects, loaded whole into memory up front so
they play the instant they are asked for, several at once if need be.

assets/music holds long tracks, only ever streamed from disk one at a
time through pygame.mixer.music, so a five minute soundtrack never sits
decoded in memory.

Both are keyed by file name without the extension. A machine with no
audio device at all gets silence (see src/audio.py), never an error. """
AUDIO_EXTENSIONS = (".wav", ".ogg", ".mp3")

""" How many effects can sound at the same time. pygame's default of 8 is
easily used up by a few enemies swinging at once, and once every channel
is busy a new effect is simply dropped. """
SOUND_CHANNELS = 32


def _init_mixer() -> bool:
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
    except pygame.error:
        return False

    pygame.mixer.set_num_channels(SOUND_CHANNELS)
    return True


def _audio_files(folder_name: str) -> Dict[str, pathlib.Path]:
    folder = BASE_DIR / "assets" / folder_name

    if not folder.is_dir():
        return {}

    return {
        path.stem: path
        for path in sorted(folder.iterdir())
        if path.suffix.lower() in AUDIO_EXTENSIONS
    }


AUDIO_ENABLED = _init_mixer()

SOUNDS = (
    {name: pygame.mixer.Sound(str(path)) for name, path in _audio_files("sounds").items()}
    if AUDIO_ENABLED else {}
)

MUSIC = _audio_files("music") if AUDIO_ENABLED else {}


# ------------------------------------------------------------
# Colors
# ------------------------------------------------------------
COLOR_BACKGROUND = (12, 12, 16)
COLOR_TEXT = (222, 218, 208)
COLOR_DIM = (140, 136, 128)
COLOR_ACCENT = (198, 158, 92)

ATTACK_HITBOX_COLOR = (153, 183, 224)

# ------------------------------------------------------------
# Title screen
# ------------------------------------------------------------
""" Scaled once at load time, its own aspect ratio (860x484) is already almost 
exactly 16:9, same as the virtual surface, so this stretch is barely noticeable. """
TITLE_BACKGROUND = pygame.transform.smoothscale(
    pygame.image.load(BASE_DIR / "assets" / "title_background" / "title_background.png"),
    (VIRTUAL_WIDTH, VIRTUAL_HEIGHT),
)