"""
ISPPV1 2023
Study Case: Flappy Bird

Author: Alejandro Mujica
alejandro.j.mujic4@gmail.com

This file contains the definition of the class World: the scrolling
background/ground, and the log pairs the bird must fly through.
"""

import random
from typing import List
from typing import Optional

import pygame

from gale.factory import Factory

import settings
from src.LogPair import LogPair, DynLogPair
from src.GameMode import GameMode, NormalMode, HardMode
from src.PowerUp import PowerUp

class World:
    def __init__(self, generate_logs: bool = False, 
                 mode: Optional[GameMode] = None) -> None:
        self.generate_logs: bool = generate_logs
        self.mode = mode if mode is not None else NormalMode()
        self.background_x: float = 0.0
        self.ground_x: float = 0.0
        self.logs: List[LogPair] = []
        self.logs_spawn_timer: float = 0.0
        self.power_up_spawn_timer: float = 0.0
        self.power_up: PowerUp = None
        self.last_log_y: float = settings.MIN_LOG_Y + random.randint(0, 80) + 20
        self.log_pair_factory: Factory = Factory(LogPair)
        self.din_log_pair_factory: Factory = Factory(DynLogPair)
        self.power_up_factory: Factory = Factory(PowerUp)

    def reset(self, generate_logs: bool) -> None:
        self.generate_logs = generate_logs

    def collides(self, rect: pygame.Rect) -> bool:
        if rect.bottom >= settings.VIRTUAL_HEIGHT or rect.left <= 0 or rect.right >= settings.VIRTUAL_WIDTH:
            return True

        return any(log_pair.collides(rect) for log_pair in self.logs)

    def power_up_collides(self, rect: pygame.Rect) -> bool:
        return self.power_up.get_rect().colliderect(rect) if self.power_up is not None else False  

    def update_scored(self, rect: pygame.Rect) -> bool:
        return any(log_pair.update_scored(rect) for log_pair in self.logs)

    def update(self, dt: float) -> None:
        mode = self.mode

        if self.generate_logs:
            self.logs_spawn_timer += dt

            if self.logs_spawn_timer >= mode.log_spawn_time():
                self.logs_spawn_timer = 0.0
                y = max(
                    settings.MIN_LOG_Y,
                    min(mode.next_log_y(self.last_log_y), settings.MAX_LOG_Y),
                )
                self.last_log_y = y
                if mode.should_appear_log_pair():
                    self.logs.append(self.log_pair_factory.create(settings.VIRTUAL_WIDTH, y, {"aperture": mode.aperture()}))
                else:
                    self.logs.append(self.din_log_pair_factory.create(settings.VIRTUAL_WIDTH, y, {"aperture": mode.aperture()}))

        if self.mode.allow_power_up():
            self.power_up_spawn_timer += dt

            if self.power_up_spawn_timer >= mode.power_up_spawn_time():
                self.power_up_spawn_timer = 0.0
                y = max(
                    10, 
                    min(mode.next_power_up_y(),
                        settings.VIRTUAL_HEIGHT - settings.POWER_UP_HEIGHT - 10
                    )
                )
                self.power_up = self.power_up_factory.create(settings.VIRTUAL_WIDTH, y)

        if self.power_up is not None:
            self.power_up.update(dt)

        self.background_x += -settings.BACK_SCROLL_SPEED * dt

        if self.background_x <= -settings.BACKGROUND_LOOPING_POINT:
            self.background_x = 0

        self.ground_x += mode.ground_speed(dt)

        if self.ground_x <= -settings.VIRTUAL_WIDTH:
            self.ground_x = 0

        for log_pair in self.logs:
            log_pair.update(dt, mode)

        self.logs = [log_pair for log_pair in self.logs if not log_pair.is_out_of_game()]

    def render(self, surface: pygame.Surface) -> None:
        surface.blit(settings.TEXTURES["background"], (round(self.background_x), 0))

        for log_pair in self.logs:
            log_pair.render(surface)

        if self.power_up is not None:
            self.power_up.render(surface)

        surface.blit(
            settings.TEXTURES["ground"],
            (round(self.ground_x), settings.VIRTUAL_HEIGHT - settings.GROUND_HEIGHT),
        )
