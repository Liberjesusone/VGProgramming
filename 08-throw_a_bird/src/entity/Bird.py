"""
ISPPV1 2023
Study Case: Throw a Bird

Author: Alejandro Mujica
alejandro.j.mujic4@gmail.com

This file contains the class Bird: the parrot sitting in the slingshot,
ported from main.script + the parrot.go. It is a plain dynamic circle
body -- heavy, invulnerable (no destructible.script attached, matching
the original) -- driven entirely by PlayState (aiming/panning/flinging
live there, since in the original they are main.script's own concerns,
not the parrot's).
"""

import math

import pygame

from gale.physics.shapes import CircleShape
from gale.physics.world import World

import settings
from src.definitions.entity import BIRD, density_for_circle

# How far to the side a bird produced by a split is placed, measured from
# the one it came out of. It has to clear a whole diameter or the two
# would be created overlapping, and Box2D resolves an overlap by shoving
# the pair apart hard, which would add speed the split is not supposed to
# give. A few pixels over is enough.
SPLIT_SPAWN_GAP = BIRD["radius"] * 2 + 4


class Bird:
    def __init__(self, world: World, x: float, y: float) -> None:
        self.radius: float = BIRD["radius"]
        self.mass: float = BIRD["mass"]

        density = density_for_circle(self.mass, self.radius)
        self.body = world.create_dynamic_body(
            x,
            y,
            CircleShape(
                radius=self.radius,
                density=density,
                friction=BIRD["friction"],
                restitution=BIRD["restitution"],
            ),
        )
        self.body.set_damping(BIRD["linear_damping"], BIRD["angular_damping"])
        self.body.user_data = self

        # Kept so the bird can be sent back to the slingshot and so
        # PlayState can measure how far a throw has travelled. For a bird
        # made by split_off this is wherever it was created, which is
        # never used: only the one that started in the slingshot is ever
        # reset or measured from.
        self.initial_position = pygame.Vector2(x, y)
        self.image = settings.TEXTURES[BIRD["sprite"]]

        # Held on to so a bird can take itself out of the simulation, and
        # so it can create another one of itself when it splits.
        self.world = world

    @property
    def position(self) -> pygame.Vector2:
        return self.body.position

    def reset(self) -> None:
        """
        Put the bird back to rest in the slingshot, ready for another
        throw -- ported from main.script's idle_frames > 100 branch.
        """
        self.body.position = self.initial_position
        self.body.angle = 0.0
        self.body.velocity = (0, 0)
        self.body.angular_velocity = 0.0

    def split_off(self, angle_degrees: float) -> "Bird":
        """
        Builds another bird carrying this one's speed, turned by
        angle_degrees.

        The velocity is rotated rather than rebuilt, so the new bird flies
        at exactly the speed this one had at the moment of the split and
        only its heading changes, which is what the brief asks for. A
        positive angle turns the flight downward and a negative one turns
        it upward, and each new bird is placed to the side its own turn
        takes it, so the three fan out from a common point instead of
        being created stacked on top of each other.
        """
        velocity = self.body.velocity

        heading = (
            velocity.normalize()
            if velocity.length_squared() > 0
            else pygame.Vector2(1, 0)
        )
        # Perpendicular to the flight, pointing to whichever side this
        # bird is turning toward. Sideways rather than forward on purpose:
        # placing them along their own new headings would leave the two
        # of them barely apart at small angles, and they would overlap.
        sideways = pygame.Vector2(-heading.y, heading.x)

        if angle_degrees < 0:
            sideways = -sideways

        spawn = self.position + sideways * SPLIT_SPAWN_GAP
        other = Bird(self.world, spawn.x, spawn.y)
        other.body.velocity = velocity.rotate(angle_degrees)
        other.body.angle = self.body.angle
        other.body.angular_velocity = self.body.angular_velocity
        return other

    def destroy(self) -> None:
        """Removes this bird from the physics world. Used on the extra
        birds a split produced once the turn is over."""
        self.world.destroy_body(self.body)

    def is_hitting_something(self) -> bool:
        """
        Whether this bird is in contact with anything real right now.

        The wind zones are sensors, and Body.touching_bodies reports
        sensor overlaps just like solid contacts, so flying into one would
        otherwise read as an impact. Wind is not something the bird hits,
        it is a volume that pushes it back, so it does not count.
        """
        return any(
            body.user_data != "wind" for body in self.body.touching_bodies
        )

    def render(self, surface: pygame.Surface, camera) -> None:
        diameter = max(1, round(self.radius * 2 * camera.zoom))
        scaled = pygame.transform.smoothscale(self.image, (diameter, diameter))
        rotated = pygame.transform.rotate(scaled, -math.degrees(self.body.angle))
        rect = rotated.get_rect(center=camera.world_to_screen(self.body.position))
        surface.blit(rotated, rect)
