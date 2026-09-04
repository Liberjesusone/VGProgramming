"""
ISPPV1 2023
Study Case: Super Martian (Platformer)

Author: Alejandro Mujica
alejandro.j.mujic4@gmail.com

This file contains the base class GameEntity.
"""

from typing import TypeVar, Dict, Any, Tuple

from gale.state import StateMachine, BaseState
from gale.tilemap import move_and_collide

import settings
from src import mixins


class GameEntity(mixins.DrawableMixin, mixins.AnimatedMixin, mixins.CollidableMixin):
    COLLISION_LAYER = "ground"

    def __init__(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        texture_id: str,
        game_level: TypeVar("GameLevel"),
        states: Dict[str, BaseState],
        animation_defs: Dict[str, Dict[str, Any]],
    ) -> None:
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.vx: float = 0
        self.vy: float = 0
        self.move_direction: int = 0
        self.jump_requested: bool = False
        self.jump_held: bool = False
        self.texture_id = texture_id
        self.frame_index = -1
        self.game_level = game_level
        self.tilemap = self.game_level.tilemap
        self.on_ground = False
        self.hit_ceiling = False
        self.collided_x = False
        self.state_machine = StateMachine(states)
        self.current_animation = None
        self.animations = {}
        self.generate_animations(animation_defs)
        self.flipped = False
        self.is_dead = False

    def change_state(
        self, state_id: str, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> None:
        self.state_machine.change(state_id, *args, **kwargs)

    def update(self, dt: float) -> None:
        # Applied unconditionally (not just while jumping/falling) so the
        # vertical move below is never a no-op dy=0 call, which would skip
        # move_and_collide's y-axis check and leave on_ground stale.
        self.vy += settings.GRAVITY * dt

        self.state_machine.update(dt)
        mixins.AnimatedMixin.update(self, dt)

        self.x, self.y, self.collided_x, collided_y = move_and_collide(
            self.tilemap,
            self.COLLISION_LAYER,
            self.x,
            self.y,
            self.width,
            self.height,
            self.vx * dt,
            self.vy * dt,
        )

        if collided_y:
            """ Both flags are re-derived every frame from the sign of vy
            *before* it gets zeroed below, that sign is the only
            thing that says whether we landed on something or banged
            our head into it, and it is gone one line later.
            """
            self.on_ground = self.vy > 0
            self.hit_ceiling = self.vy < 0
            self.vy = 0
        else:
            self.on_ground = False
            self.hit_ceiling = False

        # Keep the entity from walking off either edge of the world.
        if self.x < 0:
            self.x = 0
        elif self.x + self.width > self.tilemap.pixel_width:
            self.x = self.tilemap.pixel_width - self.width
