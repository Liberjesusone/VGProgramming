"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

Turns the raw generated art in assets/source into what the game actually
loads, in assets/graphics. Run it by hand whenever a source image
changes; the game itself never does any of this, it just loads the
result.

Two jobs:

Floors. Each source texture is one continuous, seamless 1254x1254 image.
Shrinking it down to a single 32x32 tile turns it to mush, so instead it
becomes a 256x256 block, which is a grid of 8x8 tiles. Because the
texture is continuous, those 64 tiles also line up against each other, so
one image gives a whole floor material with 64 variants and no visible
repetition.

Props. The image generator cannot produce a real alpha channel, so the
prompt asked for a flat magenta background instead, which is cleared
here. Two rules decide what goes, because neither one alone is right:

Anything that is very nearly pure magenta goes, wherever it is. The
brazier is the case that needs this: the openings in its rim and the gaps
between its legs are background enclosed by metal, unreachable from the
outside, and leaving them in paints bright pink arcs across the sprite.

Anything only roughly magenta goes only if it can be reached from the
image border. That protects a sprite that genuinely contains a purple or
pink detail from having it punched out.

Characters. Same magenta cutout as props (cut_out_sprite is the shared
step), but only three directions are ever drawn: a hooded, faceless
design was deliberate so the same character reads as the same character
across three independent generations with no shared memory between them.
The left-facing frame is never generated at all -- it is the right-facing
one mirrored, which is both one fewer image to get right and a guarantee
that left and right are perfectly symmetric instead of two separate
drawings that might not quite agree.
"""

import collections
import pathlib
import sys

import numpy
import pygame

pygame.init()
pygame.display.set_mode((1, 1))

BASE = pathlib.Path(__file__).resolve().parent.parent
SOURCE = BASE / "assets" / "source"
TILESETS = BASE / "assets" / "graphics" / "tilesets"
PROPS_OUT = BASE / "assets" / "graphics" / "props"
CHARACTERS_OUT = BASE / "assets" / "graphics" / "characters"

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

# Floor materials. Every one becomes a BLOCK_SIZE tileset.
FLOORS = [
    "weathered_cracked_stone_slabs",
    "damp_mossy_cobblestone",
    "wet_dark_packed_earth_with_small_pebbles",
    "rotten_wooden_planks",
    "grey_ash_and_fine_gravel",
]

# Props, with the height in game pixels each one should end up at. The
# player is 64 px tall, so these are read against that: the boulder comes
# up to the shoulder, the pillar is twice the player's height, the dead
# tree towers over everything. Widths follow from each source image's own
# proportions, never forced.
PROPS = {
    "broken_stone_pillar": 112,
    "dead_leafless_tree": 160,
    "mossy_boulder": 64,
    "rusted_iron_brazier": 80,
    "stone_sarcophagus": 88,
}

# The height every character pose is scaled to. 64 is not arbitrary: it
# is settings.PLAYER_HEIGHT, the figure the "how big should the player
# read on screen" sizing pass (see settings.py) already settled on.
# Width is never forced -- it follows each direction's own silhouette,
# which is why down, up and right end up three different widths.
CHARACTER_HEIGHT = 64

# One entry per character. Each pose lists the directions that were
# actually generated; "left" is never one of them (see the module
# docstring) -- build_character always derives it from "right".
#
# Source filenames follow whatever order they actually came back in
# (direction before the pose name, e.g. archer_bow_down_charge_1), not
# the pose_direction order the *output* files use -- the two are
# unrelated, build_character always writes archer_<pose>_<direction>.png
# regardless of what the source happened to be called.
#
# Not every pose here exists as a source image yet -- this batch is being
# generated a handful at a time. build_character skips whatever it can't
# find instead of failing the whole run, so this can be re-run as often
# as new ones arrive; settings.py falls back to a placeholder for
# anything still missing, so the game stays playable throughout.
CHARACTERS = {
    "archer": {
        # "down" points at archer_down_2, not archer_down: a second take
        # on the same pose, picked over the first one on looks alone.
        # archer_down.png is still sitting in assets/source, unused.
        "idle": {"down": "archer_down_2", "up": "archer_up", "right": "archer_right"},
        # The bow's own walk cycle -- no "bow" in these filenames because
        # this was generated before the sword got its own separate one
        # below, back when there was only a single shared cycle planned.
        "walk": {
            "down": "archer_down_walk_1",
            "up": "archer_up_walk_1",
            "right": "archer_right_walk_1",
        },
        "sword_idle": {
            "down": "archer_sword_down",
            "up": "archer_sword_up",
            "right": "archer_sword_right",
        },
        "sword_walk": {
            "down": "archer_sword_down_walk_1",
            "up": "archer_sword_up_walk_1",
            "right": "archer_sword_right_walk_1",
        },
        "sword_charge1": {
            "down": "archer_sword_down_charge_1",
            "up": "archer_sword_up_charge_1",
            "right": "archer_sword_right_charge_1",
        },
        "sword_charge2": {
            "down": "archer_sword_down_charge_2",
            "up": "archer_sword_up_charge_2",
            "right": "archer_sword_right_charge_2",
        },
        "sword_attack": {
            "down": "archer_sword_down_attack",
            "up": "archer_sword_up_attack",
            "right": "archer_sword_right_attack",
        },
        "bow_charge1": {
            "down": "archer_bow_down_charge_1",
            "up": "archer_bow_up_charge_1",
            "right": "archer_bow_right_charge_1",
        },
        "bow_charge2": {
            "down": "archer_bow_down_charge_2",
            "up": "archer_bow_up_charge_2",
            "right": "archer_bow_right_charge_2",
        },
        "bow_release": {
            "down": "archer_bow_down_attack",
            "up": "archer_bow_up_attack",
            "right": "archer_bow_right_attack",
        },
        # The dodge roll: one set shared by both weapons (see settings.py's
        # CHARACTER_POSE_SETS), 3 poses instead of 2 like the rest -- a
        # roll is a one-shot arc, not a repeating cycle, so it needs a
        # distinct start/mid/end to read clearly instead of just alternating.
        "roll1": {
            "down": "archer_roll1_down",
            "up": "archer_roll1_up",
            "right": "archer_roll1_right",
        },
        "roll2": {
            "down": "archer_roll2_down",
            "up": "archer_roll2_up",
            "right": "archer_roll2_right",
        },
        "roll3": {
            "down": "archer_roll3_down",
            "up": "archer_roll3_up",
            "right": "archer_roll3_right",
        },
    },
}


def background_mask(surface: pygame.Surface, tolerance: int) -> numpy.ndarray:
    """Boolean mask, True where the pixel is within `tolerance` of the
    magenta the prompt asked for."""
    rgb = pygame.surfarray.array3d(surface).astype(numpy.int16)
    return (
        (numpy.abs(rgb[:, :, 0] - MAGENTA[0]) <= tolerance)
        & (rgb[:, :, 1] <= tolerance)
        & (numpy.abs(rgb[:, :, 2] - MAGENTA[2]) <= tolerance)
    )


def outside_mask(is_background: numpy.ndarray) -> numpy.ndarray:
    """
    Flood fill inward from every border pixel, so only background that is
    genuinely connected to the outside is marked.

    A plain colour test would also erase anything inside the sprite that
    happens to be near magenta, and that is not hypothetical: the
    brazier's fire is exactly that colour.
    """
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


def build_floor(name: str) -> None:
    source = pygame.image.load(SOURCE / f"{name}.png").convert()
    block = pygame.transform.smoothscale(source, (BLOCK_SIZE, BLOCK_SIZE))
    pygame.image.save(block, TILESETS / f"floor_{name}.png")
    print(
        f"  suelo  {name:44} {source.get_width()}x{source.get_height()}"
        f" -> {BLOCK_SIZE}x{BLOCK_SIZE} ({BLOCK_TILES*BLOCK_TILES} tiles)"
    )


def grow(mask: numpy.ndarray, steps: int) -> numpy.ndarray:
    """Expands a mask by `steps` pixels in the four directions."""
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

    This exists because of how pygame downscales. smoothscale averages
    colour and alpha separately and does not premultiply, so an output
    pixel that mixes a branch (alpha 255) with the background (alpha 0)
    still averages the background's *colour* into the result. The
    background is magenta, so every thin feature comes out pink even
    though the magenta was already made invisible. Filling the hole with
    the neighbouring sprite colours first means the average is taken
    between the sprite and more of the sprite, and the edges come out
    clean.

    The reach has to cover the downscaling kernel, which spans roughly
    (source height / target height) pixels.
    """
    filled = ~hole

    for _ in range(steps):
        for axis, shift in ((0, 1), (0, -1), (1, 1), (1, -1)):
            neighbour_rgb = numpy.roll(rgb, shift, axis=axis)
            neighbour_filled = numpy.roll(filled, shift, axis=axis)
            take = neighbour_filled & ~filled
            rgb[take] = neighbour_rgb[take]
            filled = filled | take


