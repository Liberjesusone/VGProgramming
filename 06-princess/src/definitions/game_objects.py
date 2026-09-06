"""
ISPPV1 2023
Study Case: The Legend of the Princess (ARPG)

Author: Alejandro Mujica
alejandro.j.mujic4@gmail.com

This file contains the definition for game objects.
"""

from typing import Any, Dict

from gale.factory import Factory

import settings
from src.GameObject import GameObject


def _pickup_heart(player, obj) -> None:
    player.heal(2)
    settings.SOUNDS["heart-taken"].play()


GAME_OBJECT_DEFS: Dict[str, Dict[str, Any]] = {
    "switch": {
        "type": "switch",
        "texture": "switches",
        "frame": 2,
        "width": 16,
        "height": 16,
        "solid": False,
        "default_state": "unpressed",
        "states": {
            "unpressed": {"frame": 2},
            "pressed": {"frame": 1},
        },
    },
    "pot": {
        "type": "pot",
        "texture": "tiles",
        "frame": 16,
        "width": 16,
        "height": 16,
        "solid": True,
        "consumable": False,
        "default_state": "default",
        "takeable": True,
        "states": {
            "default": {"frame": 16},
        },
    },
    # Definition of heart as a consumable object type.
    "heart": {
        "type": "heart",
        "texture": "hearts",
        "frame": 5,
        "width": 16,
        "height": 16,
        "solid": False,
        "consumable": True,
        "default_state": "default",
        "states": {
            "default": {"frame": 5},
        },
        "on_consume": _pickup_heart,
    },
    # Solid, one-time obstacle that grants the bow. Not "consumable": that
    # flag makes Room.update fire on_consume for every frame the player's
    # rect merely overlaps the object, with no key press involved. fine
    # for a coin you walk over, wrong for something you should have to
    # press "enter" in front of. Room.take_adjacent_pot (the same
    # interact-key handler the pot uses) special-cases obj.type == "chest"
    # instead, and its own "opened" state doubles as the "already given
    # out its bow" flag so it can never do so twice.
    "chest": {
        "type": "chest",
        "texture": "tiles",
        "frame": 167,  # row 9, col 15 (1-based) of tileset.png
        "width": 16,
        "height": 16,
        "solid": True,
        "takeable": True,
        "default_state": "closed",
        "states": {
            "closed": {"frame": 167},  # row 9,  col 15
            "opened": {"frame": 128},  # row 7,  col 14
        },
    },
    # The arrow fired by the bow. Not solid/consumable/takeable, it's
    # only ever wrapped in a Projectile (see create_arrow below), which
    # drives its x/y and asks Room.update to check it against entities,
    # not the object-collision loop that solid/consumable/takeable feed.
    "arrow": {
        "type": "arrow",
        "texture": "tiles",
        "frame": 152,
        "width": 16,
        "height": 16,
        "solid": False,
        "default_state": "down",
        "states": {
            "up": {"frame": 95},     # row 5, col 19
            "right": {"frame": 114}, # row 6, col 19
            "left": {"frame": 133},  # row 7, col 19
            "down": {"frame": 152},  # row 8, col 19
        },
    },
    # The mage's projectile. Same deal as the arrow, it only ever lives
    # wrapped in a Projectile, except it needs no per-direction state:
    # the sprite is a round ball of fire that reads the same flying any
    # which way.
    "fireball": {
        "type": "fireball",
        "texture": "fireballs",
        "frame": settings.FIREBALL_FRAME,
        "width": settings.TILE_SIZE,
        "height": settings.TILE_SIZE,
        "solid": False,
        "default_state": "default",
        "states": {
            "default": {"frame": settings.FIREBALL_FRAME},
        },
    },
}

_ARROW_FACTORY: Factory = Factory(GameObject)
_FIREBALL_FACTORY: Factory = Factory(GameObject)


def create_arrow(x: float, y: float, direction: str) -> GameObject:
    """ Builds one arrow GameObject via Factory, facing `direction`,
    meant to be wrapped in a src.Projectile.Projectile right away 
    by the caller, the same way an already-existing GameObject 
    (the pot) gets wrapped in one to be thrown.
    """
    arrow = _ARROW_FACTORY.create(x, y, {"definition": GAME_OBJECT_DEFS["arrow"]})
    arrow.state = direction
    return arrow


def create_fireball(x: float, y: float) -> GameObject:
    """Builds one fireball GameObject, to be wrapped in a
    src.Projectile.Projectile by the caller (BossChaseState) exactly the
    way create_arrow's result is."""
    return _FIREBALL_FACTORY.create(x, y, {"definition": GAME_OBJECT_DEFS["fireball"]})
