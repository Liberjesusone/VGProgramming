"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains the class PlayerIdleState.
"""

from src.states.entity.player.PlayerBaseState import PlayerBaseState


class PlayerIdleState(PlayerBaseState):
    def enter(self) -> None:
        """ No bob while standing still, WalkState is the only thing that
        ever sets this away from 0. """
        self.player.bob_offset = 0.0
        self.player.pose = "idle"

    def update(self, dt: float) -> None:
        self._update_roll()

        # _update_roll can change the state to roll, same check as below
        if self.player.state_machine.current is not self:
            return

        self._update_charge(dt)

        # Since _update_charge can change the pose and the state to attack we check
        if self.player.state_machine.current is not self:
            return

        # _update_charge already claimed the pose for this frame if a
        # charge is building; otherwise idle keeps showing.
        if not self.player.attack_held:
            self.player.pose = "idle"

        if any(self.player.held.values()):
            self.player.change_state("walk")
