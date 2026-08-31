from typing import TypeVar, Any

import pygame

import settings
from src.powerups.PowerUp import PowerUp


class StopBall(PowerUp):
    """
    The power up that stops one ball when it touches the paddle, allowing the player to 
    serve it again in while the game continues playing.
    """
    def __init__(self, x: int, y: int) -> None:
        super().__init__(x, y, 7)

    def take(self, play_state: TypeVar("PlayState")) -> None:
        play_state.stuck_next = True
        self.active = False
        
