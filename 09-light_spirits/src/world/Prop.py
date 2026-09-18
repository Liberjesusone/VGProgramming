"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains the class Prop: a piece of scenery that stands on the
floor, is taller than the ground it occupies, and can be walked behind.
"""

from typing import Any, Dict, List

import pygame

import settings


class Prop:
    """ A pillar, a tree, a sarcophagus: anything drawn on top of the floor
    rather than painted into it.

    Prop stands for property.

    Props are deliberately not tiles. A tile is one cell of a grid that
    the floor is made of; a pillar is one picture several tiles tall that
    happens to stand on a single cell. Keeping them apart means the art
    never has to be cut up to fit the grid, and it is what makes walking
    behind things possible at all.

    Two ideas do all the work here:

    The anchor is the feet, not a corner. x and y are the point where the
    prop meets the ground, at the bottom centre of its image, and the
    image is drawn upward from there. That single point is also the sort
    key the level uses to decide what is in front of what.

    What blocks is only the base. A dead tree is 160 px tall but the
    trunk it stands on is a couple of tiles wide and barely one deep, so
    solid_rect covers that base and nothing else. The whole crown above
    it is drawn but passable, which is exactly what "walking behind a
    tree" means.

    This separetion between what we draw and what we collide with is the 
    logic that allows that deep perspective 
    """

    def __init__(self, definition: Dict[str, Any], x: float, y: float) -> None:
        self.name: str = definition["name"]
        self.image: pygame.Surface = settings.TEXTURES[f"prop-{self.name}"]

        # Ground contact point: bottom centre of the image.
        self.x: float = x
        self.y: float = y

        self.width: int = self.image.get_width()
        self.height: int = self.image.get_height()

        """ The solid base, as fractions of the image's own width and a depth
        in pixels, so a prop keeps the same footprint if its art is later
        redrawn at another size. One centred part unless the definition
        lists its own (see src/definitions/props.py). A prop never moves
        once placed, so its collision boxes never change either. """
        self.solid_depth: float = definition["solid_depth"]
        if "solid_parts" in definition:
            parts = definition["solid_parts"]
        else:
            parts = [(0.5, definition["solid_width_ratio"])]

        left = self.x - self.width / 2

        self.solid_rects: List[pygame.Rect] = [
            pygame.Rect(
                round(left + self.width * centre - self.width * ratio / 2),
                round(self.y - self.solid_depth),
                round(self.width * ratio),
                round(self.solid_depth),
            )
            for centre, ratio in parts
        ]

        # The whole footprint in one box, what placement spacing is measured against.
        self.solid_rect: pygame.Rect = self.solid_rects[0].unionall(self.solid_rects[1:])

    @property
    def sort_y(self) -> float:
        """ Where this prop sits in the front-to-back order. The feet, so a
        player standing lower on the screen is drawn in front of it."""
        return self.y

    @property
    def image_rect(self) -> pygame.Rect:
        """ The whole drawn area, in world coordinates. """
        return pygame.Rect(
            round(self.x - self.width / 2),
            round(self.y - self.height),
            self.width,
            self.height,
        )

    def render(self, surface: pygame.Surface, camera: Any) -> None:
        surface.blit(self.image, camera.apply(self.image_rect))

    def render_debug(self, surface: pygame.Surface, camera: Any) -> None:
        pygame.draw.rect(surface, (90, 140, 220), camera.apply(self.image_rect), 1)

        for part in self.solid_rects:
            pygame.draw.rect(surface, (220, 80, 80), camera.apply(part), 1)
