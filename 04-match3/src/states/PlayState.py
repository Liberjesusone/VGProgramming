"""
ISPPV1 2023
Study Case: Match-3

Author: Alejandro Mujica
alejandro.j.mujic4@gmail.com

This file contains the class PlayState.
"""

from typing import Dict, Any, List

import pygame

from gale.input_handler import InputData
from gale.state import BaseState
from gale.text import render_text
from gale.timer import Timer

import settings
from src.Tile import Tile


class PlayState(BaseState):
    def enter(self, **enter_params: Dict[str, Any]) -> None:
        self.level = enter_params["level"]
        self.board = enter_params["board"]
        self.score = enter_params["score"]

        # The tile currently being dragged by the mouse, or None.
        self.grabbed_tile = None

        # Current mouse position, in virtual coordinates (updated on every
        # "mouse_move" input, used to draw the grabbed tile under the cursor).
        self.mouse_x = 0
        self.mouse_y = 0

        self.active = True

        self.timer = settings.LEVEL_TIME

        self.goal_score = self.level * 1.25 * 1000

        # A surface that supports alpha to draw behind the text.
        self.text_alpha_surface = pygame.Surface((212, 136), pygame.SRCALPHA)
        pygame.draw.rect(
            self.text_alpha_surface, (56, 56, 56, 234), pygame.Rect(0, 0, 212, 136)
        )

        # A surface that supports alpha to cover the grabbed tile's original
        # cell, built once here instead of every render() call.
        self.grab_cover_surface = pygame.Surface(
            (settings.TILE_SIZE, settings.TILE_SIZE), pygame.SRCALPHA
        )
        pygame.draw.rect(
            self.grab_cover_surface,
            (0, 0, 0, 100),
            pygame.Rect(0, 0, settings.TILE_SIZE, settings.TILE_SIZE),
            border_radius=7
        )

        def decrement_timer():
            self.timer -= 1

            # Play warning sound on timer if we get low
            if self.timer <= 5:
                settings.SOUNDS["clock"].play()

        Timer.every(1, decrement_timer)

    def update(self, _: float) -> None:
        if self.timer <= 0:
            Timer.clear()
            settings.SOUNDS["game-over"].play()
            self.state_machine.change("game-over", score=self.score)

        if self.score >= self.goal_score:
            Timer.clear()
            settings.SOUNDS["next-level"].play()
            self.state_machine.change("begin", level=self.level + 1, score=self.score)

    def render(self, surface: pygame.Surface) -> None:
        # Draws every tile at its logical grid position -- this includes the
        # grabbed tile too, since we don't touch its .i/.j until it's dropped.
        self.board.render(surface)

        if self.grabbed_tile is not None:
            # Cover the tile's original cell with a semi-transparent block
            # so it reads as "lifted off the grid" instead of duplicated.
            original_pos = (
                self.grabbed_tile.x + self.board.x,
                self.grabbed_tile.y + self.board.y,
            )
            surface.blit(self.grab_cover_surface, original_pos)

            # Re-render the same tile centered on the cursor, on top of
            # everything else. Tile.render draws at (self.x + offset_x,
            # self.y + offset_y), so we compute the offset that lands it
            # exactly under the mouse instead of at its grid position.
            offset_x = self.mouse_x - settings.TILE_SIZE // 2 - self.grabbed_tile.x
            offset_y = self.mouse_y - settings.TILE_SIZE // 2 - self.grabbed_tile.y
            self.grabbed_tile.render(surface, offset_x, offset_y)

        surface.blit(self.text_alpha_surface, (16, 16))
        render_text(
            surface,
            f"Level: {self.level}",
            settings.FONTS["medium"],
            30,
            24,
            (99, 155, 255),
            shadowed=True,
        )
        render_text(
            surface,
            f"Score: {self.score}",
            settings.FONTS["medium"],
            30,
            52,
            (99, 155, 255),
            shadowed=True,
        )
        render_text(
            surface,
            f"Goal: {self.goal_score}",
            settings.FONTS["medium"],
            30,
            80,
            (99, 155, 255),
            shadowed=True,
        )
        render_text(
            surface,
            f"Timer: {self.timer}",
            settings.FONTS["medium"],
            30,
            108,
            (99, 155, 255),
            shadowed=True,
        )

    def _cell_at(self, pos_x: int, pos_y: int):
        """Convert a window-space mouse position to a (i, j) board cell,
        or None if it falls outside the board."""
        pos_x = pos_x * settings.VIRTUAL_WIDTH // settings.WINDOW_WIDTH
        pos_y = pos_y * settings.VIRTUAL_HEIGHT // settings.WINDOW_HEIGHT
        i = (pos_y - self.board.y) // settings.TILE_SIZE
        j = (pos_x - self.board.x) // settings.TILE_SIZE

        if 0 <= i < settings.BOARD_HEIGHT and 0 <= j < settings.BOARD_WIDTH:
            return i, j

        return None

    def on_input(self, input_id: str, input_data: InputData) -> None:
        if input_id == "mouse_move":
            self.mouse_x = input_data.position[0] * settings.VIRTUAL_WIDTH // settings.WINDOW_WIDTH
            self.mouse_y = input_data.position[1] * settings.VIRTUAL_HEIGHT // settings.WINDOW_HEIGHT
            return

        if not self.active:
            return

        if input_id == "click" and input_data.pressed:
            cell = self._cell_at(*input_data.position)
            if cell is not None:
                i, j = cell
                self.grabbed_tile = self.board.tiles[i][j]

        elif input_id == "click" and input_data.released and self.grabbed_tile is not None:
            tile1 = self.grabbed_tile
            self.grabbed_tile = None

            cell = self._cell_at(*input_data.position)
            if cell is None:
                return

            i2, j2 = cell

            if (i2, j2) == (tile1.i, tile1.j):
                # Released on the same cell it was grabbed from: this was
                # a click, not a drag. Activate the power-up if it is one.
                if tile1.combo_level is not None:
                    self._activate_powerup(tile1)
                return

            di = abs(i2 - tile1.i)
            dj = abs(j2 - tile1.j)

            if not (di <= 1 and dj <= 1 and di != dj):
                return

            tile2 = self.board.tiles[i2][j2]

            # Swap the LOGICAL positions first, no animation yet 
            # so calculate_matches_for can look at the
            # grid as it would be *after* the move.
            self._swap_logical(tile1, tile2)
            matches = self.board.calculate_matches_for([tile1, tile2])

            if matches is None:
                # Invalid move: undo the logical swap immediately. Nothing
                # was ever animated, so there is nothing to undo visually --
                # the tile will just render back at its original x/y since
                # self.grabbed_tile is already None.
                self._swap_logical(tile1, tile2)
                return

            # Valid move: now play the visual swap, and resolve the match
            # we already found once it finishes. tile1 is the dragged tile,
            # so it's the anchor for any power-up this match creates.
            self.active = False
            Timer.tween(
                0.25,
                [
                    (tile1, {"x": tile2.x, "y": tile2.y}),
                    (tile2, {"x": tile1.x, "y": tile1.y}),
                ],
                on_finish=lambda: self._resolve_matches(matches, moved_tile=tile1),
            )

    def _swap_logical(self, tile1, tile2) -> None:
        """Swap two tiles positions in the grid (self.board.tiles and
        their .i/.j), without render them or changing their cordinates. Calling
        this twice in a row is a no-op, the swap is its own inverse."""
        (
            self.board.tiles[tile1.i][tile1.j],
            self.board.tiles[tile2.i][tile2.j],
        ) = (
            self.board.tiles[tile2.i][tile2.j],
            self.board.tiles[tile1.i][tile1.j],
        )
        tile1.i, tile1.j, tile2.i, tile2.j = tile2.i, tile2.j, tile1.i, tile1.j

    def _resolve_matches(self, matches: List, moved_tile: Tile = None) -> None:
        settings.SOUNDS["match"].stop()
        settings.SOUNDS["match"].play()

        # Figure out which matches earn a power-up *before* remove_matches
        # wipes the tiles, we need their .i/.j/.color while they still
        # exist, but the power-up itself has to be placed *after* removal,
        # or it would just get destroyed along with the rest of its match.
        powerups_to_create = []

        for match in matches:
            self.score += len(match) * 50

            if len(match) >= 4:
                anchor = moved_tile if moved_tile in match else match[0]
                combo_level = 5 if len(match) >= 5 else 4
                powerups_to_create.append(
                    (anchor.i, anchor.j, anchor.color, anchor.variety, combo_level)
                )

        self.board.remove_matches()

        for i, j, color, variety, combo_level in powerups_to_create:
            powerup_tile = Tile(i, j, color, variety)
            powerup_tile.combo_level = combo_level
            self.board.tiles[i][j] = powerup_tile

        self._settle_board()

    def _activate_powerup(self, tile: Tile) -> None:
        """Direct click on a power-up tile: trigger its effect without it
        needing to be part of a match first."""
        settings.SOUNDS["match"].stop()
        settings.SOUNDS["match"].play()

        self.active = False
        self.board.destroy_tile(tile)
        self._settle_board()

    def _settle_board(self) -> None:
        """After tiles were removed (by a match or a power-up), let
        whatever is above fall into the gaps, then check for a cascade."""
        falling_tiles = self.board.get_falling_tiles()

        Timer.tween(
            0.25,
            falling_tiles,
            on_finish=lambda: self._calculate_matches(
                [item[0] for item in falling_tiles]
            ),
        )

    def _calculate_matches(self, tiles: List) -> None:
        matches = self.board.calculate_matches_for(tiles)

        if matches is None:
            while not self._board_has_valid_move():
                self.board._initialize_tiles()

            self.active = True
            return

        self._resolve_matches(matches)

    def _board_has_valid_move(self) -> bool:
        """Try every adjacent pair on the board (each pair only once, via
        the right and down neighbors) by actually swapping it, checking for
        a match with the same tool calculate_matches_for uses for a real
        move, then reverting, stopping at the first one that works."""
        for i in range(settings.BOARD_HEIGHT):
            for j in range(settings.BOARD_WIDTH):
                for di, dj in ((0, 1), (1, 0)):
                    i2, j2 = i + di, j + dj

                    if i2 >= settings.BOARD_HEIGHT or j2 >= settings.BOARD_WIDTH:
                        continue

                    tile1 = self.board.tiles[i][j]
                    tile2 = self.board.tiles[i2][j2]

                    self._swap_logical(tile1, tile2)
                    matches = self.board.calculate_matches_for([tile1, tile2])
                    self._swap_logical(tile1, tile2)

                    if matches is not None:
                        self.board.matches = []
                        return True

        return False
