"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains the class EnemyChaseState: closes in on the player at
full speed until within the attack's engage_range, then starts charging.
Never gives up the chase on its own once aggroed.
"""

import math

from src.states.entity.enemy.EnemyBaseState import EnemyBaseState

# How fast the walk pose alternates with idle, same idea as the player's
# own 2-pose step cycle in PlayerWalkState.
STEP_SPEED = 8.0


class EnemyChaseState(EnemyBaseState):
    def enter(self) -> None:
        self.phase = 0.0

    def update(self, dt: float) -> None:
        enemy = self.enemy
        to_player = enemy.to_player()

        if to_player.length() <= enemy.attack["engage_range"]:
            enemy.change_state("charge")
            return

        enemy.face(to_player)
        enemy.move_towards(to_player, enemy.definition["speed"], dt)

        self.phase += dt * STEP_SPEED
        enemy.pose = "walk" if math.sin(self.phase) > 0 else "idle"
