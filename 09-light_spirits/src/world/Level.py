"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains the class Level: the floor, the scenery standing on
it, and the front-to-back ordering that makes the two read as one scene.

The map is generated in code for now. A Tiled map will replace
_build_floor, _place_props and _place_enemies later; nothing else in
the file has to change when it does, because everything downstream
only ever reads the tilemap, the prop list and the entity list.

The layout is meant to be the same every time the game runs, the way a
hand-designed level would be, so generation is seeded (see MAP_SEED) and
uses its own random.Random instead of the global random module. Using
the global module here would have seeded every *other* random roll in
the game too, enemy AI, loot, damage, tying all of it to the order
level generation happens in and making bugs elsewhere depend on level
layout in ways that would be very hard to trace back.
"""

import random
from typing import Any, List, Tuple

import pygame

from gale.tilemap import TileMap

import settings
from src.definitions.props import PROP_DEFS
from src.entity.Enemy import Enemy
from src.world.Prop import Prop

MAP_COLS = 60
MAP_ROWS = 40

# The material the whole floor starts as, before patches of the others are laid over it.
BASE_MATERIAL = "weathered_cracked_stone_slabs"

""" Patches of a second material, so the ground is not one flat surface.
Each is a rough blob rather than a rectangle, which reads as wear
rather than as a tiled area. """
NUM_PATCHES = 14
PATCH_MIN_RADIUS = 3
PATCH_MAX_RADIUS = 7

NUM_PROPS = 46

""" Interim, procedural stand-in for hand-placed spawns: once the map
moves to Tiled, this becomes reading spawn points from an object layer
instead, the same swap the module docstring already describes for
_build_floor and _place_props. One enemy per entry, in this order. """
ENEMY_SPAWNS = ["zombie", "zombie", "witch", "zombie", "golem", "witch"]

""" No enemy spawns this close to the map's centre, where the player
always starts (see spawn_point), so a run never opens with a guard
already standing on top of them. """
ENEMY_SPAWN_EXCLUSION_RADIUS = 160

# Arbitrary. Change this to get a different fixed layout; the layout
# stays whatever this value produces until it is changed again.
MAP_SEED = 20260909

# No prop may stand within this many tiles of the map edge, so none is
# ever cut in half by the boundary the camera clamps to.
EDGE_MARGIN_TILES = 3

# Minimum gap between two props' solid bases, so the player can always
# walk between them instead of finding a wall of scenery.
MIN_PROP_GAP = 26


class Level:
    def __init__(self) -> None:
        """ Own instance, not the global random module, see the module docstring 
        for why. Every random call this class makes goes through it. """
        self._rng = random.Random(MAP_SEED)

        self.tilemap = TileMap(
            settings.TILE_SIZE, settings.TILE_SIZE, MAP_COLS, MAP_ROWS
        )

        for tileset in settings.FLOOR_TILESETS.values():
            self.tilemap.add_tileset(tileset)

        self._build_floor()

        self.props: List[Prop] = []
        self._place_props()

        self.entities: List[Enemy] = []
        self._place_enemies()

        # The player's arrows currently in flight, they only ever hit enemies.
        self.projectiles: List[Any] = []

        # Enemy attacks still in flight (the witch's AreaShot), they only ever hit the player.
        self.hazards: List[Any] = []

    # ------------------------------------------------------------
    # geometry
    # ------------------------------------------------------------
    @property
    def pixel_width(self) -> int:
        return MAP_COLS * settings.TILE_SIZE

    @property
    def pixel_height(self) -> int:
        return MAP_ROWS * settings.TILE_SIZE

    @property
    def bounds(self) -> pygame.Rect:
        return pygame.Rect(0, 0, self.pixel_width, self.pixel_height)

    def spawn_point(self) -> Tuple[float, float]:
        """ Somewhere near the middle with nothing standing on it. """
        centre_x = self.pixel_width / 2
        centre_y = self.pixel_height / 2

        for radius in range(0, 400, 20):
            for _ in range(20):
                x = centre_x + self._rng.uniform(-radius, radius)
                y = centre_y + self._rng.uniform(-radius, radius)
                probe = pygame.Rect(round(x) - 20, round(y) - 20, 40, 40)

                if not any(prop.solid_rect.colliderect(probe) for prop in self.props):
                    return (x, y)

        return (centre_x, centre_y)

    def blocked(self, rect: pygame.Rect) -> bool:
        """ Whether something the size of rect can stand there. Both the
        map edge and every prop's base count. """
        if not self.bounds.contains(rect):
            return True

        return any(prop.solid_rect.colliderect(rect) for prop in self.props)


    # ------------------------------------------------------------
    # Update 
    # ------------------------------------------------------------
    def update(self, dt: float, player: Any) -> None:
        """ Advances the player's arrows against enemies' bodies, every
        enemy against the player, and every enemy hazard until it lands,
        then drops whatever is done: arrows that hit or ran out of range,
        dead enemies, and hazards that already landed. """
        for arrow in list(self.projectiles):
            arrow.update(dt)

            for entity in self.entities:
                if arrow.dead:
                    break

                if entity.hurt_rect.collidepoint(arrow.x, arrow.y):
                    entity.damage(arrow.damage)
                    entity.change_state("chase")
                    arrow.dead = True

            if arrow.dead:
                self.projectiles.remove(arrow)

        for entity in self.entities:
            entity.update(dt, player)

        for hazard in self.hazards:
            hazard.update(dt, player)

        self.entities = [entity for entity in self.entities if not entity.dead]
        self.hazards = [hazard for hazard in self.hazards if not hazard.dead]


    # ------------------------------------------------------------
    # generation
    # ------------------------------------------------------------
    def _build_floor(self) -> None:
        floor = self.tilemap.add_layer("floor")

        for row in range(MAP_ROWS):
            for col in range(MAP_COLS):
                floor[row][col] = self._gid(BASE_MATERIAL, row, col)

        others = [
            name for name in settings.FLOOR_MATERIALS if name != BASE_MATERIAL
        ]

        for _ in range(NUM_PATCHES):
            material = self._rng.choice(others)
            centre_row = self._rng.randrange(MAP_ROWS)
            centre_col = self._rng.randrange(MAP_COLS)
            radius = self._rng.randint(PATCH_MIN_RADIUS, PATCH_MAX_RADIUS)

            for row in range(centre_row - radius, centre_row + radius + 1):
                for col in range(centre_col - radius, centre_col + radius + 1):
                    if not self.tilemap.in_bounds(row, col):
                        continue

                    distance = ((row - centre_row) ** 2 + (col - centre_col) ** 2) ** 0.5

                    """ A soft edge rather than a circle: the closer to the
                    rim, the less likely the tile is replaced, which frays 
                    the boundary into something that reads as worn ground. """
                    if distance > radius or self._rng.random() < distance / radius:
                        continue

                    floor[row][col] = self._gid(material, row, col)

    @staticmethod
    def _gid(material: str, row: int, col: int) -> int:
        """ The tile of `material` that belongs at this spot.

        A material is a block of BLOCK_TILES x BLOCK_TILES tiles cut out
        of one continuous texture, so its tiles only join cleanly in the
        arrangement they were cut in. Repeating that arrangement across
        the map keeps every join invisible; picking a tile at random,
        which would look like the obvious way to add variety, puts
        neighbours together that never touched in the source and shows a
        hard edge at every one of them. """
        block = settings.BLOCK_TILES
        return (
            settings.FLOOR_FIRST_GID[material]
            + (row % block) * block
            + (col % block)
        )

    def _place_props(self) -> None:
        names = list(PROP_DEFS.keys())
        margin = EDGE_MARGIN_TILES * settings.TILE_SIZE
        attempts = 0

        while len(self.props) < NUM_PROPS and attempts < NUM_PROPS * 60:
            attempts += 1

            definition = PROP_DEFS[self._rng.choice(names)]
            candidate = Prop(
                definition,
                self._rng.uniform(margin, self.pixel_width - margin),
                self._rng.uniform(margin + 100, self.pixel_height - margin),
            )

            if not self.bounds.contains(candidate.solid_rect):
                continue

            spaced = candidate.solid_rect.inflate(MIN_PROP_GAP, MIN_PROP_GAP)

            if any(spaced.colliderect(prop.solid_rect) for prop in self.props):
                continue

            self.props.append(candidate)

    def _place_enemies(self) -> None:
        margin = EDGE_MARGIN_TILES * settings.TILE_SIZE
        centre = pygame.Vector2(self.pixel_width / 2, self.pixel_height / 2)
        attempts = 0

        while len(self.entities) < len(ENEMY_SPAWNS) and attempts < len(ENEMY_SPAWNS) * 60:
            attempts += 1

            x = self._rng.uniform(margin, self.pixel_width - margin)
            y = self._rng.uniform(margin + 100, self.pixel_height - margin)

            if (pygame.Vector2(x, y) - centre).length() < ENEMY_SPAWN_EXCLUSION_RADIUS:
                continue

            candidate = Enemy(ENEMY_SPAWNS[len(self.entities)], x, y, self)

            if self.blocked(candidate.feet_rect):
                continue

            self.entities.append(candidate)


    # ------------------------------------------------------------
    # rendering
    # ------------------------------------------------------------
    def render_floor(self, surface: pygame.Surface, camera: Any) -> None:
        self.tilemap.render(surface, camera)

    def render_telegraphs(self, surface: pygame.Surface, camera: Any) -> None:
        """ Every enemy attack warning, drawn flat on the ground right after
        the floor and before anything standing on it, so a red cone or
        circle never covers a sprite, whoever is standing inside it. """
        for entity in self.entities:
            entity.render_telegraph(surface, camera)

        for hazard in self.hazards:
            hazard.render_telegraph(surface, camera)

    def drawables(self, extra: List[Any]) -> List[Any]:
        """ Everything standing on the floor, ordered back to front.

        Normally the extra parametter is just the player, send by the PlayState

        Sorting by sort_y, the y of each thing's feet, is the whole trick
        behind walking behind a pillar: whoever is lower on the screen is
        nearer the camera, so it is drawn last and covers what is above
        it. Props, entities and projectiles all share the same anchor
        precisely so they can go into one list together. """
        return sorted(
            self.props + self.projectiles + self.hazards + self.entities + extra,
            key=lambda thing: thing.sort_y,
        )
