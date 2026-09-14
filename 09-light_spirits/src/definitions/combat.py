"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains the combat rules shared by the player and every enemy:
lerp for charge scaling, how much each charge pose slows its owner down,
and what each level of stun does to whoever receives it. Anything that
differs between one weapon or one enemy and another lives in
src/definitions/weapons.py and src/definitions/enemies.py instead.
"""


def lerp(low: float, high: float, fraction: float) -> float:
    """ fraction=0 gives low, fraction=1 gives high, linear in between.
    Callers are expected to have already clamped fraction to [0, 1]. """
    return low + (high - low) * fraction


""" Movement speed multiplier while holding each charge pose. The heavier
the attack being wound up, the more committed its owner becomes, which
is what makes a full charge a real decision instead of a free upgrade. """
CHARGE_SPEED_FACTORS = {
    "charge1": 0.7,
    "charge2": 0.45,
}

""" duration: seconds without control after the hit.
knockback: pixels pushed away from whatever landed the hit.
knockback_time: seconds that push is spread over, always shorter than
the stun itself so the victim stops sliding before regaining control.
shake: amplitude in pixels of the stagger wobble drawn on the sprite. """
STUNS = {
    "light": {"duration": 0.35, "knockback": 16.0, "knockback_time": 0.12, "shake": 2.0},
    "heavy": {"duration": 1.0, "knockback": 46.0, "knockback_time": 0.25, "shake": 3.5},
}

# How long a sprite stays tinted after taking damage, and the tint added.
HIT_FLASH_TIME = 0.12
HIT_FLASH_COLOR = (120, 40, 40)
