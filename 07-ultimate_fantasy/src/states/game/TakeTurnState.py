"""
ISPPV1 2023
Study Case: Ultimate Fantasy (RPG)

Author: Alejandro Mujica
alejandro.j.mujic4@gmail.com

Turn order rewritten by Liber Jesus Puccini (liberjesusone@gmail.com):
rounds used to be a fixed loop, every party member in slot order and then
every enemy in list order. Now each battle entity has to rest for its own
number of seconds after acting, and whoever finishes resting first takes
the next turn, so a fast fighter simply gets more turns than a slow one.

This file contains the class TakeTurnState: the clock the whole battle
runs on, plus the victory (experience and level up) and defeat flows,
which are unchanged.
"""

import math
import random
from typing import Any, List, Optional

import pygame

from gale.state import BaseState
from gale.timer import Timer

import settings
from src.entity.Character import Character


class TakeTurnState(BaseState):
    """
    Advances every entity's rest timer and hands the turn to the first one
    that finishes.

    The clock only runs while this state is on top of the stack, and that
    is exactly the behaviour the mechanic needs. gale.state.StateStack
    updates the top state and nothing else, so the moment a turn pushes a
    menu or a message the timers stop dead and only start again once the
    player has answered. Thinking time is free: waiting on the action menu
    never charges anyone else's recovery, and the seconds that count are
    the ones the battle itself is actually spending.
    """

    def enter(self, battle_state: Any) -> None:
        self.battle_state = battle_state

        # Set once the battle is decided, so a stray frame between the
        # last blow and the fade cannot hand out one more turn.
        self.finished = False

        # A random slice of each entity's own rest is treated as already
        # served, so the opening turns arrive spread out instead of the
        # whole board acting on the very first frame it becomes ready.
        for entity in self._battle_entities():
            entity.start_random_rest()

    # -- the clock -------------------------------------------------------

    def _battle_entities(self) -> List[Any]:
        keys = sorted(self.battle_state.party.characters.keys())
        characters = [self.battle_state.party.characters[key] for key in keys]
        return characters + list(self.battle_state.enemies)

    def update(self, dt: float) -> None:
        for enemy in self.battle_state.enemies:
            if not enemy.dead:
                enemy.update(dt)

        if self.finished:
            return

        actor = self._advance_clock(dt)

        if actor is not None:
            self._take_turn(actor)

    def _advance_clock(self, dt: float) -> Optional[Any]:
        """
        :returns: The entity whose turn it is now, or None if nobody has
            finished resting yet. When several are ready at once the one
            that has been waiting longest past its own rest time goes
            first, which keeps a fast entity from being starved by a slow
            one that happened to come up in the same frame.
        """
        ready = []

        for entity in self._battle_entities():
            if entity.dead:
                continue

            entity.rest(dt)

            if entity.is_rested():
                ready.append(entity)

        if not ready:
            return None

        return max(ready, key=lambda entity: entity.rest_timer - entity.rest_time)

    def _take_turn(self, entity: Any) -> None:
        # Back of the queue right away, before the turn is even resolved,
        # so a menu left open on screen cannot let the same entity come up
        # again the frame after it closes.
        entity.start_rest()

        if isinstance(entity, Character):
            self._character_turn(entity)
        else:
            self._enemy_turn(entity)

    def _after_action(self) -> None:
        """Called once a turn has fully played out. Nothing else to do
        when the battle is still going: update simply picks the clock back
        up on the next frame."""
        if all(enemy.dead for enemy in self.battle_state.enemies):
            self.finished = True
            self._victory()
        elif all(
            character.dead for character in self.battle_state.party.characters.values()
        ):
            self.finished = True
            self._faint()

    # -- party turns -----------------------------------------------------

    def _character_turn(self, character: Any) -> None:
        from src.states.game.BattleMessageState import BattleMessageState

        self.state_machine.push(
            BattleMessageState(self.state_machine),
            battle_state=self.battle_state,
            message=f"Turn for {character.name}! Select an action.",
            on_close=lambda: self._prompt_action(character),
        )

    def _prompt_action(self, character: Any) -> None:
        from src.states.game.SelectActionState import SelectActionState

        self.state_machine.push(
            SelectActionState(self.state_machine),
            battle_state=self.battle_state,
            entity=character,
            on_action_selected=self._after_action,
        )

    # -- enemy turns -----------------------------------------------------

    def _enemy_turn(self, enemy: Any) -> None:
        """
        The boss used to get extra swings through a counter that let it
        act again without giving up its turn. It does not need one any
        more: its rest time is roughly half of everything else's, so the
        clock hands it about two turns per turn of the party's on its own.
        """
        action = random.choice(enemy.actions)

        if action["target_type"] == "enemy":
            targets = list(self.battle_state.party.characters.values())
            target_label = "you"
        else:
            targets = self.battle_state.enemies
            target_label = "them"

        if action["require_target"]:
            alive = [target for target in targets if not target.dead]
            target = random.choice(alive)
            amount = action["func"](enemy, target, action.get("strength"))
            settings.SOUNDS[action["sound_effect"]].play()
            Timer.tween(0.5, [(target.energy_bar, {"value": target.current_hp})])
            message = (
                f"{enemy.name} used {action['name']} for {amount} HP on {target.name}."
            )
        else:
            alive_targets = [target for target in targets if not target.dead]
            amount = action["func"](enemy, alive_targets, action.get("strength"))
            settings.SOUNDS[action["sound_effect"]].play()

            for target in alive_targets:
                Timer.tween(0.5, [(target.energy_bar, {"value": target.current_hp})])

            message = (
                f"{enemy.name} used {action['name']} for {amount} HP on all of "
                f"{target_label}."
            )

        if all(
            character.dead for character in self.battle_state.party.characters.values()
        ):
            self.finished = True
            self._faint()
            return

        from src.states.game.BattleMessageState import BattleMessageState

        self.state_machine.push(
            BattleMessageState(self.state_machine),
            battle_state=self.battle_state,
            message=message,
            on_close=self._after_action,
        )

    # -- victory / experience --------------------------------------------

    def _victory(self) -> None:
        settings.stop_music("battle")
        self._victory_channel = settings.SOUNDS["victory"].play(loops=-1)

        from src.states.game.BattleMessageState import BattleMessageState

        self.state_machine.push(
            BattleMessageState(self.state_machine),
            battle_state=self.battle_state,
            message="Victory!",
            on_close=self._start_exp,
        )

    def _start_exp(self) -> None:
        total_level = sum(enemy.level for enemy in self.battle_state.enemies)
        num_characters = len(self.battle_state.party.characters)
        opponent_level = total_level / num_characters
        self._inc_exp(0, opponent_level)

    def _party_keys(self):
        return sorted(self.battle_state.party.characters.keys())

    def _inc_exp(self, index: int, opponent_level: float) -> None:
        keys = self._party_keys()

        if index >= len(keys):
            self._fade_out()
            return

        character = self.battle_state.party.characters[keys[index]]

        if character.dead:
            self._inc_exp(index + 1, opponent_level)
            return

        exp = math.ceil(
            (character.hpiv + character.attackiv + character.defenseiv + character.magiciv)
            * opponent_level
        )

        from src.states.game.BattleMessageState import BattleMessageState

        self.state_machine.push(
            BattleMessageState(self.state_machine),
            battle_state=self.battle_state,
            message=f"{character.name} earned {exp} experience points!",
            on_close=None,
            can_input=False,
        )
        Timer.after(1.5, lambda: self._apply_exp(character, exp, index, opponent_level))

    def _apply_exp(
        self, character: Any, exp: int, index: int, opponent_level: float
    ) -> None:
        settings.SOUNDS["exp"].play()
        new_value = min(character.current_exp + exp, character.exp_to_level)
        Timer.tween(
            0.5,
            [(character.exp_bar, {"value": new_value})],
            on_finish=lambda: self._exp_applied(character, exp, index, opponent_level),
        )

    def _exp_applied(
        self, character: Any, exp: int, index: int, opponent_level: float
    ) -> None:
        # Pops the can_input=False experience-gain message, which never
        # auto-closes on its own.
        self.state_machine.pop()
        character.current_exp += exp

        if character.current_exp >= character.exp_to_level:
            settings.SOUNDS["levelup"].play()
            character.current_exp -= character.exp_to_level
            last_level = character.level
            increases = character.level_up()
            hp_increase = increases[0]
            Timer.tween(
                0.5, [(character.energy_bar, {"value": character.current_hp - hp_increase})]
            )

            from src.states.game.BattleMessageState import BattleMessageState

            message = (
                f"Congratulations! {character.name} advanced from level "
                f"{last_level} level {character.level}!"
            )
            self.state_machine.push(
                BattleMessageState(self.state_machine),
                battle_state=self.battle_state,
                message=message,
                on_close=lambda: self._show_stats(character, increases, index, opponent_level),
            )
        else:
            self._inc_exp(index + 1, opponent_level)

    def _show_stats(self, character: Any, increases: Any, index: int, opponent_level: float) -> None:
        from src.states.game.StatsMenuState import StatsMenuState

        self.state_machine.push(
            StatsMenuState(self.state_machine),
            character=character,
            stats=increases,
            on_close=lambda: self._inc_exp(index + 1, opponent_level),
        )

    def _fade_out(self) -> None:
        if self._victory_channel is not None:
            self._victory_channel.stop()

        from src.states.game.FadeInState import FadeInState
        from src.states.game.FadeOutState import FadeOutState

        if self.battle_state.final_boss:

            def on_complete() -> None:
                # Pops this lingering TakeTurnState, then the BattleState
                # underneath it (matches the original's "pop twice"). The
                # second pop runs BattleState.exit(), which always calls
                # the on_exit it was pushed with (see
                # PartyWalkState._trigger_encounter). For a NORMAL battle
                # that's the whole point (it un-pauses the overworld's
                # "world"/"town" music the encounter had merely paused,
                # not stopped, so walking around resumes right where the
                # music left off), but here there's no overworld to return
                # to: the very next thing on screen is TheEndState. Without
                # silencing what that on_exit just resumed, it played
                # underneath "the-end" for the rest of the game. _victory
                # already stopped "battle" and _fade_out already stopped
                # the "victory" jingle, so this only has the resumed
                # overworld music left to clean up, but stopping "battle"
                # again too is harmless and keeps this correct even if
                # that ordering ever changes.
                self.state_machine.pop()
                self.state_machine.pop()
                settings.stop_music("battle")
                settings.stop_music("world")
                settings.stop_music("town")
                # A bare SOUNDS["the-end"].play() (the original code here)
                # starts a plain, untracked Sound channel, unlike every
                # other music cue in this game: it was never routed
                # through play_music, so nothing could stop it the same
                # way the stops above stop everything else (see
                # TheEndState's restart handler).
                settings.play_music("the-end")

                from src.states.game.TheEndState import TheEndState

                self.state_machine.push(TheEndState(self.state_machine))
                self.state_machine.push(
                    FadeOutState(self.state_machine),
                    color=(0, 0, 0),
                    time=1,
                    on_complete=lambda: None,
                )

            self.state_machine.push(
                FadeInState(self.state_machine),
                color=(0, 0, 0),
                time=3,
                on_complete=on_complete,
            )
        else:

            def on_complete() -> None:
                # Pops this lingering TakeTurnState, then the BattleState
                # underneath it (BattleState.exit() stops battle music and
                # restores the party's overworld position/music).
                self.state_machine.pop()
                self.state_machine.pop()
                self.state_machine.push(
                    FadeOutState(self.state_machine),
                    color=(255, 255, 255),
                    time=1,
                    on_complete=lambda: None,
                )

            self.state_machine.push(
                FadeInState(self.state_machine),
                color=(255, 255, 255),
                time=1,
                on_complete=on_complete,
            )

    def _faint(self) -> None:
        settings.stop_music("battle")
        settings.SOUNDS["game-over"].play()

        from src.states.game.FadeInState import FadeInState

        def on_complete() -> None:
            from src.states.game.GameOverState import GameOverState

            self.state_machine.push(GameOverState(self.state_machine))

        self.state_machine.push(
            FadeInState(self.state_machine),
            color=(0, 0, 0),
            time=1,
            on_complete=on_complete,
        )

    _victory_channel = None
