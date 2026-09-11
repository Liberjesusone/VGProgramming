"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains PROP_DEFS: the footprint of every piece of scenery.

Only what blocks movement is described here. Sizes come from the images
themselves (see tools/build_assets.py), so redrawing a prop bigger or
smaller needs no change in this file.

solid_width_ratio is how much of the image's width the base takes up, and
solid_depth is how deep that base is in pixels. Both are small on purpose:
a top-down game reads correctly when the player can overlap the upper part
of a prop and is only stopped by the ground it actually stands on. The
depth stays well under a tile so brushing past a pillar does not feel
sticky.
"""

from typing import Any, Dict

PROP_DEFS: Dict[str, Dict[str, Any]] = {
    "broken_stone_pillar": {
        "name": "broken_stone_pillar",
        "solid_width_ratio": 0.85,
        "solid_depth": 14,
    },
    "dead_leafless_tree": {
        # Wide crown, narrow trunk: almost the whole picture is passable.
        "name": "dead_leafless_tree",
        "solid_width_ratio": 0.28,
        "solid_depth": 12,
    },
    "mossy_boulder": {
        "name": "mossy_boulder",
        "solid_width_ratio": 0.9,
        "solid_depth": 18,
    },
    "rusted_iron_brazier": {
        "name": "rusted_iron_brazier",
        "solid_width_ratio": 0.55,
        "solid_depth": 14,
    },
    "stone_sarcophagus": {
        # Drawn at a strong three quarter angle, so its base covers most
        # of the image and is deep enough to read as a solid block.
        "name": "stone_sarcophagus",
        "solid_width_ratio": 0.92,
        "solid_depth": 30,
    },
}
