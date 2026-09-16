"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains the class BossDissolveState: a boss holding one pose for
a moment, then switching to another while it fades out completely, after
which it is removed from the level. The spirit holds its defeated pose and
then breaks apart in its dissolve pose; the samurai's body, still kneeling,
simply fades away with it.
"""

from gale.timer import Timer

from src.states.entity.boss.BossBaseState import BossBaseState


class BossDissolveState(BossBaseState):
    def enter(self, hold_pose: str, hold_time: float, fade_pose: str, fade_time: float) -> None:
        self.boss.vulnerable = False
        self.boss.plan.clear()
        self.boss.pose = hold_pose
        self.hold_time = hold_time
        self.fade_pose = fade_pose
        self.fade_time = fade_time
        self.elapsed = 0.0
        self.fading = False

    def update(self, dt: float) -> None:
        self.elapsed += dt

        if self.fading or self.elapsed < self.hold_time:
            return

        self.fading = True
        self.boss.pose = self.fade_pose
        Timer.tween(self.fade_time, [(self.boss, {"alpha": 0.0})], on_finish=self._gone)

    def _gone(self) -> None:
        self.boss.removed = True
