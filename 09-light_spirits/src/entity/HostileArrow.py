"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains the class HostileArrow: an arrow shot at the player
instead of by them, the spirit's. It flies exactly like the player's own
Arrow, but lives in Level.hazards and tests the player's body instead of
the enemies'. While the player is rolling it flies straight through them,
rather than being spent on a hit that did nothing.
"""

from typing import Any, Optional

import pygame

from src.entity.Arrow import Arrow

COLOR = (150, 235, 210)


class HostileArrow(Arrow):
    def __init__(
        self,
        x: float,
        y: float,
        direction: pygame.Vector2,
        speed: float,
        damage: int,
        max_range: float,
        stun: Optional[str] = None,
    ) -> None:
        super().__init__(x, y, direction, speed, damage, max_range)
        self.stun = stun

    def update(self, dt: float, player: Any) -> None:
        super().update(dt)

        if self.dead or player.invulnerable:
            return

        if player.image_rect.collidepoint(self.x, self.y):
            player.damage(self.damage, self.stun, self.position - self.direction * 20)
            self.dead = True

    def render(self, surface: pygame.Surface, camera: Any) -> None:
        tail = self.position - self.direction * 14
        pygame.draw.line(
            surface,
            COLOR,
            camera.world_to_screen((tail.x, tail.y)),
            camera.world_to_screen((self.x, self.y)),
            2,
        )

    def render_telegraph(self, surface: pygame.Surface, camera: Any) -> None:
        pass
