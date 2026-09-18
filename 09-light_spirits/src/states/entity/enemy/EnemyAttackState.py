"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains the class EnemyAttackState: resolves whatever
EnemyChargeState locked in, holds the attack pose for swing_duration,
then stands idle for recovery before chasing again.

A melee attack hits the player the instant this starts if they are still
inside the cone. An area attack instead spawns an AreaShot into
Level.hazards, which lands on its own after this state has moved on.
Player.damage already ignores anything that lands while the player is
rolling, so neither branch has to check for that.
"""

from typing import Any

import pygame

from src import audio
from src.combat.cone import contains_point, polygon_points
from src.combat.visuals import ENEMY_TELEGRAPH_COLOR, draw_translucent_polygon
from src.definitions.combat import lerp
from src.entity.AreaShot import AreaShot
from src.states.entity.enemy.EnemyBaseState import EnemyBaseState


class EnemyAttackState(EnemyBaseState):
    def enter(self, charge: float, aim: pygame.Vector2, target_point: pygame.Vector2) -> None:
        enemy = self.enemy
        attack = enemy.attack

        enemy.pose = "attack"
        enemy.face(aim)

        self.charge = charge
        self.aim = aim
        self.elapsed = 0.0

        audio.play(attack.get("sound"))

        if attack["kind"] == "melee":
            self._melee_strike(attack)
        else:
            self._area_shot(attack, target_point)

    def _melee_strike(self, attack: Any) -> None:
        enemy = self.enemy
        player = enemy._player

        self.half_angle = lerp(attack["min_half_angle"], attack["max_half_angle"], self.charge)
        self.reach = lerp(attack["min_reach"], attack["max_reach"], self.charge)
        damage = round(lerp(attack["min_damage"], attack["max_damage"], self.charge))

        if contains_point(enemy.center, self.aim, self.half_angle, 
                          self.reach, player.center):
            player.damage(damage, attack["stun"], enemy.center)

    def _area_shot(self, attack: Any, target_point: pygame.Vector2) -> None:
        enemy = self.enemy
        enemy.level.hazards.append(
            AreaShot(
                pygame.Vector2(enemy.x, enemy.y),
                enemy.body_height * 0.6,
                target_point,
                attack["radius"],
                attack["damage"],
                attack["stun"],
                attack["projectile_speed"],
                land_sound=attack.get("land_sound"),
            )
        )

    def update(self, dt: float) -> None:
        enemy = self.enemy
        attack = enemy.attack
        self.elapsed += dt

        if self.elapsed >= attack["swing_duration"]:
            enemy.pose = "idle"

        if self.elapsed >= attack["swing_duration"] + attack["recovery"]:
            enemy.change_state("chase")

    def render_telegraph(self, surface: pygame.Surface, camera: Any) -> None:
        """ The swing itself, solid for as long as the attack pose holds,
        so a hit or a near miss reads clearly after the fact. """
        enemy = self.enemy

        if enemy.attack["kind"] != "melee" or self.elapsed >= enemy.attack["swing_duration"]:
            return

        points = [
            camera.world_to_screen((point.x, point.y))
            for point in polygon_points(enemy.center, self.aim, self.half_angle, self.reach)
        ]
        draw_translucent_polygon(surface, ENEMY_TELEGRAPH_COLOR, 110, points, 2)
