"""
ISPPV1 2023
Study Case: The Legend of the Princess (ARPG)

Author: Alejandro Mujica
alejandro.j.mujic4@gmail.com

This file contains the class PlayerPotIdleState.
"""

from typing import Any, TypeVar

import pygame

from gale.input_handler import InputData
from gale.state import StateMachine

from src.Projectile import Projectile
from src.states.entity.BaseEntityState import BaseEntityState


class PlayerPotIdleState(BaseEntityState):
    def __init__(
        self,
        player: TypeVar("Player"),
        state_machine: StateMachine,
        dungeon: TypeVar("Dungeon"),
    ) -> None:
        super().__init__(player, state_machine)
        self.dungeon = dungeon
        self.entity.change_animation(f"pot-idle-{self.entity.direction}")

    def enter(self, pot: Any) -> None:
        self.pot = pot

    def update(self, dt: float) -> None:
        held = self.entity.held

        if held["move_left"] or held["move_right"] or held["move_up"] or held["move_down"]:
            self.entity.change_state("pot-walk", pot=self.pot)

    def on_input(self, input_id: str, input_data: InputData) -> None:
        if input_id == "enter" and input_data.pressed:
            self.dungeon.current_room.projectiles.append(
                Projectile(self.pot, self.entity.direction)
            )
            self.entity.change_state("idle")

    def render(self, surface: pygame.Surface) -> None:
        anim = self.entity.current_animation
        self.entity.render_sprite(surface, anim.texture_id, anim.get_current_frame())
        self.pot.render(surface)
