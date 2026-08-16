"""
ISPPV1 2023
Study Case: The Legend of the Princess (ARPG)

Author: Alejandro Mujica
alejandro.j.mujic4@gmail.com

This file contains the class EntityWalkState.
"""

import random
from typing import TypeVar

import pygame

from src.states.entity.BaseEntityState import BaseEntityState
from src.states.entity.movement import move_and_bump

_DIRECTIONS = ["left", "right", "up", "down"]


class EntityWalkState(BaseEntityState):
    def enter(self) -> None:
        self.entity.change_animation("walk-down")

        # Used for AI control.
        self.move_duration = 0
        self.movement_timer = 0

        # Keeps track of whether we just hit a wall.
        self.bumped = False

    def update(self, dt: float) -> None:
        self.bumped = move_and_bump(self.entity, dt)

    def process_ai(self, room: TypeVar("Room"), dt: float) -> None:
        if self.move_duration == 0 or self.bumped:
            self.move_duration = random.randint(1, 5)
            self.entity.direction = random.choice(_DIRECTIONS)
            self.entity.change_animation(f"walk-{self.entity.direction}")
        elif self.movement_timer > self.move_duration:
            self.movement_timer = 0

            # Chance to go idle.
            if random.randint(1, 3) == 1:
                self.entity.change_state("idle")
                return

            self.move_duration = random.randint(1, 5)
            self.entity.direction = random.choice(_DIRECTIONS)
            self.entity.change_animation(f"walk-{self.entity.direction}")

        self.movement_timer += dt

    def render(self, surface: pygame.Surface) -> None:
        anim = self.entity.current_animation
        self.entity.render_sprite(surface, anim.texture_id, anim.get_current_frame())
