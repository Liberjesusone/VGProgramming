"""
ISPPV1 2023
Study Case: Throw a Bird

Author: Alejandro Mujica
alejandro.j.mujic4@gmail.com

This file contains set_damping, a tiny helper shared by Bird and
Destructible. gale.physics.Body does not expose linear/angular damping
(only friction/restitution/density, set per-fixture through the shape
descriptors), but every archetype ported from the Lua source specifies
both, so this reaches one level past gale's public Body API, straight to
the underlying pybox2d body it wraps (Body._b2_body), to set them --
the only place in this project that does so.
"""

from gale.physics.body import Body


def set_damping(body: Body, linear_damping: float, angular_damping: float) -> None:
    body._b2_body.linearDamping = linear_damping
    body._b2_body.angularDamping = angular_damping
