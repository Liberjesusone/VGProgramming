"""
ISPPV1 2023
Study Case: Ultimate Fantasy (RPG)

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains the class PartyMenuState: the overworld status screen,
with a card per party member and the two ways of healing them.
"""

from typing import Any, Dict, List, Optional

import pygame

from gale.state import BaseState
from gale.text import Text
from gale.ui.button import Button
from gale.ui.container import Container
from gale.ui.theme import Theme

import settings
from src.gui.Backdrop import Backdrop
from src.gui.CharacterCard import CARD_HEIGHT, CARD_WIDTH, CharacterCard

CARDS_Y = 24
CARD_GAP = 4

BUTTON_WIDTH = 110
BUTTON_HEIGHT = 22
BUTTON_GAP = 8
BUTTONS_Y = 164

TITLE_Y = 6
HINT_Y = 192
MESSAGE_Y = 206

# How long a heal result stays on screen before fading out of the way.
MESSAGE_TIME = 2.5

HINT = "Arrows move, Enter uses, I or Space closes. The mouse works too."

# The shared DEFAULT_THEME leaves hover and focus at gale's own defaults,
# which are a blue grey and a bright yellow: fine on a light widget, but
# here they sit next to white text on a dark panel. These keep the same
# palette the rest of the game uses and only change how much the button
# lights up.
BUTTON_THEME = Theme(
    font=settings.FONTS["small"],
    text_color=pygame.Color(255, 255, 255),
    background_color=pygame.Color(56, 56, 56),
    border_color=pygame.Color(255, 255, 255),
    border_width=2,
    hover_color=pygame.Color(92, 92, 92),
    focus_color=pygame.Color(120, 90, 40),
    disabled_color=pygame.Color(120, 120, 120),
    padding=3,
)


