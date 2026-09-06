"""
ISPPV1 2023
Study Case: The Legend of the Princess (ARPG)

Author: Alejandro Mujica
alejandro.j.mujic4@gmail.com

This file contains the class Projectile.
"""

from typing import Any

import pygame

import settings

_SPEED = 150
_MAX_TILES = 4


class Projectile:
    def __init__(
        self,
        obj: Any,
        direction: str,
        speed: float = _SPEED,
        max_tiles: float = _MAX_TILES,
        damage: int = 1,
        owner: str = "player",
    ) -> None:
        self.obj = obj
        self.direction = direction
        self.distance = 0.0
        self.dead = False

        # Speed and range used to be the module constants above, fixed for
        # every projectile because the only one was a thrown pot. The
        # mage's fireball is slower but has to cross the whole room, so
        # both became per-projectile, with the pot's old values as the
        # defaults, every existing `Projectile(obj, direction)` call
        # keeps behaving exactly as it did.
        self.speed = speed
        self.max_tiles = max_tiles

        self.damage = damage

        # "player" (arrows, thrown pots) or "boss" (fireballs). Room.update
        # checks a projectile only against the *other* side, which is what
        # makes the fire mage immune to his own fire without a single
        # special case anywhere in the collision code.
        self.owner = owner

    def get_collision_rect(self) -> pygame.Rect:
        return self.obj.get_collision_rect()

    def update(self, dt: float) -> None:
        if self.dead:
            return

        d = self.speed * dt

        if self.direction == "up":
            self.obj.y -= d
            limit = settings.MAP_RENDER_OFFSET_Y + settings.TILE_SIZE - self.obj.height / 2
            if self.obj.y <= limit:
                self.obj.y = limit
                self.dead = True
        elif self.direction == "down":
            self.obj.y += d
            bottom_edge = (
                settings.MAP_HEIGHT * settings.TILE_SIZE
                + settings.MAP_RENDER_OFFSET_Y
                - settings.TILE_SIZE
            )
            if self.obj.y + self.obj.height >= bottom_edge:
                self.obj.y = bottom_edge - self.obj.height
                self.dead = True
        elif self.direction == "left":
            self.obj.x -= d
            limit = settings.MAP_RENDER_OFFSET_X + settings.TILE_SIZE
            if self.obj.x <= limit:
                self.obj.x = limit
                self.dead = True
        elif self.direction == "right":
            self.obj.x += d
            limit = settings.VIRTUAL_WIDTH - settings.TILE_SIZE * 2
            if self.obj.x + self.obj.width >= limit:
                self.obj.x = limit - self.obj.width
                self.dead = True

        if self.dead:
            settings.SOUNDS["pot-wall"].play()
            return

        self.distance += d

        if self.distance > self.max_tiles * settings.TILE_SIZE:
            self.dead = True

    def render(
        self, surface: pygame.Surface, offset_x: float = 0, offset_y: float = 0
    ) -> None:
        self.obj.render(surface, offset_x, offset_y)

    def collides(self, target: Any) -> bool:
        return self.get_collision_rect().colliderect(target.get_collision_rect())
