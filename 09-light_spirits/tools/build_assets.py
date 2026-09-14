"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

Turns the raw generated art in assets/source into the tilesets both the
game and Tiled load, in assets/tilesets: one PNG per category, plus a JSON
index naming every region inside it. Run it by hand whenever a source
image changes. The game never processes art itself, it only slices the
finished tilesets back into textures (see settings.py).

assets/source holds the full resolution originals and is kept out of the
repository for its size, so this script only runs where those originals
live. A source that is missing is skipped with a message, never an error.

Map tilesets (floors, walls, fences, forest, rocks, cliffs) sit on the
same 32 px grid as the map, so Tiled can paint with them directly: every
region in them spans a whole number of tiles.

Sprite tilesets (player, enemies, bosses, props, decor, bonfire, hud) use
one uniform cell per tileset, sized for its largest sprite. Each sprite
sits bottom centre in its cell, the way Tiled anchors tile objects, and
the index stores its exact rect, so the game gets back the tight sprite
and never the padding around it.

The image generator cannot produce a real alpha channel, so every prompt
asks for a flat magenta background, cleared here by two rules, because
neither one alone is right:

Anything very nearly pure magenta goes, wherever it is. The brazier needs
this: the openings in its rim are background enclosed by metal,
unreachable from the outside.

Anything only roughly magenta goes only if it can be reached from the
image border. That protects a sprite that genuinely contains a purple or
pink detail from having it punched out.

The bonfire flames are the one exception: they came back on black, which
suits fire anyway, and their brightness becomes their alpha.
"""

import collections
import json
import math
import pathlib
import sys

import numpy
import pygame

pygame.init()
pygame.display.set_mode((1, 1))

BASE = pathlib.Path(__file__).resolve().parent.parent
SOURCE = BASE / "assets" / "source"
OUTPUT = BASE / "assets" / "tilesets"

TILE_SIZE = 32
BLOCK_TILES = 8
BLOCK_SIZE = TILE_SIZE * BLOCK_TILES

MAGENTA = (255, 0, 255)

# Near enough to the background colour to be background no matter where
# it sits. Tight, so a sprite's own colours are never caught by it.
MAGENTA_PURE_TOLERANCE = 25

# Roughly magenta. Only removed when it can be reached from the border,
# since at this distance a sprite's own detail could look like this too.
MAGENTA_LOOSE_TOLERANCE = 60

# Pixels of the antialiased rim between sprite and background to discard.
EDGE_TRIM = 2

""" Sheets come back with noisy magenta, and small pockets of it trapped
between an arm and the body are neither pure enough for the pure rule nor
reachable by the flood fill. For sheets and a few pieces, any pixel whose
red and blue both clearly dominate a near absent green is background too.
Red hair, rust, fire or amber all have low blue and are never caught;
props never use this, since the brazier's fire really is that colour. """
MAGENTA_HUE_MIN = 110
MAGENTA_HUE_GREEN_RATIO = 0.6

""" The same test extended to dark magenta, where a dark detail was
antialiased against the background (the foot of a cliff face, thin iron
bars). Those pixels are recoloured grey rather than removed, see
neutralised. A dark pixel only counts if its red and blue are also
balanced within MAGENTA_DARK_BALANCE of each other, which keeps crimson
and rust out. Used on new map pieces, props and the hud, never on the
bosses, whose purple smoke is part of the drawing. """
MAGENTA_DARK_MIN = 40
MAGENTA_DARK_BALANCE = 0.7

""" A row or column of a sheet counts as occupied only if it holds at
least SHEET_NOISE_PIXELS sprite pixels and SHEET_NOISE_FRACTION of the
busiest row or column, so stray specks and thin wisps of smoke drifting
between two rows don't glue them together into one. """
SHEET_NOISE_PIXELS = 3
SHEET_NOISE_FRACTION = 0.02

# Background kept around each cell cut from a sheet, so the flood fill
# always has magenta border to start from.
SHEET_CELL_PADDING = 10

""" Light drawn on black (the flames). A channel value above
LIGHT_OCCUPIED marks a pixel as flame when splitting the sheet. Anything
up to LIGHT_FLOOR is the soft glow around the flame and becomes fully
transparent: kept, it would end in a hard rectangle wherever the cell is
cropped, and the game draws its own glow instead. """
LIGHT_OCCUPIED = 120
LIGHT_CELL_PADDING = 24
LIGHT_CROP_ALPHA = 20
LIGHT_FLOOR = 60

# Pixels cross faded across the two ends of a strip, so it wraps around
# onto itself without a visible seam.
SEAM_OVERLAP = 8

# The three directions every character sheet is drawn in. "left" is never
# generated: it is always "right" mirrored, which also guarantees the two
# are perfectly symmetric.
SHEET_DIRECTIONS = ("down", "up", "right")
DIRECTIONS = ("down", "up", "left", "right")


