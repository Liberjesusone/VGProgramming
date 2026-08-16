"""
ISPPV1 2023
Study Case: The Legend of the Princess (ARPG)

Author: Alejandro Mujica
alejandro.j.mujic4@gmail.com

This file contains the class PlayerIdleState.
"""

from typing import TypeVar

import pygame

from gale.input_handler import InputData
from gale.state import StateMachine

from src.states.entity.BaseEntityState import BaseEntityState


class PlayerIdleState(BaseEntityState):
    def __init__(
        self,
        player: TypeVar("Player"),
        state_machine: StateMachine,
        dungeon: TypeVar("Dungeon"),
    ) -> None:
        super().__init__(player, state_machine)
        self.dungeon = dungeon

    def enter(self) -> None:
        # Render offset for spaced character sprite.
        self.entity.offset_y = 5
        self.entity.offset_x = 0
        self.entity.change_animation(f"idle-{self.entity.direction}")

    def update(self, dt: float) -> None:
        held = self.entity.held

        if held["move_left"] or held["move_right"] or held["move_up"] or held["move_down"]:
            self.entity.change_state("walk")

    def on_input(self, input_id: str, input_data: InputData) -> None:
        if input_id == "sword" and input_data.pressed:
            self.entity.change_state("swing-sword")
        elif input_id == "enter" and input_data.pressed:
            self.dungeon.current_room.take_adjacent_pot(self.entity)

    def render(self, surface: pygame.Surface) -> None:
        anim = self.entity.current_animation
        self.entity.render_sprite(surface, anim.texture_id, anim.get_current_frame())
