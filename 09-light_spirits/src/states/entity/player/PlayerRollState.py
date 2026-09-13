"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains the class PlayerRollState: a fixed-distance dash,
covering DISTANCE over DURATION at constant speed, toward whatever
movement key is held or, with none held, toward the mouse instead.
Grants invulnerability for a duration (see Player.invulnerable)
and spends any charge already building, the same way PlayerAttackState's
own entry does, rolling out of a charge cancels it rather than
carrying it into the roll.
"""

import pygame

from actions import MOVE_DOWN, MOVE_LEFT, MOVE_RIGHT, MOVE_UP
from src.states.entity.player.PlayerBaseState import PlayerBaseState

DURATION = 0.45
DISTANCE = 130.0

""" Elapsed-time fraction at which the pose switches from roll1 to roll2
to roll3, three equal thirds, matching the three source poses (start
crouch, tucked mid-roll, recovery), unlike the walk cycle's own 2-pose
alternation, a roll is a one-shot arc, not a repeating cycle. """
POSE_1_END = 1 / 3
POSE_2_END = 2 / 3

STAMINA_COST = 1.5

class PlayerRollState(PlayerBaseState):
    def enter(self) -> None:
        player = self.player
        dx = player.held[MOVE_RIGHT] - player.held[MOVE_LEFT]
        dy = player.held[MOVE_DOWN] - player.held[MOVE_UP]

        # Select the moving direction or the aim direction if we are idle
        self.direction_vector = (
            pygame.Vector2(dx, dy).normalize()
            if (dx, dy) != (0, 0)
            else pygame.Vector2(player.aim_direction)
        )
        player.direction = player._bucket_direction(self.direction_vector)

        player.charge = 0.0
        player.attack_held = False

        player.pose = "roll1"
        player.invulnerable = True

        self.elapsed = 0.0
        self.speed = DISTANCE / DURATION

        # Stamina waste
        player.current_stamina -= STAMINA_COST

    def update(self, dt: float) -> None:
        self.elapsed += dt
        player = self.player

        step = self.direction_vector * self.speed * dt
        player._move_axis(step.x, 0)
        player._move_axis(0, step.y)

        fraction = self.elapsed / DURATION

        if fraction < POSE_1_END:
            player.pose = "roll1"
        elif fraction < POSE_2_END:
            player.pose = "roll2"
            player.invulnerable = False
        else:
            player.pose = "roll3"

        if self.elapsed >= DURATION:
            player.change_state("idle")

    def exit(self) -> None:
        self.player.invulnerable = False
