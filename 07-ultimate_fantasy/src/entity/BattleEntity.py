"""
ISPPV1 2023
Study Case: Ultimate Fantasy (RPG)

Author: Alejandro Mujica
alejandro.j.mujic4@gmail.com

This file contains the class BattleEntity: adds battle stats (HP/attack/
defense/magic), the damage/heal/compute formulas shared by both Character
(playable) and Enemy, and the rest clock that decides whose turn is next.
"""

import math
import random
from typing import Any, Dict, List

from src.definitions.entity import DEFAULT_REST_TIME, REST_HEAD_START
from src.entity.Entity import Entity


class BattleEntity(Entity):
    def __init__(self, definition: Dict[str, Any]) -> None:
        super().__init__(definition)

        self.klass: str = definition["class"]
        self.actions: List[Dict[str, Any]] = definition["actions"]
        self.level: int = definition.get("level", 1)
        self.dead: bool = definition.get("dead", False)

        self.base_hp: float = definition["baseHP"]
        self.base_attack: float = definition["baseAttack"]
        self.base_defense: float = definition["baseDefense"]
        self.base_magic: float = definition["baseMagic"]

        self.hp: float = self.base_hp
        self.attack: float = self.base_attack
        self.defense: float = self.base_defense
        self.magic: float = self.base_magic

        self.current_hp: float = self.hp

        # Turns are not taken in a fixed order any more. Every entity has
        # to sit out rest_time seconds after acting, and whoever finishes
        # first gets to move next, so a fast class simply acts more often
        # than a slow one. TakeTurnState owns the clock that feeds this.
        self.rest_time: float = definition.get("rest_time", DEFAULT_REST_TIME)
        self.rest_timer: float = 0.0

        # Filled in by BattleState so the bar over the sprite can show how
        # close this entity is to its next turn. None outside a battle.
        self.rest_bar = None

    def rest(self, dt: float) -> None:
        """Advances this entity's recovery by dt, keeping the bar over its
        sprite in step."""
        self.rest_timer += dt

        if self.rest_bar is not None:
            self.rest_bar.value = min(self.rest_timer, self.rest_time)

    def is_rested(self) -> bool:
        return self.rest_timer >= self.rest_time

    def start_rest(self, head_start: float = 0.0) -> None:
        """Sends this entity back to the end of the queue. head_start is a
        fraction of its own rest_time to begin with already served, used
        once at the start of a battle to stagger the opening turns."""
        self.rest_timer = self.rest_time * head_start

        if self.rest_bar is not None:
            self.rest_bar.value = self.rest_timer

    def start_random_rest(self) -> None:
        self.start_rest(random.uniform(0, REST_HEAD_START))

    def damage(self, amount: float) -> None:
        self.current_hp -= amount

        if self.current_hp <= 0:
            self.dead = True

    def heal(self, amount: float) -> None:
        if not self.dead:
            self.current_hp = min(self.hp, self.current_hp + amount)

    def compute_attack(self) -> int:
        return math.floor(random.random() / 2 * self.attack + random.random() / 4 * self.magic)

    def compute_defense(self) -> int:
        return math.floor(
            random.random() / 4 * self.defense + random.random() / 8 * self.magic
        )

    def compute_healing(self) -> int:
        return math.floor(random.random() * 2 * self.magic)
