"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains the class BossRepositionState: how the spirit chooses
its next move, always trying to keep the player at bow range.

In order of priority: if the player got close enough to strike, it swings
its bow; if the arrow rain is ready, it casts it; if a shot is ready, it
fires. Otherwise it moves: backing away from a player inside keep_min,
walking closer to one beyond keep_max, and drifting sideways in between,
flipping that drift every so often, or at once when it bumps into
something, so it never stands still as an easy target.
"""

import random

import pygame

from src.states.entity.boss.BossBaseState import BossBaseState


class BossRepositionState(BossBaseState):
    def enter(self) -> None:
        self.boss.vulnerable = True
        self.strafe_sign = random.choice((-1, 1))
        self.flip_timer = random.uniform(*self.boss.definition["strafe_flip"])

    def update(self, dt: float) -> None:
        boss = self.boss
        definition = boss.definition
        to_player = boss.to_player()
        distance = to_player.length()

        if distance <= definition["melee_trigger"] and boss.ready("melee"):
            boss.act("melee")
            return

        if boss.ready("rain") and distance <= definition["bow"]["range"]:
            boss.act("rain")
            return

        if boss.ready("bow") and distance <= definition["bow"]["range"]:
            boss.act("shoot")
            return

        self.flip_timer -= dt

        if self.flip_timer <= 0:
            self.strafe_sign *= -1
            self.flip_timer = random.uniform(*definition["strafe_flip"])

        if distance < definition["keep_min"]:
            direction = -to_player
        elif distance > definition["keep_max"]:
            direction = pygame.Vector2(to_player)
        else: # We rotate the to_player vector to seem that the spirit is walking sideways
            direction = pygame.Vector2(-to_player.y, to_player.x) * self.strafe_sign

        if not boss.move_towards(direction, definition["speed"], dt):
            self.strafe_sign *= -1

        boss.face(to_player)
        boss.walk_pose(dt)
