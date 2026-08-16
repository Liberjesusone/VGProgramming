"""
ISPPV1 2023
Study Case: Super Martian (Platformer)

Author: Alejandro Mujica
alejandro.j.mujic4@gmail.com

This file contains the class FallState for player.
"""

from gale.input_handler import InputData

import settings
from src.states.entities.BaseEntityState import BaseEntityState


class FallState(BaseEntityState):
    def enter(self) -> None:
        self.entity.change_animation("jump")

    def update(self, dt: float) -> None:
        if self.entity.on_ground:
            if self.entity.vx > 0:
                self.entity.change_state("walk", "right")
            elif self.entity.vx < 0:
                self.entity.change_state("walk", "left")
            else:
                self.entity.change_state("idle")

    def on_input(self, input_id: str, input_data: InputData) -> None:
        if input_id == "move_left":
            if input_data.pressed:
                self.entity.vx = -settings.PLAYER_SPEED
                self.entity.flipped = True
            elif input_data.released and self.entity.vx <= 0:
                self.entity.vx = 0

        elif input_id == "move_right":
            if input_data.pressed:
                self.entity.vx = settings.PLAYER_SPEED
                self.entity.flipped = False
            elif input_data.released and self.entity.vx >= 0:
                self.entity.vx = 0
