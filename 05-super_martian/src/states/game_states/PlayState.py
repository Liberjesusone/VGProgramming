"""
ISPPV1 2023
Study Case: Super Martian (Platformer)

Author: Alejandro Mujica
alejandro.j.mujic4@gmail.com

This file contains the class PlayState.
"""

from typing import Dict, Any

import pygame

from gale.camera import Camera
from gale.input_handler import InputData
from gale.state import BaseState
from gale.text import render_text
from gale.timer import Timer

import settings
from src.Clock import Clock
from src.GameLevel import GameLevel
from src.Player import Player
from src.MagicBox import MagicBox


class PlayState(BaseState):
    def enter(self, **enter_params: Dict[str, Any]) -> None:
        self.level = enter_params.get("level", 1)
        self.game_level = enter_params.get("game_level")
        if self.game_level is None:
            self.game_level = GameLevel(self.level)
            pygame.mixer.music.load(
                settings.BASE_DIR / "assets" / "sounds" / "music_grassland.ogg"
            )
            pygame.mixer.music.play(loops=-1)
            pygame.mixer.music.set_volume(settings.MUSIC_VOLUME)

        self.tilemap = self.game_level.tilemap
        self.player: Player = enter_params.get("player")
        if self.player is None:
            # Asked to the level instead of hardcoding a row: level 1 runs
            # horizontally with its ground near the top, level 2 is a
            # vertical climb whose floor is 70+ rows down, and both start
            # the player standing on that floor.
            spawn_x, spawn_y = self.game_level.get_player_spawn(20)
            self.player = Player(spawn_x, spawn_y, self.game_level)
            self.player.change_state("idle")

        self.camera = enter_params.get("camera")

        if self.camera is None:
            self.camera = Camera(settings.VIRTUAL_WIDTH, settings.VIRTUAL_HEIGHT)
            self.camera.follow(self.player, rate=settings.CAMERA_FOLLOW_RATE)
            self.camera.bounds = self.game_level.get_rect()
            self.camera.x, self.camera.y = self.player.x, self.player.y
            self.camera.update(0)

        self.clock = enter_params.get("clock")

        if self.clock is None:
            self.clock = Clock(120)

            def countdown_timer():
                self.clock.count_down()

                if 0 < self.clock.time <= 5:
                    settings.SOUNDS["timer"].play()

                if self.clock.time == 0:
                    self.player.change_state("dead")

            # Handle kept so score_achieved() can stop *only* the
            # countdown. Timer.pause() would freeze every timer in the
            # game, the key's spawn tween included, and the key would
            # never come out of the box.
            self.countdown = Timer.every(1, countdown_timer)
        else:
            self.countdown = enter_params.get("countdown")
            Timer.resume()

        """ Preserved across the pause round-trip the same way the player,
        camera and clock are: enter() runs again on the way back, and a
        fresh MagicBox would forget it had already been placed while
        its tile stayed written in the tilemap.
        """        
        self.magic_box = enter_params.get("magic_box")

        if self.magic_box is None:
            self.magic_box = MagicBox()

        # True once the target score is reached: the countdown is stopped
        # and coins stop being collectable, leaving the key as the only
        # thing left to pick up.
        self.score_achieved = enter_params.get("score_achieved", False)

        # Guards _complete_level: the key stays picked up, so update()
        # would otherwise re-trigger the transition on every frame while
        # the iris is still closing.
        self.transitioning = False

        # Iris wipe. Coming back from pause carries the radius over so the
        # screen does not re-open every time; a brand new level starts
        # fully closed and irises open.
        self.iris_radius = enter_params.get("iris_radius")

        if self.iris_radius is None:
            self.iris_radius = 0.0
            Timer.tween(
                settings.IRIS_OPEN_TIME,
                [(self, {"iris_radius": settings.IRIS_MAX_RADIUS})],
            )

    def update(self, dt: float) -> None:
        if self.player.is_dead:
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
            Timer.clear()
            self.state_machine.change("game_over", self.player)

        # Frozen while the iris closes: the level is already decided and
        # letting the player walk (or die) mid-transition looks wrong.
        if not self.transitioning:
            self.player.update(dt)

        if (
            not self.score_achieved
            and self.player.score >= settings.SCORE_TO_SPAWN_MAGIC_BOX
        ):
            self._on_score_achieved()

        # To handle the colision with the magic box
        if self.player.hit_ceiling and self.magic_box.is_active:
            row, col = self.tilemap.tile_at(
                self.player.x + self.player.width / 2,   # horizontal center
                self.player.y - 1,                       # 1 px above the upper border
            )
            if (row, col) == (self.magic_box.row, self.magic_box.col):
                if self.magic_box.hit():
                    self._spawn_key()

        if self.player.y >= self.tilemap.pixel_height:
            self.player.change_state("dead")

        self.camera.update(dt)
        self.game_level.update(dt)

        for creature in self.game_level.creatures:
            if self.player.collides(creature):
                self.player.change_state("dead")

        for item in self.game_level.items:
            if not item.active or not item.collidable:
                continue

            # Once the target score is reached the coins are done: only
            # the key is still worth anything, so everything else stops
            # responding to the player.
            if self.score_achieved and item.frame_index != settings.KEY_FRAME_INDEX:
                continue

            if self.player.collides(item):
                item.on_collide(self.player)
                item.on_consume(self.player)

        # pickup_key only raises the flag; the whole completion sequence
        # lives here, so it stays in one place.
        if self.player.has_key:
            self._complete_level()

    def _on_score_achieved(self) -> None:
        """Target score reached: freeze the clock, take the coins out of
        play and drop the magic box into the map. Runs exactly once."""
        self.score_achieved = True

        # Only this timer is removed, not Timer.pause(): pausing would
        # also freeze the key's spawn tween later on.
        if self.countdown is not None:
            self.countdown.remove()

        self.magic_box.appear(self.tilemap)

    def _complete_level(self) -> None:
        """The key was picked up: close the iris, and only once it is shut
        move on to the next level (or end the run)."""
        if self.transitioning:
            return

        self.transitioning = True
        settings.SOUNDS["level_complete"].stop()
        settings.SOUNDS["level_complete"].play()

        Timer.tween(
            settings.IRIS_CLOSE_TIME,
            [(self, {"iris_radius": 0.0})],
            on_finish=self._go_to_next_level,
        )

    def _go_to_next_level(self) -> None:
        """Runs when the iris has finished closing, so the level swap
        happens behind a black screen."""
        Timer.clear()

        if self.level >= settings.NUM_LEVELS:
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
            self.state_machine.change("game_over", self.player)
            return

        # Nothing is handed over, so enter() builds a fresh GameLevel,
        # player, camera and clock -- which also resets the score to 0.
        # That is on purpose: every level is scored against the same
        # SCORE_TO_SPAWN_MAGIC_BOX threshold, so carrying the score over
        # would make the next level's box pop out immediately.
        self.state_machine.change("play", level=self.level + 1)

    def _spawn_key(self) -> None:
        """Build the key on top of the magic box and tween it upward one
        tile, so it reads as being pushed out of the block rather than
        just appearing. The key is a GameItem living in
        game_level.items, so it is not solid: the player
        walks into it and PlayState's existing item loop consumes it."""
        settings.SOUNDS["spawn_key"].stop()
        settings.SOUNDS["spawn_key"].play()

        x, y = self.magic_box.get_pixel_position(self.tilemap)

        key = self.game_level.add_item(
            {
                "item_name": "key",
                "frame_index": settings.KEY_FRAME_INDEX,
                "x": x,
                "y": y,
                "width": self.tilemap.tile_width,
                "height": self.tilemap.tile_height,
            }
        )

        # Not collidable while it is still travelling, so it cannot be
        # picked up mid-flight before the little animation is even seen.
        key.collidable = False

        def landed() -> None:
            key.collidable = True

        def down() -> None:
            Timer.tween(
                0.35,
                [(key, {"y": y - self.tilemap.tile_height})],
                on_finish=landed,              
            )

        Timer.tween(
            0.2,
            [(key, {"y": y - self.tilemap.tile_height * 3})],
            on_finish=down,
        )

    def render(self, surface: pygame.Surface) -> None:
        self.game_level.render(surface, self.camera)
        self.player.render(surface, self.camera)

        render_text(
            surface,
            f"Score: {self.player.score}",
            settings.FONTS["small"],
            5,
            5,
            (255, 255, 255),
            shadowed=True,
        )

        self._render_iris(surface)

        render_text(
            surface,
            f"Time: {self.clock.time}",
            settings.FONTS["small"],
            settings.VIRTUAL_WIDTH - 60,
            5,
            (255, 255, 255),
            shadowed=True,
        )

    def _render_iris(self, surface: pygame.Surface) -> None:
        """Black mask with a circular hole punched in it. Drawing with an
        alpha of 0 on an SRCALPHA surface writes the colour rather than
        blending it, which is what makes the hole actually transparent."""
        if self.iris_radius >= settings.IRIS_MAX_RADIUS:
            return

        mask = pygame.Surface(
            (settings.VIRTUAL_WIDTH, settings.VIRTUAL_HEIGHT), pygame.SRCALPHA
        )
        mask.fill((0, 0, 0, 255))

        if self.iris_radius > 0:
            pygame.draw.circle(
                mask,
                (0, 0, 0, 0),
                (settings.VIRTUAL_WIDTH // 2, settings.VIRTUAL_HEIGHT // 2),
                int(self.iris_radius),
            )

        surface.blit(mask, (0, 0))

    def on_input(self, input_id: str, input_data: InputData) -> None:
        if input_id == "pause" and input_data.pressed:
            Timer.pause()
            self.state_machine.change(
                "pause",
                level=self.level,
                camera=self.camera,
                game_level=self.game_level,
                player=self.player,
                clock=self.clock,
                magic_box=self.magic_box,
                countdown=self.countdown,
                score_achieved=self.score_achieved,
                iris_radius=self.iris_radius,
            )
        else:
            self.player.on_input(input_id, input_data)
