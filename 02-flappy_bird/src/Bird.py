"""
ISPPV1 2023
Study Case: Flappy Bird

Author: Alejandro Mujica
alejandro.j.mujic4@gmail.com

This file contains the definition of the class Bird.
"""

import pygame

import settings
from gale.timer import Timer


class Bird:
    def __init__(self, x: float, y: float, width: float, height: float) -> None:
        self.x: float = x
        self.y: float = y
        self.width: float = width
        self.height: float = height
        self.vy: float = 0.0
        self.vx: float = 0.0
        self.jumping: bool = False
        self.is_ghost = False

    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(round(self.x), round(self.y), self.width, self.height)

    def jump(self) -> None:
        self.jumping = True

    def set_ghost(self) -> None:
        self.is_ghost = True
        pygame.mixer.music.load(settings.GHOST_MUSIC)
        pygame.mixer.music.play(loops=-1)
        Timer.after(5, self.end_ghost)

    def end_ghost(self) -> None:
        self.is_ghost = False
        pygame.mixer.music.load(settings.NORMAL_MUSIC)
        pygame.mixer.music.play()

    def move(self, move_left: bool, was_pressed: bool) -> None:
        if move_left:
            self.vx = -settings.BIRD_X_SPEED if was_pressed else 0
        else:
            self.vx = settings.BIRD_X_SPEED if was_pressed else 0

    def update(self, dt: float) -> None:
        self.vy += settings.GRAVITY * dt

        if self.jumping:
            settings.SOUNDS["jump"].play()
            self.vy = -settings.JUMP_TAKEOFF_SPEED
            self.jumping = False

        self.x += self.vx * dt
        self.y += self.vy * dt

    def render(self, surface: pygame.Surface) -> None:
        if self.is_ghost:
            surface.blit(settings.TEXTURES["ghost"], self.get_rect())
        else:   
            surface.blit(settings.TEXTURES["bird"], self.get_rect())
