"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains the tuning of both forms of the final boss: Samurai
Gurenmaru, and the Light Spirit that rises from his body once he falls.
Their classes (src/entity/SamuraiBoss.py, src/entity/SpiritBoss.py) and
states only ever read these dicts, the same way Enemy reads ENEMY_DEFS.

Every melee attack either form has is a strike, all resolved by the same
BossStrikeState:

poses: (first half of the charge, second half, release).
charge_time: seconds from the start of the wind up to the release.
lock_fraction: fraction of charge_time after which the aim stops
    following the player. The telegraph outline thickens at that moment,
    the player's cue that the attack is committed.
half_angle / reach: the cone, see src/combat/cone.py. A tiny half_angle
    with a long reach is the thin strip of the samurai's thrust.
damage / stun: what a landed hit does, stun is None or a key of
    combat.STUNS.
swing: seconds the release pose holds.
recovery: seconds of standing still after the swing, before deciding again.
lunge: pixels the boss steps forward along its aim during the swing.
cue: optional sound and camera shake at the lock moment, the warning.
impact_shake: optional camera shake at the release, (magnitude, seconds).

Tuning is a first pass meant to be adjusted in play, like ENEMY_DEFS.
"""

from typing import Any, Dict

SAMURAI: Dict[str, Any] = {
    "name": "Samurai Gurenmaru",
    "max_health": 5,
    "aggro_radius": 230.0,
    "speed": 130.0,
    # How often the pursuit rolls for a surprise dash, so the chance
    # does not depend on the frame rate.
    "decision_interval": 0.4,
    "slash_trigger": 80.0,
    "thrust_trigger": 140.0,
    "thrust_chance": 0.4,
    "thrust_cooldown": 7.0,
    # After every normal slash, the chance of an immediate second one.
    "double_chance": 0.45,
    "dash": {
        "pose": "charge1",
        "speed": 560.0,
        "distance": 170.0,
        "windup": 0.18,
        "stop_distance": 52.0,
        "min_range": 110.0,
        "max_range": 300.0,
        "chance": 0.35,
        "cooldown": 3.5,
    },
    "strikes": {
        "slash": {
            "poses": ("charge1", "charge2", "attack"),
            "charge_time": 0.75,
            "lock_fraction": 0.75,
            "half_angle": 60.0,
            "reach": 96.0,
            "damage": 2,
            "stun": "light",
            "swing": 0.3,
            "recovery": 0.55,
            "lunge": 14.0,
        },
        "double": {
            "poses": ("charge2", "charge2", "attack"),
            "charge_time": 0.28,
            "lock_fraction": 0.5,
            "half_angle": 60.0,
            "reach": 96.0,
            "damage": 2,
            "stun": "light",
            "swing": 0.3,
            "recovery": 0.7,
            "lunge": 18.0,
        },
        "thrust": {
            "poses": ("ground_charge1", "ground_charge2", "ground_attack"),
            "charge_time": 1.1,
            "lock_fraction": 0.8,
            "half_angle": 9.0,
            "reach": 240.0,
            "damage": 1,
            "stun": "heavy",
            "swing": 0.4,
            "recovery": 0.15,
            "lunge": 0.0,
            "cue": {"sound": "samurai_thrust_cue", "shake": (4.0, 0.35)},
            "impact_shake": (3.0, 0.25),
        },
        # The three fast hits that always follow the thrust, landed or not.
        # No stun of their own, so a player who recovers can still roll out.
        "combo": {
            "poses": ("charge2", "charge1", "attack"),
            "charge_time": 0.22,
            "lock_fraction": 0.6,
            "half_angle": 55.0,
            "reach": 90.0,
            "damage": 2,
            "stun": None,
            "swing": 0.2,
            "recovery": 0.05,
            "lunge": 22.0,
        },
    },
}

SPIRIT: Dict[str, Any] = {
    "name": "Light Spirit of Samurai Gurenmaru",
    "max_health": 5,
    "speed": 120.0,
    # How opaque the spirit is at most, and how much it flickers below that.
    "alpha": 150.0,
    "flicker": 0.08,
    "emerge_time": 3.0,
    "emerge_rise": 56.0,
    # The distance band the spirit tries to keep from the player.
    "keep_min": 150.0,
    "keep_max": 260.0,
    # Seconds between flips of its sideways drift while inside that band.
    "strafe_flip": (1.0, 2.2),
    "melee_trigger": 64.0,
    "melee_cooldown": 2.0,
    "bow": {
        "range": 360.0,
        "cooldown": 1.8,
        "charge_time": 0.8,
        "lock_fraction": 0.8,
        "arrow_speed": 1100.0,
        "arrow_range": 420.0,
        "damage": 3,
        "stun": "light",
        "swing": 0.25,
        "recovery": 0.3,
    },
    "rain": {
        "first_delay": 6.0,
        "cooldown": 9.0,
        "charge_time": 1.3,
        "count": 100,
        # Every arrow lands somewhere inside this radius around the player.
        "radius": 250.0,
        "shot_radius": 34.0,
        "shot_speed": 260.0,
        # The arrows leave over this many seconds instead of all at once.
        "spread": 0.7,
        "damage": 1,
        "stun": None,
        "swing": 0.4,
        "recovery": 0.6,
    },
    "backdash": {
        "pose": "walk",
        "speed": 600.0,
        "distance": 180.0,
        "windup": 0.0,
        "stop_distance": 0.0,
    },
    "flee": {
        "speed": 180.0,
        "duration": 2.2,
        # Seconds before it picks a new escape direction on its own.
        "repick": 0.6,
    },
    "strikes": {
        # A swing of a wooden bow: very fast, weak, but it launches the player.
        "melee": {
            "poses": ("melee_charge", "melee_charge", "melee_attack"),
            "charge_time": 0.22,
            "lock_fraction": 0.4,
            "half_angle": 55.0,
            "reach": 74.0,
            "damage": 1,
            "stun": "launch",
            "swing": 0.25,
            "recovery": 0.05,
            "lunge": 0.0,
        },
    },
}
