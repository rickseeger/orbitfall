"""Unit tests for the on-screen containment boundary (off-screen-flight fix).

`physics.contain_on_screen` is the pure, deterministic clamp that guarantees the
drone can never be stranded off-screen. These tests pin down the exact behavior
at every edge and for inward vs outward velocity.
"""

import math

from game import config, physics
from game.entities import Vec2

W = config.WINDOW_WIDTH
H = config.WINDOW_HEIGHT
M = config.BOUNDARY_MARGIN


def test_inside_position_is_unchanged():
    pos = Vec2(W / 2, H / 2)
    vel = Vec2(30.0, -40.0)
    np, nv = physics.contain_on_screen(pos, vel)
    assert np.to_tuple() == pos.to_tuple()
    assert nv.to_tuple() == vel.to_tuple()


def test_clamp_left_edge_and_kill_outward_velocity():
    np, nv = physics.contain_on_screen(Vec2(-50.0, 100.0), Vec2(-200.0, 0.0))
    assert np.x == M
    assert np.y == 100.0
    assert nv.x == 0.0          # outward (leftward) velocity killed
    assert nv.y == 0.0


def test_clamp_right_edge():
    np, nv = physics.contain_on_screen(Vec2(W + 500.0, 50.0), Vec2(300.0, 10.0))
    assert np.x == W - M
    assert nv.x == 0.0          # outward (rightward) velocity killed
    assert nv.y == 10.0         # along-edge velocity preserved


def test_clamp_top_edge():
    np, nv = physics.contain_on_screen(Vec2(200.0, -999.0), Vec2(0.0, -500.0))
    assert np.y == M
    assert nv.y == 0.0


def test_clamp_bottom_edge():
    np, nv = physics.contain_on_screen(Vec2(200.0, H + 999.0), Vec2(0.0, 500.0))
    assert np.y == H - M
    assert nv.y == 0.0


def test_inward_velocity_preserved_at_edge():
    # pinned at the left edge but moving inward (right) keeps its velocity
    np, nv = physics.contain_on_screen(Vec2(-10.0, 200.0), Vec2(150.0, 0.0))
    assert np.x == M
    assert nv.x == 150.0        # inward velocity untouched


def test_margin_matches_window_and_is_positive():
    assert M > 0.0
    assert 2 * M < W
    assert 2 * M < H


def test_clamped_position_is_always_finite_and_in_bounds():
    cases = [
        (Vec2(-1e9, -1e9), Vec2(-1e9, -1e9)),
        (Vec2(1e9, 1e9), Vec2(1e9, 1e9)),
        (Vec2(W + 1e6, -1e6), Vec2(1e6, -1e6)),
        (Vec2(-1e6, H + 1e6), Vec2(-1e6, 1e6)),
    ]
    for pos, vel in cases:
        np, nv = physics.contain_on_screen(pos, vel)
        assert M <= np.x <= W - M
        assert M <= np.y <= H - M
        assert math.isfinite(np.x) and math.isfinite(np.y)
        assert math.isfinite(nv.x) and math.isfinite(nv.y)