# ------------------------------------------------------------
# Map tilesets
# ------------------------------------------------------------
""" Every entry is (kind, source, size):

block: a seamless square texture, becomes BLOCK_TILES x BLOCK_TILES tiles
    that still join cleanly, since the source was one continuous image.
block_alpha: the same, but keeping transparency where the source is magenta.
strip_h / strip_v: a strip that repeats left to right / top to bottom.
    size is its thickness in tiles; its length is whatever keeps its
    proportions, rounded to whole tiles.
piece: a single object fitted inside a block of (width, height) tiles,
    standing bottom centre, used for the ends and corners strips can't do.
mirror: size names another region of the same tileset, flipped left to right.

The floors keep their original material names without the "floor_"
prefix, so the five the level already uses keep the same textures. """
FLOORS = {
    "weathered_cracked_stone_slabs": "weathered_cracked_stone_slabs",
    "damp_mossy_cobblestone": "damp_mossy_cobblestone",
    "wet_dark_packed_earth_with_small_pebbles": "wet_dark_packed_earth_with_small_pebbles",
    "rotten_wooden_planks": "rotten_wooden_planks",
    "grey_ash_and_fine_gravel": "grey_ash_and_fine_gravel",
    "royal_marble": "floor_royal_marble",
    "black_marble": "floor_black_marble",
    "cracked_marble": "floor_cracked_marble",
    "calm_grass": "floor_calm_grass",
    "grass_stepping_stones": "floor_grass_stepping_stones",
    "dark_shrine_flagstones": "floor_dark_shrine_flagstones",
    "black_ash_gravel": "floor_black_ash_gravel",
    "cracked_temple_stone": "floor_cracked_temple_stone",
}

MAP_TILESETS = {
    "floors": {f"floor_{name}": ("block", source, None) for name, source in FLOORS.items()},
    "walls": {
        "wall_stone_front": ("strip_h", "wall_stone_front", 3),
        "wall_stone_front2": ("strip_h", "wall_stone_front2", 3),
        "wall_stone_side": ("strip_v", "wall_stone_side", 1),
        "wall_stone_pillar": ("piece", "wall_stone_pillar", (2, 4)),
        "wall_marble_front": ("strip_h", "wall_marble_front", 3),
        "wall_marble_side": ("strip_v", "wall_marble_side", 1),
        "wall_marble_pillar": ("piece", "wall_marble_pillar", (2, 4)),
    },
    "fences": {
        "fence_wood_front": ("strip_h", "fence_wood_front", 2),
        "fence_wood_side": ("strip_v", "fence_wood_side", 1),
        "fence_iron_front": ("strip_h", "fence_iron_front", 2),
        "fence_iron_side": ("strip_v", "fence_iron_side", 1),
    },
    "forest": {
        "forest_canopy": ("block", "forest_canopy", None),
        "forest_edge_south": ("strip_h", "forest_edge_south", 4),
        "forest_edge_north": ("strip_h", "forest_edge_north", 3),
        "forest_edge_east": ("strip_v", "forest_edge_side", 3),
        "forest_edge_west": ("mirror", None, "forest_edge_east"),
    },
    "rocks": {
        "rock_field": ("block", "rock_field", None),
        "hill_edge_south": ("strip_h", "hill_edge_south", 3),
        "hill_edge_east": ("strip_v", "hill_edge_side", 3),
        "hill_edge_west": ("mirror", None, "hill_edge_east"),
    },
    "cliffs": {
        "cliff_edge_south": ("strip_h", "cliff_edge_south", 4),
        "cliff_edge_north": ("strip_h", "cliff_edge_north", 3),
        "cliff_edge_east": ("strip_v", "cliff_edge_east", 3),
        "cliff_edge_west": ("mirror", None, "cliff_edge_east"),
        "cliff_corner_southeast": ("piece", "cliff_outer_corner", (4, 5)),
        "cliff_corner_southwest": ("mirror", None, "cliff_corner_southeast"),
        "abyss_clouds": ("block", "abyss_clouds", None),
        "abyss_mist": ("block_alpha", "abyss_mist", None),
    },
}


# ------------------------------------------------------------
# Sprite tilesets
# ------------------------------------------------------------
""" The player's poses, each generated as one image per direction. Source
filenames follow whatever order they came back in (direction before the
pose, e.g. archer_bow_down_charge_1), unrelated to the region names this
writes, always archer_<pose>_<direction>. "down" for bow_idle points at
archer_down_2, a second take picked over the first on looks alone. """
PLAYER_POSES = {
    "bow_idle": {"down": "archer_down_2", "up": "archer_up", "right": "archer_right"},
    "bow_walk": {"down": "archer_down_walk_1", "up": "archer_up_walk_1", "right": "archer_right_walk_1"},
    "bow_charge1": {"down": "archer_bow_down_charge_1", "up": "archer_bow_up_charge_1", "right": "archer_bow_right_charge_1"},
    "bow_charge2": {"down": "archer_bow_down_charge_2", "up": "archer_bow_up_charge_2", "right": "archer_bow_right_charge_2"},
    "bow_release": {"down": "archer_bow_down_attack", "up": "archer_bow_up_attack", "right": "archer_bow_right_attack"},
    "sword_idle": {"down": "archer_sword_down", "up": "archer_sword_up", "right": "archer_sword_right"},
    "sword_walk": {"down": "archer_sword_down_walk_1", "up": "archer_sword_up_walk_1", "right": "archer_sword_right_walk_1"},
    "sword_charge1": {"down": "archer_sword_down_charge_1", "up": "archer_sword_up_charge_1", "right": "archer_sword_right_charge_1"},
    "sword_charge2": {"down": "archer_sword_down_charge_2", "up": "archer_sword_up_charge_2", "right": "archer_sword_right_charge_2"},
    "sword_attack": {"down": "archer_sword_down_attack", "up": "archer_sword_up_attack", "right": "archer_sword_right_attack"},
    "roll1": {"down": "archer_roll1_down", "up": "archer_roll1_up", "right": "archer_roll1_right"},
    "roll2": {"down": "archer_roll2_down", "up": "archer_roll2_up", "right": "archer_roll2_right"},
    "roll3": {"down": "archer_roll3_down", "up": "archer_roll3_up", "right": "archer_roll3_right"},
}

