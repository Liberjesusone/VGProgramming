"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains the class Arrow: what the bow's attack actually
spawns. Once PlayerAttackState creates one and hands it to
Level.projectiles, it lives entirely on its own, Level.update ticks it
every frame same as every other project on this course has ticked its
own projectiles, and it does not know or care that a player fired it; 
a future enemy's own ranged attack can reuse this exact class.
"""

from typing import Any

import pygame


class Arrow:
    def __init__(
        self,
        x: float,
        y: float,
        direction: pygame.Vector2,
        speed: float,
        damage: int,
        max_range: float,
    ) -> None:
        self.x = x
        self.y = y
        self.direction = direction
        self.speed = speed
        self.damage = damage
        self.max_range = max_range

        self.traveled = 0.0
        self.dead = False

    @property
    def sort_y(self) -> float:
        """ So an arrow depth-sorts against props and the player exactly
        like everything else standing in the scene, instead of always
        drawing on top of or under them regardless of where it actually
        is."""
        return self.y

    @property
    def position(self) -> pygame.Vector2:
        return pygame.Vector2(self.x, self.y)

    def update(self, dt: float) -> None:
        step: pygame.Vector2 = self.direction * self.speed * dt
        self.x += step.x
        self.y += step.y
        self.traveled += step.length()

        if self.traveled >= self.max_range:
            self.dead = True

    def render(self, surface: pygame.Surface, camera: Any) -> None:
        """ Placeholder: a short line along the direction of travel, in
        place of real arrow art. Anchored at the current position the
        same way everything else here is, so swapping in a sprite
        later only touches this method. """
        tail = self.position - self.direction * 10
        pygame.draw.line(
            surface,
            (222, 200, 150),
            camera.world_to_screen((tail.x, tail.y)),
            camera.world_to_screen((self.x, self.y)),
            2,
        )

    def render_debug(self, surface: pygame.Surface, camera: Any) -> None:
        """ Every drawable in Level.drawables() (Player, Prop, and this) is
        expected to answer to render_debug, PlayState._render_debug
        calls it on all of them without checking which kind each one
        is. A dot at the exact point Level.update tests for a hit,
        since render()'s own trailing line does not pin that down. """
        pygame.draw.circle(surface, (240, 80, 200), camera.world_to_screen((self.x, self.y)), 2)
