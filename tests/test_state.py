"""Unit tests for the score/combo/lives state machine (DESIGN.md section 11)."""

from game import config, state


def test_collect_cell_uses_combo_and_increments():
    s = state.RunStats()
    assert state.collect_cell(s) == config.CELL_VALUE * 1
    assert s.combo == 2
    assert s.score == config.CELL_VALUE
    assert state.collect_cell(s) == config.CELL_VALUE * 2
    assert s.combo == 3


def test_combo_capped():
    s = state.RunStats()
    for _ in range(30):
        state.collect_cell(s)
    assert s.combo == config.COMBO_CAP


def test_combo_resets_after_window_expires():
    s = state.RunStats()
    state.collect_cell(s)
    state.collect_cell(s)
    assert s.combo == 3
    state.tick_combo(s, config.COMBO_WINDOW + 0.01)
    assert s.combo == 1
    state.tick_combo(s, 10.0)  # stays reset
    assert s.combo == 1


def test_combo_kept_within_window():
    s = state.RunStats()
    state.collect_cell(s)          # combo 2, timer = COMBO_WINDOW
    state.tick_combo(s, 1.0)       # 1.0 s left
    state.collect_cell(s)          # within window -> combo 3
    assert s.combo == 3


def test_lose_life_decrements_and_signals_game_over():
    s = state.RunStats()           # config.LIVES == 3
    assert state.lose_life(s) is False
    assert s.lives == 2
    assert state.lose_life(s) is False
    assert state.lose_life(s) is True
    assert s.lives == 0
    assert state.lose_life(s) is True   # clamps at zero, still game over
    assert s.lives == 0


def test_lose_life_resets_combo():
    s = state.RunStats()
    state.collect_cell(s)
    state.collect_cell(s)
    assert s.combo > 1
    state.lose_life(s)
    assert s.combo == 1
    assert s.combo_timer == 0.0


def test_add_score_clamps_negatives():
    s = state.RunStats()
    state.add_score(s, 150)
    state.add_score(s, -50)
    assert s.score == 150


def test_wave_clear_bonus_scales_with_wave_and_time():
    assert state.wave_clear_bonus(1, 30.0) == config.WAVE_CLEAR_BONUS_BASE * 1 + 30 * config.TIME_BONUS_PER_SECOND
    assert state.wave_clear_bonus(5, 0.0) == config.WAVE_CLEAR_BONUS_BASE * 5
    assert state.wave_clear_bonus(3, -5.0) == config.WAVE_CLEAR_BONUS_BASE * 3


def test_phase_transition_table():
    P = state.GamePhase
    assert state.can_transition(P.TITLE, P.PLAYING)
    assert not state.can_transition(P.TITLE, P.PAUSED)
    assert not state.can_transition(P.TITLE, P.GAMEOVER)
    assert state.can_transition(P.PLAYING, P.PAUSED)
    assert state.can_transition(P.PLAYING, P.GAMEOVER)
    assert not state.can_transition(P.PLAYING, P.TITLE)
    assert state.can_transition(P.PAUSED, P.PLAYING)
    assert state.can_transition(P.PAUSED, P.TITLE)
    assert state.can_transition(P.GAMEOVER, P.PLAYING)
    assert state.can_transition(P.GAMEOVER, P.TITLE)


def test_transition_applies_legal_and_rejects_illegal():
    P = state.GamePhase
    assert state.transition(P.TITLE, P.PLAYING) == P.PLAYING
    assert state.transition(P.PLAYING, P.PAUSED) == P.PAUSED
    assert state.transition(P.TITLE, P.GAMEOVER) == P.TITLE  # illegal -> unchanged
    assert state.transition(P.PLAYING, P.TITLE) == P.PLAYING  # illegal -> unchanged


def test_run_stats_defaults():
    s = state.RunStats()
    assert s.score == 0
    assert s.combo == 1
    assert s.lives == config.LIVES
    assert s.wave == 1
