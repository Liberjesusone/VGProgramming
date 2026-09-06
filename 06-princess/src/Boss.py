"""
ISPPV1 2023
Study Case: The Legend of the Princess (ARPG)

This file contains the class Boss.
"""

import settings
from src.definitions.entity import ENTITY_DEFS
from src.Entity import Entity
from src.states.entity.boss.BossChaseState import BossChaseState
from src.states.entity.boss.BossStunState import BossStunState


class Boss(Entity):
    """
    The fire mage. A plain Entity underneath, it keeps Entity.update, so
    the invulnerability timers and the animation clock still run, which is
    exactly what the stun leans on for its blink, with two states of its
    own instead of the wander/idle pair every other enemy gets, and no
    reference to the player at all: process_ai(room, dt) already hands it
    the room, and room.player is right there.
    """

    def __init__(self, x: float, y: float) -> None:
        definition = ENTITY_DEFS["villain"]

        super().__init__(
            x=x,
            y=y,
            width=settings.BOSS_WIDTH,
            height=settings.BOSS_HEIGHT,
            walk_speed=settings.BOSS_WALK_SPEED,
            health=settings.BOSS_HEALTH,
            animation_defs=definition["animations"],
            states={},
        )

        # Kept so the health bar can draw a fraction; self.health is what
        # actually gets whittled down.
        self.max_health = settings.BOSS_HEALTH

        self.contact_damage = settings.BOSS_CONTACT_DAMAGE

        # The 32x64 frame is taller than the 32x44 hitbox, and the mage is
        # drawn sitting on the bottom of it, so shifting the sprite up by
        # the difference puts his feet on the bottom of the box and lets
        # the hood overhang the top, the same perspective trick the
        # player's offset_y = 5 pulls.
        self.offset_x = 0
        self.offset_y = settings.VILLAIN_FRAME_HEIGHT - settings.BOSS_HEIGHT

        # Counts down to 0 in update(); while it is above 0 the mage
        # cannot be stunned again.
        self.stun_cooldown = 0.0

        # Bound with a default argument rather than closing over the name,
        # the same guard Room._generate_entities uses, so each lambda
        # keeps its own state class instead of all of them resolving to
        # whichever one the loop variable happened to end on.
        self.state_machine.states = {
            "chase": lambda sm, e=self: BossChaseState(e, sm),
            "stun": lambda sm, e=self: BossStunState(e, sm),
        }
        self.change_state("chase")

    def stun(self) -> bool:
        """
        Called by Room.update for every player projectile that connects,
        an arrow or a thrown pot. The cooldown check lives in here, not at
        the call site, on purpose: a hit that arrives too soon after the
        last stun still lands its damage, it just does not stagger him
        again. Otherwise a player could stand at range and chain arrows to
        keep the mage frozen for the whole fight.

        :returns: Whether the hit actually staggered him.
        """
        if self.stun_cooldown > 0:
            return False

        self.stun_cooldown = settings.BOSS_STUN_INTERVAL
        self.change_state("stun")
        return True

    def update(self, dt: float) -> None:
        if self.stun_cooldown > 0:
            self.stun_cooldown = max(0.0, self.stun_cooldown - dt)

        super().update(dt)
