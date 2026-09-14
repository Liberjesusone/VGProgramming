"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains the class EnemyBaseState: the base every enemy state
extends. Holds nothing but the enemy reference, the same shape
PlayerBaseState uses for the player's own states.
"""

from typing import TYPE_CHECKING

from gale.state import BaseState, StateMachine

""" Enemy.py imports this whole package to build its state machine, so
importing Enemy back here at module load time would be circular. Only
type checkers read this import, at no point during a real run. """
if TYPE_CHECKING:
    from src.entity.Enemy import Enemy


class EnemyBaseState(BaseState):
    def __init__(self, enemy: "Enemy", state_machine: StateMachine) -> None:
        super().__init__(state_machine)
        self.enemy = enemy