class PartyMenuState(BaseState):
    """
    Pushed over PlayState, which keeps drawing the frozen town under the
    backdrop while this is on top.

    Everything on screen hangs off a single root Container: the backdrop
    at the bottom, then a card per party member, then the two heal
    buttons. Mouse events are handed to that root and it does the rest,
    hit testing back to front and stopping at the first widget that takes
    the event, so a click on a heal line inside a card never also counts
    as a click on the card behind it.
    """

    def enter(self, world: Any) -> None:
        self.world = world
        self.party = world.party
        self.message: Optional[str] = None
        self.message_timer = 0.0

        total_width = CARD_WIDTH * 4 + CARD_GAP * 3
        first_x = (settings.VIRTUAL_WIDTH - total_width) // 2

        self.cards: List[CharacterCard] = []

        for slot, key in enumerate(sorted(self.party.characters.keys())):
            card = CharacterCard(
                first_x + slot * (CARD_WIDTH + CARD_GAP),
                CARDS_Y,
                self.party.characters[key],
                on_action=self._use_action,
            )
            self.cards.append(card)

        buttons_width = BUTTON_WIDTH * 2 + BUTTON_GAP
        buttons_x = (settings.VIRTUAL_WIDTH - buttons_width) // 2

        self.heal_one_button = Button(
            buttons_x,
            BUTTONS_Y,
            BUTTON_WIDTH,
            BUTTON_HEIGHT,
            "Heal one",
            on_click=self._heal_one,
            theme=BUTTON_THEME,
        )
        self.heal_all_button = Button(
            buttons_x + BUTTON_WIDTH + BUTTON_GAP,
            BUTTONS_Y,
            BUTTON_WIDTH,
            BUTTON_HEIGHT,
            "Heal everyone",
            on_click=self._heal_all,
            theme=BUTTON_THEME,
        )
        self.buttons = [self.heal_one_button, self.heal_all_button]

        self.root = Container(
            0,
            0,
            settings.VIRTUAL_WIDTH,
            settings.VIRTUAL_HEIGHT,
            children=[
                Backdrop(0, 0, settings.VIRTUAL_WIDTH, settings.VIRTUAL_HEIGHT),
                *self.cards,
                *self.buttons,
            ],
        )

        self.focus_index = 0
        self._refresh_buttons()

        # Last window position the hover was resolved for. Hovering is
        # read from pygame every frame rather than bound as an input
        # action (see settings), and comparing against this keeps it from
        # being recomputed while the mouse sits still.
        self._last_mouse = None

    # -- healing ---------------------------------------------------------

    def _healer(self) -> Optional[Any]:
        """The living party member who can cast heals. Nothing else in the
        game is allowed to heal, so with the healer down both buttons go
        dead."""
        for key in sorted(self.party.characters.keys()):
            character = self.party.characters[key]

            if character.dead:
                continue

            if any(action.get("heals") for action in character.actions):
                return character

        return None

    def _heal_action(self, healer: Any, require_target: bool) -> Optional[Dict[str, Any]]:
        for action in healer.actions:
            if action.get("heals") and action["require_target"] == require_target:
                return action

        return None

    def _refresh_buttons(self) -> None:
        healer = self._healer()
        self.heal_one_button.enabled = healer is not None and self._heal_action(healer, True) is not None
        self.heal_all_button.enabled = healer is not None and self._heal_action(healer, False) is not None
        self._apply_focus()

    def _apply_focus(self) -> None:
        for index, button in enumerate(self.buttons):
            button.focused = button.enabled and index == self.focus_index

    def _use_action(self, character: Any, action: Dict[str, Any]) -> None:
        """Fired when a heal line inside a card is clicked. Only the
        healer's own lines are ever enabled, so the character passed in is
        always the one casting."""
        if action["require_target"]:
            self._pick_target(character, action)
        else:
            self._cast_on_everyone(character, action)

    def _heal_one(self) -> None:
        healer = self._healer()
        action = self._heal_action(healer, True) if healer is not None else None

        if action is not None:
            self._pick_target(healer, action)

    def _heal_all(self) -> None:
        healer = self._healer()
        action = self._heal_action(healer, False) if healer is not None else None

        if action is not None:
            self._cast_on_everyone(healer, action)

    def _pick_target(self, healer: Any, action: Dict[str, Any]) -> None:
        from src.states.game.SelectHealTargetState import SelectHealTargetState

        self.state_machine.push(
            SelectHealTargetState(self.state_machine),
            cards=self.cards,
            on_selected=lambda target: self._cast_on(healer, action, target),
            on_cancel=lambda: None,
        )

    def _cast_on(self, healer: Any, action: Dict[str, Any], target: Any) -> None:
        # Same call the battle makes: the action carries its own formula
        # and its own strength, so healing out here cannot drift away from
        # healing in a fight.
        amount = action["func"](healer, target, action.get("strength"))
        settings.SOUNDS[action["sound_effect"]].play()
        self._after_heal(f"{healer.name} healed {target.name} for {amount} HP.")

    def _cast_on_everyone(self, healer: Any, action: Dict[str, Any]) -> None:
        targets = [
            character for character in self.party.characters.values() if not character.dead
        ]

        if not targets:
            return

        amount = action["func"](healer, targets, action.get("strength"))
        settings.SOUNDS[action["sound_effect"]].play()
        self._after_heal(f"{healer.name} healed the whole party for {amount} HP each.")

    def _after_heal(self, message: str) -> None:
        for card in self.cards:
            card.refresh()

        self.message = message
        self.message_timer = MESSAGE_TIME

        # Healing is progress, so a save made after it is worth making.
        self.world.dirty = True

    # -- BaseState -------------------------------------------------------

    def close(self) -> None:
        self.state_machine.pop()

    def _is_top(self) -> bool:
        """Whether nothing is covering this menu right now.

        The stack renders every state it holds, so while the heal target
        picker is open this one is still drawing. Both want the same line
        at the bottom of the screen for their own prompt, and the picker's
        is the one that matters then, so this menu steps aside.
        """
        return self.state_machine.states[-1] is self

    def update(self, dt: float) -> None:
        self._track_mouse()
        self.root.update(dt)

        if self.message_timer > 0:
            self.message_timer -= dt

            if self.message_timer <= 0:
                self.message = None

    def _track_mouse(self) -> None:
        position = pygame.mouse.get_pos()

        if position == self._last_mouse:
            return

        self._last_mouse = position
        self.root.on_mouse_motion(settings.to_virtual(position))

    def on_input(self, input_id: str, input_data: Any) -> None:
        if input_id == "click":
            self.root.on_mouse_click(settings.to_virtual(input_data.position), input_data)
            return

        if not input_data.pressed:
            return

        if input_id in ("party_menu", "space"):
            self.close()
        elif input_id == "move_left":
            self._move_focus(-1)
        elif input_id == "move_right":
            self._move_focus(1)
        elif input_id == "enter":
            self.buttons[self.focus_index].on_confirm()

    def _move_focus(self, offset: int) -> None:
        self.focus_index = (self.focus_index + offset) % len(self.buttons)
        self._apply_focus()
        settings.SOUNDS["blip"].stop()
        settings.SOUNDS["blip"].play()

    def render(self, surface: pygame.Surface) -> None:
        self.root.render(surface)

        Text(
            "Party",
            settings.FONTS["medium"],
            settings.VIRTUAL_WIDTH // 2,
            TITLE_Y,
            (255, 255, 255),
            center=True,
            shadowed=True,
        ).render(surface)

        if self._is_top():
            Text(
                HINT,
                settings.FONTS["small"],
                settings.VIRTUAL_WIDTH // 2,
                HINT_Y,
                (170, 170, 170),
                center=True,
            ).render(surface)

        if self.message is not None:
            Text(
                self.message,
                settings.FONTS["small"],
                settings.VIRTUAL_WIDTH // 2,
                MESSAGE_Y,
                (150, 235, 150),
                center=True,
            ).render(surface)