# settings.PLAYER_HEIGHT: every standing pose is scaled to it.
CHARACTER_HEIGHT = 64

# Sitting at the bonfire, only drawn facing the camera, noticeably lower than standing.
PLAYER_RESTING = ("archer_resting", 44)

""" Enemies and bosses arrive as sprite sheets: 3 rows (down, up, right)
by 5 columns. The number is the height the idle pose ends up at, in game
pixels; every other pose of the kind is scaled by that same factor rather
than each to that height, so a raised weapon or a crouch keeps its size
relative to the body. A kind without a sheet can instead come as separate
files, enemy_<kind>_<pose>_<direction>.png. """
ENEMY_POSES = ("idle", "walk", "charge1", "charge2", "attack")
ENEMIES = {"zombie": 64, "witch": 64, "golem": 96}

# A boss's second sheet has no idle of its own, so it reuses the first sheet's scale.
BOSSES = {
    "samurai": (
        128,
        [
            ("boss_samurai_sheet", ENEMY_POSES),
            ("boss_samurai_sheet2", ("ground_charge1", "ground_charge2", "ground_attack", "transition", "defeated")),
        ],
    ),
    "spirit": (
        128,
        [
            ("boss_spirit_sheet", ENEMY_POSES),
            ("boss_spirit_sheet2", ("emerge", "melee_charge", "melee_attack", "defeated", "dissolve")),
        ],
    ),
}

""" Props, with the height in game pixels each one ends up at. The player
is 64 px tall, so these read against that: the boulder comes up to the
shoulder, the pillar is twice the player's height, the torii towers over
everything. Widths follow each source's own proportions. """
PROPS = {
    "broken_stone_pillar": 112,
    "dead_leafless_tree": 160,
    "mossy_boulder": 64,
    "rusted_iron_brazier": 80,
    "stone_sarcophagus": 88,
    "broken_torii_gate": 176,
    "stone_lantern": 72,
    "dead_black_pine": 160,
    "katana_grave": 56,
    "tattered_war_banner": 128,
    "fallen_shrine_bell": 64,
    "armor_remains": 48,
}

LEGACY_PROPS = ("broken_stone_pillar", "dead_leafless_tree", "mossy_boulder", "rusted_iron_brazier", "stone_sarcophagus")

# Sheets of 3 rows by 5 columns of small objects: (source, height of the tallest one).
DECOR_SHEETS = {
    "calm_decor": ("calm_decor_sheet", 40),
    "marble_decor": ("marble_decor_sheet", 56),
    "rocks": ("rocks_sheet", 64),
    "bonfire_seats": ("bonfire_seats", 48),
}

BONFIRE_PIECES = {
    "bonfire_unlit": ("bonfire_unlit", 56),
    "bonfire_lit_base": ("bonfire_lit_base", 56),
    "bonfire_scorched_ground": ("bonfire_scorched_ground", 40),
}

# Animation sheets of 2 rows by 4 columns: (source, height of the tallest frame, background).
BONFIRE_ANIMATIONS = {
    "bonfire_flame_a": ("bonfire_flames_sheet", 40, "light"),
    "bonfire_flame_b": ("bonfire_flames_sheet2", 40, "light"),
    "bonfire_kindle": ("bonfire_kindle_sheet", 72, "magenta"),
    "bonfire_embers": ("bonfire_embers_sheet", 28, "magenta"),
}

HUD = {
    "hud_slot": ("hud_slot", 40),
    "hud_flask_full": ("hud_flask_full", 30),
    "hud_flask_empty": ("hud_flask_empty", 30),
    "hud_bow": ("hud_bow", 30),
    "hud_sword": ("hud_sword", 30),
    "hud_quiver": ("hud_quiver", 30),
    "bonfire_banner": ("bonfire_banner", 48),
}


# ------------------------------------------------------------
# Background removal
# ------------------------------------------------------------
def load_source(name: str):
    path = SOURCE / f"{name}.png"

    if not path.exists():
        print(f"    falta {name}.png, se omite")
        return None

    return pygame.image.load(path).convert()


def background_mask(surface: pygame.Surface, tolerance: int) -> numpy.ndarray:
    """ Boolean mask, True where the pixel is within `tolerance` of magenta. """
    rgb = pygame.surfarray.array3d(surface).astype(numpy.int16)
    return (
        (numpy.abs(rgb[:, :, 0] - MAGENTA[0]) <= tolerance)
        & (rgb[:, :, 1] <= tolerance)
        & (numpy.abs(rgb[:, :, 2] - MAGENTA[2]) <= tolerance)
    )


