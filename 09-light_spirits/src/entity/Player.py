"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains the class Player.

The art is not drawn yet, so for now the player is a plain shape at the
exact size the real sprite will be (settings.PLAYER_WIDTH x
PLAYER_HEIGHT). Everything around it, the anchor at the feet, the small
collision box, the depth sorting, is already final, so dropping in the
sprite later changes only render().
"""

from typing import Any, Dict, List

import pygame

import settings

SPEED = 150.0

""" How much of the player blocks. Not the whole body: in a top-down view
 only the feet are really on the ground, so a narrow box down there is
 what bumps into things. It is also what lets the head overlap a prop
 standing behind them without being stopped by it.
 """ 
FEET_WIDTH = 20
FEET_DEPTH = 12

BODY_COLOR = (206, 198, 176)
BODY_EDGE = (56, 52, 46)
CLOAK_COLOR = (92, 74, 108)
SHADOW_COLOR = (0, 0, 0, 90)


class Player:
    def __init__(self, x: float, y: float) -> None:
        # The feet, same anchor every prop uses, so both can be sorted
        # against each other with no conversion.
        self.x: float = x
        self.y: float = y

        self.width: int = settings.PLAYER_WIDTH
        self.height: int = settings.PLAYER_HEIGHT

        self.health: int = 6
        self.direction: str = "down"

        self.held: Dict[str, bool] = {
            "move_left": False,
            "move_right": False,
            "move_up": False,
            "move_down": False,
        }

        self._shadow = pygame.Surface((self.width, FEET_DEPTH), pygame.SRCALPHA)
        pygame.draw.ellipse(self._shadow, SHADOW_COLOR, self._shadow.get_rect())

    @property
    def dead(self) -> bool:
        return self.health <= 0

    @property
    def sort_y(self) -> float:
        return self.y

    @property
    def center(self) -> pygame.Vector2:
        """The middle of the body, which is what the camera follows.
        Following the feet instead would sit the view half a body too
        low."""
        return pygame.Vector2(self.x, self.y - self.height / 2)

    def feet_rect_at(self, x: float, y: float) -> pygame.Rect:
        return pygame.Rect(
            round(x - FEET_WIDTH / 2), round(y - FEET_DEPTH), FEET_WIDTH, FEET_DEPTH)

    @property
    def feet_rect(self) -> pygame.Rect:
        return self.feet_rect_at(self.x, self.y)

    @property
    def image_rect(self) -> pygame.Rect:
        return pygame.Rect(
            round(self.x - self.width / 2),
            round(self.y - self.height),
            self.width,
            self.height)

    def on_input(self, input_id: str, input_data: Any) -> None:
        if input_id not in self.held:
            return

        if input_data.pressed:
            self.held[input_id] = True
        elif input_data.released:
            self.held[input_id] = False

    def update(self, dt: float, level: Any) -> None:
        # If we click both keys at a time, no movement will be made
        dx = self.held["move_right"] - self.held["move_left"]
        dy = self.held["move_down"] - self.held["move_up"]

        if dx == 0 and dy == 0:
            return

        """ Normalised, so walking diagonally is not faster than walking
        straight, which it would be if both axes moved a full step. """
        movement = pygame.Vector2(dx, dy).normalize() * SPEED * dt

        if abs(dx) > abs(dy):
            self.direction = "right" if dx > 0 else "left"
        else:
            self.direction = "down" if dy > 0 else "up"

        # One axis at a time, so running into a wall diagonally s
        # lides along it instead of stopping.
        self._move_axis(movement.x, 0, level)
        self._move_axis(0, movement.y, level)

    def _move_axis(self, dx: float, dy: float, level: Any) -> None:
        """ Move the collision rect and checks if it the level allows it.
        It's used to move one axis at a time. """
        target_x = self.x + dx
        target_y = self.y + dy

        if level.blocked(self.feet_rect_at(target_x, target_y)):
            return

        self.x, self.y = target_x, target_y

    def render(self, surface: pygame.Surface, camera: Any) -> None:
        shadow_rect = pygame.Rect(round(self.x - self.width / 2), 
                                  round(self.y - 8),
                                  self.width, 12)
        surface.blit(
            pygame.transform.scale(self._shadow, camera.apply(shadow_rect).size),
            camera.apply(shadow_rect),
        )

        body = camera.apply(self.image_rect)
        pygame.draw.rect(surface, CLOAK_COLOR, body, border_radius=max(1, body.width // 3))
        head = pygame.Rect(0, 0, body.width, body.height // 3)
        head.midtop = body.midtop
        pygame.draw.rect(surface, BODY_COLOR, head, border_radius=max(1, head.width // 3))
        pygame.draw.rect(surface, BODY_EDGE, body, 1, border_radius=max(1, body.width // 3))

    def render_debug(self, surface: pygame.Surface, camera: Any) -> None:
        pygame.draw.rect(surface, (90, 220, 140), camera.apply(self.image_rect), 1)
        pygame.draw.rect(surface, (220, 80, 80), camera.apply(self.feet_rect), 1)
