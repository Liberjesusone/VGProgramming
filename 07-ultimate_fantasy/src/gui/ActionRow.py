"""
ISPPV1 2023
Study Case: Ultimate Fantasy (RPG)

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains the class ActionRow: one line of a character card
listing a single action the character owns.
"""

from typing import Any, Callable, Dict, Optional, Tuple

import pygame

from gale.input_handler import MouseClickData
from gale.text import Text
from gale.ui.widget import Widget

import settings

# How washed out an action that cannot be used right now is drawn. Low
# enough to read as disabled at a glance, high enough that the name is
# still legible, since the point is to show what the character can do in
# battle, not to hide it.
DISABLED_OPACITY = 90

TEXT_COLOR = (255, 255, 255)
HEAL_COLOR = (150, 235, 150)
HOVER_COLOR = (86, 86, 86)


class ActionRow(Widget):
    """
    A clickable line showing one action's name.

    Out in the overworld the only thing that makes sense to use is
    healing, so every other action is drawn faded and ignores the mouse.
    That is the whole reason this is a widget instead of a plain string
    drawn by the card: enabled already means "reacts to input" for every
    gale.ui widget, so the transparency and the click handling end up
    driven by the same flag.
    """

    def __init__(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        action: Dict[str, Any],
        on_click: Optional[Callable[[Dict[str, Any]], None]] = None,
        enabled: bool = True,
    ) -> None:
        super().__init__(x, y, width, height)
        self.action = action
        self.on_click = on_click
        self.enabled = enabled
        self.focusable = enabled

    @property
    def heals(self) -> bool:
        return bool(self.action.get("heals", False))

    def render(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return

        if self.enabled and self.hovered:
            pygame.draw.rect(surface, HOVER_COLOR, self.rect)

        color = HEAL_COLOR if self.heals else TEXT_COLOR
        label = Text(
            self.action["name"],
            settings.FONTS["small"],
            self.rect.x + 2,
            self.rect.y + 1,
            color,
        )

        if self.enabled:
            label.render(surface)
            return

        # A Text draws straight onto whatever surface it is given, and a
        # per blit alpha is not something blit takes, so the faded rows go
        # through a scratch surface that can carry one.
        scratch = pygame.Surface((int(self.width), int(self.height)), pygame.SRCALPHA)
        label.x, label.y = 2, 1
        label.render(scratch)
        scratch.set_alpha(DISABLED_OPACITY)
        surface.blit(scratch, (self.rect.x, self.rect.y))

    def on_mouse_click(
        self, position: Tuple[float, float], data: MouseClickData
    ) -> bool:
        if not self.enabled or not self.contains(position):
            return False

        if data.released and self.on_click is not None:
            self.on_click(self.action)

        return True

    def on_confirm(self) -> bool:
        if not self.enabled or self.on_click is None:
            return False

        self.on_click(self.action)
        return True
