"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains the class PlayState: 
the world, the player in it, and the camera that follows them.
"""

from typing import Any

import pygame

from gale.camera import Camera
from gale.state import BaseState
from gale.text import render_text

import settings
from actions import DEBUG
from src.entity.Player import Player
from src.world.Level import Level

CAMERA_FOLLOW_RATE = 7.0

HUD_TEXT = "WASD     F1 shows the boxes"


class PlayState(BaseState):
    def enter(self) -> None:
        self.level = Level()

        spawn_x, spawn_y = self.level.spawn_point()
        self.player = Player(spawn_x, spawn_y, self.level)

        self.camera = Camera(settings.VIRTUAL_WIDTH, settings.VIRTUAL_HEIGHT)
        self.camera.bounds = self.level.bounds

        """ The camera follows a point rather than the player object
        directly: the player's own x and y are their feet, and aiming
        the view there would sit it half a body too low. This tracks
        their middle instead, and gale.Camera is happy with anything
        that has x and y, which a Vector2 does.
        """
        self.camera_target = pygame.Vector2(self.player.center)
        self.camera.follow(self.camera_target, rate=CAMERA_FOLLOW_RATE)
        self.camera.x, self.camera.y = self.camera_target
        self.camera.update(0)

        self.debug = False

    def update(self, dt: float) -> None:
        """ The player. Takes the camera, not the level: level is already
        stored on the player itself (movement/collision need it),
        camera is what turns the mouse into a world-space aim direction
        every frame, and is never cached on Player since PlayState is
        the one that could someday swap it (a boss-room camera cut, a
        zoom effect) out from under it. """ 
        self.player.update(dt, self.camera)
        self.level.update(dt, self.player)

        if self.player.dead:
            self._on_game_over()
            return

        # The camera
        self.camera_target.update(self.player.center)
        self.camera.update(dt)

    def _on_game_over(self) -> None:
        from src.states.game.GameOverState import GameOverState

        self.state_machine.push(GameOverState(self.state_machine))

    def on_input(self, input_id: str, input_data: Any) -> None:
        if input_id == DEBUG and input_data.pressed:
            self.debug = not self.debug
            return

        self.player.on_input(input_id, input_data)

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(settings.COLOR_BACKGROUND)

        self.level.render_floor(surface, self.camera)
        self.level.render_telegraphs(surface, self.camera)

        """ One pass over props and entities together, back to front. This
        is what puts the player behind a pillar when they are above it
        and in front of it when they are below. """
        for thing in self.level.drawables([self.player]):
            thing.render(surface, self.camera)

        # Render the debug collision squares
        if self.debug:
            self._render_debug(surface)

        # HUD
        render_text(
            surface, HUD_TEXT, settings.FONTS["small"], 8, 8, settings.COLOR_DIM
        )
        self.player.render_hud(surface)

    def _render_debug(self, surface: pygame.Surface) -> None:
        """ Draws every collision box and the exact line each thing is
        sorted by, so the depth ordering can be checked by eye instead of
        guessed at. """
        for thing in self.level.drawables([self.player]):
            thing.render_debug(surface, self.camera)

            feet_y = round(thing.sort_y)
            left, _ = self.camera.world_to_screen((thing.x - 20, feet_y))
            right, screen_y = self.camera.world_to_screen((thing.x + 20, feet_y))
            pygame.draw.line(
                surface, (250, 220, 90), (left, screen_y), (right, screen_y), 1
            )

        info = (
            f"player ({self.player.x:.0f}, {self.player.y:.0f})   "
            f"props {len(self.level.props)}   "
            f"enemies {len(self.level.entities)}   "
            f"map {self.level.pixel_width}x{self.level.pixel_height}"
        )
        render_text(
            surface,
            info,
            settings.FONTS["small"],
            8,
            settings.VIRTUAL_HEIGHT - 22,
            settings.COLOR_ACCENT,
        )
