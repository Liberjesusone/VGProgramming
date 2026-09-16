"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains the class BossRainState: the spirit aiming high and
loosing a volley of arrows that fall all around the player.

While it charges, a wide faint circle follows the player, the zone about
to be covered. On release, every arrow picks its own landing point at
random inside that circle, around wherever the player stood at that
instant, and leaves a little after the previous ones, so they come down
as a rain rather than one single blow. Each one is an AreaShot, the same
lobbed arrow the witch fires, with its own red circle on the ground.
"""

import math
import random
from typing import Any

import pygame

from src.combat.visuals import ENEMY_TELEGRAPH_COLOR, draw_translucent_circle
from src.entity.AreaShot import AreaShot
from src.states.entity.boss.BossBaseState import BossBaseState


class BossRainState(BossBaseState):
    def enter(self) -> None:
        self.rain = self.boss.definition["rain"]
        self.phase = "charge"
        self.elapsed = 0.0

        self.boss.vulnerable = True
        self.boss.pose = "charge2"
        self.boss.face(self.boss.to_player())

    def update(self, dt: float) -> None:
        boss = self.boss
        rain = self.rain
        self.elapsed += dt

        if self.phase == "charge":
            boss.face(boss.to_player())

            if self.elapsed >= rain["charge_time"]:
                self._release()
        elif self.phase == "swing" and self.elapsed >= rain["swing"]:
            self.phase, self.elapsed = "recovery", 0.0
            boss.pose = "idle"
        elif self.phase == "recovery" and self.elapsed >= rain["recovery"]:
            boss.start_cooldown("rain", rain["cooldown"])
            boss.decide()

    def _release(self) -> None:
        boss = self.boss
        rain = self.rain
        player = boss._player
        centre = pygame.Vector2(player.x, player.y)

        for _ in range(rain["count"]):
            # sqrt spreads the points evenly over the disc instead of
            # crowding them toward its centre.
            distance = rain["radius"] * math.sqrt(random.random())
            angle = random.uniform(0, math.tau)
            target = centre + pygame.Vector2(math.cos(angle), math.sin(angle)) * distance

            boss.level.hazards.append(
                AreaShot(
                    pygame.Vector2(boss.x, boss.y),
                    boss.body_height * 0.7,
                    target,
                    rain["shot_radius"],
                    rain["damage"],
                    rain["stun"],
                    rain["shot_speed"],
                    delay=random.uniform(0.0, rain["spread"]),
                )
            )

        self.phase, self.elapsed = "swing", 0.0
        boss.pose = "attack"

    def render_telegraph(self, surface: pygame.Surface, camera: Any) -> None:
        if self.phase != "charge":
            return

        player = self.boss._player
        draw_translucent_circle(
            surface,
            ENEMY_TELEGRAPH_COLOR,
            25,
            camera.world_to_screen((player.x, player.y)),
            self.rain["radius"] * camera.zoom,
            1,
        )
