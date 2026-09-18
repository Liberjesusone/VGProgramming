"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains the class Boss: everything both forms of the final
boss share, whatever they decide to do with it. SamuraiBoss and
SpiritBoss extend it with their own states and their own decide().

A boss lives in Level.entities next to the regular enemies, so the
player's arrows and sword reach it with no code of their own, but it
answers two questions differently than an Enemy does:

hittable is False whenever the boss should not take damage: while
dormant is fine, but not while falling, rising or dissolving. Level and
the player's attack both skip anything that is not hittable.

dead only becomes True once the boss has fully faded out (removed),
not when its health reaches zero, since the samurai's body stays on the
ground as a corpse for the whole second phase.

What it does next is always decided in one place, decide(), which first
empties plan, a queue of actions queued up by earlier ones (the thrust
queues a dash and three combo hits), and only then looks at the fight.
"""

import collections
import math
from typing import Any, Deque, Dict, List

import pygame

from gale.state import StateMachine

import settings
from src.combat.visuals import flashed
from src.definitions.combat import HIT_FLASH_TIME

FEET_DEPTH = 12
SHADOW_COLOR = (0, 0, 0, 100)

# Afterimages left behind while dashing: at most this many, each fading out
# at TRAIL_FADE of its opacity per second.
TRAIL_LENGTH = 6
TRAIL_FADE = 4.0
TRAIL_ALPHA = 120

# How fast the walk pose alternates with idle.
STEP_SPEED = 7.0


class Boss:
    def __init__(self, form: str, definition: Dict[str, Any], x: float, y: float, level: Any) -> None:
        self.form = form
        self.definition = definition
        self.name: str = definition["name"]
        self.max_health: int = definition["max_health"]
        self.health: int = self.max_health

        # Feet, same anchor every other entity uses.
        self.x = x
        self.y = y
        self.level = level

        self.direction = "down"
        self.pose = "idle"
        self.hit_flash = 0.0
        self.step_phase = 0.0

        # Tweened by the states that make the boss appear or fade away.
        self.alpha = 255.0
        self.vulnerable = False
        self.removed = False

        self.plan: Deque[str] = collections.deque()
        self.cooldowns: Dict[str, float] = {}
        self.trail: List[List[Any]] = []
        self.elapsed = 0.0

        idle = self.texture("idle", "down")
        self.body_width = idle.get_width()
        self.body_height = idle.get_height()

        shadow_width = int(self.body_width * 0.7)
        self._shadow = pygame.Surface((shadow_width, FEET_DEPTH), pygame.SRCALPHA)
        pygame.draw.ellipse(self._shadow, SHADOW_COLOR, self._shadow.get_rect())

        # Set fresh every frame by update(), same as Enemy.
        self._player: Any = None

        self.state_machine = StateMachine(self.build_states())

    def build_states(self) -> Dict[str, Any]:
        raise NotImplementedError

    def decide(self) -> None:
        raise NotImplementedError

    def on_strike_finished(self, name: str) -> None:
        self.decide()

    def change_state(self, name: str, *args: Any, **kwargs: Any) -> None:
        self.state_machine.change(name, *args, **kwargs)

    # ------------------------------------------------------------
    # Properties and Geometry
    # ------------------------------------------------------------
    @property
    def dead(self) -> bool:
        return self.removed

    @property
    def hittable(self) -> bool:
        return self.vulnerable and self.health > 0

    @property
    def sort_y(self) -> float:
        return self.y

    @property
    def center(self) -> pygame.Vector2:
        return pygame.Vector2(self.x, self.y - self.body_height / 2)

    def texture(self, pose: str, direction: str) -> pygame.Surface:
        regions = settings.TILESETS["bosses"]
        return regions.get(f"boss_{self.form}_{pose}_{direction}") or regions[f"boss_{self.form}_idle_down"]

    @property
    def sprite(self) -> pygame.Surface:
        return self.texture(self.pose, self.direction)

    def feet_rect_at(self, x: float, y: float) -> pygame.Rect:
        width = self.body_width * 0.4
        return pygame.Rect(round(x - width / 2), round(y - FEET_DEPTH), round(width), FEET_DEPTH)

    @property
    def feet_rect(self) -> pygame.Rect:
        return self.feet_rect_at(self.x, self.y)

    @property
    def hurt_rect(self) -> pygame.Rect:
        width = self.body_width * 0.55
        height = self.body_height * 0.85
        return pygame.Rect(round(self.x - width / 2), round(self.y - height), round(width), round(height))

    def to_player(self) -> pygame.Vector2:
        return self._player.center - self.center

    def aim_at_player(self, fallback: pygame.Vector2) -> pygame.Vector2:
        to_player = self.to_player()
        return to_player.normalize() if to_player.length_squared() > 1 else pygame.Vector2(fallback)

    def face(self, vector: pygame.Vector2) -> None:
        if vector.length_squared() < 1e-6:
            return

        if abs(vector.x) > abs(vector.y):
            self.direction = "right" if vector.x > 0 else "left"
        else:
            self.direction = "down" if vector.y > 0 else "up"

    # ------------------------------------------------------------
    # Movement
    # ------------------------------------------------------------
    def try_move(self, dx: float, dy: float) -> bool:
        """ Moves one axis at a time, same as every other entity, so a
        diagonal move that clips a prop still slides along it. Returns
        whether it moved at all, which is how a dash or an escape notices
        it has run into something. """
        moved = False

        for step_x, step_y in ((dx, 0.0), (0.0, dy)):
            if step_x == 0.0 and step_y == 0.0:
                continue

            target_x, target_y = self.x + step_x, self.y + step_y

            if not self.level.blocked(self.feet_rect_at(target_x, target_y)):
                self.x, self.y = target_x, target_y
                moved = True

        return moved

    def move_towards(self, vector: pygame.Vector2, speed: float, dt: float) -> bool:
        if vector.length_squared() < 1:
            return False

        step = vector.normalize() * speed * dt
        return self.try_move(step.x, step.y)

    def walk_pose(self, dt: float) -> None:
        self.step_phase += dt * STEP_SPEED
        self.pose = "walk" if math.sin(self.step_phase) > 0 else "idle"

    def add_trail(self) -> None:
        self.trail.append([self.x, self.y, self.sprite, 1.0])
        del self.trail[:-TRAIL_LENGTH]

    # ------------------------------------------------------------
    # Combat
    # ------------------------------------------------------------
    def damage(self, amount: int) -> None:
        if not self.hittable:
            return

        self.health = max(0, self.health - amount)
        self.hit_flash = HIT_FLASH_TIME

    def provoke(self) -> None:
        """ An arrow never interrupts a boss the way it does a regular
        enemy; a dormant samurai wakes up when it detects damage see BoosDormantState. """

    def ready(self, name: str) -> bool:
        return self.cooldowns.get(name, 0.0) <= 0.0

    def start_cooldown(self, name: str, seconds: float) -> None:
        self.cooldowns[name] = seconds

    # ------------------------------------------------------------
    # Update
    # ------------------------------------------------------------
    def update(self, dt: float, player: Any) -> None:
        self._player = player
        self.elapsed += dt
        self.hit_flash = max(0.0, self.hit_flash - dt)

        for name in self.cooldowns:
            self.cooldowns[name] = max(0.0, self.cooldowns[name] - dt)

        for ghost in self.trail: # We rest the opacity of the trail sprites
            ghost[3] -= dt * TRAIL_FADE

        self.trail = [ghost for ghost in self.trail if ghost[3] > 0]
        self.state_machine.update(dt)

    # ------------------------------------------------------------
    # Render
    # ------------------------------------------------------------
    def display_alpha(self) -> float:
        return self.alpha

    def _rect_for(self, surface: pygame.Surface, x: float, y: float) -> pygame.Rect:
        return pygame.Rect(
            round(x - surface.get_width() / 2),
            round(y - surface.get_height()),
            surface.get_width(),
            surface.get_height(),
        )

    def render(self, surface: pygame.Surface, camera: Any) -> None:
        alpha = self.display_alpha()

        if alpha <= 0:
            return

        shadow = self._shadow.copy()
        shadow.set_alpha(int(alpha))
        shadow_rect = pygame.Rect(
            round(self.x - shadow.get_width() / 2), round(self.y - FEET_DEPTH + 3),
            shadow.get_width(), FEET_DEPTH,
        )
        surface.blit(shadow, camera.apply(shadow_rect))

        for x, y, image, life in self.trail:
            ghost = image.copy()
            ghost.set_alpha(int(TRAIL_ALPHA * life * alpha / 255))
            surface.blit(ghost, camera.apply(self._rect_for(ghost, x, y)))

        sprite = flashed(self.sprite) if self.hit_flash > 0 else self.sprite

        if alpha < 255:
            sprite = sprite.copy()
            sprite.set_alpha(int(alpha))

        surface.blit(sprite, camera.apply(self._rect_for(sprite, self.x, self.y)))

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
