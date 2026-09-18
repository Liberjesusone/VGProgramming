"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains the class BossShootState: the spirit drawing its bow
and loosing a single arrow, much faster and stronger than the player's.
While it draws, a red line shows where the arrow will fly, following the
player until the lock and thickening once it stops.
"""

from typing import Any

import pygame

from src.combat.visuals import ENEMY_TELEGRAPH_COLOR
from src.entity.HostileArrow import HostileArrow
from src.states.entity.boss.BossBaseState import BossBaseState


class BossShootState(BossBaseState):
    def enter(self) -> None:
        boss = self.boss
        self.bow = boss.definition["bow"]
        self.phase = "charge"
        self.charge = 0.0
        self.elapsed = 0.0
        self.locked = False
        self.aim = boss.aim_at_player(pygame.Vector2(0, 1))

        boss.vulnerable = True
        boss.pose = "charge1"
        boss.face(self.aim)

    def update(self, dt: float) -> None:
        boss = self.boss
        bow = self.bow

        if self.phase == "charge":
            self.charge = min(1.0, self.charge + dt / bow["charge_time"])

            if not self.locked:
                self.aim = boss.aim_at_player(self.aim)
                self.locked = self.charge >= bow["lock_fraction"]

            boss.pose = "charge1" if self.charge < 0.5 else "charge2"
            boss.face(self.aim)

            if self.charge >= 1.0:
                self._loose()
            return

        self.elapsed += dt

        if self.phase == "swing" and self.elapsed >= bow["swing"]:
            self.phase, self.elapsed = "recovery", 0.0
            boss.pose = "idle"
        elif self.phase == "recovery" and self.elapsed >= bow["recovery"]:
            boss.start_cooldown("bow", bow["cooldown"])
            boss.decide()

    def _loose(self) -> None:
        boss = self.boss
        bow = self.bow
        centre = boss.center

        boss.level.hazards.append(
            HostileArrow(
                centre.x, centre.y, pygame.Vector2(self.aim),
                bow["arrow_speed"], bow["damage"], bow["arrow_range"], bow["stun"],
            )
        )
        self.phase, self.elapsed = "swing", 0.0
        boss.pose = "attack"

    def render_telegraph(self, surface: pygame.Surface, camera: Any) -> None:
        if self.phase != "charge":
            return

        centre = self.boss.center
        tip = centre + self.aim * self.bow["range"]
        pygame.draw.line(
            surface,
            ENEMY_TELEGRAPH_COLOR,
            camera.world_to_screen((centre.x, centre.y)),
            camera.world_to_screen((tip.x, tip.y)),
            2 if self.locked else 1,
        )
