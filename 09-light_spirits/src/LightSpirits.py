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

from actions import QUIT
from src.states.game.StartState import StartState


class LightSpirits(Game):
    def __init__(self) -> None:
        """ Borderless, sized to the whole desktop (settings.WINDOW_WIDTH/
        HEIGHT), reads as fullscreen without pygame.FULLSCREEN's own
        display-mode switch, which flickers on the way in and is slow
        to restore on Alt+Tab back in. Since gale.Game already scales
        its own virtual surface onto whatever window exists, an actual
        exclusive-fullscreen mode buys nothing here. """
        super().__init__(flags=pygame.NOFRAME)

        """ Confines the mouse to the window while it has focus, so aiming
        near an edge can no longer slip a few pixels out and click
        whatever sits behind the game. SDL releases the grab on focus
        loss and reapplies it on refocus, so Alt+Tab still works to
        step out of the game. """
        pygame.event.set_grab(True)

    def init(self) -> None:
        self.state_stack = StateStack()
        self.state_stack.push(StartState(self.state_stack))

    def update(self, dt: float) -> None:
        self.state_stack.update(dt)

    def render(self, surface: pygame.Surface) -> None:
        self.state_stack.render(surface)

    def on_input(self, input_id: str, input_data: InputData) -> None:
        if input_id == QUIT and input_data.pressed:
            self.quit()
        else:
            self.state_stack.on_input(input_id, input_data)