def magenta_hue_mask(surface: pygame.Surface, dark: bool = False) -> numpy.ndarray:
    rgb = pygame.surfarray.array3d(surface).astype(numpy.int16)
    red, green, blue = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    if not dark:
        return (
            (red > MAGENTA_HUE_MIN)
            & (blue > MAGENTA_HUE_MIN)
            & (green < MAGENTA_HUE_GREEN_RATIO * numpy.minimum(red, blue))
        )

    return (
        (numpy.minimum(red, blue) > MAGENTA_DARK_MIN)
        & (green < MAGENTA_HUE_GREEN_RATIO * numpy.minimum(red, blue))
        & (blue > MAGENTA_DARK_BALANCE * red)
        & (red > MAGENTA_DARK_BALANCE * blue)
    )


def neutralised(source: pygame.Surface) -> pygame.Surface:
    """ A copy of source with every dark magenta pixel turned to the grey of
    its own brightness. These are dark edges tinted by the background, not
    background themselves: removing them would erase thin details like
    iron bars outright, while grey is what they were meant to be. """
    copy = source.copy()
    tinted = magenta_hue_mask(copy, dark=True)
    rgb = pygame.surfarray.pixels3d(copy)
    grey = (rgb[tinted].astype(numpy.float32) @ numpy.array([0.3, 0.59, 0.11], dtype=numpy.float32))
    rgb[tinted] = numpy.clip(grey, 0, 255).astype(numpy.uint8)[:, None]
    del rgb
    return copy


def outside_mask(is_background: numpy.ndarray) -> numpy.ndarray:
    """ Flood fill inward from every border pixel, so only background that
    is genuinely connected to the outside is marked. A plain colour test
    would also erase anything inside the sprite that happens to be near
    magenta, and the brazier's fire is exactly that colour. """
    width, height = is_background.shape
    background = is_background.reshape(-1)
    outside = bytearray(width * height)
    queue = collections.deque()

    def push(index: int) -> None:
        if background[index] and not outside[index]:
            outside[index] = 1
            queue.append(index)

    # surfarray is indexed [x][y], so a flat index is x * height + y.
    for x in range(width):
        push(x * height)
        push(x * height + height - 1)

    for y in range(height):
        push(y)
        push((width - 1) * height + y)

    while queue:
        index = queue.popleft()
        x, y = divmod(index, height)

        if x > 0:
            push(index - height)
        if x < width - 1:
            push(index + height)
        if y > 0:
            push(index - 1)
        if y < height - 1:
            push(index + 1)

    return numpy.frombuffer(bytes(outside), dtype=numpy.uint8).reshape(width, height).astype(bool)


def grow(mask: numpy.ndarray, steps: int) -> numpy.ndarray:
    """ Expands a mask by `steps` pixels in the four directions. """
    grown = mask.copy()

    for _ in range(steps):
        step = grown.copy()
        step[1:, :] |= grown[:-1, :]
        step[:-1, :] |= grown[1:, :]
        step[:, 1:] |= grown[:, :-1]
        step[:, :-1] |= grown[:, 1:]
        grown = step

    return grown


def bleed_colours(rgb: numpy.ndarray, hole: numpy.ndarray, steps: int) -> None:
    """
    Spreads the sprite's own colours outward into the area that is about
    to become transparent, in place.

    pygame's smoothscale averages colour and alpha separately and does not
    premultiply, so an output pixel mixing a branch (alpha 255) with the
    background (alpha 0) still averages the background's colour into the
    result, and every thin feature would come out pink. Filling the hole
    with neighbouring sprite colours first keeps the edges clean. The
    reach has to cover the downscaling kernel, roughly the shrink factor.
    """
    filled = ~hole

    for _ in range(steps):
        for axis, shift in ((0, 1), (0, -1), (1, 1), (1, -1)):
            neighbour_rgb = numpy.roll(rgb, shift, axis=axis)
            neighbour_filled = numpy.roll(filled, shift, axis=axis)
            take = neighbour_filled & ~filled
            rgb[take] = neighbour_rgb[take]
            filled = filled | take


def reach_for(shrink: float) -> int:
    return max(4, round(shrink) + 4)


def background_of(
    source: pygame.Surface, strip_magenta_hue: bool = False, dark_magenta: bool = False
) -> numpy.ndarray:
    """ Everything that is background in source, already widened by EDGE_TRIM
    to drop the antialiased rim the generator leaves around the sprite. """
    pure = background_mask(source, MAGENTA_PURE_TOLERANCE)
    loose = background_mask(source, MAGENTA_LOOSE_TOLERANCE)
    outside = outside_mask(loose) | pure

    if strip_magenta_hue or dark_magenta:
        outside |= magenta_hue_mask(source)

    return grow(outside, EDGE_TRIM)