def cut_out_sprite(source: pygame.Surface, target_height: int):
    """
    Clears the magenta background off `source` and returns it scaled to
    `target_height`, cropped tight to its own silhouette. Shared by
    build_prop and build_character -- a prop and a character sit on the
    same flat magenta and need exactly the same treatment.

    :returns: (final_surface, source_box, enclosed_px) -- source_box is
        the tight crop in the *source* image's own coordinates (only used
        for the log line), enclosed_px is how many pixels of background
        were trapped inside the sprite and only removed by the pure-colour
        rule (see the module docstring) -- 0 most of the time.
    """
    pure = background_mask(source, MAGENTA_PURE_TOLERANCE)
    loose = background_mask(source, MAGENTA_LOOSE_TOLERANCE)

    reachable = outside_mask(loose)
    outside = reachable | pure
    enclosed = int((pure & ~reachable).sum())

    # The generator antialiased the sprite against the magenta, leaving a
    # rim one or two pixels wide that is neither sprite nor background.
    # Widening the hole a little drops that rim, and at this resolution
    # it costs well under one pixel of the finished sprite.
    outside = grow(outside, EDGE_TRIM)

    cut = source.convert_alpha()

    rgb = pygame.surfarray.pixels3d(cut)
    reach = max(4, round(source.get_height() / target_height) + 4)
    bleed_colours(rgb, outside, reach)
    del rgb

    alpha = pygame.surfarray.pixels_alpha(cut)
    alpha[outside] = 0
    del alpha

    columns = numpy.where(~outside.all(axis=1))[0]
    rows = numpy.where(~outside.all(axis=0))[0]
    box = pygame.Rect(
        int(columns[0]),
        int(rows[0]),
        int(columns[-1] - columns[0] + 1),
        int(rows[-1] - rows[0] + 1),
    )

    cropped = cut.subsurface(box).copy()
    target_width = max(1, round(box.width * target_height / box.height))
    final = pygame.transform.smoothscale(cropped, (target_width, target_height))
    return final, box, enclosed


