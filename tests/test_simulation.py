"""Integration tests for the Game loop wiring (headless, dummy SDL drivers).

These exercise the real main-loop Game object: orbit stability, determinism,
gate activation, wave progression, and game-over -- without a display.
"""

import math

from game import config, state
from game.entities import Vec2
from game.main import Game


def _no_input():
    return {"thrust": False, "rotate_left": False, "rotate_right": False}


def _make_game(seed=1, start=True):
    return Game(seed=seed, start=start)


def test_game_starts_in_playing_state():
    g = _make_game(start=True)
    assert g.phase == state.GamePhase.PLAYING
    assert g.wave == 1
    assert g.stats.lives == config.LIVES
    assert len(g.cells) == config.CELLS_BASE + config.CELLS_PER_WAVE


def test_drone_orbits_bounded_with_no_input():
    g = _make_game(start=True)
    for _ in range(600):  # 5 simulated seconds
        g._step(config.FIXED_DT, _no_input())
    p = g.drone.pos
    assert math.isfinite(p.x) and math.isfinite(p.y)
    d = p.distance(g.star.pos)
    assert d > 100.0          # did not fall into the star
    assert d < 600.0          # did not fly off to infinity


def test_deterministic_replay_same_seed_and_inputs():
    actions = []
    for i in range(300):
        actions.append(
            {
                "thrust": (i % 50) < 20,
                "rotate_left": (i % 30) < 10,
                "rotate_right": (i % 40) < 5,
            }
        )
    g1 = _make_game(seed=123)
    g2 = _make_game(seed=123)
    for a in actions:
        g1._step(config.FIXED_DT, a)
        g2._step(config.FIXED_DT, a)
    assert g1.drone.pos.to_tuple() == g2.drone.pos.to_tuple()
    assert g1.drone.vel.to_tuple() == g2.drone.vel.to_tuple()
    assert g1.stats.score == g2.stats.score


def test_gate_activates_when_all_cells_collected():
    g = _make_game(start=True)
    assert g.gate.active is False
    for c in g.cells:
        c.collected = True
    g._step(config.FIXED_DT, _no_input())
    assert g.gate.active is True


def test_crossing_gate_clears_wave_and_advances():
    g = _make_game(start=True)
    for c in g.cells:
        c.collected = True
    g._step(config.FIXED_DT, _no_input())
    assert g.gate.active is True

    g.drone.pos = g.gate.pos.copy()
    g.drone.vel = Vec2(0.0, 0.0)
    g._step(config.FIXED_DT, _no_input())  # cross gate -> clear wave
    assert g._between_waves is True

    for _ in range(int(2.0 / config.FIXED_DT) + 5):  # run the inter-wave beat
        g._step(config.FIXED_DT, _no_input())
    assert g.wave == 2
    assert g.phase == state.GamePhase.PLAYING


def test_game_over_after_three_deaths():
    g = _make_game(start=True)
    for _ in range(3):
        g.drone.invuln = 0.0
        g.drone.pos = g.star.pos.copy()
        g._step(config.FIXED_DT, _no_input())
    assert g.phase == state.GamePhase.GAMEOVER
    assert g.stats.lives == 0


def test_impulse_consumes_charge_and_changes_velocity():
    g = _make_game(start=True)
    charges = g.impulse_charges
    v_before = g.drone.vel.copy()
    g._fire_impulse()
    assert g.impulse_charges == charges - 1.0
    assert g.drone.vel.to_tuple() != v_before.to_tuple()


def test_cell_collection_scores_and_refills_impulse():
    g = _make_game(start=True)
    # move the drone onto the first cell (invulnerable at spawn)
    cell = g.cells[0]
    g.drone.pos = cell.pos.copy()
    g.drone.vel = Vec2(0.0, 0.0)
    score_before = g.stats.score
    g._step(config.FIXED_DT, _no_input())
    assert cell.collected is True
    assert g.stats.score > score_before


def test_renderer_draws_every_phase_without_crash():
    """Each screen (title/playing/pause/game-over) renders headlessly."""
    g = _make_game(start=False)      # TITLE backdrop
    g.renderer.draw(g, 1.0 / 60.0)

    g._start_run()                    # PLAYING
    g.renderer.draw(g, 1.0 / 60.0)

    g._toggle_pause()                 # PAUSED
    assert g.phase == state.GamePhase.PAUSED
    g.renderer.draw(g, 1.0 / 60.0)

    g._resume()
    for _ in range(3):                # force game over
        g.drone.invuln = 0.0
        g.drone.pos = g.star.pos.copy()
        g._step(config.FIXED_DT, _no_input())
    assert g.phase == state.GamePhase.GAMEOVER
    g.renderer.draw(g, 1.0 / 60.0)
