"""
ISPPV1 2023
Study Case: Super Martian (Platformer)

Author: Alejandro Mujica
alejandro.j.mujic4@gmail.com

This file contains the class SnailWalkState.
"""

from gale.tilemap import CollisionType, collision_type_at

from src.states.entities.BaseEntityState import BaseEntityState


class SnailWalkState(BaseEntityState):
    def enter(self, flipped: bool) -> None:
        self.entity.change_animation("walk")
        self.entity.flipped = flipped
        self.entity.vx = -self.entity.walk_speed
        if self.entity.flipped:
            self.entity.vx *= -1

    def update(self, dt: float) -> None:
        if self.check_boundary():
            self.entity.vx *= -1
            self.entity.flipped = not self.entity.flipped

    def check_boundary(self) -> bool:
        world_width = self.entity.tilemap.pixel_width

        if self.entity.x + self.entity.width >= world_width:
            self.entity.x = world_width - self.entity.width
            return True
        elif self.entity.x <= 0:
            self.entity.x = 0
            return True

        if self.entity.collided_x:
            return True

        # Avoid falling off a ledge: peek at the tile just ahead of the
        # leading foot, one row below.
        tilemap = self.entity.tilemap
        row = int(self.entity.y // tilemap.tile_height)

        if self.entity.vx > 0:
            col = int((self.entity.x + self.entity.width) // tilemap.tile_width)
        else:
            col = int(self.entity.x // tilemap.tile_width)

        ahead = collision_type_at(tilemap, self.entity.COLLISION_LAYER, row + 1, col)
        return ahead == CollisionType.NONE
