"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains the class PlayerAttackState: whatever the equipped
weapon's charge turns into once the button is released.

How hard a swing hits, or how fast an arrow flies, is decided the
instant this starts, out of however long the button was held, charging
again mid-attack is not possible, the same way a real swing can't be
redirected once it is thrown or a loosed arrow called back. The two
weapon kinds (see src/definitions/weapons.py) part ways only in what the
attack actually resolves as: a melee swing tests a cone against whatever
is standing in it right now, a ranged shot spawns an Arrow that lives on
in Level.projectiles long after this state itself has already returned
to idle.
"""

from typing import Any, Set

import pygame
import settings

from src.combat.cone import contains_point, polygon_points
from src.definitions.combat import lerp
from src.states.entity.player.PlayerBaseState import PlayerBaseState

MELEE_STAMINA_HIGH_COST = 2
MELEE_STAMINA_COST = 1.3
BOW_STAMINA_HIGH_COST = 3
BOW_STAMINA_COST = 2


class PlayerAttackState(PlayerBaseState):
    def enter(self) -> None:
        player = self.player
        weapon = player.weapon_def
        charge = player.charge

        player.direction = player._aim_bucket()
        player.pose = "attack"

        # Spent: the next charge only starts once back in idle/walk.
        player.charge = 0.0
        player.attack_held = False
        self.time_in_charge1_percent = weapon["charge1_time"] / weapon["charge_time"]

        self.elapsed = 0.0
        self.duration = weapon["swing_duration"]

        if weapon["kind"] == "melee":
            self._melee_strike(weapon, charge)
        else:
            self._ranged_shot(weapon, charge)

    def _melee_strike(self, weapon: Any, charge: float) -> None:
        # We aproximate one frame more the hit with the last charge and get the aporximate damage
        self.half_angle = lerp(weapon["min_half_angle"], weapon["max_half_angle"], charge)
        self.range = lerp(weapon["min_reach"], weapon["max_reach"], charge)
        self.damage = round(lerp(weapon["min_damage"], weapon["max_damage"], charge))

        player = self.player
        origin = player.center
        already_hit: Set[Any] = set()

        # Stamina waste
        player.current_stamina -= MELEE_STAMINA_COST if charge < self.time_in_charge1_percent  else MELEE_STAMINA_HIGH_COST

        """ Currently a loop over an empty sequence, Level has no
        entities to hit until enemies exist, a later milestone. Written
        the way it will actually run once that list is real, rather
        than bolted on afterwards. """
        for entity in getattr(player.level, "entities", []):
            if entity in already_hit:
                continue

            target = pygame.Vector2(entity.x, entity.y)

            if contains_point(origin, player.aim_direction,
                              self.half_angle, 
                              self.range, target):
                already_hit.add(entity)
                entity.damage(self.damage)

    def _ranged_shot(self, weapon: Any, charge: float) -> None:
        from src.entity.Arrow import Arrow

        player = self.player
        speed = lerp(weapon["min_speed"], weapon["max_speed"], charge)
        range = lerp(weapon["min_range"], weapon["max_range"], charge)
        damage = round(lerp(weapon["min_damage"], weapon["max_damage"], charge))

        # Stamina waste
        player.current_stamina -= BOW_STAMINA_COST if charge < self.time_in_charge1_percent  else BOW_STAMINA_HIGH_COST
        
        arrow = Arrow(
            player.center.x,
            player.center.y,
            player.aim_direction,
            speed,
            damage,
            range,
        )
        player.level.projectiles.append(arrow)

    def update(self, dt: float) -> None:
        self.elapsed += dt

        if self.elapsed >= self.duration:
            self.player.change_state("idle")

    def render_hit(self, surface: pygame.Surface, camera: Any) -> None:
        """ Renders the same hit but a bit thicker to seem that is has 
        made damage. Only the melee branch leaves anything worth drawing
        after the fact, a ranged shot's own Arrow already renders itself, 
        flying across the room long after this state has moved on. """
        if not hasattr(self, "half_angle"):
            return

        points = [
            camera.world_to_screen((point.x, point.y))
            for point in polygon_points(
                self.player.center, self.player.aim_direction, self.half_angle, self.range
            )
        ]
        pygame.draw.polygon(surface, settings.ATTACK_HITBOX_COLOR, points, 2)
