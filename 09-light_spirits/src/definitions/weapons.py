"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains WEAPON_DEFS: everything that differs between the bow
and the sword. Player only ever reads this dict, switching weapons is
nothing more than changing which key of it is currently active (see
Player.equipped_weapon), and every state (idle, walk, attack) asks it
"what does my current pose look like" and "how does my attack play"
instead of knowing anything weapon-specific itself.

Every texture key below is a template with a {direction} placeholder,
resolved against settings.PLAYER_DIRECTIONS. Each weapon has its own
"step" pose (the walking silhouette) -- the bow's own art came first,
back when the plan was for both weapons to share one shared walk cycle,
but the sword ended up with a dedicated one of its own too, so there was
no longer a reason to make it share.

Tuning is a first guess, not a measured one: there is nothing in the
game yet for either weapon to actually hit (enemies are a later
milestone), so expect to retune all of this once there is something to
fight.
"""

from typing import Any, Dict

WEAPON_DEFS: Dict[str, Dict[str, Any]] = {
    "bow": {
        "kind": "ranged",
        # Seconds held to go from the weakest shot to the strongest.
        "charge_time": 0.9,
        "charge1_time": 0.6,
        "idle_texture": "player-bow-idle-{direction}",
        "step_texture": "player-bow-walk-{direction}",
        "charge1_texture": "player-bow-charge1-{direction}",
        "charge2_texture": "player-bow-charge2-{direction}",
        "attack_texture": "player-bow-release-{direction}",
        # How long the release *pose* holds before returning to idle,
        # not how long the arrow itself keeps flying, which is a
        # property of the Arrow that pose spawns and then lives on
        # independently of this state.
        "swing_duration": 0.15,
        "min_speed": 220.0,
        "max_speed": 940.0,
        "min_damage": 1,
        "max_damage": 2,
        "min_range": 60.0,
        "max_range": 540.0,
    },
    "sword": {
        "kind": "melee",
        "charge_time": 0.9,
        "charge1_time": 0.6,
        "idle_texture": "player-sword-idle-{direction}",
        "step_texture": "player-sword-walk-{direction}",
        "charge1_texture": "player-sword-charge1-{direction}",
        "charge2_texture": "player-sword-charge2-{direction}",
        "attack_texture": "player-sword-attack-{direction}",
        "swing_duration": 0.25,
        # The cone's half-angle in degrees (the full cone is twice
        # this), at no charge and at full charge. A charged swing is
        # deliberately wider, not just stronger, holding the button
        # should visibly promise to catch more of what is in front of
        # the player, not only hit it harder.
        "min_half_angle": 20.0,
        "max_half_angle": 55.0,
        "min_reach": 46.0,
        "max_reach": 78.0,
        "min_damage": 1,
        "max_damage": 3,
    },
}

""" The order weapons cycle through when the switch key is pressed. A list
rather than relying on dict order directly so this stays correct even
if WEAPON_DEFS is ever reordered for readability. """
WEAPON_ORDER = ["bow", "sword"]
