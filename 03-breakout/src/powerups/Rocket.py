from typing import TypeVar, Any

import pygame

import settings
from src.powerups.PowerUp import PowerUp
from typing import Optional


class Rocket(PowerUp):
    """
    The power up that gives you 1 rocket to destroy any brick no matter it's color or tier.
    """
    def __init__(self, x: int, y: int) -> None:
        self.was_fired = False
        self.was_taken = False
        self.is_left = False
        super().__init__(x, y, 3)

    def get_collision_rect(self) -> pygame.Rect:
        return pygame.Rect(self.x, self.y, 16, 32)

    def update(self, dt: float) -> None:
        if self.was_fired:
            self.y -= 70 * dt
            if self.y <= 0:
                self.active = False  
        elif self.was_taken:
            return
        else:
            return super().update(dt)

    def render(self, surface: pygame.Surface,  play_state: Optional[TypeVar("PlayState")] = None) -> None:
        if self.was_taken:
            surface.blit(settings.TEXTURES["rocket"], (self.x, self.y))
        else:
            super().render(surface)

    def take(self, play_state: TypeVar("PlayState")) -> None:
        play_state.l_rocket = Rocket(play_state.paddle.x, play_state.paddle.y)
        play_state.r_rocket = Rocket(play_state.paddle.x + play_state.paddle.width, play_state.paddle.y)
        play_state.l_rocket.was_taken = True
        play_state.l_rocket.is_left = True
        play_state.r_rocket.was_taken = True
        play_state.r_rocket.is_left = False
        self.active = False

    def fire(self) -> None:
        self.was_fired = True        
