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

solid_parts replaces the single centred base for a prop that stands on
more than one foot, or off centre: a list of (centre_ratio, width_ratio)
pairs, both fractions of the image's width. The torii gate uses it so
only its two pillars block and the passage between them stays open.
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
    "broken_torii_gate": {
        "name": "broken_torii_gate",
        "solid_parts": [(0.25, 0.23), (0.86, 0.2)],
        "solid_depth": 14,
    },
    "stone_lantern": {
        "name": "stone_lantern",
        "solid_width_ratio": 0.8,
        "solid_depth": 12,
    },
    "dead_black_pine": {
        "name": "dead_black_pine",
        "solid_width_ratio": 0.3,
        "solid_depth": 12,
    },
    "katana_grave": {
        "name": "katana_grave",
        "solid_width_ratio": 0.85,
        "solid_depth": 12,
    },
    "tattered_war_banner": {
        # Only the pole blocks, and it stands left of the image's centre.
        "name": "tattered_war_banner",
        "solid_parts": [(0.33, 0.2)],
        "solid_depth": 8,
    },
    "fallen_shrine_bell": {
        "name": "fallen_shrine_bell",
        "solid_width_ratio": 0.9,
        "solid_depth": 20,
    },
    "armor_remains": {
        "name": "armor_remains",
        "solid_width_ratio": 0.8,
        "solid_depth": 12,
    },
}
