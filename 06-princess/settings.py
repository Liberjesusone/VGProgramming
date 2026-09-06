"""
ISPPV1 2023
Study Case: The Legend of the Princess (ARPG)

Author: Alejandro Mujica
alejandro.j.mujic4@gmail.com

This file contains the game settings that include the association of the
inputs with an their ids, constants of values to set up the game, sounds,
textures, frames, and fonts.
"""

import pathlib

import pygame

from gale import frames
from gale import input_handler
from gale import tilemap

input_handler.InputHandler.set_keyboard_action(input_handler.KEY_ESCAPE, "quit")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_LEFT, "move_left")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_RIGHT, "move_right")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_UP, "move_up")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_DOWN, "move_down")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_SPACE, "sword")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_RETURN, "enter")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_KP_ENTER, "enter")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_f, "fire")

TITLE = "The Legend of the Princess"

BASE_DIR = pathlib.Path(__file__).parent

VIRTUAL_WIDTH = 384
VIRTUAL_HEIGHT = 216

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720

TILE_SIZE = 16

#
# map constants
#
MAP_WIDTH = VIRTUAL_WIDTH // TILE_SIZE - 2
MAP_HEIGHT = VIRTUAL_HEIGHT // TILE_SIZE - 2

MAP_RENDER_OFFSET_X = (VIRTUAL_WIDTH - MAP_WIDTH * TILE_SIZE) // 2
MAP_RENDER_OFFSET_Y = (VIRTUAL_HEIGHT - MAP_HEIGHT * TILE_SIZE) // 2

#
# tile IDs (1-based, matching the tilesheet's row-major slicing)
#
TILE_TOP_LEFT_CORNER = 4
TILE_TOP_RIGHT_CORNER = 5
TILE_BOTTOM_LEFT_CORNER = 23
TILE_BOTTOM_RIGHT_CORNER = 24

TILE_EMPTY = 19

TILE_FLOORS = [
    7, 8, 9, 10, 11, 12, 13,
    26, 27, 28, 29, 30, 31, 32,
    45, 46, 47, 48, 49, 50, 51,
    64, 65, 66, 67, 68, 69, 70,
    88, 89, 107, 108,
]

TILE_TOP_WALLS = [58, 59, 60]
TILE_BOTTOM_WALLS = [79, 80, 81]
TILE_LEFT_WALLS = [77, 96, 115]
TILE_RIGHT_WALLS = [78, 97, 116]


""" The two sheets the boss needs are not drawn to this game's grid, so
 both are reshaped once here, at import, instead of at every blit.

 villian.png is 1536x1024 concept art: a 4x3 grid of ~190x300 mages
 (column 1 faces down, 2 left, 3 up, 4 right; the three rows are the
 walk cycle) sitting on a soft glow, so the cells line up with no neat
 grid at all. hence the hand-measured bounding boxes below, one per
 mage, in source pixels.
 """ 
_VILLAIN_BOXES = (
    (176, 47, 195, 301), (528, 54, 155, 294), (832, 60, 193, 288), (1163, 54, 159, 294),
    (176, 368, 198, 299), (523, 385, 169, 285), (832, 385, 193, 292), (1158, 385, 167, 284),
    (176, 692, 198, 308), (524, 707, 169, 289), (832, 707, 194, 289), (1158, 707, 168, 285),
)

# Twice the player's 16x32 frame.
VILLAIN_FRAME_WIDTH = 32
VILLAIN_FRAME_HEIGHT = 64

""" One single scale for all twelve, never one per box: scaling each mage
to fill its own cell would make the sprite breathe between frames of
the walk cycle. The widest mage (198 px) is the one that has to fit the
32 px cell, which lands the tallest (308 px) at ~50 px, the ~14 px of
headroom left over at the top of every cell is what Boss.offset_y
accounts for.
"""
_VILLAIN_SCALE = VILLAIN_FRAME_WIDTH / 198