def box_of(outside: numpy.ndarray) -> pygame.Rect:
    columns = numpy.where(~outside.all(axis=1))[0]
    rows = numpy.where(~outside.all(axis=0))[0]
    return pygame.Rect(
        int(columns[0]), int(rows[0]),
        int(columns[-1] - columns[0] + 1), int(rows[-1] - rows[0] + 1),
    )


def finish(source: pygame.Surface, outside: numpy.ndarray, reach: int, box: pygame.Rect) -> pygame.Surface:
    """ Makes the background transparent, bleeds colour into it, and crops to box. """
    cut = source.convert_alpha()

    rgb = pygame.surfarray.pixels3d(cut)
    bleed_colours(rgb, outside, reach)
    del rgb

    alpha = pygame.surfarray.pixels_alpha(cut)
    alpha[outside] = 0
    del alpha

    return cut.subsurface(box).copy()


def fit_height(surface: pygame.Surface, height: int) -> pygame.Surface:
    width = max(1, round(surface.get_width() * height / surface.get_height()))
    return pygame.transform.smoothscale(surface, (width, height))


def cut_out_sprite(
    source: pygame.Surface, height: int, strip_magenta_hue: bool = False, dark_magenta: bool = False
) -> pygame.Surface:
    """ One sprite, cleared of its background, cropped tight and scaled to height. """
    outside = background_of(source, strip_magenta_hue, dark_magenta)

    if dark_magenta:
        source = neutralised(source)

    cropped = finish(source, outside, reach_for(source.get_height() / height), box_of(outside))
    return fit_height(cropped, height)


def mirrored(surface: pygame.Surface) -> pygame.Surface:
    return pygame.transform.flip(surface, True, False)


# ------------------------------------------------------------
# Sheets
# ------------------------------------------------------------
def _bands(occupied: numpy.ndarray, count: int):
    """
    Groups consecutive True entries of a 1D occupancy array into
    (start, end) bands, then merges the two bands with the smallest gap
    between them until exactly `count` remain. A gap inside one sprite (a
    bow held clear of the body) is always narrower than the gap between two
    sprites, so it is the first to be merged away.

    :returns: The bands, or None if there were fewer than count to begin with.
    """
    bands = []
    start = None

    for index, value in enumerate(occupied):
        if value and start is None:
            start = index
        elif not value and start is not None:
            bands.append([start, index])
            start = None

    if start is not None:
        bands.append([start, len(occupied)])

    if len(bands) < count:
        return None

    while len(bands) > count:
        gaps = [bands[i + 1][0] - bands[i][1] for i in range(len(bands) - 1)]
        i = gaps.index(min(gaps))
        bands[i] = [bands[i][0], bands[i + 1][1]]
        del bands[i + 1]

    return bands


def _occupied_lines(counts: numpy.ndarray) -> numpy.ndarray:
    return counts >= max(SHEET_NOISE_PIXELS, SHEET_NOISE_FRACTION * counts.max())


def split_sheet(sheet: pygame.Surface, rows: int, columns: int, occupied: numpy.ndarray, padding: int):
    """
    Cuts a sheet into its cells by where the sprites actually are, not by
    dividing the image into equal parts: an image generator lays a grid out
    roughly, never to the pixel. Rows are found first from which pixel rows
    hold anything, then columns within each row the same way.

    :param occupied: [x][y] mask of pixels that belong to some sprite.
    :returns: The cells' rects in reading order, or None if the sheet does
        not split into rows by columns.
    """
    row_bands = _bands(_occupied_lines(occupied.sum(axis=0)), rows)

    if row_bands is None:
        return None

    rects = []

    for top, bottom in row_bands:
        column_bands = _bands(_occupied_lines(occupied[:, top:bottom].sum(axis=1)), columns)

        if column_bands is None:
            return None

        for left, right in column_bands:
            rect = pygame.Rect(left, top, right - left, bottom - top)
            rects.append(rect.inflate(padding * 2, padding * 2).clip(sheet.get_rect()))

    return rects


def magenta_cells(sheet: pygame.Surface, rows: int, columns: int):
    """ Splits a magenta sheet and clears every cell's background, all at
    full resolution: (cell, outside mask, tight box) per cell, not yet
    scaled, so the caller can pick one scale for the whole sheet first. """
    occupied = ~background_mask(sheet, MAGENTA_LOOSE_TOLERANCE)
    rects = split_sheet(sheet, rows, columns, occupied, SHEET_CELL_PADDING)

    if rects is None:
        return None

    cells = []

    for rect in rects:
        cell = sheet.subsurface(rect).copy()
        outside = background_of(cell, strip_magenta_hue=True)
        cells.append((cell, outside, box_of(outside)))

    return cells


def scale_cells(cells, scale: float):
    """ Finishes every cell from magenta_cells at one shared scale. """
    finished = []

    for cell, outside, box in cells:
        cropped = finish(cell, outside, reach_for(1 / scale), box)
        height = max(1, round(box.height * scale))
        finished.append(fit_height(cropped, height))

    return finished


