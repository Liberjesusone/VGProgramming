"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains the class SpiritBoss: the Light Spirit of Samurai
Gurenmaru, the second form of the final boss, rising out of his body. An
archer that always wants distance: it shoots fast, heavy arrows, casts a
rain of arrows around the player every so often, and when the player gets
too close it swings its bow to launch them away, then immediately escapes,
dashing back if the way behind it is clear, or running off for a few
seconds if it is cornered against a wall or the edge of the map.

It is drawn translucent and flickering, the only way the spirit's ghostly
look can exist: the art itself is fully opaque (see its prompts).
"""

import math
from typing import Any, Dict

import pygame

from src.definitions.bosses import SPIRIT
from src.entity.Boss import Boss
from src.states.entity import boss as boss_states

# Distance between the samples that check whether a backdash has room.
PATH_STEP = 16.0


class SpiritBoss(Boss):
    def __init__(self, x: float, y: float, level: Any) -> None:
        self.emerged = False
        super().__init__("spirit", SPIRIT, x, y, level)
        self.start_cooldown("rain", self.definition["rain"]["first_delay"])
        self.change_state("emerge")

    def build_states(self) -> Dict[str, Any]:
        return {
            "emerge": lambda sm, b=self: boss_states.BossEmergeState(b, sm),
            "reposition": lambda sm, b=self: boss_states.BossRepositionState(b, sm),
            "shoot": lambda sm, b=self: boss_states.BossShootState(b, sm),
            "rain": lambda sm, b=self: boss_states.BossRainState(b, sm),
            "strike": lambda sm, b=self: boss_states.BossStrikeState(b, sm),
            "dash": lambda sm, b=self: boss_states.BossDashState(b, sm),
            "flee": lambda sm, b=self: boss_states.BossFleeState(b, sm),
            "dissolve": lambda sm, b=self: boss_states.BossDissolveState(b, sm),
        }

    def act(self, action: str) -> None:
        if action == "melee":
            self.start_cooldown("melee", self.definition["melee_cooldown"])
            self.change_state("strike", "melee")
        elif action == "escape":
            if self.can_dash_away():
                self.change_state("dash", self.definition["backdash"], False)
            else:
                self.change_state("flee")
        elif action in ("shoot", "rain"):
            self.change_state(action)
        else:
            self.change_state("reposition")

    def decide(self) -> None:
        self.act(self.plan.popleft() if self.plan else "reposition")

    def on_strike_finished(self, name: str) -> None:
        # Landed or not, the swing is always followed by getting away.
        self.plan.appendleft("escape")
        self.decide()

    def can_dash_away(self) -> bool:
        """ Whether the full backdash, straight away from the player, runs
        clear of every prop and the edge of the map, sampled every
        PATH_STEP pixels along the way. """
        away = -self.aim_at_player(pygame.Vector2(0, 1))
        distance = self.definition["backdash"]["distance"]
        travelled = PATH_STEP

        while travelled <= distance:
            point = pygame.Vector2(self.x, self.y) + away * travelled

            if self.level.blocked(self.feet_rect_at(point.x, point.y)):
                return False

            travelled += PATH_STEP

        return True

    def display_alpha(self) -> float:
        flicker = 1.0 - self.definition["flicker"] * (0.5 + 0.5 * math.sin(self.elapsed * 6.0))
        return self.alpha * flicker