def build_prop(name: str, target_height: int) -> None:
    source = pygame.image.load(SOURCE / f"{name}.png").convert()
    final, box, enclosed = cut_out_sprite(source, target_height)
    pygame.image.save(final, PROPS_OUT / f"{name}.png")

    note = f", {enclosed} px de hueco cerrado limpiados" if enclosed else ""
    print(
        f"  prop   {name:44} caja {box.width}x{box.height}"
        f" -> {final.get_width()}x{final.get_height()}{note}"
    )


def build_character(character: str, pose: str, sources: dict) -> None:
    """
    Processes whichever of this pose's source images already exist and
    quietly skips the rest -- this whole batch is being generated a
    handful at a time, so a pose only half-delivered so far (say, "down"
    is done but "up" and "right" are not yet) still gets what it can out
    of what has actually arrived, instead of the run failing outright
    over the pieces still missing.
    """
    made = {}
    missing = []

    for direction, source_name in sources.items():
        path = SOURCE / f"{source_name}.png"

        if not path.exists():
            missing.append(direction)
            continue

        source = pygame.image.load(path).convert()
        final, box, _enclosed = cut_out_sprite(source, CHARACTER_HEIGHT)
        made[direction] = final
        pygame.image.save(final, CHARACTERS_OUT / f"{character}_{pose}_{direction}.png")
        print(
            f"  pj     {character}_{pose}_{direction:6} caja {box.width}x{box.height}"
            f" -> {final.get_width()}x{final.get_height()}"
        )

    if "right" in made and "left" not in sources:
        mirrored = pygame.transform.flip(made["right"], True, False)
        pygame.image.save(mirrored, CHARACTERS_OUT / f"{character}_{pose}_left.png")
        print(
            f"  pj     {character}_{pose}_left   (espejo de right, "
            f"{mirrored.get_width()}x{mirrored.get_height()})"
        )

    if missing and not made:
        print(f"  pj     {character}_{pose}: aun no generado, se omite")
    elif missing:
        print(f"  pj     {character}_{pose}: faltan {', '.join(missing)} todavia")


def main() -> int:
    if not SOURCE.is_dir():
        print(f"No encuentro {SOURCE}", file=sys.stderr)
        return 1

    TILESETS.mkdir(parents=True, exist_ok=True)
    PROPS_OUT.mkdir(parents=True, exist_ok=True)
    CHARACTERS_OUT.mkdir(parents=True, exist_ok=True)

    print("Construyendo assets\n")

    for name in FLOORS:
        build_floor(name)

    print()

    for name, height in PROPS.items():
        build_prop(name, height)

    print()

    for character, poses in CHARACTERS.items():
        for pose, sources in poses.items():
            build_character(character, pose, sources)

    print("\nListo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
