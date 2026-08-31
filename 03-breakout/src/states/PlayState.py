"""
ISPPV1 2023
Study Case: Breakout

Author: Alejandro Mujica
alejandro.j.mujic4@gmail.com

This file contains the class to define the Play state.
"""

import random

import pygame

from gale.factory import AbstractFactory
from gale.state import BaseState
from gale.input_handler import InputData
from gale.text import render_text
from typing import Optional

import settings
import src.powerups


class PlayState(BaseState):
    def enter(self, **params: dict):
        self.level = params["level"]
        self.score = params["score"]
        self.lives = params["lives"]
        self.paddle = params["paddle"]
        self.balls = params["balls"]
        self.brickset = params["brickset"]
        self.live_factor = params["live_factor"]
        self.points_to_next_live = params["points_to_next_live"]
        self.points_to_next_grow_up = (
            self.score
            + settings.PADDLE_GROW_UP_POINTS * (self.paddle.size + 1) * self.level
        )
        self.powerups = params.get("powerups", [])

        if not params.get("resume", False):
            self.balls[0].vx = random.randint(-80, 80)
            self.balls[0].vy = random.randint(-170, -100)
            settings.SOUNDS["paddle_hit"].play()

        self.powerups_abstract_factory = AbstractFactory("src.powerups")

        self.stuck_next = False # True when have earned a StopBall power_up
        self.l_rocket = None    # left rocket
        self.r_rocket = None    # right rocket

    def update(self, dt: float) -> None:
        self.paddle.update(dt)

        for ball in self.balls:
            ball.update(dt)
            if ball.is_stuck: 
                continue
            
            ball.solve_world_boundaries()

            # Check collision with the paddle
            if ball.collides(self.paddle):
                settings.SOUNDS["paddle_hit"].stop()
                settings.SOUNDS["paddle_hit"].play()
                if self.stuck_next:
                    ball.is_stuck = True
                else:
                    ball.rebound(self.paddle)
                    ball.push(self.paddle)

            # Check collision with brickset
            if not ball.collides(self.brickset):
                continue

            brick = self.brickset.get_colliding_brick(ball.get_collision_rect())

            if brick is None:
                continue

            brick.hit()
            self.score += brick.score()
            ball.rebound(brick)

            # Check earn life
            if self.score >= self.points_to_next_live:
                settings.SOUNDS["life"].play()
                self.lives = min(3, self.lives + 1)
                self.live_factor += 0.5
                self.points_to_next_live += settings.LIVE_POINTS_BASE * self.live_factor

            # Check growing up of the paddle
            if self.score >= self.points_to_next_grow_up:
                settings.SOUNDS["grow_up"].play()
                self.points_to_next_grow_up += (
                    settings.PADDLE_GROW_UP_POINTS * (self.paddle.size + 1) * self.level
                )
                self.paddle.inc_size()

            # Chance to generate two more balls
            if random.random() < 0.1:
                r = brick.get_collision_rect()
                self.powerups.append(
                    self.powerups_abstract_factory.get_factory("TwoMoreBall").create(
                        r.centerx - 8, r.centery - 8
                    )
                )
            # Chance to generate one StopBall power up
            elif random.random() < 0.3:
                r = brick.get_collision_rect()
                self.powerups.append(
                    self.powerups_abstract_factory.get_factory("StopBall").create(
                        r.centerx - 8, r.centery - 8
                    )
                )
            # Chance to generate one Rocket power up
            elif random.random() < 0.5 and self.l_rocket is None and self.r_rocket is None:
                r = brick.get_collision_rect()
                self.powerups.append(
                    self.powerups_abstract_factory.get_factory("Rocket").create(
                        r.centerx - 8, r.centery - 8
                    )
                )
            # Chance to generate one BreakBrick power up
            elif random.random() < 1:
                r = brick.get_collision_rect()
                self.powerups.append(
                    self.powerups_abstract_factory.get_factory("BreakBricks").create(
                        r.centerx - 8, r.centery - 8
                    )
                )

        def rocket_update(rocket):
            if rocket is None:
                return None
            if rocket.was_taken and not rocket.was_fired:
                rocket.x = self.paddle.x - 16 if rocket.is_left else self.paddle.x + self.paddle.width
                rocket.y = self.paddle.y
            rocket.update(dt)
            brick = self.brickset.get_colliding_brick(rocket.get_collision_rect())
            if brick is not None:
                brick.destroy()
                self.score += brick.score()
                return None  # it was consumed
            return rocket    # it's still alived

        self.l_rocket = rocket_update(self.l_rocket)
        self.r_rocket = rocket_update(self.r_rocket)

        # Removing all balls that are not in play
        self.balls = [ball for ball in self.balls if ball.active]

        self.brickset.update(dt)

        if not self.balls:
            self.lives -= 1
            if self.lives == 0:
                self.state_machine.change("game_over", score=self.score)
            else:
                self.paddle.dec_size()
                self.state_machine.change(
                    "serve",
                    level=self.level,
                    score=self.score,
                    lives=self.lives,
                    paddle=self.paddle,
                    brickset=self.brickset,
                    points_to_next_live=self.points_to_next_live,
                    live_factor=self.live_factor,
                )

        # Update powerups
        for powerup in self.powerups:
            powerup.update(dt)

            if powerup.collides(self.paddle):
                powerup.take(self)

        # Remove powerups that are not in play
        self.powerups = [p for p in self.powerups if p.active]

        # Check victory
        if self.brickset.size == 0:
            self.state_machine.change(
                "victory",
                lives=self.lives,
                level=self.level,
                score=self.score,
                paddle=self.paddle,
                balls=self.balls,
                points_to_next_live=self.points_to_next_live,
                live_factor=self.live_factor,
            )

    def render(self, surface: pygame.Surface) -> None:
        heart_x = settings.VIRTUAL_WIDTH - 120

        i = 0
        # Draw filled hearts
        while i < self.lives:
            surface.blit(
                settings.TEXTURES["hearts"], (heart_x, 5), settings.FRAMES["hearts"][0]
            )
            heart_x += 11
            i += 1

        # Draw empty hearts
        while i < 3:
            surface.blit(
                settings.TEXTURES["hearts"], (heart_x, 5), settings.FRAMES["hearts"][1]
            )
            heart_x += 11
            i += 1

        render_text(
            surface,
            f"Score: {self.score}",
            settings.FONTS["tiny"],
            settings.VIRTUAL_WIDTH - 80,
            5,
            (255, 255, 255),
        )

        self.brickset.render(surface)

        self.paddle.render(surface)

        for ball in self.balls:
            if ball.is_stuck:
                ball.x = self.paddle.x + self.paddle.width / 2
                ball.y = self.paddle.y - 5
            ball.render(surface)

        if self.l_rocket is not None:
            self.l_rocket.render(surface, self)
        if self.r_rocket is not None:
            self.r_rocket.render(surface, self)

        for powerup in self.powerups:
            powerup.render(surface)

    def on_input(self, input_id: str, input_data: InputData) -> None:
        if input_id == "move_left":
            if input_data.pressed:
                self.paddle.vx = -settings.PADDLE_SPEED
            elif input_data.released and self.paddle.vx < 0:
                self.paddle.vx = 0
        elif input_id == "move_right":
            if input_data.pressed:
                self.paddle.vx = settings.PADDLE_SPEED
            elif input_data.released and self.paddle.vx > 0:
                self.paddle.vx = 0
        elif input_id == "pause" and input_data.pressed:
            self.state_machine.change(
                "pause",
                level=self.level,
                score=self.score,
                lives=self.lives,
                paddle=self.paddle,
                balls=self.balls,
                brickset=self.brickset,
                points_to_next_live=self.points_to_next_live,
                live_factor=self.live_factor,
                powerups=self.powerups,
            )
        elif input_id == "serve" and any(ball.is_stuck for ball in self.balls):
            self.stuck_next = False
            stuck_ball = [ball for ball in self.balls if ball.is_stuck]
            for ball in stuck_ball:                
                ball.vx = random.randint(-80, 80)
                ball.vy = random.randint(-170, -100)
                settings.SOUNDS["paddle_hit"].play()
                ball.is_stuck = False
        elif input_id == "fire" and self.l_rocket is not None and self.r_rocket is not None:
            if not self.l_rocket.was_fired and not self.r_rocket.was_fired:
                self.l_rocket.fire()
                self.r_rocket.fire()