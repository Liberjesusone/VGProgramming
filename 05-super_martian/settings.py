"""
ISPPV1 2023
Study Case: Super Martian (Platformer)

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

input_handler.InputHandler.set_keyboard_action(input_handler.KEY_ESCAPE, "quit")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_p, "pause")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_RETURN, "enter")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_KP_ENTER, "enter")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_RIGHT, "move_right")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_d, "move_right")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_LEFT, "move_left")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_a, "move_left")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_SPACE, "jump")
input_handler.InputHandler.set_mouse_click_action(input_handler.MOUSE_BUTTON_1, "jump")

TITLE = "Super Martian"

# Size we want to emulate
VIRTUAL_WIDTH = 400
VIRTUAL_HEIGHT = 192

# Size of our actual window
WINDOW_WIDTH = VIRTUAL_WIDTH * 3 + 100
WINDOW_HEIGHT = VIRTUAL_HEIGHT * 3 + 100

PLAYER_SPEED = 80

GRAVITY = 980

# Variable-height jump: the takeoff speed is always the same (full arc if
# held), but releasing "jump" early while still ascending clamps vy up to
# JUMP_CUT_VELOCITY (a smaller upward speed), so the arc peaks sooner and
# lower. The longer the button stays held, the closer the jump gets to
# its full height.
JUMP_TAKEOFF_SPEED = GRAVITY / 3
JUMP_CUT_VELOCITY = GRAVITY / 8

CAMERA_FOLLOW_RATE = 8.0

# Random delay range (seconds) between one flying creature leaving the
# level and the next one spawning.
FLYING_CREATURE_MIN_SPAWN_DELAY = 4
FLYING_CREATURE_MAX_SPAWN_DELAY = 9

NUM_LEVELS = 2

BASE_DIR = pathlib.Path(__file__).parent

""" gid of the tile used for the magic box. Must be a tile whose
"collision" custom property is set to "solid", otherwise the player
would walk straight through it. gid 69 is one of the blank cells of
tileset.png, marked solid in level1.json for exactly this.
"""
MAGIC_BOX_GID = 69

""" Index into settings.FRAMES["tiles"] for the key sprite. NOT a gid:
 FRAMES is 0-based while tilemap gids start at firstgid (1 here), so
 this is the gid of the drawing minus one -- the key is drawn on gid
 70's cell. The key is a GameItem, not a tile, so it needs no
 collision property.
"""
KEY_FRAME_INDEX = 69

import math

# Iris-wipe transition between levels: the radius that fully uncovers the
# screen is the distance from its centre to a corner, so the circle has to
# grow past the diagonal's half to leave no black corners behind.
IRIS_MAX_RADIUS = math.hypot(VIRTUAL_WIDTH / 2, VIRTUAL_HEIGHT / 2)
IRIS_CLOSE_TIME = 0.6
IRIS_OPEN_TIME = 0.5

# Score the player must reach for the magic box to show up.
SCORE_TO_SPAWN_MAGIC_BOX = 200

TILEMAPS = {
    i: str(BASE_DIR / "assets" / "tilemaps" / f"level{i}.json")
    for i in range(1, NUM_LEVELS + 1)
}

TEXTURES = {
    "tiles": pygame.image.load(BASE_DIR / "assets" / "graphics" / "tileset.png"),
    "martian": pygame.image.load(BASE_DIR / "assets" / "graphics" / "martian.png"),
    "creatures": pygame.image.load(BASE_DIR / "assets" / "graphics" / "creatures.png"),
}

FRAMES = {
    "tiles": frames.generate_frames(TEXTURES["tiles"], 16, 16),
    "martian": frames.generate_frames(TEXTURES["martian"], 16, 20),
    "creatures": frames.generate_frames(TEXTURES["creatures"], 16, 16),
}

def _sound(filename: str, fallback: str = "pickup_coin.wav") -> pygame.mixer.Sound:
    """Load a sound, falling back to an existing one when the file is not
    there yet, so a missing asset does not stop the game from starting."""
    path = BASE_DIR / "assets" / "sounds" / filename

    if not path.exists():
        path = BASE_DIR / "assets" / "sounds" / fallback

    return pygame.mixer.Sound(path)


SOUNDS = {
    "pickup_coin": pygame.mixer.Sound(
        BASE_DIR / "assets" / "sounds" / "pickup_coin.wav"
    ),
    "jump": pygame.mixer.Sound(BASE_DIR / "assets" / "sounds" / "jump.wav"),
    "timer": pygame.mixer.Sound(BASE_DIR / "assets" / "sounds" / "timer.wav"),
    "count": pygame.mixer.Sound(BASE_DIR / "assets" / "sounds" / "count.wav"),
    # Drop the real files in assets/sounds/ and these pick them up on
    # their own; until then they fall back to pickup_coin.wav.
    "spawn_key": _sound("spawn_key.mp3"),
    "pickup_key": _sound("pickup_key.mp3"),
    "level_complete": _sound("level_complete.mp3"),
    "magic_box_appear": _sound("magic_box_appear.mp3"),
}

SOUNDS["pickup_coin"].set_volume(0.05)
SOUNDS["jump"].set_volume(0.05)

# Applied right after every pygame.mixer.music.play(), since the music
# channel is separate from the SOUNDS above and load()/unload() runs on
# each state change.
MUSIC_VOLUME = 0.15

FONTS = {
    "small": pygame.font.Font(BASE_DIR / "assets" / "fonts" / "font.ttf", 8),
    "medium": pygame.font.Font(BASE_DIR / "assets" / "fonts" / "font.ttf", 16),
}
