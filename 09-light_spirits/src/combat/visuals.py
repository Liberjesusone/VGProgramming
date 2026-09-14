"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains the drawing helpers every attack telegraph and hit
reaction shares: translucent shapes on the ground, and the tinted copy
of a sprite shown for an instant after it takes damage.

pygame.draw ignores alpha when drawing straight onto the game surface,
so every translucent shape here is drawn onto its own small SRCALPHA
surface, just big enough to hold it, and blitted from there.
"""

from typing import Sequence, Tuple

import pygame

from src.definitions.combat import HIT_FLASH_COLOR

ENEMY_TELEGRAPH_COLOR = (205, 52, 48)


def draw_translucent_polygon(
    surface: pygame.Surface,
    color: Tuple[int, int, int],
    alpha: int,
    points: Sequence[Tuple[float, float]],
    outline_width: int = 1,
) -> None:
    # We get the top and left points from the list 
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    left, top = int(min(xs)), int(min(ys))
    width, height = int(max(xs)) - left + 2, int(max(ys)) - top + 2

    layer = pygame.Surface((width, height), pygame.SRCALPHA)
    
    # We rest the left/top points to all the rest, to turn them into local coords
    local = [(x - left, y - top) for x, y in points]
    pygame.draw.polygon(layer, (*color, alpha), local)
    surface.blit(layer, (left, top))

    pygame.draw.polygon(surface, color, points, outline_width)


def draw_translucent_circle(
    surface: pygame.Surface,
    color: Tuple[int, int, int],
    alpha: int,
    center: Tuple[float, float],
    radius: float,
    outline_width: int = 1,
) -> None:
    size = int(radius * 2) + 2
    layer = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(layer, (*color, alpha), (size // 2, size // 2), int(radius))
    surface.blit(layer, (int(center[0]) - size // 2, int(center[1]) - size // 2))

    pygame.draw.circle(surface, color, (int(center[0]), int(center[1])), int(radius), outline_width)


def flashed(sprite: pygame.Surface) -> pygame.Surface:
    """ A copy of sprite with HIT_FLASH_COLOR added to its colour but its
    alpha left untouched, so the tint follows the silhouette exactly. """
    tinted = sprite.copy()
    tinted.fill(HIT_FLASH_COLOR, special_flags=pygame.BLEND_RGB_ADD)
    return tinted
