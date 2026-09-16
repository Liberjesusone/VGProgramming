"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains the class BossStrikeState: every melee attack of both
boss forms, from the samurai's slash and thrust to the spirit's bow swing.
Which one it is comes entirely from the strike definition it is entered
with (see src/definitions/bosses.py), so a new attack is a new entry
there, never a new state.

A strike runs in three phases: charge, where the telegraph fills in and
the aim follows the player until lock_fraction; swing, where the hit is
resolved once at the release and the boss lunges forward; and recovery,
standing still before the boss decides what comes next.
"""

from typing import Any

import pygame

from src import audio
from src.combat.cone import contains_point, polygon_points
from src.combat.visuals import ENEMY_TELEGRAPH_COLOR, draw_translucent_polygon
from src.states.entity.boss.BossBaseState import BossBaseState


class BossStrikeState(BossBaseState):
    def enter(self, name: str) -> None:
        boss = self.boss
        self.name = name
        self.strike = boss.definition["strikes"][name]

        self.phase = "charge"
        self.charge = 0.0
        self.elapsed = 0.0
        self.locked = False
        self.aim = boss.aim_at_player(pygame.Vector2(0, 1))

        boss.vulnerable = True
        boss.pose = self.strike["poses"][0]
        boss.face(self.aim)

    def update(self, dt: float) -> None:
        if self.phase == "charge":
            self._update_charge(dt)
        elif self.phase == "swing":
            self._update_swing(dt)
        else:
            self.elapsed += dt

            if self.elapsed >= self.strike["recovery"]:
                self.boss.on_strike_finished(self.name)

    def _update_charge(self, dt: float) -> None:
        boss = self.boss
        strike = self.strike
        self.charge = min(1.0, self.charge + dt / strike["charge_time"])

        if not self.locked:
            self.aim = boss.aim_at_player(self.aim)

            if self.charge >= strike["lock_fraction"]:
                self.locked = True
                self._cue()

        boss.pose = strike["poses"][0] if self.charge < 0.5 else strike["poses"][1]
        boss.face(self.aim)

        if self.charge >= 1.0:
            self._release()

    def _cue(self) -> None:
        cue = self.strike.get("cue")

        if cue is None:
            return

        audio.play(cue.get("sound"))

        if cue.get("shake"):
            self.boss.level.request_shake(*cue["shake"])

    def _release(self) -> None:
        boss = self.boss
        strike = self.strike
        player = boss._player

        self.phase = "swing"
        self.elapsed = 0.0
        boss.pose = strike["poses"][2]

        if contains_point(boss.center, self.aim, strike["half_angle"], strike["reach"], player.center):
            player.damage(strike["damage"], strike["stun"], boss.center)

        if strike.get("impact_shake"):
            boss.level.request_shake(*strike["impact_shake"])

    def _update_swing(self, dt: float) -> None:
        boss = self.boss
        strike = self.strike
        self.elapsed += dt

        # The lunge is spread over the whole swing instead of snapping forward.
        if strike["lunge"] > 0:
            step = self.aim * strike["lunge"] * dt / strike["swing"]
            boss.try_move(step.x, step.y)

        if self.elapsed >= strike["swing"]:
            self.phase = "recovery"
            self.elapsed = 0.0
            boss.pose = "idle"

    def render_telegraph(self, surface: pygame.Surface, camera: Any) -> None:
        if self.phase == "charge":
            alpha = int(30 + 70 * self.charge)
            outline = 2 if self.locked else 1
        elif self.phase == "swing":
            alpha, outline = 120, 2
        else:
            return

        points = [
            camera.world_to_screen((point.x, point.y))
            for point in polygon_points(
                self.boss.center, self.aim, self.strike["half_angle"], self.strike["reach"]
            )
        ]
        draw_translucent_polygon(surface, ENEMY_TELEGRAPH_COLOR, alpha, points, outline)
