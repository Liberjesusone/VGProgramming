"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains the class StartState: 
It just represents the title screen.
"""

from typing import Any

import numpy
import pygame

from gale.state import BaseState
from gale.text import render_text

from src.states.game.PlayState import PlayState

import settings
from actions import CONFIRM

""" How dark the vignette gets at the very corners (0 = no darkening,
255 = fully black), and how much of the image around the centre stays
untouched before the falloff starts, as a fraction of the distance to
the corner. """
VIGNETTE_MAX_ALPHA = 190
VIGNETTE_INNER_RADIUS = 0.35

""" A flat, low-alpha wash over the whole image, warm and slightly worn,
for the "aged ruins" look asked for, separate from the vignette
above, which only darkens the borders/corners. """
RUIN_TINT_COLOR = (150, 115, 40)
RUIN_TINT_ALPHA = 40


def _build_vignette(width: int, height: int) -> pygame.Surface:
    """ A black surface whose alpha grows from 0 at the centre to
    VIGNETTE_MAX_ALPHA at the corners, built once with numpy, this 
    only ever runs once per visit to the title screen. """
    ys, xs = numpy.mgrid[0:height, 0:width]
    nx = (xs - width / 2) / (width / 2)
    ny = (ys - height / 2) / (height / 2)
    distance = numpy.sqrt(nx**2 + ny**2)

    falloff = numpy.clip(
        (distance - VIGNETTE_INNER_RADIUS) / (1.0 - VIGNETTE_INNER_RADIUS), 0.0, 1.0
    )
    alpha = (falloff**1.6 * VIGNETTE_MAX_ALPHA).astype(numpy.uint8)

    vignette = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.surfarray.pixels_alpha(vignette)[:, :] = alpha.T
    return vignette


def _build_background() -> pygame.Surface:
    background = settings.TITLE_BACKGROUND.copy()

    tint = pygame.Surface(background.get_size(), pygame.SRCALPHA)
    tint.fill((*RUIN_TINT_COLOR, RUIN_TINT_ALPHA))
    background.blit(tint, (0, 0))

    background.blit(_build_vignette(*background.get_size()), (0, 0))
    return background


class StartState(BaseState):
    def enter(self) -> None:
        self.elapsed = 0.0
        # Built once per visit, not per frame, see _build_background.
        self._background = _build_background()

    def update(self, dt: float) -> None:
        self.elapsed += dt

    def on_input(self, input_id: str, input_data: Any) -> None:
        # Start the game itself
        if input_id == CONFIRM and input_data.pressed:
            self.state_machine.push(PlayState(self.state_machine))

    def render(self, surface: pygame.Surface) -> None:
        # If it's not the current state we avoid the rendering 
        if self.state_machine.states[-1] is not self:
          return
        
        surface.blit(self._background, (0, 0))

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
                "Link Your Spirit",
                settings.FONTS["medium"],
                settings.VIRTUAL_WIDTH // 2,
                settings.VIRTUAL_HEIGHT // 2 + 30,
                settings.COLOR_ACCENT,
                center=True,
            )
