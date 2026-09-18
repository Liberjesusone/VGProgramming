"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains the class Decor: scenery that is drawn and depth sorted
exactly like a Prop, anchored on its feet, but never blocks anything.
Grass, flowers, rubble, bonfire seats.
"""

from typing import Any

import pygame


class Decor:
    def __init__(self, image: pygame.Surface, x: float, y: float) -> None:
        self.image = image

        # Ground contact point: bottom centre of the image, same as Prop.
        self.x = x
        self.y = y

    @property
    def sort_y(self) -> float:
        return self.y

    @property
    def image_rect(self) -> pygame.Rect:
        return pygame.Rect(
            round(self.x - self.image.get_width() / 2),
            round(self.y - self.image.get_height()),
            self.image.get_width(),
            self.image.get_height(),
        )

    def render(self, surface: pygame.Surface, camera: Any) -> None:
        surface.blit(self.image, camera.apply(self.image_rect))

    # ------------------------------------------------------------
    # Debug
    # ------------------------------------------------------------
    def render_debug(self, surface: pygame.Surface, camera: Any) -> None:
        pygame.draw.rect(surface, (120, 200, 120), camera.apply(self.image_rect), 1)
