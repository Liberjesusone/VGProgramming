"""
ISPPV1 2023
Study Case: Flappy Bird

Author: Alejandro Mujica
alejandro.j.mujic4@gmail.com

This file contains the definition of the class LogPair: a top log
(rendered flipped upside down) and a bottom log, LOGS_GAP pixels
apart, that scroll left together and score once the bird passes them.
"""

import pygame

import settings
from src.GameMode import GameMode, NormalMode, HardMode
import random

class LogPair:
    def __init__(self, x: float, y: float, aperture: int) -> None:
        self.x: float = x
        self.y: float = y
        self.scored: bool = False
        self.aperture = aperture

    def get_top_rect(self) -> pygame.Rect:
        return pygame.Rect(round(self.x), round(self.y), settings.LOG_WIDTH, settings.LOG_HEIGHT)

    def get_bottom_rect(self) -> pygame.Rect:
        return pygame.Rect(
            round(self.x),
            round(self.y + self.aperture + settings.LOG_HEIGHT),
            settings.LOG_WIDTH,
            settings.LOG_HEIGHT,
        )

    def collides(self, rect: pygame.Rect) -> bool:
        has_collided = self.get_top_rect().colliderect(rect) or self.get_bottom_rect().colliderect(rect)
        if has_collided: 
            settings.SOUNDS["explosion"].play()
        return has_collided
                        

    def update(self, dt: float, mode: GameMode) -> None:
        self.x += mode.ground_speed(dt)

    def is_out_of_game(self) -> bool:
        return self.x < -settings.LOG_WIDTH

    def update_scored(self, rect: pygame.Rect) -> bool:
        if self.scored:
            return False

        if rect.left > self.x + settings.LOG_WIDTH:
            self.scored = True
            return True

        return False

    def render(self, surface: pygame.Surface) -> None:
        surface.blit(settings.TEXTURES["log_inverted"], self.get_top_rect())
        surface.blit(settings.TEXTURES["log"], self.get_bottom_rect())


class DynLogPair(LogPair):
    def __init__(self, x: float, y: float, aperture: int) -> None:
        self.x: float = x
        self.y: float = y
        self.displacement = 0
        self.scored: bool = False
        self.aperture: int = aperture
        self.is_closing: bool = random.randint(0,1) == 1

    def collides(self, rect: pygame.Rect) -> bool:
        has_collided = self.get_top_rect().colliderect(rect) or self.get_bottom_rect().colliderect(rect)
        if has_collided: 
            settings.SOUNDS["punch"].play()
        return has_collided

    def update(self, dt: float, mode: GameMode) -> None:
        self.x += mode.ground_speed(dt)

        delta = settings.LOGS_CLOSING_SPEED * dt
        self.y += delta if self.is_closing else -delta
        self.aperture += -delta * 2 if self.is_closing else delta * 2

        if self.aperture < settings.LOGS_MIN_GAP:
           self.aperture = settings.LOGS_MIN_GAP
           self.is_closing = False
        elif self.aperture > settings.LOGS_MAX_GAP:
           self.aperture = settings.LOGS_MAX_GAP
           self.is_closing = True
