"""
ISPPV1 2023
Study Case: The Legend of the Princess (ARPG)

Author: Alejandro Mujica
alejandro.j.mujic4@gmail.com

This file contains the definition for entities.
"""

from typing import Any, Dict

ENTITY_DEFS: Dict[str, Dict[str, Any]] = {
    "player": {
        "walk_speed": 60,
        "animations": {
            "walk-left": {
                "frames": [13, 14, 15, 16],
                "interval": 0.155,
                "texture": "character-walk",
            },
            "walk-right": {
                "frames": [5, 6, 7, 8],
                "interval": 0.15,
                "texture": "character-walk",
            },
            "walk-down": {
                "frames": [1, 2, 3, 4],
                "interval": 0.15,
                "texture": "character-walk",
            },
            "walk-up": {
                "frames": [9, 10, 11, 12],
                "interval": 0.15,
                "texture": "character-walk",
            },
            "idle-left": {"frames": [13], "texture": "character-walk"},
            "idle-right": {"frames": [5], "texture": "character-walk"},
            "idle-down": {"frames": [1], "texture": "character-walk"},
            "idle-up": {"frames": [9], "texture": "character-walk"},
            "sword-left": {
                "frames": [13, 14, 15, 16],
                "interval": 0.05,
                "loops": 1,
                "texture": "character-swing-sword",
            },
            "sword-right": {
                "frames": [9, 10, 11, 12],
                "interval": 0.05,
                "loops": 1,
                "texture": "character-swing-sword",
            },
            "sword-down": {
                "frames": [1, 2, 3, 4],
                "interval": 0.05,
                "loops": 1,
                "texture": "character-swing-sword",
            },
            "sword-up": {
                "frames": [5, 6, 7, 8],
                "interval": 0.05,
                "loops": 1,
                "texture": "character-swing-sword",
            },
            "pot-lift-down": {
                "frames": [1, 2, 3],
                "interval": 0.1,
                "loops": 1,
                "texture": "character-pot-lift",
            },
            "pot-lift-right": {
                "frames": [4, 5, 6],
                "interval": 0.1,
                "loops": 1,
                "texture": "character-pot-lift",
            },
            "pot-lift-up": {
                "frames": [7, 8, 9],
                "interval": 0.1,
                "loops": 1,
                "texture": "character-pot-lift",
            },
            "pot-lift-left": {
                "frames": [10, 11, 12],
                "interval": 0.1,
                "loops": 1,
                "texture": "character-pot-lift",
            },
            "pot-walk-down": {
                "frames": [1, 2, 3, 4],
                "interval": 0.15,
                "texture": "character-pot-walk",
            },
            "pot-walk-right": {
                "frames": [5, 6, 7, 8],
                "interval": 0.15,
                "texture": "character-pot-walk",
            },
            "pot-walk-up": {
                "frames": [9, 10, 11, 12],
                "interval": 0.15,
                "texture": "character-pot-walk",
            },
            "pot-walk-left": {
                "frames": [13, 14, 15, 16],
                "interval": 0.15,
                "texture": "character-pot-walk",
            },
            "pot-idle-down": {"frames": [1], "texture": "character-pot-walk"},
            "pot-idle-right": {"frames": [5], "texture": "character-pot-walk"},
            "pot-idle-up": {"frames": [9], "texture": "character-pot-walk"},
            "pot-idle-left": {"frames": [13], "texture": "character-pot-walk"},
        },
    },
    "skeleton": {
        "texture": "entities",
        "animations": {
            "walk-left": {"frames": [22, 23, 24, 23], "interval": 0.2},
            "walk-right": {"frames": [34, 35, 36, 35], "interval": 0.2},
            "walk-down": {"frames": [10, 11, 12, 11], "interval": 0.2},
            "walk-up": {"frames": [46, 47, 48, 47], "interval": 0.2},
            "idle-left": {"frames": [23]},
            "idle-right": {"frames": [35]},
            "idle-down": {"frames": [11]},
            "idle-up": {"frames": [47]},
        },
    },
    "slime": {
        "texture": "entities",
        "animations": {
            "walk-left": {"frames": [61, 62, 63, 62], "interval": 0.2},
            "walk-right": {"frames": [73, 74, 75, 74], "interval": 0.2},
            "walk-down": {"frames": [49, 50, 51, 50], "interval": 0.2},
            "walk-up": {"frames": [86, 86, 87, 86], "interval": 0.2},
            "idle-left": {"frames": [62]},
            "idle-right": {"frames": [74]},
            "idle-down": {"frames": [50]},
            "idle-up": {"frames": [86]},
        },
    },
    "bat": {
        "texture": "entities",
        "animations": {
            "walk-left": {"frames": [64, 65, 66, 65], "interval": 0.2},
            "walk-right": {"frames": [76, 77, 78, 77], "interval": 0.2},
            "walk-down": {"frames": [52, 53, 54, 53], "interval": 0.2},
            "walk-up": {"frames": [88, 89, 90, 89], "interval": 0.2},
            "idle-left": {"frames": [64, 65, 66, 65], "interval": 0.2},
            "idle-right": {"frames": [76, 77, 78, 77], "interval": 0.2},
            "idle-down": {"frames": [52, 53, 54, 53], "interval": 0.2},
            "idle-up": {"frames": [88, 89, 90, 89], "interval": 0.2},
        },
    },
    "ghost": {
        "texture": "entities",
        "animations": {
            "walk-left": {"frames": [67, 68, 69, 68], "interval": 0.2},
            "walk-right": {"frames": [79, 80, 81, 80], "interval": 0.2},
            "walk-down": {"frames": [55, 56, 57, 56], "interval": 0.2},
            "walk-up": {"frames": [91, 92, 93, 92], "interval": 0.2},
            "idle-left": {"frames": [68]},
            "idle-right": {"frames": [80]},
            "idle-down": {"frames": [56]},
            "idle-up": {"frames": [92]},
        },
    },
    # The boss. Its sheet is the one settings._build_villain_sheet lays
    # out: a 4x3 grid where column 1 faces down, 2 left, 3 up and 4 right,
    # and the three rows are the walk cycle, so a frame number is
    # (row - 1) * 4 + column, 1-based like every other frame list here.
    # "texture" goes on every single animation, the way the player's
    # entries do it, and NOT once at the top the way the enemies above
    # appear to: Entity._create_animations reads it off each animation's
    # own dict and falls back to "entities" when it is missing, so the
    # entity-level key those enemies carry is in fact dead, they only
    # work because "entities" is the fallback anyway.
    "villain": {
        "animations": {
            "walk-down": {"frames": [1, 5, 9, 5], "interval": 0.18, "texture": "villain"},
            "walk-left": {"frames": [2, 6, 10, 6], "interval": 0.18, "texture": "villain"},
            "walk-up": {"frames": [3, 7, 11, 7], "interval": 0.18, "texture": "villain"},
            "walk-right": {"frames": [4, 8, 12, 8], "interval": 0.18, "texture": "villain"},
            "idle-down": {"frames": [1], "texture": "villain"},
            "idle-left": {"frames": [2], "texture": "villain"},
            "idle-up": {"frames": [3], "texture": "villain"},
            "idle-right": {"frames": [4], "texture": "villain"},
        },
    },
    "spider": {
        "texture": "entities",
        "animations": {
            "walk-left": {"frames": [70, 71, 72, 71], "interval": 0.2},
            "walk-right": {"frames": [82, 83, 84, 83], "interval": 0.2},
            "walk-down": {"frames": [58, 59, 60, 59], "interval": 0.2},
            "walk-up": {"frames": [94, 95, 96, 95], "interval": 0.2},
            "idle-left": {"frames": [71]},
            "idle-right": {"frames": [83]},
            "idle-down": {"frames": [59]},
            "idle-up": {"frames": [95]},
        },
    },
}
