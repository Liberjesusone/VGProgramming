"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This module contains the player's own states.
"""

from src.states.entity.player.PlayerAttackState import PlayerAttackState
from src.states.entity.player.PlayerIdleState import PlayerIdleState
from src.states.entity.player.PlayerRollState import PlayerRollState
from src.states.entity.player.PlayerStunState import PlayerStunState
from src.states.entity.player.PlayerWalkState import PlayerWalkState

(
    PlayerAttackState,
    PlayerIdleState,
    PlayerRollState,
    PlayerStunState,
    PlayerWalkState,
)
