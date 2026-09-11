"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains the class GameOverState.

It is pushed on top of PlayState rather than replacing it, so the world
stays on screen, frozen, underneath the message. gale.state.StateStack
draws every state it holds but only updates the top one, so freezing the
game is what pushing a state already does.
"""

from typing import Any

import pygame

from gale.state import BaseState
from gale.text import render_text

import settings


class GameOverState(BaseState):
    def enter(self) -> None:
        self.veil = pygame.Surface(
            (settings.VIRTUAL_WIDTH, settings.VIRTUAL_HEIGHT), pygame.SRCALPHA
        )
        self.veil.fill((0, 0, 0, 170))

    def on_input(self, input_id: str, input_data: Any) -> None:
        if input_id == "confirm" and input_data.pressed:
            # Pops this state and the run underneath it, leaving the
            # title screen that was there before them.
            self.state_machine.pop()
            self.state_machine.pop()

    def render(self, surface: pygame.Surface) -> None:
        surface.blit(self.veil, (0, 0))

        render_text(
            surface,
            "Spirit Corrupted",
            settings.FONTS["large"],
            settings.VIRTUAL_WIDTH // 2,
            settings.VIRTUAL_HEIGHT // 2 - 40,
            (188, 66, 60),
            center=True,
        )
        render_text(
            surface,
            "Press enter to start again",
            settings.FONTS["medium"],
            settings.VIRTUAL_WIDTH // 2,
            settings.VIRTUAL_HEIGHT // 2 + 24,
            settings.COLOR_DIM,
            center=True,
        )