def _build_villain_sheet(source: pygame.Surface) -> pygame.Surface:
    """Cuts each mage out of the concept art and drops it bottom-centred
    into a 4x3 grid of VILLAIN_FRAME_WIDTH x VILLAIN_FRAME_HEIGHT cells,
    so gale.frames.generate_frames can slice it like any other sheet.
    Bottom-centred rather than centred so the feet stay planted while the
    silhouette changes width between the front and side views."""
    sheet = pygame.Surface(
        (VILLAIN_FRAME_WIDTH * 4, VILLAIN_FRAME_HEIGHT * 3), pygame.SRCALPHA
    )

    for i, (x, y, w, h) in enumerate(_VILLAIN_BOXES):
        sprite = pygame.transform.smoothscale(
            source.subsurface(pygame.Rect(x, y, w, h)),
            (round(w * _VILLAIN_SCALE), round(h * _VILLAIN_SCALE)),
        )
        cell_x = (i % 4) * VILLAIN_FRAME_WIDTH
        cell_y = (i // 4) * VILLAIN_FRAME_HEIGHT
        sheet.blit(
            sprite,
            (
                cell_x + (VILLAIN_FRAME_WIDTH - sprite.get_width()) // 2,
                cell_y + VILLAIN_FRAME_HEIGHT - sprite.get_height(),
            ),
        )

    return sheet


""" fireballs.png has no alpha channel at all: every sprite sits on this
 flat colour, which has to become the colorkey or each fireball would
 fly around inside a dark purple square.
 """
_FIREBALL_BACKGROUND = (31, 16, 42)


def _build_fireball_sheet(source: pygame.Surface) -> pygame.Surface:
    """768x384 down to 256x128, i.e. 48x48 frames down to 16x16 ones,
    matching this game's tile size. The division is exact and lossless:
    the sheet is 3x-upscaled pixel art (every 3x3 block is a single
    logical pixel), which is also why this is plain nearest-neighbour
    scale() and not smoothscale(), blending would bleed the background
    colour into the sprite edges and break the colorkey."""
    sheet = pygame.transform.scale(
        source, (source.get_width() // 3, source.get_height() // 3)
    )
    sheet.set_colorkey(_FIREBALL_BACKGROUND)
    return sheet


#
# boss (the fire mage) constants
#
BOSS_HEALTH = 80
BOSS_WALK_SPEED = 10

""" The mage's hitbox. As wide as his frame but a good deal shorter, so the
hood and shoulders overhang the box the way the player's sprite does,
Boss.offset_y absorbs the difference (see the sheet builder above).
"""
BOSS_WIDTH = VILLAIN_FRAME_WIDTH
BOSS_HEIGHT = 32

""" Body contact with the mage costs a whole heart instead of the half a
regular enemy takes off (see Entity.contact_damage).
"""
BOSS_CONTACT_DAMAGE = 2

TIME_FOR_BOSS_TO_FIRE = 2.0

""" How long the mage stays stunned, and how long he then stays immune to
being stunned again, without the second one, a player standing at
range could chain arrows and keep him locked in place forever.
"""
BOSS_STUN_TIME = 2.0
BOSS_STUN_INTERVAL = 5.0

# Chance that the next room the player walks into is the mage's.
BOSS_ROOM_CHANCE = 0.70

# Damage per weapon. The sword is what the fight is actually built
# around; the bow chips away and, more importantly, stuns.
SWORD_DAMAGE = 5
ARROW_DAMAGE = 1

# Fireballs cross the whole room instead of dying after 4 tiles the way a
# thrown pot does, so range is per-Projectile now (see src/Projectile.py).
FIREBALL_SPEED = 90
FIREBALL_RANGE_TILES = MAP_WIDTH

# Frame of the (downscaled) fireballs sheet used for the projectile:
# row 2, column 1 of its 16x8 grid, 1-based, so (2 - 1) * 16 + 1.
FIREBALL_FRAME = 17

TEXTURES = {
    "tiles": pygame.image.load(BASE_DIR / "assets" / "graphics" / "tilesheet.png"),
    "background": pygame.image.load(BASE_DIR / "assets" / "graphics" / "background.png"),
    "character-walk": pygame.image.load(
        BASE_DIR / "assets" / "graphics" / "character_walk.png"
    ),
    "character-swing-sword": pygame.image.load(
        BASE_DIR / "assets" / "graphics" / "character_swing_sword.png"
    ),
    "hearts": pygame.image.load(BASE_DIR / "assets" / "graphics" / "hearts.png"),
    "switches": pygame.image.load(BASE_DIR / "assets" / "graphics" / "switches.png"),
    "entities": pygame.image.load(BASE_DIR / "assets" / "graphics" / "entities.png"),
    "character-pot-lift": pygame.image.load(
        BASE_DIR / "assets" / "graphics" / "character_pot_lift.png"
    ),
    "character-pot-walk": pygame.image.load(
        BASE_DIR / "assets" / "graphics" / "character_pot_walk.png"
    ),
    "villain": _build_villain_sheet(
        pygame.image.load(BASE_DIR / "assets" / "graphics" / "villian.png")
    ),
    "fireballs": _build_fireball_sheet(
        pygame.image.load(BASE_DIR / "assets" / "graphics" / "fireballs.png")
    ),
}

# Used by Room's gale.tilemap.TileMap: TILE_* ids above are 1-based,
# matching this tileset's default first_gid, so they double as gids.
TILESET = tilemap.Tileset(TEXTURES["tiles"], TILE_SIZE, TILE_SIZE)

FRAMES = {
    "tiles": frames.generate_frames(TEXTURES["tiles"], 16, 16),
    "character-walk": frames.generate_frames(TEXTURES["character-walk"], 16, 32),
    "character-swing-sword": frames.generate_frames(
        TEXTURES["character-swing-sword"], 32, 32
    ),
    "hearts": frames.generate_frames(TEXTURES["hearts"], 16, 16),
    "switches": frames.generate_frames(TEXTURES["switches"], 16, 18),
    "entities": frames.generate_frames(TEXTURES["entities"], 16, 16),
    "character-pot-lift": frames.generate_frames(TEXTURES["character-pot-lift"], 16, 32),
    "character-pot-walk": frames.generate_frames(TEXTURES["character-pot-walk"], 16, 32),
    "villain": frames.generate_frames(
        TEXTURES["villain"], VILLAIN_FRAME_WIDTH, VILLAIN_FRAME_HEIGHT
    ),
    "fireballs": frames.generate_frames(TEXTURES["fireballs"], TILE_SIZE, TILE_SIZE),
}


def frame(texture_id, one_based_index):
    """
    Every frame index in this project's own code (tile IDs, quad numbers,
    animation frame lists) is written 1-based, matching the original
    Lua/LOVE2D source it was ported from, since gale.frames.generate_frames
    (like Lua tables) still needs a 0-based lookup.
    """
    return FRAMES[texture_id][one_based_index - 1]


FONTS = {
    "princess": pygame.font.Font(BASE_DIR / "assets" / "fonts" / "princess.otf", 32),
    "princess-small": pygame.font.Font(
        BASE_DIR / "assets" / "fonts" / "princess.otf", 24
    ),
}

SOUNDS = {
    "sword": pygame.mixer.Sound(BASE_DIR / "assets" / "sounds" / "sword.wav"),
    "hit-enemy": pygame.mixer.Sound(BASE_DIR / "assets" / "sounds" / "hit_enemy.wav"),
    "hit-player": pygame.mixer.Sound(BASE_DIR / "assets" / "sounds" / "hit_player.wav"),
    "door": pygame.mixer.Sound(BASE_DIR / "assets" / "sounds" / "door.wav"),
    "heart-taken": pygame.mixer.Sound(
        BASE_DIR / "assets" / "sounds" / "heart_taken.wav"
    ),
    "pot-wall": pygame.mixer.Sound(BASE_DIR / "assets" / "sounds" / "pot_wall.wav"),
}

MUSIC = {
    "start": str(BASE_DIR / "assets" / "sounds" / "start_music.mp3"),
    "dungeon": str(BASE_DIR / "assets" / "sounds" / "dungeon_music.mp3"),
    "game-over": str(BASE_DIR / "assets" / "sounds" / "game_over_music.mp3"),
}

COLOR_TITLE_SHADOW = (34, 34, 34)
COLOR_TITLE = (175, 53, 42)
COLOR_WHITE = (255, 255, 255)
