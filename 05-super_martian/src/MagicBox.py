"""
ISPPV1 2023
Study Case: Super Martian (Platformer)

This file contains the class MagicBox: the solid block that shows up
once the player reaches the target score, and that releases the level's
key when the player hits it from below.
"""

import random
from typing import Any, Optional, Tuple

import settings


class MagicBox:
    """ The block lives *inside the tilemap*, not as an entity: appear()
    writes a solid gid into the collision layer, so gale's
    move_and_collide treats it as solid on all four sides for free,
    no manual push-out code at all. This class only remembers where it
    was placed and whether it has already been hit.
    """

    LAYER = "ground"

    """ How many tiles above the ground the block sits. The player's head
    clears roughly 4.6 tiles (JUMP_TAKEOFF_SPEED 326.7 against GRAVITY
    980), so 3 leaves comfortable margin instead of demanding a
    pixel-perfect jump.
    """
    TILES_ABOVE_GROUND = 3

    def __init__(self) -> None:
        self.is_active: bool = False  
        self.was_hit: bool = False    
        self.row: Optional[int] = None
        self.col: Optional[int] = None

    def appear(self, tilemap: Any) -> None:
        """Place the block once. Calling this again does nothing, so it
        is safe to call every frame from PlayState.update."""
        if self.is_active:
            return
            
        settings.SOUNDS["magic_box_appear"].play()

        spot = self._pick_spot(tilemap)

        if spot is None:
            return

        self.row, self.col = spot
        tilemap.set_gid(self.LAYER, self.row, self.col, settings.MAGIC_BOX_GID)
        self.is_active = True

    def hit(self) -> bool:
        """Register a hit from below.

        :returns: True only on the very first hit, so the caller can
                  spawn the key exactly once.
        """
        if not self.is_active or self.was_hit:
            return False

        self.was_hit = True
        return True

    def get_pixel_position(self, tilemap: Any) -> Tuple[float, float]:
        """Top-left corner of the block, in world pixels, where the
        key has to be born from."""
        return tilemap.position_of(self.row, self.col)

    def _pick_spot(self, tilemap: Any) -> Optional[Tuple[int, int]]:
        """Pick a random column that has ground, and return the cell
        TILES_ABOVE_GROUND tiles above that ground, so the block is
        always reachable with a jump from a place the player can stand
        on. Cells that are already occupied are skipped."""
        candidates = []

        for col in range(tilemap.cols):
            ground_row = self._first_solid_row(tilemap, col)

            if ground_row is None:
                continue

            row = ground_row - self.TILES_ABOVE_GROUND

            # Must be inside the map and empty, or set_gid would
            # overwrite an existing tile of the level.
            if row < 0 or tilemap.get_gid(self.LAYER, row, col) != 0:
                continue

            candidates.append((row, col))

        return random.choice(candidates) if candidates else None

    def _first_solid_row(self, tilemap: Any, col: int) -> Optional[int]:
        """Scan a column from the sky down, returning the row of the
        first non-empty tile, or None if the column is all air."""
        for row in range(tilemap.rows):
            if tilemap.get_gid(self.LAYER, row, col) != 0:
                return row

        return None
