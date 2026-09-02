"""
ISPPV1 2023
Study Case: Flappy Bird

Author: Alejandro Mujica
alejandro.j.mujic4@gmail.com

This file contains the game settings that include the association of the
inputs with an their ids, constants of values to set up the game, sounds,
textures, and fonts.
"""

from pathlib import Path

import pygame

from gale import input_handler

input_handler.InputHandler.set_keyboard_action(input_handler.KEY_ESCAPE, "quit")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_RETURN, "confirm")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_SPACE, "jump")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_p, "pause")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_h, "hard_mode")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_BACKSPACE, "return_home")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_RIGHT, "move_right")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_LEFT, "move_left")

TITLE = "Flappy Bird"

# Size of our actual window
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720

# Size we are trying to emulate
VIRTUAL_WIDTH = 512
VIRTUAL_HEIGHT = 288

BIRD_WIDTH = 39
BIRD_HEIGHT = 28
BIRD_X_SPEED = BIRD_HEIGHT * 3

LOG_WIDTH = 70
LOG_HEIGHT = 288
LOGS_GAP = 90
LOGS_CLOSING_SPEED = 20
LOGS_MIN_GAP = BIRD_HEIGHT * 2.5
LOGS_MAX_GAP = VIRTUAL_HEIGHT - 60

GROUND_HEIGHT = 16

# Vertical range a log pair's top-log y may take (see World.update). The
# lower bound keeps a sliver of the top log's edge on screen; the upper
# bound keeps the full LOGS_GAP opening above the ground -- without it, a
# pair could spawn so low the top log's bottom edge sits at or past the
# ground, leaving no passable opening at all.
MIN_LOG_Y = -LOG_HEIGHT + 10
MAX_LOG_Y = VIRTUAL_HEIGHT - GROUND_HEIGHT - LOGS_GAP - LOG_HEIGHT

BACKGROUND_LOOPING_POINT = 1157

MAIN_SCROLL_SPEED = 100
BACK_SCROLL_SPEED = 50  # MAIN_SCROLL_SPEED / 2

GRAVITY = 980
JUMP_TAKEOFF_SPEED = GRAVITY / 6

TIME_TO_SPAWN_LOGS = 1.5

MEDIUM_TEXT_SIZE = 18
HUGE_TEXT_SIZE = 56
FLAPPY_TEXT_SIZE = 28

POWER_UP_WIDTH = 35
POWER_UP_HEIGHT = 35
POWER_UP_SPEED = 70
POWER_UP_SPAWN_TIME = 8

BASE_DIR = Path(__file__).parent

TEXTURES = {
    "bird": pygame.image.load(BASE_DIR / "assets" / "graphics" / "bird.png"),
    "ghost": pygame.image.load(BASE_DIR / "assets" / "graphics" / "ghost.png"),
    "power_up": pygame.transform.scale(
      pygame.image.load(BASE_DIR / "assets" / "graphics" / "power_up.png"),
      (POWER_UP_WIDTH, POWER_UP_HEIGHT)),
    "background": pygame.image.load(BASE_DIR / "assets" / "graphics" / "background.png"),
    "ground": pygame.image.load(BASE_DIR / "assets" / "graphics" / "ground.png"),
    "log": pygame.image.load(BASE_DIR / "assets" / "graphics" / "log.png"),
}
# The top log of every pair is the same image, flipped upside down.
TEXTURES["log_inverted"] = pygame.transform.flip(TEXTURES["log"], False, True)

SOUNDS = {
    "jump": pygame.mixer.Sound(BASE_DIR / "assets" / "sounds" / "jump.wav"),
    "explosion": pygame.mixer.Sound(BASE_DIR / "assets" / "sounds" / "explosion.wav"),
    "hurt": pygame.mixer.Sound(BASE_DIR / "assets" / "sounds" / "hurt.wav"),
    "score": pygame.mixer.Sound(BASE_DIR / "assets" / "sounds" / "score.wav"),
    "punch": pygame.mixer.Sound(BASE_DIR / "assets" / "sounds" / "punch.mp3"),
}

NORMAL_MUSIC = BASE_DIR / "assets" / "sounds" / "marios_way.wav" 
GHOST_MUSIC = BASE_DIR / "assets" / "sounds" / "ghost.wav" 

pygame.mixer.music.load(NORMAL_MUSIC)

FONTS = {
    "medium": pygame.font.Font(BASE_DIR / "assets" / "fonts" / "font.ttf", MEDIUM_TEXT_SIZE),
    "huge": pygame.font.Font(BASE_DIR / "assets" / "fonts" / "font.ttf", HUGE_TEXT_SIZE),
    "flappy": pygame.font.Font(
        BASE_DIR / "assets" / "fonts" / "flappy.ttf", FLAPPY_TEXT_SIZE
    ),
}

COLOR_BACKGROUND = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
