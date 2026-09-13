"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains lerp, the one small helper every weapon's charge math
needs. The tuning itself (how wide a cone, how fast an arrow, how much
either hits for) lives in src/definitions/weapons.py now, next to
everything else that differs between weapons
"""


def lerp(low: float, high: float, fraction: float) -> float:
    """ fraction=0 gives low, fraction=1 gives high, linear in between.
    Callers are expected to have already clamped fraction to [0, 1]. """
    return low + (high - low) * fraction
