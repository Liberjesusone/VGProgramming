"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains the class Level: the floor, the scenery standing on
it, and the front-to-back ordering that makes the two read as one scene.

The level comes from one of two places. If the Tiled map at
TILED_MAP_PATH exists, it is built from that (see try_load_tilemap).
Otherwise it is generated in code, the procedural ruins the game started
with. Everything downstream only ever reads the tilemap, the prop, decor
and entity lists, blocked() and the two spawn points, so nothing else in
the game knows which of the two it got.

The generated layout is meant to be the same every time the game runs,
the way a hand-designed level would be, so generation is seeded (see
MAP_SEED) and uses its own random.Random instead of the global random
module. Using the global module here would have seeded every *other*
random roll in the game too, enemy AI, loot, damage, tying all of it to
the order level generation happens in and making bugs elsewhere depend on
level layout in ways that would be very hard to trace back.
"""

import random
from typing import Any, List, Optional, Set, Tuple

import pygame

from gale.tilemap import TileMap, Tileset

import settings
from src import audio
from src.definitions.props import PROP_DEFS
from src.entity.Enemy import Enemy
from src.world import tiled
from src.world.Decor import Decor
from src.world.Prop import Prop

# ------------------------------------------------------------
# Tiled map
# ------------------------------------------------------------
TILED_MAP_PATH = settings.BASE_DIR / "assets" / "maps" / "ruins_v2.tmj"

""" The only tile layer that blocks, and only on tiles marked
collision = solid. Every other tile layer is drawn and nothing more,
whatever its tiles are marked with. """
COLLISION_LAYER = "walls"

# ------------------------------------------------------------
# Procedural map
# ------------------------------------------------------------
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

# The props the generator picks from, the original five, so the seeded layout never changes.
PROCEDURAL_PROPS = [
    "broken_stone_pillar",
    "dead_leafless_tree",
    "mossy_boulder",
    "rusted_iron_brazier",
    "stone_sarcophagus",
]

# One enemy per entry, in this order.
ENEMY_SPAWNS = ["zombie", "zombie", "witch", "zombie", "golem", "witch"]

""" No enemy spawns this close to the map's centre, where the player
always starts (see spawn_point), so a run never opens with a guard
already standing on top of them. """
ENEMY_SPAWN_EXCLUSION_RADIUS = 160

""" The boss arena: a clear circle centred on the samurai's spawn, near the
top of the map and well away from where the player starts. Props are
removed from it and regular enemies kept further out still, see
_clear_arena and _place_enemies. """
BOSS_ARENA_Y = 260
BOSS_ARENA_RADIUS = 230
ARENA_PROP_MARGIN = 40
ARENA_ENEMY_MARGIN = 160

# Arbitrary. Change this to get a different fixed layout; the layout
# stays whatever this value produces until it is changed again.
MAP_SEED = 20260909

# No prop may stand within this many tiles of the map edge, so none is
# ever cut in half by the boundary the camera clamps to.
EDGE_MARGIN_TILES = 3

# Minimum gap between two props' solid bases, so the player can always
# walk between them instead of finding a wall of scenery.
MIN_PROP_GAP = 26

# ------------------------------------------------------------
# Spawn search
# ------------------------------------------------------------
# How far from the wanted spot, and in what steps, a free spot is searched for.
SPAWN_SEARCH_RADIUS = 400
SPAWN_SEARCH_STEP = 20
SPAWN_SEARCH_TRIES = 20
SPAWN_PROBE_SIZE = 40


class Level:
    def __init__(self) -> None:
        """ Own instance, not the global random module, see the module docstring
        for why. Every random call this class makes goes through it. """
        self._rng = random.Random(MAP_SEED)

        self.tilemap: TileMap = None
        self.props: List[Prop] = []

        # Scenery that is drawn and depth sorted like a prop but never blocks.
        self.decor: List[Decor] = []
        self.entities: List[Any] = []

        # (row, col) of every tile that blocks, empty for the generated map.
        self.solid_cells: Set[Tuple[int, int]] = set()

        # Where the player starts and where the samurai waits.
        self.player_start: Tuple[float, float] = (0.0, 0.0)
        self.boss_spawn: Tuple[float, float] = (0.0, 0.0)

        # The player's arrows currently in flight, they only ever hit enemies.
        self.projectiles: List[Any] = []

        # Enemy attacks still in flight (the witch's AreaShot), they only ever hit the player.
        self.hazards: List[Any] = []

        # The strongest camera shake asked for since PlayState last applied one.
        self.shake_request: Optional[Tuple[float, float]] = None

        if not self.try_load_tilemap():
            self._generate()

    # ------------------------------------------------------------
    # geometry
    # ------------------------------------------------------------
    @property
    def pixel_width(self) -> int:
        return self.tilemap.pixel_width

    @property
    def pixel_height(self) -> int:
        return self.tilemap.pixel_height

    @property
    def bounds(self) -> pygame.Rect:
        return pygame.Rect(0, 0, self.pixel_width, self.pixel_height)

    def spawn_point(self) -> Tuple[float, float]:
        return self.free_point_near(*self.player_start)

    def free_point_near(self, x: float, y: float) -> Tuple[float, float]:
        """ The first spot around (x, y), searched outward in growing
        squares, with room for a body and nothing blocking it. """
        half = SPAWN_PROBE_SIZE // 2

        for radius in range(0, SPAWN_SEARCH_RADIUS, SPAWN_SEARCH_STEP):
            for _ in range(SPAWN_SEARCH_TRIES):
                probe_x = x + self._rng.uniform(-radius, radius)
                probe_y = y + self._rng.uniform(-radius, radius)
                probe = pygame.Rect(round(probe_x) - half, round(probe_y) - half, SPAWN_PROBE_SIZE, SPAWN_PROBE_SIZE)

                if not self.blocked(probe):
                    return (probe_x, probe_y)

        return (x, y)

    def blocked(self, rect: pygame.Rect) -> bool:
        """ Whether something the size of rect can stand there. The map
        edge, every solid tile and every prop's base count. """
        if not self.bounds.contains(rect):
            return True

        if self.solid_cells and self._touches_solid_cell(rect):
            return True

        return any(part.colliderect(rect) for prop in self.props for part in prop.solid_rects)

    def _touches_solid_cell(self, rect: pygame.Rect) -> bool:
        """ Gets the amount of tiles that would overlap min 1, and max 4, of a normal
        given :param rect: then checks if those coords are in the solid_cells set 
        turning into a O(1) collision checks just as the move_and_collide gale function"""
        tile_width = self.tilemap.tile_width
        tile_height = self.tilemap.tile_height

        for row in range(rect.top // tile_height, (rect.bottom - 1) // tile_height + 1):
            for col in range(rect.left // tile_width, (rect.right - 1) // tile_width + 1):
                if (row, col) in self.solid_cells:
                    return True

        return False

    def in_arena(self, x: float, y: float, margin: float = 0.0) -> bool:
        """ True if the given coords are inside of the BOSS_ARENA_RADIUS"""
        distance = (pygame.Vector2(x, y) - pygame.Vector2(self.boss_spawn)).length()
        return distance <= BOSS_ARENA_RADIUS + margin

    def request_shake(self, magnitude: float, duration: float) -> None:
        """ Asked for by whatever lands a heavy blow; PlayState owns the
        camera and applies it. Two requests in the same frame keep the
        stronger one instead of the last one. """
        if self.shake_request is None or magnitude > self.shake_request[0]:
            self.shake_request = (magnitude, duration)


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

                # A fallen boss's body is still drawn but no longer there to hit.
                if not entity.hittable:
                    continue

                if entity.hurt_rect.collidepoint(arrow.x, arrow.y):
                    audio.play("arrow_impact_body")
                    entity.damage(arrow.damage)
                    entity.provoke()
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
    # Tiled map
    # ------------------------------------------------------------
    def try_load_tilemap(self) -> bool:
        """
        Builds the level from the Tiled map at TILED_MAP_PATH.

        Every tile layer is drawn, in the map's own order, whether or not
        it was left hidden in Tiled. Only COLLISION_LAYER blocks.

        Every tile object becomes what its tileset says it is, whichever
        object layer it was placed on: a prop, decor, an enemy, where the
        samurai waits, or where the player starts. See _place_object.

        :returns: Whether the map existed and the level was built from it.
        """
        if not TILED_MAP_PATH.exists():
            return False

        # Load the .tmj data
        map_data = tiled.load(TILED_MAP_PATH)
        map_tilesets = tiled.tilesets(map_data)
        cols, rows = map_data["width"], map_data["height"]

        self.tilemap = TileMap(map_data["tilewidth"], map_data["tileheight"], cols, rows)
        solid = tiled.solid_gids(map_tilesets)
        used_gids: Set[int] = set()

        # Load the Tile-Layers (floor, walls, visual_adjust), where the collision tiles are
        for layer in map_data["layers"]:
            if layer["type"] != "tilelayer":
                continue

            gids = [gid & tiled.GID_MASK for gid in layer["data"]]
            used_gids.update(gids)
            self.tilemap.add_layer(layer["name"], [gids[row * cols:(row + 1) * cols] for row in range(rows)])

            if layer["name"] == COLLISION_LAYER:
                self.solid_cells = {divmod(index, cols) for index, gid in enumerate(gids) if gid in solid}

        # Load the used tilesets, checking if they contain at leats one of the used_gids 
        used_gids.discard(0)

        for map_tileset in map_tilesets:
            if any(map_tileset.contains(gid) for gid in used_gids):
                image = pygame.image.load(settings.TILESETS_DIR / f"{map_tileset.name}.png").convert_alpha()
                self.tilemap.add_tileset(
                    Tileset(image, map_tileset.tile_width, map_tileset.tile_height, first_gid=map_tileset.first_gid)
                )

        # Iterate for all the objects in the Object-Layers
        self._markers = {"player": None, "bonfire": None, "seats": []}

        for layer in map_data["layers"]:
            if layer["type"] != "objectgroup":
                continue

            for obj in layer["objects"]:
                if "gid" not in obj:
                    continue

                gid = obj["gid"] & tiled.GID_MASK
                map_tileset = tiled.tileset_for(map_tilesets, gid) # The current gid's tileset
                x, y = tiled.feet(obj, map_tileset)      # The y anchor we are used to use
                self._place_object(map_tileset.name, map_tileset.region(gid), x, y)

        self.player_start = self._resolve_player_start()
        return True

    def _place_object(self, tileset: str, region: str, x: float, y: float) -> None:
        """ Turns one tile object into what its tileset says it is. Only
        the tileset decides, not the layer, so an object dropped on the
        wrong layer still becomes the right thing. 
        :param region: is the name of the tile, got by the tiled class that loads the data
        from our .json that are next to every tileset.png """
        if tileset == "props":
            self.props.append(Prop(PROP_DEFS[region], x, y))
        elif tileset in ("decor", "bonfire"):
            self.decor.append(Decor(settings.TILESETS[tileset][region], x, y))

            if tileset == "bonfire" and self._markers["bonfire"] is None:
                self._markers["bonfire"] = (x, y)
            elif region.startswith("bonfire_seats"):
                self._markers["seats"].append((x, y))
        elif tileset == "enemies":
            # enemy_<kind>_<pose>_<direction>
            self.entities.append(Enemy(region.split("_")[1], x, y, self))
        elif tileset == "bosses":
            self.boss_spawn = (x, y)
        elif tileset == "player" and self._markers["player"] is None:
            self._markers["player"] = (x, y)

    def _resolve_player_start(self) -> Tuple[float, float]:
        """ Where the player starts, in order of preference: an archer
        placed from the player tileset; the bonfire, where a run of a
        souls-like begins; the middle of the bonfire seating, which marks
        the rest area even before the bonfire itself is placed; or, with
        none of them, the middle of the map.

        The middle of the seating is the median of their positions, not
        the mean, so a few seats placed elsewhere on the map do not drag
        the start away from where most of them are. """
        if self._markers["player"] is not None:
            return self._markers["player"]

        if self._markers["bonfire"] is not None:
            return self._markers["bonfire"]

        seats = self._markers["seats"]

        if seats:
            middle = len(seats) // 2
            return (sorted(x for x, _ in seats)[middle], sorted(y for _, y in seats)[middle])

        return (self.pixel_width / 2, self.pixel_height / 2)


    # ------------------------------------------------------------
    # Procedural map
    # ------------------------------------------------------------
    def _generate(self) -> None:
        self.tilemap = TileMap(settings.TILE_SIZE, settings.TILE_SIZE, MAP_COLS, MAP_ROWS)

        for tileset in settings.FLOOR_TILESETS.values():
            self.tilemap.add_tileset(tileset)

        self._build_floor()
        self._place_props()

        # Where the samurai waits, see BOSS_ARENA_Y. BossFight spawns him there.
        self.boss_spawn = (self.pixel_width / 2, BOSS_ARENA_Y)
        self._clear_arena()
        self._place_enemies()

        self.player_start = (self.pixel_width / 2, self.pixel_height / 2)

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
        margin = EDGE_MARGIN_TILES * settings.TILE_SIZE
        attempts = 0

        while len(self.props) < NUM_PROPS and attempts < NUM_PROPS * 60:
            attempts += 1

            definition = PROP_DEFS[self._rng.choice(PROCEDURAL_PROPS)]
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

    def _clear_arena(self) -> None:
        """ Removes every prop standing inside the boss arena, so both forms
        have room to dash, strafe and flee instead of snagging on scenery.
        Filtering after placement, rather than rejecting positions while
        placing, keeps every other prop exactly where the seed put it. """
        self.props = [
            prop for prop in self.props
            if not self.in_arena(prop.solid_rect.centerx, prop.solid_rect.centery, margin=ARENA_PROP_MARGIN)
        ]

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

            # Regular enemies are kept well clear of the boss, so neither fight spills into the other.
            if self.in_arena(x, y, margin=ARENA_ENEMY_MARGIN):
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
        it. Props, decor, entities and projectiles all share the same
        anchor precisely so they can go into one list together. """
        return sorted(
            self.props + self.decor + self.projectiles + self.hazards + self.entities + extra,
            key=lambda thing: thing.sort_y,
        )
