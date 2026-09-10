"""Unit tests for the pure-math physics core (DESIGN.md section 11)."""

import math

from game import config, physics
from game.entities import Cell, Drone, Vec2


def test_gravity_accel_inverse_square():
    g1 = physics.gravity_accel(300.0)
    g2 = physics.gravity_accel(600.0)
    assert abs(g1 - 4.0 * g2) < 1e-9


def test_gravity_accel_softened_no_singularity():
    a0 = physics.gravity_accel(0.0)
    a_soft = physics.gravity_accel(config.SOFTENING_RADIUS)
    assert a0 == a_soft
    assert a0 > 0.0
    assert math.isfinite(a0)


def test_gravity_vector_points_toward_star():
    a = physics.gravity_vector(Vec2(100.0, 0.0))
    assert a.x > 0.0
    assert abs(a.y) < 1e-12


def test_gravity_vector_zero_distance_returns_zero():
    a = physics.gravity_vector(Vec2(0.0, 0.0))
    assert a.x == 0.0 and a.y == 0.0


def test_heading_vec_unit_length():
    v = physics.heading_vec(0.0)
    assert abs(v.x - 1.0) < 1e-9
    assert abs(v.y) < 1e-9
    v2 = physics.heading_vec(90.0)
    assert abs(v2.x) < 1e-9
    assert abs(v2.y - 1.0) < 1e-9


def test_circular_orbit_speed_matches_formula():
    r = 300.0
    v = physics.circular_orbit_speed(r)
    assert abs(v - math.sqrt(config.GRAVITY_G / r)) < 1e-6


def test_orbit_tangent_is_unit_and_perpendicular():
    center = Vec2(0.0, 0.0)
    pos = Vec2(100.0, 0.0)
    t = physics.orbit_tangent(center, pos, 1.0)
    assert abs(t.length() - 1.0) < 1e-9
    assert abs(t.dot(pos - center)) < 1e-9  # perpendicular to radius


def test_orbit_tangent_zero_radius_returns_zero():
    assert physics.orbit_tangent(Vec2(0, 0), Vec2(0, 0)).length() == 0.0


def test_integrate_is_symplectic_euler():
    pos = Vec2(0.0, 0.0)
    vel = Vec2(0.0, 0.0)
    accel = Vec2(1.0, 0.0)
    new_pos, new_vel = physics.integrate(pos, vel, accel, 0.5)
    assert abs(new_vel.x - 0.5) < 1e-9      # velocity updated first
    assert abs(new_pos.x - 0.25) < 1e-9     # position uses the NEW velocity


def test_step_mutates_body_in_place():
    class Body:
        pass

    b = Body()
    b.pos = Vec2(0.0, 0.0)
    b.vel = Vec2(0.0, 0.0)
    b.accel = Vec2(2.0, 0.0)
    physics.step(b, 1.0)
    assert b.vel.x == 2.0
    assert b.pos.x == 2.0


def test_collide_circle_overlap_inside_tangent_outside():
    drone = Drone(pos=Vec2(0.0, 0.0), radius=8.0)
    inside = Cell(pos=Vec2(6.0, 0.0), radius=2.0)
    tangent = Cell(pos=Vec2(10.0, 0.0), radius=2.0)
    outside = Cell(pos=Vec2(20.0, 0.0), radius=2.0)
    assert physics.collide_circle(drone, inside) is True
    assert physics.collide_circle(drone, tangent) is True   # touching counts
    assert physics.collide_circle(drone, outside) is False


def test_circles_overlap_direct():
    # distance 5 == radius sum 5 -> touching counts as overlap
    assert physics.circles_overlap(Vec2(0, 0), 5, Vec2(3, 4), 0) is True
    # distance 6 > radius sum 5.5 -> no overlap
    assert physics.circles_overlap(Vec2(0, 0), 5, Vec2(6, 0), 0.5) is False


def test_circular_orbit_stays_bounded_over_long_integration():
    """Symplectic Euler keeps a circular orbit bounded (no NaN, no runaway)."""
    center = Vec2(0.0, 0.0)
    r = 300.0
    pos = Vec2(r, 0.0)
    vel = physics.orbit_tangent(center, pos, 1.0) * physics.circular_orbit_speed(r)
    dt = config.FIXED_DT
    rmin = rmax = r
    for _ in range(12000):  # 100 simulated seconds
        rel = center - pos
        accel = physics.gravity_vector(rel)
        pos, vel = physics.integrate(pos, vel, accel, dt)
        assert math.isfinite(pos.x) and math.isfinite(pos.y)
        d = pos.length()
        rmin = min(rmin, d)
        rmax = max(rmax, d)
    # Bounded within 5% of the starting radius (no spiral in/out).
    assert rmin > r * 0.95
    assert rmax < r * 1.05
