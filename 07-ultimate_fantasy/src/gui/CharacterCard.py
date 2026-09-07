"""
ISPPV1 2023
Study Case: Ultimate Fantasy (RPG)

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains the class CharacterCard: the boxed read out of one
party member shown by the party menu.
"""

from typing import Any, Callable, Dict, List, Optional

import pygame

from gale.text import Text
from gale.ui.container import Container
from gale.ui.progress_bar import ProgressBar

import settings
from src.definitions.entity import DEFAULT_CHARACTER_FRAME
from src.gui.ActionRow import ActionRow
from src.gui.Panel import Panel
from src.gui.theme import BAR_THEME

CARD_WIDTH = 92
CARD_HEIGHT = 130

PAD = 5
SPRITE_WIDTH = 16
SPRITE_HEIGHT = 18

BAR_WIDTH = CARD_WIDTH - PAD * 2
BAR_HEIGHT = 4

HP_COLOR = pygame.Color(189, 32, 32)
EXP_COLOR = pygame.Color(32, 32, 189)

LABEL_COLOR = (255, 255, 255)
DIM_COLOR = (150, 150, 150)
DEAD_COLOR = (215, 90, 90)
DIVIDER_COLOR = (110, 110, 110)
SELECTED_COLOR = (255, 210, 60)

# Vertical offsets inside the card, all relative to its own top edge.
NAME_Y = 5
LEVEL_Y = 16
HP_LABEL_Y = 30
HP_BAR_Y = 40
EXP_LABEL_Y = 48
EXP_BAR_Y = 58
MAGIC_Y = 66
DIVIDER_Y = 78
ACTIONS_LABEL_Y = 82
ACTIONS_Y = 94
ACTION_ROW_HEIGHT = 11
ACTION_ROW_SPACING = 12


class CharacterCard(Container):
    """
    One party member's own box: portrait, name, level, HP and experience
    bars, magic, and the list of actions the character can perform.

    It is a Container rather than a lump of draw calls so the action
    lines inside it are real widgets. Container hit tests its children
    back to front and stops at the first one that takes the click, which
    is exactly the layering the menu needs: the card swallows clicks that
    land on it, and a click that lands on a usable action reaches that
    action.

    render is overridden instead of leaning on Container's, which just
    draws children in order, because the stats have to be painted between
    the panel underneath and the action rows on top.
    """

    def __init__(
        self,
        x: float,
        y: float,
        character: Any,
        on_action: Optional[Callable[[Any, Dict[str, Any]], None]] = None,
    ) -> None:
        super().__init__(x, y, CARD_WIDTH, CARD_HEIGHT)
        self.character = character
        self.on_action = on_action

        # Drawn by this class' own render, not added as a child, so the
        # stats can go on top of it. It is only here to paint the box.
        self.panel = Panel(x, y, CARD_WIDTH, CARD_HEIGHT)

        self.hp_bar = ProgressBar(
            x + PAD,
            y + HP_BAR_Y,
            BAR_WIDTH,
            BAR_HEIGHT,
            value=character.current_hp,
            max_value=character.hp,
            color=HP_COLOR,
            theme=BAR_THEME,
        )
        self.exp_bar = ProgressBar(
            x + PAD,
            y + EXP_BAR_Y,
            BAR_WIDTH,
            BAR_HEIGHT,
            value=character.current_exp,
            max_value=character.exp_to_level,
            color=EXP_COLOR,
            theme=BAR_THEME,
        )

        self.action_rows: List[ActionRow] = []

        for i, action in enumerate(character.actions):
            row = ActionRow(
                x + PAD,
                y + ACTIONS_Y + i * ACTION_ROW_SPACING,
                BAR_WIDTH,
                ACTION_ROW_HEIGHT,
                action,
                on_click=self._on_row_clicked,
                # Attacking a townsperson is not a thing, so out here only
                # the healing actions are live. The rest are listed faded,
                # which is what the brief asks the panel to show.
                enabled=bool(action.get("heals", False)) and not character.dead,
            )
            self.action_rows.append(row)
            self.add_child(row)

        # Raised by the menu while this card is the one being pointed at
        # during a single target heal.
        self.selected = False

    def _on_row_clicked(self, action: Dict[str, Any]) -> None:
        if self.on_action is not None:
            self.on_action(self.character, action)

    def refresh(self) -> None:
        """Pulls the bars back in line with the character after a heal."""
        self.hp_bar.value = self.character.current_hp
        self.hp_bar.max_value = self.character.hp
        self.exp_bar.value = self.character.current_exp
        self.exp_bar.max_value = self.character.exp_to_level

    def render(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return

        self.panel.render(surface)

        if self.selected:
            pygame.draw.rect(surface, SELECTED_COLOR, self.rect, 2, border_radius=3)

        self._render_header(surface)
        self._render_stats(surface)

        pygame.draw.line(
            surface,
            DIVIDER_COLOR,
            (self.rect.x + PAD, self.rect.y + DIVIDER_Y),
            (self.rect.right - PAD, self.rect.y + DIVIDER_Y),
        )
        self._text("Actions", self.rect.x + PAD, self.rect.y + ACTIONS_LABEL_Y, DIM_COLOR).render(
            surface
        )

        for row in self.action_rows:
            row.render(surface)

    def _render_header(self, surface: pygame.Surface) -> None:
        character = self.character

        surface.blit(
            settings.TEXTURES[character.texture],
            (self.rect.x + PAD, self.rect.y + NAME_Y - 1),
            settings.frame(character.texture, DEFAULT_CHARACTER_FRAME),
        )

        text_x = self.rect.x + PAD + SPRITE_WIDTH + 4
        color = DEAD_COLOR if character.dead else LABEL_COLOR
        self._text(character.name, text_x, self.rect.y + NAME_Y, color).render(surface)

        subtitle = "KO" if character.dead else f"Lv {character.level} {character.klass}"
        self._text(subtitle, text_x, self.rect.y + LEVEL_Y, DIM_COLOR).render(surface)

    def _render_stats(self, surface: pygame.Surface) -> None:
        character = self.character

        self._text(
            f"HP {int(character.current_hp)}/{int(character.hp)}",
            self.rect.x + PAD,
            self.rect.y + HP_LABEL_Y,
            LABEL_COLOR,
        ).render(surface)
        self.hp_bar.render(surface)

        self._text(
            f"EXP {int(character.current_exp)}/{int(character.exp_to_level)}",
            self.rect.x + PAD,
            self.rect.y + EXP_LABEL_Y,
            LABEL_COLOR,
        ).render(surface)
        self.exp_bar.render(surface)

        self._text(
            f"Magic {int(character.magic)}   Atk {int(character.attack)}",
            self.rect.x + PAD,
            self.rect.y + MAGIC_Y,
            LABEL_COLOR,
        ).render(surface)

    @staticmethod
    def _text(value: str, x: float, y: float, color) -> Text:
        return Text(value, settings.FONTS["small"], x, y, color)
