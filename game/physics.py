"""Pure-math simulation core: integrator, gravity, collision resolution.

Per DESIGN.md section 9 this module must stay pure and deterministic: no
pygame import, no wall-clock, no rendering -- so it is fully unit-testable in
headless CI.

Public API:
    gravity_accel(radius, G=..., soft=...) -> float
    gravity_vector(rel, G=..., soft=...) -> Vec2    (rel = star - body)
    heading_vec(heading_deg) -> Vec2
    circular_orbit_speed(radius, G=..., soft=...) -> float
    orbit_tangent(center, pos, sign=1.0) -> Vec2
    integrate(pos, vel, accel, dt) -> (pos, vel)    # symplectic Euler
    step(body, dt) -> None                          # body has .pos/.vel/.accel
    collide_circle(a, b) -> bool                    # a, b have .pos/.radius
    circles_overlap(apos, aradius, bpos, bradius) -> bool
    contain_on_screen(pos, vel, width, height, margin) -> (pos, vel)
"""

from __future__ import annotations

import math

from game import config
from game.entities import Vec2

__all__ = [
    "gravity_accel",
    "gravity_vector",
    "heading_vec",
    "circular_orbit_speed",
    "orbit_tangent",
    "integrate",
    "step",
    "collide_circle",
    "circles_overlap",
    "contain_on_screen",
]


def gravity_accel(
    radius: float,
    G: float = config.GRAVITY_G,
    soft: float = config.SOFTENING_RADIUS,
) -> float:
    """Inverse-square inward acceleration magnitude, softened near the star."""
    r = max(radius, soft)
    return G / (r * r)


def gravity_vector(
    rel: Vec2,
    G: float = config.GRAVITY_G,
    soft: float = config.SOFTENING_RADIUS,
) -> Vec2:
    """Acceleration vector toward the star. `rel` points from body to star."""
    dist = rel.length()
    if dist == 0.0:
        return Vec2(0.0, 0.0)
    return rel * (gravity_accel(dist, G, soft) / dist)


def heading_vec(heading_deg: float) -> Vec2:
    """Unit vector along a heading (degrees, 0 = right, + = clockwise)."""
    return Vec2.from_angle(heading_deg)


def circular_orbit_speed(
    radius: float,
    G: float = config.GRAVITY_G,
    soft: float = config.SOFTENING_RADIUS,
) -> float:
    """Tangential speed for a stable circular orbit at `radius` (px/s)."""
    r = max(radius, soft)
    return math.sqrt(G * r) / r


def orbit_tangent(center: Vec2, pos: Vec2, sign: float = 1.0) -> Vec2:
    """Unit tangent vector for a circular orbit around `center` at `pos`.

    `sign > 0` gives counter-clockwise motion on screen (y-down); flip it with `sign < 0`.
    """
    rel = pos - center
    length = rel.length()
    if length == 0.0:
        return Vec2(0.0, 0.0)
    tangent = rel.perp()
    return tangent * (sign / length)


def integrate(
    pos: Vec2, vel: Vec2, accel: Vec2, dt: float
) -> tuple[Vec2, Vec2]:
    """Symplectic (semi-implicit) Euler step. Returns (new_pos, new_vel)."""
    new_vel = vel + accel * dt
    new_pos = pos + new_vel * dt
    return new_pos, new_vel


def step(body, dt: float) -> None:
    """Mutate a body in place with symplectic Euler.

    `body` needs `.pos`, `.vel` and `.accel` attributes (all Vec2).
    """
    body.vel += body.accel * dt
    body.pos += body.vel * dt


def circles_overlap(
    apos: Vec2, aradius: float, bpos: Vec2, bradius: float
) -> bool:
    """True when two circles intersect (touching counts as a hit)."""
    rr = aradius + bradius
    return apos.distance(bpos) <= rr


def collide_circle(a, b) -> bool:
    """True when two circle bodies overlap. Each needs `.pos` and `.radius`."""
    return circles_overlap(a.pos, a.radius, b.pos, b.radius)


def contain_on_screen(
    pos: Vec2,
    vel: Vec2,
    width: float = config.WINDOW_WIDTH,
    height: float = config.WINDOW_HEIGHT,
    margin: float = config.BOUNDARY_MARGIN,
) -> tuple[Vec2, Vec2]:
    """Clamp a body to the playfield and kill any outward velocity.

    Keeps `pos` inside [margin, width - margin] x [margin, height - margin].
    When a coordinate is clamped to an edge, the matching velocity component
    is zeroed if it still points out of bounds, so neither gravity, thrust,
    nor impulse can eject the ship off-screen. Returns (new_pos, new_vel);
    the input vectors are not mutated.
    """
    min_x = margin
    max_x = width - margin
    min_y = margin
    max_y = height - margin

    x, y = pos.x, pos.y
    vx, vy = vel.x, vel.y

    if x < min_x:
        x = min_x
        if vx < 0.0:
            vx = 0.0
    elif x > max_x:
        x = max_x
        if vx > 0.0:
            vx = 0.0

    if y < min_y:
        y = min_y
        if vy < 0.0:
            vy = 0.0
    elif y > max_y:
        y = max_y
        if vy > 0.0:
            vy = 0.0

    return Vec2(x, y), Vec2(vx, vy)
