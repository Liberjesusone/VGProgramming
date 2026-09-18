"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

Every input action id bound in settings.py and compared against in an
on_input, gathered in one place. Anything that binds a key/click to an
action, or reads input_id, imports its name from here instead of typing
the string again, so a typo or a rename shows up as an import error
instead of a silent mismatch.

This could be used as enum to compare faster, but optimization is not 
the full point of this project
"""

# ------------------------------------------------------------
# Actions
# ------------------------------------------------------------
CONFIRM = "confirm"
QUIT = "quit"

MOVE_UP = "move_up"
MOVE_DOWN = "move_down"
MOVE_LEFT = "move_left"
MOVE_RIGHT = "move_right"

DEBUG = "debug"
DEBUG_BOSS = "debug_boss"
SWITCH_WEAPON = "switch_weapon"
ATTACK = "attack"
ROLL = "roll"
HEAL = "heal"
