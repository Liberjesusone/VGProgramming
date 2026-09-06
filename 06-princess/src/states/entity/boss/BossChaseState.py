"""
ISPPV1 2023
Study Case: The Legend of the Princess (ARPG)

This file contains the class BossChaseState.
"""

from typing import TypeVar

import pygame

import settings
from src.definitions.game_objects import create_fireball
from src.Projectile import Projectile
from src.states.entity.BaseEntityState import BaseEntityState

# The walkable rectangle of a room, in the same coordinates as any
# entity's x/y. Deliberately *not* movement.move_and_bump: that one lets
# an entity's top edge climb half its own height into the wall (a nicety
# for a 16 px enemy whose sprite is 16 px tall), which on a 44 px hitbox
# carrying a 64 px sprite would push the mage's head clean off the top of
# the screen.
_LEFT_LIMIT = settings.MAP_RENDER_OFFSET_X + settings.TILE_SIZE
_RIGHT_LIMIT = settings.VIRTUAL_WIDTH - settings.TILE_SIZE * 2
_TOP_LIMIT = settings.MAP_RENDER_OFFSET_Y + settings.TILE_SIZE
_BOTTOM_LIMIT = (
    settings.MAP_HEIGHT * settings.TILE_SIZE
    + settings.MAP_RENDER_OFFSET_Y
    - settings.TILE_SIZE
)


class BossChaseState(BaseEntityState):
    """
    Walks the mage at the player one axis at a time and throws a fireball
    every TIME_FOR_BOSS_TO_FIRE seconds.

    All of it happens in process_ai rather than update() because that is
    the half of the pair Room.update hands both the room (needed to append
    the fireball to room.projectiles, and to read room.player) and dt.
    update() is left to the base class, so Entity.update keeps ticking the
    animation and the invulnerability flash on its own.
    """

    def enter(self) -> None:
        self.entity.change_animation(f"walk-{self.entity.direction}")
        self.fire_timer = 0.0

    def process_ai(self, room: TypeVar("Room"), dt: float) -> None:
        boss = self.entity
        player = room.player

        # Centre to centre, so a wide boss does not read as being to the
        # left of a player standing right in front of his middle.
        dx = (player.x + player.width / 2) - (boss.x + boss.width / 2)
        dy = (player.y + player.height / 2) - (boss.y + boss.height / 2)

        # One axis at a time, whichever the player is further off on,
        # which also makes him face, and fire along, the direction that
        # closes the bigger gap.
        if abs(dx) >= abs(dy):
            direction = "right" if dx > 0 else "left"
        else:
            direction = "down" if dy > 0 else "up"

        if direction != boss.direction:
            boss.direction = direction
            boss.change_animation(f"walk-{direction}")

        self._walk(dt)

        self.fire_timer += dt

        if self.fire_timer >= settings.TIME_FOR_BOSS_TO_FIRE:
            self.fire_timer = 0.0
            self._fire(room)

    def _walk(self, dt: float) -> None:
        boss = self.entity
        step = boss.walk_speed * dt

        if boss.direction == "left":
            boss.x -= step
        elif boss.direction == "right":
            boss.x += step
        elif boss.direction == "up":
            boss.y -= step
        else:
            boss.y += step

        boss.x = min(max(boss.x, _LEFT_LIMIT), _RIGHT_LIMIT - boss.width)
        boss.y = min(max(boss.y, _TOP_LIMIT), _BOTTOM_LIMIT - boss.height)

    def _fire(self, room: TypeVar("Room")) -> None:
        boss = self.entity

        fireball = create_fireball(
            boss.x + boss.width / 2 - settings.TILE_SIZE / 2,
            boss.y + boss.height / 2 - settings.TILE_SIZE / 2,
        )

        room.projectiles.append(
            Projectile(
                fireball,
                boss.direction,
                speed=settings.FIREBALL_SPEED,
                max_tiles=settings.FIREBALL_RANGE_TILES,
                owner="boss",
            )
        )

        settings.SOUNDS["sword"].play()

    def render(self, surface: pygame.Surface) -> None:
        anim = self.entity.current_animation
        self.entity.render_sprite(surface, anim.texture_id, anim.get_current_frame())
