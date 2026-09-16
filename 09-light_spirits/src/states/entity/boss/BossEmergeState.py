"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains the class BossEmergeState: the spirit rising out of the
samurai's body. It starts invisible exactly where the body lies, and one
tween fades it in while lifting it emerge_rise pixels up, out of the
corpse, so for the rest of the fight it stands beside the body instead of
inside it. It cannot be hit until it has fully risen.
"""

from gale.timer import Timer

from src.states.entity.boss.BossBaseState import BossBaseState


class BossEmergeState(BossBaseState):
    def enter(self) -> None:
        boss = self.boss
        definition = boss.definition

        boss.vulnerable = False
        boss.emerged = False
        boss.alpha = 0.0
        boss.pose = "emerge"
        boss.direction = "down"

        Timer.tween(
            definition["emerge_time"],
            [(boss, {"alpha": definition["alpha"], "y": boss.y - definition["emerge_rise"]})],
            ease_function_name="out_quad",
            on_finish=self._risen,
        )

    def _risen(self) -> None:
        if not self.is_current():
            return

        # You thought it was over JAJAJA
        self.boss.emerged = True
        self.boss.decide()
