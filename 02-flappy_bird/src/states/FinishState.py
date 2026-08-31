from typing import Optional

import pygame

from gale.input_handler import InputData
from gale.state import BaseState
from gale.text import render_text

import settings
from src.Bird import Bird
from src.World import World
from src.GameMode import GameMode, HardMode, NormalMode

class FinishState(BaseState):
    def enter(self, 
              world: Optional[World] = None, 
              bird: Optional[Bird] = None,
              score: Optional[int] = None) -> None:
        self.world = world if world is not None else World()
        self.world.reset(True)

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
            settings.VIRTUAL_WIDTH / 2,
            settings.VIRTUAL_HEIGHT / 2 - 50,
            settings.COLOR_WHITE,
            shadowed=True,
            center=True   
        )
        render_text(
            surface,
            "You have lost, to play again press enter",
            settings.FONTS["medium"],
            settings.VIRTUAL_WIDTH / 2,
            settings.VIRTUAL_HEIGHT / 2,
            settings.COLOR_WHITE,
            shadowed=True,
            center=True,
        )
        render_text(
            surface,
            "To go to home press Backspace",
            settings.FONTS["medium"],
            settings.VIRTUAL_WIDTH / 2,
            settings.VIRTUAL_HEIGHT / 2 + 20,
            settings.COLOR_WHITE,
            shadowed=True,
            center=True,
        )
        
        return super().render(surface)

    def on_input(self, input_id: str, input_data: InputData) -> None:
        if input_id == "confirm" and input_data.pressed:
            self.state_machine.change("count_down", World(False,
                                       HardMode() if isinstance(self.world.mode, HardMode) else NormalMode()))
        if input_id == "return_home" and input_data.pressed:
            self.state_machine.change("title")