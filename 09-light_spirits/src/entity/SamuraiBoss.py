"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains the class SamuraiBoss: Samurai Gurenmaru, the first
form of the final boss. Relentless and close range, he always walks at
the player, dashes in to surprise them, and chains his attacks:

A normal slash may be followed at once by a second, faster one.
The thrust, a long thin strip heralded by a loud cue, stuns heavily on a
hit, and whether it hits or not it is always followed by a dash and three
fast combo hits.

Both chains live in on_strike_finished, which queues the follow ups in
plan; decide() then plays them out before looking at the fight again.
"""

import random
from typing import Any, Dict

from src.definitions.bosses import SAMURAI
from src.entity.Boss import Boss
from src.states.entity import boss as boss_states

COMBO_HITS = 3

# The dash inside the thrust combo skips most of its wind up, it follows straight on.
COMBO_DASH_WINDUP = 0.05


class SamuraiBoss(Boss):
    def __init__(self, x: float, y: float, level: Any) -> None:
        self.awake = False
        super().__init__("samurai", SAMURAI, x, y, level)
        self.start_cooldown("dash", 1.5)
        self.start_cooldown("thrust", 5.0)
        self.change_state("dormant")

    def build_states(self) -> Dict[str, Any]:
        return {
            "dormant": lambda sm, b=self: boss_states.BossDormantState(b, sm),
            "pursue": lambda sm, b=self: boss_states.BossPursueState(b, sm),
            "dash": lambda sm, b=self: boss_states.BossDashState(b, sm),
            "strike": lambda sm, b=self: boss_states.BossStrikeState(b, sm),
            "felled": lambda sm, b=self: boss_states.BossFelledState(b, sm),
            "dissolve": lambda sm, b=self: boss_states.BossDissolveState(b, sm),
        }

    def act(self, action: str) -> None:
        if action == "dash_in":
            in_combo = bool(self.plan) and self.plan[0] == "combo"
            windup = COMBO_DASH_WINDUP if in_combo else None
            self.change_state("dash", self.definition["dash"], True, windup)
        elif action in self.definition["strikes"]:
            if action == "thrust":
                self.start_cooldown("thrust", self.definition["thrust_cooldown"])
            self.change_state("strike", action)
        else:
            self.change_state("pursue")

    def decide(self) -> None:
        self.act(self.plan.popleft() if self.plan else "pursue")

    def on_strike_finished(self, name: str) -> None:
        if name == "slash" and random.random() < self.definition["double_chance"]:
            self.plan.appendleft("double")
        elif name == "thrust":
            self.plan.extend(["dash_in"] + ["combo"] * COMBO_HITS)

        self.decide()
