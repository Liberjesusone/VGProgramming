"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains what Level needs to read a map exported from Tiled as
JSON: the tilesets it references, which of our regions a tile shows, and
where a placed tile object stands.

gale ships its own loader (gale.tilemap.load_tiled_map), unused here for
two reasons. It opens every tileset image through the path Tiled wrote
into the map, which is only valid on the machine that saved it; and it
drops the gid of a tile object, the one field that says what a placed
object is. Here a tileset is matched to ours by its image's file name
alone, and every object keeps the sprite it was placed with.
"""

import json
import pathlib
from typing import Any, Dict, List, Optional, Tuple

import settings

# The top bits of a gid mark the tile as flipped or rotated; the rest is the tile itself.
GID_MASK = 0x1FFFFFFF

# Where Tiled puts an object's x and y inside its own box, as fractions of its width and height.
ALIGNMENT_ANCHORS = {
    "topleft": (0.0, 0.0),
    "top": (0.5, 0.0),
    "topright": (1.0, 0.0),
    "left": (0.0, 0.5),
    "center": (0.5, 0.5),
    "right": (1.0, 0.5),
    "bottomleft": (0.0, 1.0),
    "bottom": (0.5, 1.0),
    "bottomright": (1.0, 1.0),
}

# What an orthogonal map uses for a tileset that leaves its alignment unspecified.
DEFAULT_ALIGNMENT = "bottomleft"


class MapTileset:
    """ One tileset as a map references it: its range of gids, its tile
    size, the custom properties set on its tiles, and which of our
    tilesets in assets/tilesets it is. """

    def __init__(self, data: Dict[str, Any]) -> None:
        self.first_gid: int = data["firstgid"]
        self.name: str = pathlib.PurePath(data["image"]).stem
        self.tile_width: int = data["tilewidth"]
        self.tile_height: int = data["tileheight"]
        self.columns: int = data["columns"]
        self.tile_count: int = data["tilecount"]
        self.alignment: str = data.get("objectalignment", "unspecified")

        self.tile_properties: Dict[int, Dict[str, Any]] = {
            tile["id"]: {prop["name"]: prop["value"] for prop in tile.get("properties", [])}
            for tile in data.get("tiles", [])
        }

        self._regions: Optional[Dict[int, str]] = None

    def contains(self, gid: int) -> bool:
        return self.first_gid <= gid < self.first_gid + self.tile_count

    def region(self, gid: int) -> Optional[str]:
        """ The name of the region drawn in that tile's cell. Read from our
        own JSON index rather than from any property set in Tiled: every
        region sits inside exactly one cell of the packed image, so the
        cell alone says what it is, named in Tiled or not. """
        if self._regions is None:
            with open(settings.TILESETS_DIR / f"{self.name}.json", encoding="utf-8") as index:
                regions = json.load(index)["regions"]

            self._regions = {
                (y // self.tile_height) * self.columns + x // self.tile_width: name
                for name, (x, y, _, _) in regions.items()
            }

        return self._regions.get(gid - self.first_gid)


def load(path: pathlib.Path) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as map_file:
        return json.load(map_file)


def tilesets(map_data: Dict[str, Any]) -> List[MapTileset]:
    return sorted((MapTileset(data) for data in map_data["tilesets"]), key=lambda t: t.first_gid)


def tileset_for(map_tilesets: List[MapTileset], gid: int) -> MapTileset:
    return next(tileset for tileset in map_tilesets if tileset.contains(gid))


def solid_gids(map_tilesets: List[MapTileset]) -> set:
    """ Every gid whose tile has the custom property collision = solid. """
    return {
        tileset.first_gid + local
        for tileset in map_tilesets
        for local, properties in tileset.tile_properties.items()
        if properties.get("collision") == "solid"
    }


def feet(obj: Dict[str, Any], tileset: MapTileset) -> Tuple[float, float]:
    """ The bottom centre of a tile object, where every entity and prop in
    the game is anchored, whatever alignment its tileset uses in Tiled. """
    alignment = DEFAULT_ALIGNMENT if tileset.alignment == "unspecified" else tileset.alignment
    anchor_x, anchor_y = ALIGNMENT_ANCHORS[alignment]
    return (
        obj["x"] + (0.5 - anchor_x) * obj["width"],
        obj["y"] + (1.0 - anchor_y) * obj["height"],
    )
