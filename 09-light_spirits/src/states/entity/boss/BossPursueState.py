"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains the class BossPursueState: how the samurai chooses his
next move while closing in on the player, which he always is.

Close enough to swing, he slashes, or starts the thrust instead if it is
off cooldown and the roll goes his way. Further out, every
decision_interval seconds he rolls for the thrust (its long reach allows
it from mid range) and then for a surprise dash that ends in a slash;
the rest of the time he simply walks toward the player. Rolling on an
interval rather than every frame keeps those chances independent of the
frame rate.
"""

import random

from src.states.entity.boss.BossBaseState import BossBaseState


class BossPursueState(BossBaseState):
    def enter(self) -> None:
        self.boss.vulnerable = True
        self.roll_timer = 0.0

    def update(self, dt: float) -> None:
        boss = self.boss
        definition = boss.definition
        to_player = boss.to_player()
        distance = to_player.length()

        if distance <= definition["slash_trigger"]:
            boss.act("thrust" if self._rolls_thrust() else "slash")
            return

        self.roll_timer += dt

        if self.roll_timer >= definition["decision_interval"]:
            self.roll_timer = 0.0

            if distance <= definition["thrust_trigger"] and self._rolls_thrust():
                boss.act("thrust")
                return

            dash = definition["dash"]

            if (boss.ready("dash")
                and dash["min_range"] <= distance <= dash["max_range"]
                and random.random() < dash["chance"]):
                boss.start_cooldown("dash", dash["cooldown"])
                boss.plan.append("slash")
                boss.act("dash_in")
                return

        boss.face(to_player)
        boss.move_towards(to_player, definition["speed"], dt)
        boss.walk_pose(dt)

    def _rolls_thrust(self) -> bool:
        boss = self.boss
        return boss.ready("thrust") and random.random() < boss.definition["thrust_chance"]
