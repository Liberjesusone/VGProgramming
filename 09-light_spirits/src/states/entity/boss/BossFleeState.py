"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains the class BossFleeState: the spirit running away for a
few seconds when it cannot dash back, because a wall, a prop or the edge
of the map is right behind it.

It picks a direction roughly away from the player that is free for a
short stretch, runs that way, and picks again every repick seconds or as
soon as it bumps into something, so it zigzags off instead of pinning
itself against the obstacle it was fleeing from.
"""

import random

import pygame

from src.states.entity.boss.BossBaseState import BossBaseState

""" How far ahead a candidate direction must be free, checked every
PROBE_STEP pixels along the way, and how many random candidates to try.
Far enough that, cornered against an edge, running further into it is
rejected and the spirit runs along the edge instead. """
PROBE_DISTANCE = 96.0
PROBE_STEP = 16.0
PROBE_TRIES = 16

# The widest angle, in degrees, a direction may turn from straight away from the player.
MAX_TURN = 110.0


class BossFleeState(BossBaseState):
    def enter(self) -> None:
        self.flee = self.boss.definition["flee"]
        self.elapsed = 0.0
        self.boss.vulnerable = True
        self._pick_direction()

    def _pick_direction(self) -> None:
        boss = self.boss
        away = -boss.aim_at_player(pygame.Vector2(0, 1))
        self.repick_timer = self.flee["repick"]

        for _ in range(PROBE_TRIES):
            candidate = away.rotate(random.uniform(-MAX_TURN, MAX_TURN))

            if self._clear(candidate):
                self.direction = candidate
                return

        self.direction = away.rotate(random.uniform(-180.0, 180.0))

    def _clear(self, direction: pygame.Vector2) -> bool:
        boss = self.boss
        travelled = PROBE_STEP

        while travelled <= PROBE_DISTANCE:
            point = pygame.Vector2(boss.x, boss.y) + direction * travelled

            if boss.level.blocked(boss.feet_rect_at(point.x, point.y)):
                return False

            travelled += PROBE_STEP

        return True

    def update(self, dt: float) -> None:
        boss = self.boss
        self.elapsed += dt
        self.repick_timer -= dt

        if not boss.move_towards(self.direction, self.flee["speed"], dt) or self.repick_timer <= 0:
            self._pick_direction()

        boss.face(self.direction)
        boss.walk_pose(dt)

        if self.elapsed >= self.flee["duration"]:
            boss.decide()
