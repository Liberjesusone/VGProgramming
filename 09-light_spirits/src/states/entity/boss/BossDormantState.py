"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains the class BossDormantState: the samurai standing still
in his arena until the player comes within his aggro radius, or hits him
from afar, whichever happens first. Waking up is what BossFight watches
for to show the health bar.
"""

from src.states.entity.boss.BossBaseState import BossBaseState


class BossDormantState(BossBaseState):
    def enter(self) -> None:
        self.boss.vulnerable = True
        self.boss.pose = "idle"

    def update(self, dt: float) -> None:
        """ The boss only wakes up here, when it detects the player or it recives dmg"""
        boss = self.boss
        close = boss.to_player().length() <= boss.definition["aggro_radius"]

        if close or boss.health < boss.max_health:
            # You must run ;)
            boss.awake = True
            boss.decide()
