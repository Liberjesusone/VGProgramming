"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains the class BossDashState: a short burst of speed in a
straight line, either toward the player (the samurai closing in by
surprise) or away (the spirit putting distance between them). The
direction is fixed when the dash starts, so a player who sidesteps after
it begins is not tracked.

It ends when it has covered its distance, when it runs into something,
or, dashing in, once it is close enough to strike; then the boss decides
what comes next, which is where a queued slash or combo hit follows.
"""

from typing import Any, Dict

import pygame

from src.states.entity.boss.BossBaseState import BossBaseState


class BossDashState(BossBaseState):
    def enter(self, dash: Dict[str, Any], toward: bool, windup: float = None) -> None:
        boss = self.boss
        self.dash = dash
        self.toward = toward
        self.windup = dash["windup"] if windup is None else windup

        aim = boss.aim_at_player(pygame.Vector2(0, 1))
        self.direction = aim if toward else -aim
        self.elapsed = 0.0
        self.traveled = 0.0

        boss.vulnerable = True
        boss.pose = dash["pose"]
        # Dashing away the boss still watches the player, it does not turn its back.
        boss.face(aim)

    def update(self, dt: float) -> None:
        boss = self.boss
        self.elapsed += dt

        if self.elapsed < self.windup:
            return

        step = self.direction * self.dash["speed"] * dt

        if not boss.try_move(step.x, step.y):
            boss.decide()
            return

        self.traveled += step.length()
        boss.add_trail()

        close_enough = self.toward and boss.to_player().length() <= self.dash["stop_distance"]

        if close_enough or self.traveled >= self.dash["distance"]:
            boss.decide()
