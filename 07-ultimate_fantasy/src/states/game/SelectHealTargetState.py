"""
ISPPV1 2023
Study Case: Ultimate Fantasy (RPG)

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains the class SelectHealTargetState: picks which party
member a single target heal is going to land on, out in the overworld.
"""

from typing import Any, Callable, List

import pygame

from gale.state import BaseState
from gale.text import Text

import settings

HINT = "Choose who to heal.  Enter confirms, Space cancels."
HINT_Y = 192


class SelectHealTargetState(BaseState):
    """
    The overworld counterpart of SelectTargetState.

    It works the same way the battle one does, walking a cursor through
    the living targets with left and right and confirming with enter, but
    it points at the character cards on screen instead of at sprites
    standing on the battle map, so it takes the menu's cards and marks the
    chosen one. The card itself draws the highlight, since the menu is
    still being rendered underneath this state.
    """

    def enter(
        self,
        cards: List[Any],
        on_selected: Callable[[Any], None],
        on_cancel: Callable[[], None],
    ) -> None:
        self.cards = cards
        self.on_selected = on_selected
        self.on_cancel = on_cancel

        self.selectable = [
            index for index, card in enumerate(cards) if not card.character.dead
        ]
        self.current = self.selectable[0] if self.selectable else 0
        self._mark()

        # Only a mouse that actually moved may take the selection over.
        # Without this the pointer sitting still on one card would snap
        # the highlight back every frame and the arrow keys would be
        # unable to move it anywhere.
        self._last_mouse = pygame.mouse.get_pos()

    def exit(self) -> None:
        for card in self.cards:
            card.selected = False

    def _mark(self) -> None:
        for index, card in enumerate(self.cards):
            card.selected = index == self.current

    def _step(self, offset: int) -> None:
        if not self.selectable:
            return

        position = self.selectable.index(self.current)
        self.current = self.selectable[(position + offset) % len(self.selectable)]
        self._mark()
        settings.SOUNDS["blip"].stop()
        settings.SOUNDS["blip"].play()

    def _confirm(self) -> None:
        if not self.selectable:
            return

        card = self.cards[self.current]
        self.state_machine.pop()
        self.on_selected(card.character)

    def _cancel(self) -> None:
        self.state_machine.pop()
        self.on_cancel()

    def update(self, dt: float) -> None:
        position = pygame.mouse.get_pos()

        if position != self._last_mouse:
            self._last_mouse = position
            self._point_at(position)

    def on_input(self, input_id: str, input_data: Any) -> None:
        if input_id == "click":
            if input_data.released and self._point_at(input_data.position):
                self._confirm()
            return

        if not input_data.pressed:
            return

        if input_id in ("move_left", "move_up"):
            self._step(-1)
        elif input_id in ("move_right", "move_down"):
            self._step(1)
        elif input_id == "enter":
            self._confirm()
        elif input_id in ("space", "party_menu"):
            self._cancel()

    def _point_at(self, window_position: Any) -> bool:
        """Moves the selection to whichever card the mouse is over.

        :returns: Whether the mouse was over a selectable card at all.
        """
        position = settings.to_virtual(window_position)

        for index in self.selectable:
            if self.cards[index].contains(position):
                if index != self.current:
                    self.current = index
                    self._mark()

                return True

        return False

    def render(self, surface: pygame.Surface) -> None:
        if self.selectable:
            card = self.cards[self.current]
            cursor = settings.TEXTURES["cursor-up"]
            surface.blit(
                cursor,
                (
                    card.rect.centerx - cursor.get_width() // 2,
                    card.rect.bottom + 2,
                ),
            )

        Text(
            HINT,
            settings.FONTS["small"],
            settings.VIRTUAL_WIDTH // 2,
            HINT_Y,
            (255, 210, 60),
            center=True,
        ).render(surface)
