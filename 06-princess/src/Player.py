"""
ISPPV1 2023
Study Case: The Legend of the Princess (ARPG)

Author: Alejandro Mujica
alejandro.j.mujic4@gmail.com

This file contains the class Player.
"""

from typing import Any

from gale.input_handler import InputData

from src.Entity import Entity


class Player(Entity):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        # Tracks which movement keys are currently held down (as opposed to
        # sword/take, which are edge-triggered through on_input directly),
        # since every player state polls this once per frame in the same
        # left/right/up/down priority order the original game used.
        self.held = {
            "move_left": False,
            "move_right": False,
            "move_up": False,
            "move_down": False,
        }

    def collides(self, target: Any) -> bool:
        """
        AABB with some slight shrinkage of the box on the top side, for
        perspective (so walking "into" the top edge of an obstacle from
        below doesn't collide until the player's feet actually reach it).
        """
        self_y = self.y + self.height / 2
        self_height = self.height - self.height / 2

        return not (
            self.x + self.width < target.x
            or self.x > target.x + target.width
            or self_y + self_height < target.y
            or self_y > target.y + target.height
        )

    def on_input(self, input_id: str, input_data: InputData) -> None:
        if input_id in self.held:
            if input_data.pressed:
                self.held[input_id] = True
            elif input_data.released:
                self.held[input_id] = False
        else:
            self.state_machine.on_input(input_id, input_data)
