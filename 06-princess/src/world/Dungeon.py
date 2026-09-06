"""
ISPPV1 2023
Study Case: The Legend of the Princess (ARPG)

Author: Alejandro Mujica
alejandro.j.mujic4@gmail.com

This file contains the class Dungeon.
"""

import math
import random
from typing import Callable, TypeVar

import pygame

from gale.timer import Timer

import settings
from src.world.Room import Room


class Dungeon:
    def __init__(
        self,
        player: TypeVar("Player"),
        on_game_over: Callable[[], None],
    ) -> None:
        self.player = player
        self.on_game_over = on_game_over

        # Set once the chest has been placed in some room (regardless of
        # whether the player has opened it yet), so no later room ever
        # rolls to spawn a second one. Read directly as self.dungeon by
        # Room, rather than through a chain like
        # player.state_machine.current.dungeon, which only holds up for
        # whichever player state happens to be active when it's checked.
        self.chest_appeared = False

        # Current room we're operating in.
        self.current_room = Room(self.player, self.on_game_over, dungeon=self)

        # Room we're moving the camera to during a shift; becomes the
        # active room afterwards.
        self.next_room = None

        # Translation offsets, only used while shifting screens.
        self.camera_x = 0
        self.camera_y = 0
        self.shifting = False

    def begin_shifting(self, shift_x: float, shift_y: float) -> None:
        """
        Prepares for the camera shifting process, kicking off a tween of the
        camera position. Triggered via a doorway collision, from
        PlayerWalkState/PlayerPotWalkState.
        """
        self.shifting = True

        # Every room transition in the game funnels through here -- both
        # PlayerWalkState._check_doorways and PlayerPotWalkState's copy of
        # it call this and nothing else -- so this is the one place the
        # boss room has to be rolled for, instead of the same roll and the
        # same flag written twice over in the two walk states. shift_x and
        # shift_y already say which of the new room's doors the player
        # will step out of, so there is nothing extra to thread through
        # either.
        entry_direction = self._entry_direction_for(shift_x, shift_y)

        # Gated on the bow, and not only on the roll: the mage is the one
        # fight in the dungeon that is not meant to be won on the sword
        # alone -- arrows are what stagger him (Boss.stun) -- so sending a
        # player who has not found the chest yet into a room that locks
        # its doors behind them would just be a dead end. The chest is
        # itself only ever placed in a regular room, since a boss room
        # skips _generate_objects entirely, so the two can never deadlock
        # each other.
        is_boss = self.player.has_bow and random.random() < settings.BOSS_ROOM_CHANCE

        self.next_room = Room(
            self.player,
            self.on_game_over,
            dungeon=self,
            is_boss=is_boss,
            entry_direction=entry_direction,
        )

        # Start all doors in next room as open until we get in.
        for doorway in self.next_room.doorways:
            doorway.open = True

        self.next_room.adjacent_offset_x = shift_x
        self.next_room.adjacent_offset_y = shift_y

        player_x, player_y = self.player.x, self.player.y

        if shift_x > 0:
            player_x = settings.VIRTUAL_WIDTH + (
                settings.MAP_RENDER_OFFSET_X + settings.TILE_SIZE
            )
        elif shift_x < 0:
            player_x = -settings.VIRTUAL_WIDTH + (
                settings.MAP_RENDER_OFFSET_X
                + settings.MAP_WIDTH * settings.TILE_SIZE
                - settings.TILE_SIZE
                - self.player.width
            )
        elif shift_y > 0:
            player_y = settings.VIRTUAL_HEIGHT + (
                settings.MAP_RENDER_OFFSET_Y + self.player.height / 2
            )
        else:
            player_y = -settings.VIRTUAL_HEIGHT + settings.MAP_RENDER_OFFSET_Y + (
                settings.MAP_HEIGHT * settings.TILE_SIZE
                - settings.TILE_SIZE
                - self.player.height
            )

        # Tween the camera in whichever direction the new room is in, as
        # well as the player to be at the opposite door in the next room,
        # walking through the wall (whose art will cover them there).
        to_tween = [
            (self, {"camera_x": shift_x, "camera_y": shift_y}),
            (self.player, {"x": player_x, "y": player_y}),
        ]

        pot = getattr(self.player.state_machine.current, "pot", None)

        if pot is not None:
            to_tween.append((pot, {"x": player_x, "y": player_y - pot.height / 2}))

        Timer.tween(1, to_tween, on_finish=self._finish_shifting_and_place_player)

    @staticmethod
    def _entry_direction_for(shift_x: float, shift_y: float) -> str:
        """
        :returns: The doorway of the room being entered that the player
            comes out of. Walking right, into the room to the east, drops
            them at that room's *left* door, and so on -- the mirror of
            the direction they were travelling in.
        """
        if shift_x > 0:
            return "left"

        if shift_x < 0:
            return "right"

        if shift_y > 0:
            return "top"

        return "bottom"

    def _finish_shifting_and_place_player(self) -> None:
        shift_x = self.camera_x
        shift_y = self.camera_y

        self._finish_shifting()

        # Reset player to the correct location in the room.
        if shift_x < 0:
            self.player.x = (
                settings.MAP_RENDER_OFFSET_X
                + settings.MAP_WIDTH * settings.TILE_SIZE
                - settings.TILE_SIZE
                - self.player.width
            )
            self.player.direction = "left"
        elif shift_x > 0:
            self.player.x = settings.MAP_RENDER_OFFSET_X + settings.TILE_SIZE
            self.player.direction = "right"
        elif shift_y < 0:
            self.player.y = (
                settings.MAP_RENDER_OFFSET_Y
                + settings.MAP_HEIGHT * settings.TILE_SIZE
                - settings.TILE_SIZE
                - self.player.height
            )
            self.player.direction = "up"
        else:
            self.player.y = settings.MAP_RENDER_OFFSET_Y + self.player.height / 2
            self.player.direction = "down"

        # Close all doors in the room we just entered (self.current_room
        # was just swapped to it by _finish_shifting above) — they were
        # only forced open so the player could visually walk through the
        # wall opening during the transition.
        for doorway in self.current_room.doorways:
            doorway.open = False

        # ...except, in the mage's room, the one the player just came
        # through: the fight is a room the player is locked into, but
        # never a trap, since the way back out is the way they came in.
        # The other three stay shut for good -- putting him down ends the
        # run outright (Room._on_boss_defeated), so there is nothing left
        # behind them worth opening them for.
        if self.current_room.is_boss:
            self.current_room.doorway_for(self.current_room.entry_direction).open = True

        # Avoid receiving damage right as we enter the new room.
        self.player.go_invulnerable(1)

        settings.SOUNDS["door"].play()

    def _finish_shifting(self) -> None:
        """
        Resets a few variables needed to perform a camera shift and swaps
        the next and current room.
        """
        self.camera_x = 0
        self.camera_y = 0
        self.shifting = False
        self.current_room = self.next_room
        self.next_room = None
        self.current_room.adjacent_offset_x = 0
        self.current_room.adjacent_offset_y = 0

    def update(self, dt: float) -> None:
        # Pause updating if we're in the middle of shifting.
        if not self.shifting:
            self.current_room.update(dt)
        else:
            # Still update the player animation if we're shifting rooms.
            if self.player.current_animation:
                self.player.current_animation.update(dt)

    def render(self, surface: pygame.Surface) -> None:
        # Applied directly to every draw call (rather than composited
        # through an intermediate surface) so a room positioned a full
        # screen away by its adjacent offset isn't clipped away by an
        # equally screen-sized buffer before the camera pans over to it.
        offset_x = -math.floor(self.camera_x)
        offset_y = -math.floor(self.camera_y)

        self.current_room.render(surface, offset_x, offset_y)

        if self.next_room:
            self.next_room.render(surface, offset_x, offset_y)
