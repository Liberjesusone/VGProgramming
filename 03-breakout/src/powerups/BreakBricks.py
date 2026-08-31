from typing import TypeVar, Any

import pygame

import settings
import random
from src.powerups.PowerUp import PowerUp
from typing import Optional

class BreakBricks(PowerUp):
    """
    The power up that breaks completly a random amount of bricks betweeen 3-10.
    """
    def __init__(self, x: int, y: int) -> None:
        super().__init__(x, y, 1)

    def take(self, play_state: TypeVar("PlayState")) -> None:
        p = random.random()

        if p <= 0.09:
            amount = 10
        elif p <= 0.11:
            amount = 9
        elif p <= 0.13:
            amount = 8
        elif p <= 0.16:
            amount = 7
        elif p <= 0.19:
            amount = 6
        elif p <= 0.22:
            amount = 5
        elif p <= 0.5:
            amount = 4
        else:
            amount = 3

        candidates = [b for b in play_state.brickset.bricks.values() if not b.broken]
        amount = min(amount, len(candidates))

        for b in random.sample(candidates, amount):
            b.destroy()

        self.active = False

    def fire(self) -> None:
        self.was_fired = True        
