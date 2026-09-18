"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains the class EnemyGuardState: stands still where the
enemy spawned, watching every frame for the player to come within its
aggro_radius.
"""

from src.states.entity.enemy.EnemyBaseState import EnemyBaseState


class EnemyGuardState(EnemyBaseState):
    def enter(self) -> None:
        self.enemy.pose = "idle"

    def update(self, dt: float) -> None:
        enemy = self.enemy

        if enemy.to_player().length() <= enemy.definition["aggro_radius"]:
            enemy.change_state("chase")