def light_cells(sheet: pygame.Surface, rows: int, columns: int):
    """ Splits a sheet of light drawn on black, turning brightness into
    alpha and un-premultiplying the colour, so a flame keeps its full hue at
    the faint edge of its glow instead of fading towards black. """
    rgb = pygame.surfarray.array3d(sheet)
    occupied = rgb.max(axis=2) > LIGHT_OCCUPIED
    rects = split_sheet(sheet, rows, columns, occupied, LIGHT_CELL_PADDING)

    if rects is None:
        return None

    cells = []

    for rect in rects:
        cell_rgb = rgb[rect.x:rect.right, rect.y:rect.bottom].astype(numpy.float32)
        value = cell_rgb.max(axis=2)
        alpha = numpy.clip((value - LIGHT_FLOOR) * 255.0 / (255.0 - LIGHT_FLOOR), 0, 255)
        colour = cell_rgb * (255.0 / numpy.maximum(value, 1.0))[:, :, None]

        cell = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.surfarray.pixels3d(cell)[:] = numpy.clip(colour, 0, 255).astype(numpy.uint8)
        pygame.surfarray.pixels_alpha(cell)[:] = alpha.astype(numpy.uint8)

        visible = alpha > LIGHT_CROP_ALPHA
        columns_on = numpy.where(visible.any(axis=1))[0]
        rows_on = numpy.where(visible.any(axis=0))[0]
        box = pygame.Rect(
            int(columns_on[0]), int(rows_on[0]),
            int(columns_on[-1] - columns_on[0] + 1), int(rows_on[-1] - rows_on[0] + 1),
        )
        cells.append(cell.subsurface(box).copy())

    return cells


# ------------------------------------------------------------
# Map tileset pieces
# ------------------------------------------------------------
def snap(pixels: float) -> int:
    return max(TILE_SIZE, round(pixels / TILE_SIZE) * TILE_SIZE)


def wrap_seam(surface: pygame.Surface, horizontal: bool) -> pygame.Surface:
    """
    Makes a strip repeat onto itself without a seam, and returns it
    SEAM_OVERLAP pixels shorter along its length.

    The first SEAM_OVERLAP pixels are cross faded from the strip's own last
    SEAM_OVERLAP pixels into its first ones, and that tail is then dropped.
    Laid end to end, the strip's new last pixel is followed by what used to
    come right after it in the source, so the two copies meet exactly
    where the original image was already continuous.
    """
    rgb = pygame.surfarray.array3d(surface).astype(numpy.float32)
    alpha = pygame.surfarray.array_alpha(surface).astype(numpy.float32)[:, :, None]
    pixels = numpy.concatenate([rgb, alpha], axis=2)

    if not horizontal:
        pixels = pixels.transpose(1, 0, 2)

    length = pixels.shape[0] - SEAM_OVERLAP
    t = (numpy.arange(SEAM_OVERLAP, dtype=numpy.float32) / SEAM_OVERLAP)[:, None, None]
    pixels[:SEAM_OVERLAP] = pixels[length:] * (1 - t) + pixels[:SEAM_OVERLAP] * t
    pixels = pixels[:length]

    if not horizontal:
        pixels = pixels.transpose(1, 0, 2)

    out = pygame.Surface((pixels.shape[0], pixels.shape[1]), pygame.SRCALPHA)
    pygame.surfarray.pixels3d(out)[:] = numpy.clip(pixels[:, :, :3], 0, 255).astype(numpy.uint8)
    pygame.surfarray.pixels_alpha(out)[:] = numpy.clip(pixels[:, :, 3], 0, 255).astype(numpy.uint8)
    return out


def build_strip(source: pygame.Surface, horizontal: bool, thickness_tiles: int) -> pygame.Surface:
    outside = background_of(source, dark_magenta=True)
    source = neutralised(source)
    box = box_of(outside)

    # Only trimmed across the strip's thickness: along its length both ends
    # must stay whole, since they are what wrap onto each other.
    if horizontal:
        box = pygame.Rect(0, box.y, source.get_width(), box.height)
    else:
        box = pygame.Rect(box.x, 0, box.width, source.get_height())

    thickness = thickness_tiles * TILE_SIZE
    across, along = (box.height, box.width) if horizontal else (box.width, box.height)
    scale = thickness / across
    length = snap(along * scale)

    cropped = finish(source, outside, reach_for(1 / scale), box)
    size = (length + SEAM_OVERLAP, thickness) if horizontal else (thickness, length + SEAM_OVERLAP)
    return wrap_seam(pygame.transform.smoothscale(cropped, size), horizontal)


def build_block(source: pygame.Surface, keep_alpha: bool) -> pygame.Surface:
    if not keep_alpha:
        return pygame.transform.smoothscale(source, (BLOCK_SIZE, BLOCK_SIZE))

    outside = background_of(source, dark_magenta=True)
    source = neutralised(source)
    whole = finish(source, outside, reach_for(source.get_height() / BLOCK_SIZE), source.get_rect())
    return pygame.transform.smoothscale(whole, (BLOCK_SIZE, BLOCK_SIZE))


