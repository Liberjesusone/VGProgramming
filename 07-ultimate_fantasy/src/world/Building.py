"""
ISPPV1 2023
Study Case: Ultimate Fantasy (RPG)

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains the class Building: a solid piece of scenery sitting
on top of a region's tiles, with one tile of its footprint acting as a
door.
"""

import pygame

import settings


class Building:
    """
    A rectangle of tiles the party cannot walk through, drawn from a
    single image instead of from the tileset.

    It is not part of the tilemap on purpose. Everything a Region
    generates is picked per cell out of TILE_IDS, and a house is one
    picture several tiles wide, so keeping it beside the tilemap means the
    art never has to be cut into 16 by 16 pieces and the collision stays a
    plain rectangle test.

    The bottom row holds the door. Walking into it is what takes the party
    inside, so the door is never actually walked onto and the whole
    footprint, door included, stays solid.

    The picture may be taller than the footprint, and normally is: a house
    seen from the front has a roof that rises well above the ground it
    actually stands on. Everything above the footprint is drawn but not
    solid, so the party walks in front of the roof rather than into it.
    The image is anchored by its bottom edge for that reason, and its
    height is read from the art itself, so redrawing the roof taller needs
    no numbers changed anywhere.
    """

    def __init__(
        self,
        texture_id: str,
        map_x: int,
        map_y: int,
        tile_width: int,
        tile_height: int,
        door_offset_x: int,
    ) -> None:
        self.texture_id = texture_id
        self.map_x = map_x
        self.map_y = map_y
        self.tile_width = tile_width
        self.tile_height = tile_height

        self.door_map_x = map_x + door_offset_x
        self.door_map_y = map_y + tile_height - 1

        image_height = settings.TEXTURES[texture_id].get_height()
        self.roof_tiles = max(
            0, (image_height - tile_height * settings.TILE_SIZE) // settings.TILE_SIZE
        )

    @property
    def x(self) -> float:
        return (self.map_x - 1) * settings.TILE_SIZE

    @property
    def y(self) -> float:
        return (self.map_y - 1) * settings.TILE_SIZE

    @property
    def bottom(self) -> float:
        """Pixel y of the footprint's lower edge, which the art hangs
        from."""
        return (self.map_y - 1 + self.tile_height) * settings.TILE_SIZE

    def covers(self, tile_x: int, tile_y: int) -> bool:
        """Whether this tile is part of the solid footprint."""
        return (
            self.map_x <= tile_x < self.map_x + self.tile_width
            and self.map_y <= tile_y < self.map_y + self.tile_height
        )

    def occludes(self, tile_x: int, tile_y: int) -> bool:
        """Whether this tile has any of the building drawn over it, roof
        included. Wider than covers, and used to keep townsfolk from
        spawning somewhere they would be hidden behind the art or, worse,
        drawn standing on the roof."""
        return (
            self.map_x <= tile_x < self.map_x + self.tile_width
            and self.map_y - self.roof_tiles <= tile_y < self.map_y + self.tile_height
        )

    def is_door(self, tile_x: int, tile_y: int) -> bool:
        return tile_x == self.door_map_x and tile_y == self.door_map_y

    def render(self, surface: pygame.Surface) -> None:
        image = settings.TEXTURES[self.texture_id]
        surface.blit(image, (self.x, self.bottom - image.get_height()))


def guild_hall() -> Building:
    """The town's guild hall, laid out from the values in settings so the
    art, the collision box and the door all read the same numbers."""
    return Building(
        "guild-hall",
        settings.GUILD_HALL_MAP_X,
        settings.GUILD_HALL_MAP_Y,
        settings.GUILD_HALL_TILE_WIDTH,
        settings.GUILD_HALL_TILE_HEIGHT,
        settings.GUILD_HALL_DOOR_OFFSET_X,
    )
