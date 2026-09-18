"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains the class Enemy: one class for every kind of enemy,
whose stats and single attack come from ENEMY_DEFS[kind] (see
src/definitions/enemies.py), the same way Player never branches on its
weapon and only reads WEAPON_DEFS.

Every enemy stands still on guard until the player enters its
aggro_radius, then chases, charges its attack once within engage_range,
releases it, recovers, and chases again. No patrol and no losing aggro
once triggered.

self.pose ("idle", "walk", "charge1", "charge2" or "attack") and
self.direction pick the sprite, exactly like Player.
"""

from typing import Any, Dict

import pygame

from gale.state import StateMachine

import settings
from src.combat.visuals import flashed
from src.definitions.combat import HIT_FLASH_TIME
from src.definitions.enemies import ENEMY_DEFS
from src.states.entity import enemy as enemy_states

FEET_DEPTH = 10
SHADOW_COLOR = (0, 0, 0, 90)


class Enemy:
    def __init__(self, kind: str, x: float, y: float, level: Any) -> None:
        self.kind = kind
        self.definition: Dict[str, Any] = ENEMY_DEFS[kind]

        # Feet, same anchor Player and Prop both use, so all three sort
        # and collide against each other with no conversion.
        self.x = x
        self.y = y
        self.level = level
        self.health = self.definition["max_health"]

        self.direction = "down"
        self.pose = "idle"
        self.hit_flash = 0.0

        """ Body size, read once off the idle sprite rather than whichever
        pose is showing, so the hitbox never grows just because an attack
        pose happens to hold a weapon out further. """
        idle = settings.TEXTURES[f"enemy-{kind}-idle-down"]
        self.body_width = idle.get_width()
        self.body_height = idle.get_height()

        shadow_width = int(self.body_width * 0.8)
        self._shadow = pygame.Surface((shadow_width, FEET_DEPTH), pygame.SRCALPHA)
        pygame.draw.ellipse(self._shadow, SHADOW_COLOR, self._shadow.get_rect())

        """ Set fresh every frame by update() below and never kept beyond
        that, the same way Player receives the camera per call instead of
        holding onto it. Whichever state is running reads it from here. """
        self._player: Any = None

        self.state_machine = StateMachine(
            {
                "guard": lambda sm, e=self: enemy_states.EnemyGuardState(e, sm),
                "chase": lambda sm, e=self: enemy_states.EnemyChaseState(e, sm),
                "charge": lambda sm, e=self: enemy_states.EnemyChargeState(e, sm),
                "attack": lambda sm, e=self: enemy_states.EnemyAttackState(e, sm),
            }
        )
        self.change_state("guard")

    def change_state(self, name: str, *args: Any, **kwargs: Any) -> None:
        self.state_machine.change(name, *args, **kwargs)

    # ------------------------------------------------------------
    # Properties and Geometry
    # ------------------------------------------------------------
    @property
    def attack(self) -> Dict[str, Any]:
        return self.definition["attack"]

    @property
    def dead(self) -> bool:
        return self.health <= 0

    @property
    def sort_y(self) -> float:
        return self.y

    @property
    def sprite(self) -> pygame.Surface:
        return settings.TEXTURES[f"enemy-{self.kind}-{self.pose}-{self.direction}"]

    @property
    def center(self) -> pygame.Vector2:
        return pygame.Vector2(self.x, self.y - self.body_height / 2)

    def feet_rect_at(self, x: float, y: float) -> pygame.Rect:
        width = self.body_width * 0.55
        return pygame.Rect(round(x - width / 2), round(y - FEET_DEPTH), round(width), FEET_DEPTH)

    @property
    def feet_rect(self) -> pygame.Rect:
        return self.feet_rect_at(self.x, self.y)

    @property
    def hurt_rect(self) -> pygame.Rect:
        """ The body, what the player's arrows test against. The feet box
        alone would only ever be crossed by an arrow flying at ground
        level, never by one shot from chest height at a standing enemy. """
        width = self.body_width * 0.7
        height = self.body_height * 0.9
        return pygame.Rect(round(self.x - width / 2), round(self.y - height), round(width), round(height))

    def to_player(self) -> pygame.Vector2:
        return self._player.center - self.center

    def face(self, vector: pygame.Vector2) -> None:
        if vector.length_squared() < 1e-6:
            return

        if abs(vector.x) > abs(vector.y):
            self.direction = "right" if vector.x > 0 else "left"
        else:
            self.direction = "down" if vector.y > 0 else "up"

    def move_towards(self, vector: pygame.Vector2, speed: float, dt: float) -> None:
        """ One axis at a time, same as Player._move_axis, so closing in
        while clipping a prop diagonally slides along it instead of
        stopping dead. """
        if vector.length_squared() < 1:
            return

        step = vector.normalize() * speed * dt

        for dx, dy in ((step.x, 0.0), (0.0, step.y)):
            target_x, target_y = self.x + dx, self.y + dy

            if not self.level.blocked(self.feet_rect_at(target_x, target_y)):
                self.x, self.y = target_x, target_y

    @property
    def hittable(self) -> bool:
        # A regular enemy can always be hit, see Boss.hittable for one that sometimes can't.
        return True

    def damage(self, amount: int) -> None:
        self.health = max(0, self.health - amount)
        self.hit_flash = HIT_FLASH_TIME

    def provoke(self) -> None:
        """ Called when an arrow lands: the enemy turns on the player at
        once, from guard or from the middle of an attack. """
        self.change_state("chase")

    # ------------------------------------------------------------
    # Update
    # ------------------------------------------------------------
    def update(self, dt: float, player: Any) -> None:
        self._player = player
        self.hit_flash = max(0.0, self.hit_flash - dt)
        self.state_machine.update(dt)

    # ------------------------------------------------------------
    # Render
    # ------------------------------------------------------------
    def render(self, surface: pygame.Surface, camera: Any) -> None:
        shadow_rect = pygame.Rect(
            round(self.x - self._shadow.get_width() / 2),
            round(self.y - FEET_DEPTH + 2),
            self._shadow.get_width(),
            FEET_DEPTH,
        )
        surface.blit(self._shadow, camera.apply(shadow_rect))

        sprite = self.sprite
        """ Anchored bottom centre on the feet, not sized off body_height:
        every pose keeps its own proportions from the sprite sheet, so a
        raised weapon in charge2 reaches up past the idle silhouette
        instead of squashing the whole body down to fit. """
        rect = pygame.Rect(
            round(self.x - sprite.get_width() / 2),
            round(self.y - sprite.get_height()),
            sprite.get_width(),
            sprite.get_height(),
        )
        surface.blit(flashed(sprite) if self.hit_flash > 0 else sprite, camera.apply(rect))

    def render_telegraph(self, surface: pygame.Surface, camera: Any) -> None:
        render = getattr(self.state_machine.current, "render_telegraph", None)

        if render is not None:
            render(surface, camera)

    # ------------------------------------------------------------
    # Debug
    # ------------------------------------------------------------
    def render_debug(self, surface: pygame.Surface, camera: Any) -> None:
        pygame.draw.rect(surface, (220, 80, 80), camera.apply(self.feet_rect), 1)
        pygame.draw.rect(surface, (90, 220, 140), camera.apply(self.hurt_rect), 1)
        pygame.draw.circle(
            surface,
            (200, 200, 60),
            camera.world_to_screen((self.x, self.y)),
            round(self.definition["aggro_radius"] * camera.zoom),
            1,
        )