def build_piece(source: pygame.Surface, tiles) -> pygame.Surface:
    width, height = tiles[0] * TILE_SIZE, tiles[1] * TILE_SIZE
    outside = background_of(source, dark_magenta=True)
    source = neutralised(source)
    box = box_of(outside)
    scale = min(width / box.width, height / box.height)

    cropped = finish(source, outside, reach_for(1 / scale), box)
    fitted = pygame.transform.smoothscale(
        cropped, (max(1, round(box.width * scale)), max(1, round(box.height * scale)))
    )

    block = pygame.Surface((width, height), pygame.SRCALPHA)
    block.blit(fitted, ((width - fitted.get_width()) // 2, height - fitted.get_height()))
    return block


def build_map_tileset(entries) -> dict:
    regions = {}

    for name, (kind, source_name, size) in entries.items():
        if kind == "mirror":
            if size in regions:
                regions[name] = mirrored(regions[size])
            continue

        source = load_source(source_name)

        if source is None:
            continue

        if kind in ("block", "block_alpha"):
            regions[name] = build_block(source, keep_alpha=kind == "block_alpha")
        elif kind in ("strip_h", "strip_v"):
            regions[name] = build_strip(source, kind == "strip_h", size)
        elif kind == "piece":
            regions[name] = build_piece(source, size)

    return regions


# ------------------------------------------------------------
# Sprite tileset contents
# ------------------------------------------------------------
def with_left(regions: dict, prefix: str, by_direction: dict) -> None:
    """ Adds one pose's directions in DIRECTIONS order, deriving left from right. """
    if "right" in by_direction:
        by_direction["left"] = mirrored(by_direction["right"])

    for direction in DIRECTIONS:
        if direction in by_direction:
            regions[f"{prefix}_{direction}"] = by_direction[direction]


def build_player() -> dict:
    regions = {}

    for pose, sources in PLAYER_POSES.items():
        by_direction = {}

        for direction, source_name in sources.items():
            source = load_source(source_name)

            if source is not None:
                by_direction[direction] = cut_out_sprite(source, CHARACTER_HEIGHT)

        with_left(regions, f"archer_{pose}", by_direction)

    source = load_source(PLAYER_RESTING[0])

    if source is not None:
        regions["archer_resting_down"] = cut_out_sprite(source, PLAYER_RESTING[1])

    return regions


def character_cells(sheet_name: str, poses) -> dict:
    """ {(pose, direction): (cell, outside, box)} from a 3 by 5 sheet, or from
    separate enemy_<kind>_<pose>_<direction> files when there is no sheet. """
    path = SOURCE / f"{sheet_name}.png"

    if path.exists():
        cells = magenta_cells(pygame.image.load(path).convert(), len(SHEET_DIRECTIONS), len(poses))

        if cells is None:
            print(f"    {sheet_name}: no se deja cortar en 3 filas x {len(poses)} columnas")
            return {}

        keys = [(pose, direction) for direction in SHEET_DIRECTIONS for pose in poses]
        return dict(zip(keys, cells))

    loose = {}
    kind = sheet_name.replace("enemy_", "").replace("_sheet", "")

    for pose in poses:
        for direction in SHEET_DIRECTIONS:
            source = SOURCE / f"enemy_{kind}_{pose}_{direction}.png"

            if source.exists():
                cell = pygame.image.load(source).convert()
                outside = background_of(cell, strip_magenta_hue=True)
                loose[(pose, direction)] = (cell, outside, box_of(outside))

    if not loose:
        print(f"    falta {sheet_name}.png, se omite")

    return loose


def add_character(regions: dict, prefix: str, cells: dict, poses, scale: float) -> None:
    keys = list(cells.keys())
    finished = dict(zip(keys, scale_cells([cells[key] for key in keys], scale)))

    for pose in poses:
        by_direction = {d: finished[(pose, d)] for d in SHEET_DIRECTIONS if (pose, d) in finished}
        with_left(regions, f"{prefix}_{pose}", by_direction)


def build_enemies() -> dict:
    regions = {}

    for kind, idle_height in ENEMIES.items():
        cells = character_cells(f"enemy_{kind}_sheet", ENEMY_POSES)

        if ("idle", "down") in cells:
            scale = idle_height / cells[("idle", "down")][2].height
            add_character(regions, f"enemy_{kind}", cells, ENEMY_POSES, scale)

    return regions


def build_bosses() -> dict:
    regions = {}

    for boss, (idle_height, sheets) in BOSSES.items():
        scale = None

        for sheet_name, poses in sheets:
            cells = character_cells(sheet_name, poses)

            if scale is None:
                if ("idle", "down") not in cells:
                    break
                scale = idle_height / cells[("idle", "down")][2].height

            if cells:
                add_character(regions, f"boss_{boss}", cells, poses, scale)

    return regions


def build_props() -> dict:
    regions = {}

    for name, height in PROPS.items():
        source = load_source(name)

        if source is not None:
            # The first five props are cleared exactly as they always were;
            # the brazier's fire is the reason they never use the hue rules.
            new = name not in LEGACY_PROPS
            regions[name] = cut_out_sprite(source, height, strip_magenta_hue=new, dark_magenta=new)

    return regions


def tallest_scale(cells, height: int) -> float:
    return height / max(box.height for _, _, box in cells)


def build_decor() -> dict:
    regions = {}

    for prefix, (source_name, height) in DECOR_SHEETS.items():
        source = load_source(source_name)

        if source is None:
            continue

        cells = magenta_cells(source, 3, 5)

        if cells is None:
            print(f"    {source_name}: no se deja cortar en 3 filas x 5 columnas")
            continue

        for index, sprite in enumerate(scale_cells(cells, tallest_scale(cells, height)), start=1):
            regions[f"{prefix}_{index:02d}"] = sprite

    return regions


def build_bonfire() -> dict:
    regions = {}

    for name, (source_name, height) in BONFIRE_PIECES.items():
        source = load_source(source_name)

        if source is not None:
            regions[name] = cut_out_sprite(source, height, strip_magenta_hue=True, dark_magenta=True)

    for prefix, (source_name, height, background) in BONFIRE_ANIMATIONS.items():
        source = load_source(source_name)

        if source is None:
            continue

        if background == "light":
            cells = light_cells(source, 2, 4)
            frames = None if cells is None else [
                fit_height(cell, max(1, round(cell.get_height() * height / max(c.get_height() for c in cells))))
                for cell in cells
            ]
        else:
            cells = magenta_cells(source, 2, 4)
            frames = None if cells is None else scale_cells(cells, tallest_scale(cells, height))

        if frames is None:
            print(f"    {source_name}: no se deja cortar en 2 filas x 4 columnas")
            continue

        for index, frame in enumerate(frames, start=1):
            regions[f"{prefix}_{index}"] = frame

    return regions


def build_hud() -> dict:
    regions = {}

    for name, (source_name, height) in HUD.items():
        source = load_source(source_name)

        if source is not None:
            regions[name] = cut_out_sprite(source, height, strip_magenta_hue=True, dark_magenta=True)

    return regions


# ------------------------------------------------------------
# Packing
# ------------------------------------------------------------
def pack_map(regions: dict):
    """ Shelf packs regions onto the tile grid in the order given: every
    region is already a whole number of tiles, so every position is too. """
    width = max([1024] + [surface.get_width() for surface in regions.values()])
    rects = {}
    x = y = row_height = 0

    for name, surface in regions.items():
        w, h = surface.get_size()

        if x + w > width:
            x, y, row_height = 0, y + row_height, 0

        rects[name] = [x, y, w, h]
        x += w
        row_height = max(row_height, h)

    sheet = pygame.Surface((width, y + row_height), pygame.SRCALPHA)
    sheet.fill((0, 0, 0, 0))

    for name, surface in regions.items():
        sheet.blit(surface, rects[name][:2])

    meta = {"tile_width": TILE_SIZE, "tile_height": TILE_SIZE, "columns": width // TILE_SIZE}
    return sheet, rects, meta


def pack_sprites(regions: dict, columns: int):
    """ One uniform cell per tileset, a whole number of tiles on each side,
    each sprite bottom centre inside its own. """
    cell_w = math.ceil(max(s.get_width() for s in regions.values()) / TILE_SIZE) * TILE_SIZE
    cell_h = math.ceil(max(s.get_height() for s in regions.values()) / TILE_SIZE) * TILE_SIZE
    rows = math.ceil(len(regions) / columns)

    sheet = pygame.Surface((columns * cell_w, rows * cell_h), pygame.SRCALPHA)
    sheet.fill((0, 0, 0, 0))
    rects = {}

    for index, (name, surface) in enumerate(regions.items()):
        w, h = surface.get_size()
        x = (index % columns) * cell_w + (cell_w - w) // 2
        y = (index // columns) * cell_h + cell_h - h
        sheet.blit(surface, (x, y))
        rects[name] = [x, y, w, h]

    meta = {"tile_width": cell_w, "tile_height": cell_h, "columns": columns}
    return sheet, rects, meta


def write_tileset(name: str, sheet: pygame.Surface, rects: dict, meta: dict) -> None:
    pygame.image.save(sheet, OUTPUT / f"{name}.png")

    with open(OUTPUT / f"{name}.json", "w", encoding="utf-8") as index:
        json.dump({**meta, "regions": rects}, index, indent=1)

    print(
        f"  {name:8} {sheet.get_width()}x{sheet.get_height()}, "
        f"{len(rects)} regiones, celda {meta['tile_width']}x{meta['tile_height']}"
    )


# Sprite tilesets and how many cells each row holds: directional sets are
# one pose per row, left to right down, up, left, right.
SPRITE_TILESETS = [
    ("player", build_player, 4),
    ("enemies", build_enemies, 4),
    ("bosses", build_bosses, 4),
    ("props", build_props, 6),
    ("decor", build_decor, 10),
    ("bonfire", build_bonfire, 8),
    ("hud", build_hud, 7),
]


def main() -> int:
    if not SOURCE.is_dir():
        print(f"No encuentro {SOURCE}", file=sys.stderr)
        return 1

    OUTPUT.mkdir(parents=True, exist_ok=True)
    print("Construyendo tilesets\n")

    for name, entries in MAP_TILESETS.items():
        print(f"  [{name}]")
        regions = build_map_tileset(entries)

        if regions:
            write_tileset(name, *pack_map(regions))

    for name, build, columns in SPRITE_TILESETS:
        print(f"  [{name}]")
        regions = build()

        if regions:
            write_tileset(name, *pack_sprites(regions, columns))

    print("\nListo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
