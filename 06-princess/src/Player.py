"""
ISPPV1 2023
Study Case: The Legend of the Princess (ARPG)

Author: Alejandro Mujica
alejandro.j.mujic4@gmail.com

This file contains the class Player.
"""

from typing import Any

import pygame

from gale.command import CommandBindings
from gale.input_handler import InputData

import settings
from src.commands import (
    FIRE,
    INTERACT,
    MOVE_DOWN,
    MOVE_LEFT,
    MOVE_RIGHT,
    MOVE_UP,
    STOP_MOVE_DOWN,
    STOP_MOVE_LEFT,
    STOP_MOVE_RIGHT,
    STOP_MOVE_UP,
    SWORD,
)
from src.Entity import Entity

# Bow sprite per facing direction ("tiles" texture, 1-based frame numbers,
# see settings.frame). No "up" entry on purpose: the bow is drawn behind the
# player's back when facing away from the camera, so nothing renders there.
_BOW_FRAMES = {"right": 209, "left": 228, "down": 247}

# Pixel offset from the player's own x/y (top-left of a 16x22 hitbox) to
# where the bow is drawn. Placeholders, retune once the bow/arrow art
# in _BOW_FRAMES/definitions/game_objects.py's "arrow" entry is actually
# drawn (right now those tiles are blank).
_BOW_OFFSETS = {"right": (12, 2), "left": (-12, 2), "down": (0, 12)}


class Player(Entity):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        """ Edge-triggered intent: sword/take are one-shot actions resolved
        (and cleared) by whichever player state's update() consumes them,
        the same way jump_requested works in 05-super_martian.
        """
        self.sword_requested = False
        self.interact_requested = False
        self.fire_requested = False

        # Set once by Room.take_adjacent_pot when the chest is opened.
        self.has_bow = False

        self.command_bindings = CommandBindings()
        self.command_bindings.bind("move_left", press=MOVE_LEFT, release=STOP_MOVE_LEFT)
        self.command_bindings.bind(
            "move_right", press=MOVE_RIGHT, release=STOP_MOVE_RIGHT
        )
        self.command_bindings.bind("move_up", press=MOVE_UP, release=STOP_MOVE_UP)
        self.command_bindings.bind("move_down", press=MOVE_DOWN, release=STOP_MOVE_DOWN)
        self.command_bindings.bind("sword", press=SWORD)
        self.command_bindings.bind("enter", press=INTERACT)
        self.command_bindings.bind("fire", press=FIRE)

    def collides(self, target: Any) -> bool:
        """ AABB with some slight shrinkage of the box on the top side, for
        perspective (so walking "into" the top edge of an obstacle from
        below doesn't collide until the player's feet actually reach it).
        """
        self_y = self.y + self.height / 2
        self_height = self.height - self.height / 2

        return not (
            self.x + self.width < target.x
            or self.x > target.x + target.width
            or self_y + self_height < target.y
            or self_y > target.y + target.height
        )

    def on_input(self, input_id: str, input_data: InputData) -> None:
        self.command_bindings.dispatch(self, input_id, input_data)

    def render(
        self,
        surface: pygame.Surface,
        adjacent_offset_x: float = 0,
        adjacent_offset_y: float = 0,
    ) -> None:
        # We render normally
        super().render(surface, adjacent_offset_x, adjacent_offset_y)

        # And then we render the bow over the player
        if not self.has_bow or self.direction not in _BOW_FRAMES:
            return

        # Anchored to the hitbox (x/y/width), not self.offset_x/offset_y,
        # those change per sub-state (idle/walk/sword-swing each pick their
        # own padding for the *character* sprite), which would make the
        # bow jump around instead of sitting still relative to the player.
        dx, dy = _BOW_OFFSETS[self.direction]
        texture = settings.TEXTURES["tiles"]
        frame = settings.frame("tiles", _BOW_FRAMES[self.direction])
        image = pygame.Surface((frame.width, frame.height), pygame.SRCALPHA)
        image.blit(texture, (0, 0), frame)
        surface.blit(
            image,
            (
                round(self.x + dx + adjacent_offset_x),
                round(self.y + dy + adjacent_offset_y),
            ),
        )
