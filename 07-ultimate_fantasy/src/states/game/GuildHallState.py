"""
ISPPV1 2023
Study Case: Ultimate Fantasy (RPG)

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains the class GuildHallState: the inside of the town's
guild hall, shown when the party walks through its door.
"""

from typing import Any, Callable

import pygame

from gale.state import BaseState
from gale.text import Text

import settings
from src.gui.Panel import Panel

WELCOME = "Welcome to the guild hall. Rest here as long as you like."
HINT = "Press Space to step back outside."

PANEL_HEIGHT = 28

# Where the party stands inside. The dojo's floor starts at
# GUILD_INTERIOR_FLOOR_Y and the panel takes the bottom of the screen, so
# these two rows are what is left between them, laid out two by two like
# the battle arena rather than reusing the arena's own coordinates: those
# put the party against the left edge because that is where the enemies
# are not, and in here there are no enemies to make room for.
ROW_Y = (settings.GUILD_INTERIOR_FLOOR_Y + 16, settings.GUILD_INTERIOR_FLOOR_Y + 52)
COLUMN_X = (152, 216)


class GuildHallState(BaseState):
    """
    Pushed over PlayState, the same way a battle is, and laid out like the
    battle arena: one full screen background with the party standing on
    it, no map to walk around and nobody to fight.

    The party is stood on the dojo floor on the way in and put back on the
    tile it came from on the way out, so the town never notices it was
    gone.
    """

    def enter(self, world: Any, on_exit: Callable[[], None]) -> None:
        self.world = world
        self.party = world.party
        self.on_exit = on_exit
        self.leaving = False

        self._stand_on_the_floor()

        self.panel = Panel(
            0,
            settings.VIRTUAL_HEIGHT - PANEL_HEIGHT,
            settings.VIRTUAL_WIDTH,
            PANEL_HEIGHT,
        )

    def _stand_on_the_floor(self) -> None:
        """Places the four of them facing the camera on the wooden floor.

        Pixel positions are set directly rather than map coordinates,
        because there is no tile map in here to place anything on. The
        overworld ones are restored by World.enter_building's on_exit,
        which recomputes every x and y from the tile the party walked in
        from.
        """
        for slot, key in enumerate(sorted(self.party.characters.keys())):
            character = self.party.characters[key]
            character.x = COLUMN_X[slot % 2]
            character.y = ROW_Y[slot // 2]
            character.direction = "down"

        # After the directions, so the idle state picks the right
        # animation for each of them.
        self.party.change_state("idle")

    def update(self, dt: float) -> None:
        self.party.update(dt)

    def on_input(self, input_id: str, input_data: Any) -> None:
        if self.leaving or not input_data.pressed:
            return

        if input_id in ("space", "enter"):
            self._leave()

    def _leave(self) -> None:
        from src.states.game.FadeInState import FadeInState
        from src.states.game.FadeOutState import FadeOutState

        self.leaving = True
        settings.SOUNDS["blip"].play()

        def on_complete() -> None:
            # FadeInState has already popped itself by the time this runs,
            # so this pop is the one that takes this state off the stack
            # and hands the town back to PlayState.
            self.state_machine.pop()
            self.on_exit()
            self.state_machine.push(
                FadeOutState(self.state_machine),
                color=(0, 0, 0),
                time=0.5,
                on_complete=lambda: None,
            )

        self.state_machine.push(
            FadeInState(self.state_machine),
            color=(0, 0, 0),
            time=0.5,
            on_complete=on_complete,
        )

    def render(self, surface: pygame.Surface) -> None:
        surface.blit(settings.TEXTURES["guild-interior"], (0, 0))

        for character in self.party.characters.values():
            if not character.dead:
                character.render(surface)

        self.panel.render(surface)

        # Both lines measured from the panel's own top edge and kept
        # inside its 2px border, so shrinking the panel to leave more
        # floor for the party cannot clip the second one off the bottom
        # of the screen.
        top = settings.VIRTUAL_HEIGHT - PANEL_HEIGHT

        Text(
            WELCOME,
            settings.FONTS["small"],
            settings.VIRTUAL_WIDTH // 2,
            top + 5,
            (255, 255, 255),
            center=True,
        ).render(surface)

        Text(
            HINT,
            settings.FONTS["small"],
            settings.VIRTUAL_WIDTH // 2,
            top + 15,
            (170, 170, 170),
            center=True,
        ).render(surface)
