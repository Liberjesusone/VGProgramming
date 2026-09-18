"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains the class BossBaseState: the base every boss state
extends, holding nothing but the boss, the same shape as EnemyBaseState.
"""

from typing import TYPE_CHECKING

from gale.state import BaseState, StateMachine

""" Boss.py builds its state machine out of this package, so importing
Boss back here at load time would be circular. Only type checkers read
this import. """
if TYPE_CHECKING:
    from src.entity.Boss import Boss


class BossBaseState(BaseState):
    def __init__(self, boss: "Boss", state_machine: StateMachine) -> None:
        super().__init__(state_machine)
        self.boss = boss

    def is_current(self) -> bool:
        """ Whether this state is still the one running, for callbacks that
        fire later (a tween finishing) and must do nothing if the boss has
        already moved on. """
        return self.boss.state_machine.current is self
