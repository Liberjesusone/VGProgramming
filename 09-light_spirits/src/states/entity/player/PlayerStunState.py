"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains the class PlayerStunState: the stagger after taking a
hit that carries a stun (see combat.STUNS). The player is pushed away
from whatever hit them, wobbles on screen, and has no control until the
stun runs out: no moving, no charging, no rolling.

That loss of control is the point. A single weak enemy's light stun lasts
only an instant, but it is enough for the next enemy's swing to land
before the player can roll away, so a group of weak enemies can chain
their hits into real damage and none of them is safe to ignore.

A hit landing while already stunned restarts the stagger, and keeps
whichever of the two stuns has more time left, so a light hit never cuts
a heavy stun short.
"""

import math

import pygame

from src.definitions.combat import STUNS
from src.states.entity.player.PlayerBaseState import PlayerBaseState

# Wobbles per second of the stagger shake drawn on the sprite.
SHAKE_FREQUENCY = 30.0


class PlayerStunState(PlayerBaseState):
    def enter(self, kind: str, source: pygame.Vector2, carried: float = 0.0) -> None:
        player = self.player
        self.stun = STUNS[kind]

        self.elapsed = 0.0
        self.duration = max(self.stun["duration"], carried)

        # source is the point where the hit came from
        push = player.center - pygame.Vector2(source)
        self.push_direction = push.normalize() if push.length_squared() > 1e-6 else pygame.Vector2(0, 0)

        # Whatever was being charged or queued is lost with the hit.
        player.charge = 0.0
        player.attack_held = False
        player.attack_requested = False
        player.roll_requested = False
        player.bob_offset = 0.0
        player.pose = "idle"

    @property
    def remaining(self) -> float:
        return max(0.0, self.duration - self.elapsed)

    def update(self, dt: float) -> None:
        player = self.player
        self.elapsed += dt

        # We move the player a dt step
        if self.elapsed <= self.stun["knockback_time"]:
            speed = self.stun["knockback"] / self.stun["knockback_time"]
            step = self.push_direction * speed * dt
            player._move_axis(step.x, 0)
            player._move_axis(0, step.y)

        # The less reamining time there is, the smallest the offset
        fade: float = self.remaining / self.duration
        player.stagger_offset = math.sin(self.elapsed * SHAKE_FREQUENCY) * self.stun["shake"] * fade

        if self.elapsed >= self.duration:
            player.change_state("idle")

    def exit(self) -> None:
        self.player.stagger_offset = 0.0
