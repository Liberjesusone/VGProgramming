"""
ISPPV1 2023
Study Case: Ultimate Fantasy (RPG)

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains the class Backdrop: the translucent black sheet the
party menu lays over the whole screen.
"""

from typing import Tuple

import pygame

from gale.ui.widget import Widget


class Backdrop(Widget):
    """
    A full screen rectangle of semi transparent black.

    gale.state.StateStack renders every state in the stack, bottom to
    top, and only updates the top one. So the overworld underneath keeps
    being drawn while it is frozen, and this widget is all it takes to
    dim it: the party menu goes on top of a picture of a paused town
    instead of hiding it.

    The surface is built once in the constructor rather than on every
    frame, since neither its size nor its colour ever change.
    """

    def __init__(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        color: Tuple[int, int, int] = (0, 0, 0),
        opacity: int = 190,
    ) -> None:
        super().__init__(x, y, width, height)
        self.sheet = pygame.Surface((int(width), int(height)), pygame.SRCALPHA)
        self.sheet.fill((color[0], color[1], color[2], opacity))

    def render(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return

        surface.blit(self.sheet, (int(self.x), int(self.y)))
