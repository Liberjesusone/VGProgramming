"""
ISPPV1 2023
Study Case: Match-3

Author: Alejandro Mujica
alejandro.j.mujic4@gmail.com

This file contains the class Tile.
"""

import math
from typing import Optional

import pygame

import settings


def _star_points(cx: float, cy: float, outer_r: float, inner_r: float) -> list:
    """10 points alternating outer/inner radius, giving a 5-pointed star
    centered on (cx, cy), first point straight up."""
    points = []
    for k in range(10):
        angle = math.pi / 2 + k * math.pi / 5
        r = outer_r if k % 2 == 0 else inner_r
        points.append((cx + r * math.cos(angle), cy - r * math.sin(angle)))
    return points


class Tile:
    def __init__(self, i: int, j: int, color: int, variety: int) -> None:
        self.i = i
        self.j = j
        self.x = self.j * settings.TILE_SIZE
        self.y = self.i * settings.TILE_SIZE
        self.color = color
        self.variety = variety

        # Set to 4 or 5 when this tile is a power-up (born from a match of
        # that size). None for a regular tile.
        self.combo_level: Optional[int] = None

        self.alpha_surface = pygame.Surface(
            (settings.TILE_SIZE, settings.TILE_SIZE), pygame.SRCALPHA
        )

    def render(self, surface: pygame.Surface, offset_x: int, offset_y: int) -> None:
        self.alpha_surface.blit(
            settings.TEXTURES["tiles"],
            (0, 0),
            settings.FRAMES["tiles"][self.color][self.variety],
        )
        pygame.draw.rect(
            self.alpha_surface,
            (34, 32, 52, 200),
            pygame.Rect(0, 0, settings.TILE_SIZE, settings.TILE_SIZE),
            border_radius=7,
        )
        surface.blit(self.alpha_surface, (self.x + 2 + offset_x, self.y + 2 + offset_y))
        surface.blit(
            settings.TEXTURES["tiles"],
            (self.x + offset_x, self.y + offset_y),
            settings.FRAMES["tiles"][self.color][self.variety],
        )

        if self.combo_level is not None:
            cx = self.x + offset_x + settings.TILE_SIZE / 2
            cy = self.y + offset_y + settings.TILE_SIZE / 2
            outer_r = settings.TILE_SIZE * 0.4
            inner_r = outer_r * 0.45
            points = _star_points(cx, cy, outer_r, inner_r)
            pygame.draw.polygon(surface, (255, 215, 0), points)
            pygame.draw.polygon(surface, (120, 80, 0), points, width=1)
