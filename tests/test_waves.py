"""Unit tests for wave/difficulty generators (DESIGN.md section 11)."""

from game import config, waves
from game.entities import Vec2

CENTER = Vec2(480.0, 270.0)


def test_cells_count_formula_and_cap():
    assert waves.cells_count(1) == config.CELLS_BASE + config.CELLS_PER_WAVE * 1
    assert waves.cells_count(5) == config.CELLS_BASE + config.CELLS_PER_WAVE * 5
    assert waves.cells_count(50) == config.CELLS_CAP


def test_asteroids_count_formula_and_cap():
    assert waves.asteroids_count(1) == 1
    assert waves.asteroids_count(4) == 4
    assert waves.asteroids_count(50) == config.ASTEROIDS_CAP


def test_shell_radius_monotonic_with_floor():
    prev = float("inf")
    for n in range(1, 25):
        r = waves.shell_radius(n)
        assert r <= prev
        assert r >= config.SHELL_RADIUS_FLOOR
        prev = r
    assert waves.shell_radius(1) == config.SHELL_RADIUS_INITIAL


def test_time_limit_monotonic_with_floor():
    prev = float("inf")
    for n in range(1, 40):
        t = waves.time_limit(n)
        assert t <= prev
        assert t >= config.WAVE_TIME_FLOOR
        prev = t


def test_star_kill_radius_grows_and_caps():
    assert waves.star_kill_radius(1) == config.STAR_KILL_RADIUS
    prev = 0.0
    for n in range(1, 40):
        r = waves.star_kill_radius(n)
        assert r >= prev
        assert r <= config.STAR_KILL_RADIUS_CAP
        prev = r


def test_asteroid_orbit_speed_scales_with_wave():
    base = waves.asteroid_orbit_speed(1, 300.0)
    later = waves.asteroid_orbit_speed(8, 300.0)
    assert later > base


def test_spawn_wave_is_deterministic():
    w1 = waves.spawn_wave(3, 12345, CENTER)
    w2 = waves.spawn_wave(3, 12345, CENTER)
    assert [c.pos.to_tuple() for c in w1.cells] == [c.pos.to_tuple() for c in w2.cells]
    assert w1.gate.pos.to_tuple() == w2.gate.pos.to_tuple()
    assert [a.angular_vel for a in w1.asteroids] == [a.angular_vel for a in w2.asteroids]
    assert w1.shell_radius == w2.shell_radius
    assert w1.time_limit == w2.time_limit


def test_spawn_wave_counts_match_formula():
    for n in (1, 2, 5, 9, 20):
        w = waves.spawn_wave(n, n, CENTER)
        assert len(w.cells) == waves.cells_count(n)
        assert len(w.asteroids) == waves.asteroids_count(n)


def test_spawn_wave_cells_inside_arena():
    for n in (1, 3, 7):
        w = waves.spawn_wave(n, n * 999, CENTER)
        kill = waves.star_kill_radius(n)
        for c in w.cells:
            d = c.pos.distance(CENTER)
            assert d > kill
            assert d <= w.shell_radius


def test_spawn_wave_asteroids_within_arena():
    for n in (1, 4, 8):
        w = waves.spawn_wave(n, n + 1, CENTER)
        for a in w.asteroids:
            assert 0.0 < a.orbit_radius <= w.shell_radius
            assert a.angular_vel != 0.0
            assert config.ASTEROID_RADIUS_MIN <= a.radius <= config.ASTEROID_RADIUS_MAX


def test_spawn_wave_feature_gates():
    assert waves.spawn_wave(3, 1, CENTER).gravity_pulse is False
    assert waves.spawn_wave(4, 1, CENTER).gravity_pulse is True
    assert waves.spawn_wave(5, 1, CENTER).nova is False
    assert waves.spawn_wave(6, 1, CENTER).nova is True


def test_different_seeds_produce_different_layouts():
    a = waves.spawn_wave(4, 1, CENTER)
    b = waves.spawn_wave(4, 2, CENTER)
    assert [c.pos.to_tuple() for c in a.cells] != [c.pos.to_tuple() for c in b.cells]


def test_spawn_wave_handles_tight_arena_without_crash(monkeypatch):
    """The defensive band clamp keeps cell placement valid even if the shell
    is mis-tuned tighter than the star's kill zone (future playtest tuning)."""
    monkeypatch.setattr(config, "SHELL_RADIUS_INITIAL", 40.0)
    monkeypatch.setattr(config, "SHELL_RADIUS_FLOOR", 40.0)
    monkeypatch.setattr(config, "CELL_MIN_ORBIT_RADIUS", 30.0)
    w = waves.spawn_wave(1, 7, CENTER)
    assert len(w.cells) == waves.cells_count(1)
    for c in w.cells:
        assert c.pos.distance(CENTER) > 0.0
        assert c.pos.x == c.pos.x and c.pos.y == c.pos.y  # finite
