"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains the class StartState: 
It just represents the title screen.
"""

from typing import Any

import pygame

from gale.state import BaseState
from gale.text import render_text

from src.states.game.PlayState import PlayState

import settings


class StartState(BaseState):
    def enter(self) -> None:
        self.elapsed = 0.0

    def update(self, dt: float) -> None:
        self.elapsed += dt

    def on_input(self, input_id: str, input_data: Any) -> None:
        # Start the game itself
        if input_id == "confirm" and input_data.pressed:
            self.state_machine.push(PlayState(self.state_machine))

    def render(self, surface: pygame.Surface) -> None:
        # If it's not the current state we avoid the rendering 
        if self.state_machine.states[-1] is not self:
          return
        
        surface.fill(settings.COLOR_BACKGROUND)

        # The Title
        render_text(
            surface,
            settings.TITLE.upper(),
            settings.FONTS["large"],
            settings.VIRTUAL_WIDTH // 2,
            settings.VIRTUAL_HEIGHT // 2 - 50,
            settings.COLOR_TEXT,
            center=True,
        )

        # A slow blink, so the prompt reads as waiting rather than as a static label.
        if self.elapsed % 1.4 < 0.9:
            render_text(
                surface,
                "Link Soul",
                settings.FONTS["medium"],
                settings.VIRTUAL_WIDTH // 2,
                settings.VIRTUAL_HEIGHT // 2 + 30,
                settings.COLOR_ACCENT,
                center=True,
            )
