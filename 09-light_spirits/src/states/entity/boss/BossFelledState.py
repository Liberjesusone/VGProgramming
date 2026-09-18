"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains the class BossFelledState: the samurai's fall. He
holds his transition pose, kneeling as the smoke bursts out of his armour,
for transition_time seconds, the moment the player is meant to believe
the fight is won, and then stays down in his defeated pose for good. The
body keeps being drawn right where it fell for the whole second phase,
but can no longer be hit.
"""

from src.states.entity.boss.BossBaseState import BossBaseState

TRANSITION_TIME = 2.2


class BossFelledState(BossBaseState):
    def enter(self) -> None:
        boss = self.boss
        boss.vulnerable = False
        boss.plan.clear()
        boss.trail.clear()
        boss.pose = "transition"
        boss.level.request_shake(3.0, 0.4)
        self.elapsed = 0.0

    def update(self, dt: float) -> None:
        self.elapsed += dt

        if self.elapsed >= TRANSITION_TIME:
            self.boss.pose = "defeated"
