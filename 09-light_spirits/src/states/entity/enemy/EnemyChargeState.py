"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains the class EnemyChargeState: winds up the enemy's
single attack, drawing the red telegraph of what it is about to do, and
hands over to EnemyAttackState the instant the charge reaches its target.

The target is rolled fresh every time a charge starts, from the attack's
own target_charge range. An enemy with a narrow range always lets go at
the same moment; one with a wide range (the zombie) might swing almost
immediately or hold on until fully charged, and the only warning is the
telegraph itself.

The aim follows the player while the charge is young and freezes once it
reaches lock_at. That frozen moment is the player's cue: the telegraph
stops moving and gets a thicker outline, the attack is committed and can
be walked out of or rolled through. lock_at never comes later than 80%
of the rolled target, so even the earliest possible release shows a
brief locked instant first.
"""

import random
from typing import Any

import pygame

from src.combat.cone import polygon_points
from src.combat.visuals import (
    ENEMY_TELEGRAPH_COLOR,
    draw_translucent_circle,
    draw_translucent_polygon,
)
from src.definitions.combat import CHARGE_SPEED_FACTORS, lerp
from src.states.entity.enemy.EnemyBaseState import EnemyBaseState

# Fraction of engage_range the enemy stops advancing at while charging,
# so it closes a little distance without walking straight into the player.
ADVANCE_STOP_FRACTION = 0.5


class EnemyChargeState(EnemyBaseState):
    def enter(self) -> None:
        attack = self.enemy.attack

        self.charge = 0.0
        self.target = random.uniform(*attack["target_charge"])
        self.lock_at = min(attack["charge1_fraction"], 0.8 * self.target)

        self.aim = pygame.Vector2(0, 1)
        self.target_point = pygame.Vector2(self.enemy._player.x, self.enemy._player.y)
        self._track()

    @property
    def locked(self) -> bool:
        return self.charge >= self.lock_at

    def _track(self) -> None:
        to_player = self.enemy.to_player()

        if to_player.length_squared() > 1:
            self.aim = to_player.normalize()

        self.target_point = pygame.Vector2(self.enemy._player.x, self.enemy._player.y)

    def update(self, dt: float) -> None:
        enemy = self.enemy
        attack = enemy.attack

        self.charge = min(self.target, self.charge + dt / attack["charge_time"])

        if not self.locked:
            self._track()

        enemy.pose = "charge2" if self.charge >= attack["charge1_fraction"] else "charge1"
        enemy.face(self.aim)

        to_player = enemy.to_player()

        if attack["advance_while_charging"] and to_player.length() > attack["engage_range"] * ADVANCE_STOP_FRACTION:
            speed = enemy.definition["speed"] * CHARGE_SPEED_FACTORS[enemy.pose]
            enemy.move_towards(to_player, speed, dt)

        if self.charge >= self.target:
            enemy.change_state("attack", self.charge, self.aim, self.target_point)

    def render_telegraph(self, surface: pygame.Surface, camera: Any) -> None:
        enemy = self.enemy
        attack = enemy.attack
        outline = 2 if self.locked else 1

        if attack["kind"] == "melee":
            half_angle = lerp(attack["min_half_angle"], attack["max_half_angle"], self.charge)
            reach = lerp(attack["min_reach"], attack["max_reach"], self.charge)
            points = [
                camera.world_to_screen((point.x, point.y))
                for point in polygon_points(enemy.center, self.aim, half_angle, reach)
            ]
            draw_translucent_polygon(surface, ENEMY_TELEGRAPH_COLOR, 45, points, outline)
        else:
            draw_translucent_circle(
                surface,
                ENEMY_TELEGRAPH_COLOR,
                35,
                camera.world_to_screen((self.target_point.x, self.target_point.y)),
                attack["radius"] * camera.zoom,
                outline,
            )
