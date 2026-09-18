"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains ENEMY_DEFS: everything that differs between one kind
of enemy and another. Enemy and its states only ever read this dict, the
same way Player reads WEAPON_DEFS, so a new enemy is a new entry here
plus its art, never a new class.

Every enemy has exactly one attack, charged in two tiers like the
player's own. attack["kind"] picks how that charge resolves:

melee: a cone in front of the enemy, the same shape the player's sword
uses, growing with the charge (see src/combat/cone.py).

area: a lobbed shot aimed at a point on the ground, landing after a short
flight and hitting whoever still stands inside its circle (see
src/entity/AreaShot.py).

Shared keys in attack:
engage_range: distance to the player at which charging starts.
charge_time: seconds a full charge (1.0) takes.
target_charge: (low, high) the release point is picked uniformly from,
    every time a charge starts. Equal values mean a fully predictable
    release, a wide range means an enemy that could let go at any moment.
charge1_fraction: charge at which the pose flips from charge1 to charge2.
advance_while_charging: whether the enemy keeps closing in, slowed down
    by combat.CHARGE_SPEED_FACTORS, or plants its feet while winding up.
stun: "light" or "heavy", see combat.STUNS.
sound: optional effect played the instant the attack is released.
land_sound: optional effect an area shot plays where it lands.
swing_duration: seconds the attack pose holds after release.
recovery: seconds of standing idle after that, before chasing again.

Tuning is a first pass, meant to be adjusted in play.
"""

from typing import Any, Dict

ENEMY_DEFS: Dict[str, Dict[str, Any]] = {
    "zombie": {
        "max_health": 13,
        "speed": 110.0,
        "aggro_radius": 280.0,
        "attack": {
            "kind": "melee",
            "engage_range": 56.0,
            "charge_time": 0.6,
            "target_charge": (0.35, 1.0),
            "charge1_fraction": 0.5,
            "advance_while_charging": True,
            "stun": "light",
            "sound": "sword_swing",
            "swing_duration": 0.3,
            "recovery": 0.8,
            "min_half_angle": 25.0,
            "max_half_angle": 50.0,
            "min_reach": 44.0,
            "max_reach": 70.0,
            "min_damage": 2,
            "max_damage": 5,
        },
    },
    "witch": {
        "max_health": 9,
        "speed": 80.0,
        "aggro_radius": 280.0,
        "attack": {
            "kind": "area",
            # Starts shooting a little inside her real range, not at its very edge,
            # so a shot is never wasted on a player already walking out of reach.
            "engage_range": 200.0,
            "charge_time": 1.0,
            "target_charge": (1.0, 1.0),
            "charge1_fraction": 0.5,
            "advance_while_charging": False,
            "stun": "light",
            "swing_duration": 0.25,
            "recovery": 1.2,
            "radius": 34.0,
            "damage": 3,
            "projectile_speed": 260.0,
            "land_sound": "arrow_hit",
        },
    },
    "golem": {
        "max_health": 30,
        "speed": 130.0,
        "aggro_radius": 280.0,
        "attack": {
            "kind": "melee",
            "engage_range": 60.0,
            "charge_time": 1.0,
            "target_charge": (1.0, 1.0),
            "charge1_fraction": 0.5,
            "advance_while_charging": True,
            "stun": "heavy",
            "sound": "golem_hit",
            "swing_duration": 0.45,
            "recovery": 1.4,
            "min_half_angle": 35.0,
            "max_half_angle": 60.0,
            "min_reach": 60.0,
            "max_reach": 92.0,
            "min_damage": 2,
            "max_damage": 8,
        },
    },
}
