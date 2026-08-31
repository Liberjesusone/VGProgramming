## ---------- ---------- ##
#
# Author: Liber Puccini
# liberjesusone@gmail.com
#
# This file contains the definition of the class PauseState.
# where the game is paused and the player can choose to resume 
# or go back to the main menu.
#
## ---------- ---------- ##

from typing import Optional

import pygame

from gale.input_handler import InputData
from gale.state import BaseState
from gale.text import render_text

import settings
from src.Bird import Bird
from src.World import World

class PauseState(BaseState):
    def enter(self, 
              world: Optional[World] = None, 
              bird: Optional[Bird] = None,
              score: Optional[int] = None) -> None:
        self.world = world if world is not None else World()
        
        self.bird = bird if bird is not None else Bird(
            settings.VIRTUAL_WIDTH / 2 - settings.BIRD_WIDTH / 2,
            settings.VIRTUAL_HEIGHT / 2 - settings.BIRD_HEIGHT / 2,
            settings.BIRD_WIDTH,
            settings.BIRD_HEIGHT,
        )
        self.score = score if score is not None else 0

    def render(self, surface: pygame.Surface) -> None:
        self.world.render(surface)
        self.bird.render(surface)
        render_text(
            surface,
            f"Score: {self.score}",
            settings.FONTS["flappy"],
            20,
            10,
            settings.COLOR_WHITE,
            shadowed=True,
        )

        overlay = pygame.Surface((settings.VIRTUAL_WIDTH, settings.VIRTUAL_HEIGHT),
                                 pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))  # negro con alpha=150 de 255
        surface.blit(overlay, (0, 0))

        center = (settings.VIRTUAL_WIDTH / 2, settings.VIRTUAL_HEIGHT / 2)
        pygame.draw.circle(surface, (184, 184, 184), 
                           center, 30)
        pygame.draw.rect(surface, (255, 255, 255), pygame.Rect(
                         center[0] - 20, center[1]-14, 15, 28))
        pygame.draw.rect(surface, (255, 255, 255), pygame.Rect(
                         center[0] + 5, center[1]-14, 15, 28))

    def on_input(self, input_id: str, input_data: InputData) -> None:
        if input_id == "pause" and input_data.pressed:
            self.state_machine.change("playing", world=self.world, 
                                       bird=self.bird, score=self.score)