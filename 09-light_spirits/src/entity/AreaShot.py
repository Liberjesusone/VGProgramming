"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains the class AreaShot: the witch's arrow, lobbed at a
point on the ground rather than fired straight at the player. It flies
for a fixed time along a shallow arc, and only when it lands does it
check who is standing inside its circle, so the telegraph drawn on the
ground the whole time is an honest promise: step out of the red circle
before it lands and nothing happens.

It lives in Level.hazards, apart from the player's own arrows in
Level.projectiles, since it hurts the player and never an enemy.
"""

import math
from typing import Any

import pygame

from src.combat.visuals import ENEMY_TELEGRAPH_COLOR, draw_translucent_circle

# Peak height of the arc above the straight line to the target, in pixels.
ARC_HEIGHT = 40.0

# The shortest flight allowed, so a shot at point blank range still leaves
# a visible instant of warning instead of landing the same frame.
MIN_FLIGHT_TIME = 0.2


class AreaShot:
    def __init__(
        self,
        origin: pygame.Vector2,
        origin_height: float,
        target: pygame.Vector2,
        radius: float,
        damage: int,
        stun: str,
        speed: float,
    ) -> None:
        """ origin and target are both points on the ground; origin_height
        is how far above its own ground point the shot leaves from, so it
        visibly starts at the shooter's hands and ends in the dirt. """
        self.origin = pygame.Vector2(origin)
        self.origin_height = origin_height
        self.target = pygame.Vector2(target)
        self.radius = radius
        self.damage = damage
        self.stun = stun

        distance = (self.target - self.origin).length()
        self.flight_time = max(MIN_FLIGHT_TIME, distance / speed)
        self.elapsed = 0.0
        self.dead = False

    @property
    def progress(self) -> float:
        return min(1.0, self.elapsed / self.flight_time)

    @property
    def ground(self) -> pygame.Vector2:
        return self.origin.lerp(self.target, self.progress)

    @property
    def x(self) -> float:
        return self.ground.x

    @property
    def sort_y(self) -> float:
        return self.ground.y

    def _point_at(self, progress: float) -> pygame.Vector2:
        ground = self.origin.lerp(self.target, progress)
        height = self.origin_height * (1.0 - progress) + math.sin(math.pi * progress) * ARC_HEIGHT
        return pygame.Vector2(ground.x, ground.y - height)

    def update(self, dt: float, player: Any) -> None:
        self.elapsed += dt

        if self.elapsed < self.flight_time:
            return

        feet = pygame.Vector2(player.x, player.y)

        if (feet - self.target).length() <= self.radius:
            player.damage(self.damage, self.stun, self.target)

        self.dead = True

    def render(self, surface: pygame.Surface, camera: Any) -> None:
        head = self._point_at(self.progress)
        tail = self._point_at(progress=max(0.0, self.progress - 0.04))
        pygame.draw.line(
            surface,
            (232, 120, 90),
            camera.world_to_screen((tail.x, tail.y)),
            camera.world_to_screen((head.x, head.y)),
            2,
        )

    def render_telegraph(self, surface: pygame.Surface, camera: Any) -> None:
        """ The circle fills in as the shot closes in, the closer to landing
        the more solid it reads. """
        alpha = int(40 + 90 * self.progress)
        draw_translucent_circle(
            surface,
            ENEMY_TELEGRAPH_COLOR,
            alpha,
            camera.world_to_screen((self.target.x, self.target.y)),
            self.radius * camera.zoom,
            2,
        )

    # ------------------------------------------------------------
    # Debug
    # ------------------------------------------------------------
    def render_debug(self, surface: pygame.Surface, camera: Any) -> None:
        head = self._point_at(self.progress)
        pygame.draw.circle(surface, (240, 80, 200), camera.world_to_screen((head.x, head.y)), 2)
