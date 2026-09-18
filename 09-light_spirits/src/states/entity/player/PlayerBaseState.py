"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains the class PlayerBaseState: the base every player state
extends, and the one piece of behaviour idle and walk both need in
exactly the same shape, letting whichever weapon is equipped charge
while either of them is running, and jumping to the attack the instant
the button is let go.
"""

from typing import TYPE_CHECKING

from gale.state import BaseState, StateMachine

""" Player.py imports this whole package to build its state machine, so
importing Player back here at module load time would be circular. Only
type checkers read this import, at no point during a real run. """
if TYPE_CHECKING:
    from src.entity.Player import Player


class PlayerBaseState(BaseState):
    def __init__(self, player: "Player", state_machine: StateMachine) -> None:
        super().__init__(state_machine)
        self.player = player

    def _update_charge(self, dt: float) -> None:
        """ Checks if we should start charging or change to attack_state

        Charging is not a state of its own (see the project's own design
        note on this: a charge has to keep building whether the player is
        standing still or walking, and a state machine only ever runs one
        state at a time), it is just flags on Player, read here by
        whichever state is currently allowed to charge.

        The pose flips from charge1 to charge2 at the halfway point, so
        the two-tier "light charge / heavy charge" look the player asked
        for reads directly off the same continuous value the eventual
        attack is scaled by, instead of needing its own separate tracking.

        Releasing the button is handled as requests: an edge-triggered flag, 
        set once by Player.on_input, consumed here the next time this runs.
        Callers must check afterwards whether they are still the active state,
        change_state may have just fired. """
        player = self.player
        weapon = player.weapon_def

        """ charge1_time/charge2_texture are both defined in seconds, but
        player.charge is the 0..1 fraction of charge_time already held,
        so the threshold needs the same conversion before comparing """
        charge1_fraction = weapon["charge1_time"] / weapon["charge_time"]

        if player.attack_held:
            player.charge = min(1.0, player.charge + dt / weapon["charge_time"])
            player.direction = player._aim_bucket()
            player.pose = "charge2" if player.charge >= charge1_fraction else "charge1"

        if player.attack_requested:
            player.attack_requested = False
            player.change_state("attack")

    def _update_roll(self) -> None:
        """ Checks if we sould start rolling to change to that state 
        
        Edge-triggered, the same shape as attack_requested above: set once
        by Player.on_input, consumed here the next time whichever state
        calls this runs. Only Idle and Walk call it, so a roll is never
        available mid-swing or mid-roll without either of those needing
        to guard against that themselves.

        Callers must check afterwards whether they are still the active
        state, same as after _update_charge.
        """
        if self.player.roll_requested:
            self.player.roll_requested = False
            self.player.change_state("roll")
