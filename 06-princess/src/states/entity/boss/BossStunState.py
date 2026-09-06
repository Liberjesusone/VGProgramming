"""
ISPPV1 2023
Study Case: The Legend of the Princess (ARPG)

This file contains the class BossStunState.
"""

from typing import TypeVar

import pygame

import settings
from src.states.entity.BaseEntityState import BaseEntityState


class BossStunState(BaseEntityState):
    """
    Where an arrow or a thrown pot parks the mage for BOSS_STUN_TIME
    seconds: he stops walking, stops the fire timer (this state has no
    _fire of its own, and BossChaseState.enter resets fire_timer to 0 on
    the way back, so he never comes out of a stun firing instantly), and
    turns his back to the camera.
    """

    def enter(self) -> None:
        self.timer = 0.0

        boss = self.entity
        boss.direction = "up"
        boss.change_animation("idle-up")

        # Reuses the blink Entity.update and Entity.render_sprite already
        # drive for invulnerability frames, rather than adding a second
        # flash timer next to it. It only makes him translucent every
        # ~0.06s, Entity.damage never so much as looks at the flag,
        # so he stays perfectly hittable while stunned, which is the
        # entire point of stunning him.
        boss.go_invulnerable(settings.BOSS_STUN_TIME)

        settings.SOUNDS["hit-enemy"].play()

    def process_ai(self, room: TypeVar("Room"), dt: float) -> None:
        self.timer += dt

        if self.timer >= settings.BOSS_STUN_TIME:
            self.entity.change_state("chase")

    def render(self, surface: pygame.Surface) -> None:
        anim = self.entity.current_animation
        self.entity.render_sprite(surface, anim.texture_id, anim.get_current_frame())
