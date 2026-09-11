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


def build_prop(name: str, target_height: int) -> None:
    source = pygame.image.load(SOURCE / f"{name}.png").convert()

    pure = background_mask(source, MAGENTA_PURE_TOLERANCE)
    loose = background_mask(source, MAGENTA_LOOSE_TOLERANCE)

    reachable = outside_mask(loose)
    outside = reachable | pure

    # Background the flood fill on its own would have kept: holes closed
    # off by the sprite around them.
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
    pygame.image.save(final, PROPS_OUT / f"{name}.png")

    note = f", {enclosed} px de hueco cerrado limpiados" if enclosed else ""
    print(
        f"  prop   {name:44} caja {box.width}x{box.height}"
        f" -> {target_width}x{target_height}{note}"
    )


def main() -> int:
    if not SOURCE.is_dir():
        print(f"No encuentro {SOURCE}", file=sys.stderr)
        return 1

    TILESETS.mkdir(parents=True, exist_ok=True)
    PROPS_OUT.mkdir(parents=True, exist_ok=True)

    print("Construyendo assets\n")

    for name in FLOORS:
        build_floor(name)

    print()

    for name, height in PROPS.items():
        build_prop(name, height)

    print("\nListo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
