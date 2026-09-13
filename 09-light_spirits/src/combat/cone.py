"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains a cone-shaped hitbox: contains_point is the actual hit
test, polygon_points is its outline for drawing it. Generic on purpose,
whether this cone belongs to the player's sword or, later, a boss
telegraph, is not this file's concern, so it carries no game-specific
tuning of its own (see src/definitions/combat.py for that).
"""

import math
from typing import List

import pygame

# How many straight edges approximate the cone's curved outer arc. This
# many already reads as smooth at the sizes this game draws at.
ARC_SEGMENTS = 10


def contains_point(
    origin: pygame.Vector2,
    direction: pygame.Vector2,
    half_angle_degrees: float,
    range_px: float,
    point: pygame.Vector2,
) -> bool:
    """
    :param origin: The cone's tip, in world coordinates.
    :param direction: A unit vector, the cone's own centre line.
    :param half_angle_degrees: How far the cone spreads to each side of
        direction, the full cone is twice this.
    :param range_px: How far the cone reaches.
    :param point: The point being tested, in world coordinates.

    To check if a point is contained in a cone, we get the angle
    between the line target point-origin and the cone's direction, 
    the point belongs if the angle is less than the half_angle_degrees
    and also the point is inside of range_px circle area.
    So we use the distance to check the area, and dot product to 
    check the angle
    """
    to_point = point - origin
    distance = to_point.length()

    if distance < 1e-6 or distance > range_px:
        return False

    cos_angle = direction.dot(to_point) / distance
    # Clamped: floating point can push this just past +-1, which
    # math.acos raises on.
    cos_angle = max(-1.0, min(1.0, cos_angle))
    return math.degrees(math.acos(cos_angle)) <= half_angle_degrees


def polygon_points(
    origin: pygame.Vector2,
    direction: pygame.Vector2,
    half_angle_degrees: float,
    range_px: float,
) -> List[pygame.Vector2]:
    """ The cone's outline, tip first, for pygame.draw.polygon, a fan of
    ARC_SEGMENTS straight edges standing in for its curved edge. """
    points = [origin]

    for i in range(ARC_SEGMENTS + 1):
        t = i / ARC_SEGMENTS
        angle = -half_angle_degrees + t * 2 * half_angle_degrees
        edge = direction.rotate(angle) * range_px
        points.append(origin + edge)

    return points
