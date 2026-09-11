"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains the class LightSpirits, a gale.Game specialization.

The states are held in a StateStack rather than a StateMachine: a stack
draws everything it holds and updates only the top, which is what lets a
message or a menu sit over a frozen world instead of replacing it.
"""

import pygame

from gale.game import Game
from gale.input_handler import InputData
from gale.state import StateStack

from src.states.game.StartState import StartState


class LightSpirits(Game):
    def init(self) -> None:
        self.state_stack = StateStack()
        self.state_stack.push(StartState(self.state_stack))

    def update(self, dt: float) -> None:
        self.state_stack.update(dt)

    def render(self, surface: pygame.Surface) -> None:
        self.state_stack.render(surface)

    def on_input(self, input_id: str, input_data: InputData) -> None:
        if input_id == "quit" and input_data.pressed:
            self.quit()
        else:
            self.state_stack.on_input(input_id, input_data)
