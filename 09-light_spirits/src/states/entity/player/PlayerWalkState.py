"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains the class PlayerWalkState: reads the held movement
keys into actual motion, and drives the little 2-pose step cycle
(alternating "idle" and "step") on top of the bob that has stood in for
a walk cycle since before either pose existed, both together read as
walking a good deal better than the bob alone did.
"""

import math

import pygame

from actions import MOVE_DOWN, MOVE_LEFT, MOVE_RIGHT, MOVE_UP
from src.definitions.combat import CHARGE_SPEED_FACTORS
from src.states.entity.player.PlayerBaseState import PlayerBaseState

SPEED = 110.0

""" The bob is a pure render offset, see Player.render, a sine wave
added to where the sprite is drawn, never to self.x/self.y themselves,
so it cannot desync collision or depth sorting from what is on screen. """
BOB_SPEED = 9.0
BOB_AMPLITUDE = 1.6


class PlayerWalkState(PlayerBaseState):
    def enter(self) -> None:
        self.phase = 0.0

    def update(self, dt: float) -> None:
        self._update_roll()

        # _update_roll can change the state to roll, same check as below
        if self.player.state_machine.current is not self:
            return

        self._update_charge(dt)

        # Since _update_charge can change the pose and the state to attack we check
        if self.player.state_machine.current is not self:
            return

        player = self.player
        dx = player.held[MOVE_RIGHT] - player.held[MOVE_LEFT]
        dy = player.held[MOVE_DOWN] - player.held[MOVE_UP]

        if dx == 0 and dy == 0:
            player.change_state("idle")
            return

        """ Normalised, so walking diagonally is not faster than walking straight, which it 
        would be if both axes moved a full step. _update_charge above already set the 
        pose if a charge is building, and each charge pose slows the walk down a little more. """
        speed = SPEED * CHARGE_SPEED_FACTORS.get(player.pose, 1.0)
        movement = pygame.Vector2(dx, dy).normalize() * speed * dt

        if abs(dx) > abs(dy):
            player.direction = "right" if dx > 0 else "left"
        else:
            player.direction = "down" if dy > 0 else "up"

        # One axis at a time, so running into a wall diagonally slides
        # along it instead of stopping dead.
        player._move_axis(movement.x, 0)
        player._move_axis(0, movement.y)

        self.phase += dt * BOB_SPEED
        player.bob_offset = math.sin(self.phase) * BOB_AMPLITUDE

        """ Charging overrides the step alternation, not the other way
        around: showing "about to strike" is more useful than which
        foot happens to be forward, and _update_charge already picked
        the right pose above if a charge is building. """
        if not player.attack_held:
            player.pose = "step" if math.sin(self.phase) > 0 else "idle"
