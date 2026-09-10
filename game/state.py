"""Game state machine and score/combo/lives logic (pure, DESIGN.md sec 9).

States: title / playing / paused / gameover. Score, combo and lives transitions
live here with no rendering or wall-clock dependency.

Public API:
    GamePhase (enum)
    PHASE_TRANSITIONS
    can_transition(from_phase, event) -> bool
    transition(phase, event) -> GamePhase
    RunStats (dataclass): score, combo, combo_timer, lives, wave
    collect_cell(stats, base_value) -> int
    tick_combo(stats, dt) -> None
    lose_life(stats) -> bool
    add_score(stats, points) -> None
    wave_clear_bonus(wave, time_remaining) -> int
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field

from game import config

__all__ = [
    "GamePhase",
    "PHASE_TRANSITIONS",
    "can_transition",
    "transition",
    "RunStats",
    "collect_cell",
    "tick_combo",
    "lose_life",
    "add_score",
    "wave_clear_bonus",
]


class GamePhase(enum.Enum):
    """Top-level game states."""

    TITLE = "title"
    PLAYING = "playing"
    PAUSED = "paused"
    GAMEOVER = "gameover"


# Events are also GamePhase values for simplicity: an event requests a target
# phase. `transition` validates the request against this table.
PHASE_TRANSITIONS: dict[GamePhase, set[GamePhase]] = {
    GamePhase.TITLE: {GamePhase.PLAYING},
    GamePhase.PLAYING: {GamePhase.PAUSED, GamePhase.GAMEOVER},
    GamePhase.PAUSED: {GamePhase.PLAYING, GamePhase.TITLE},
    GamePhase.GAMEOVER: {GamePhase.TITLE, GamePhase.PLAYING},
}


def can_transition(from_phase: GamePhase, event: GamePhase) -> bool:
    """Whether `event` (a requested target phase) is legal from `from_phase`."""
    return event in PHASE_TRANSITIONS.get(from_phase, set())


def transition(phase: GamePhase, event: GamePhase) -> GamePhase:
    """Move to `event` if legal, otherwise stay put."""
    if can_transition(phase, event):
        return event
    return phase


@dataclass
class RunStats:
    """Per-run score/combo/lives bookkeeping (pure)."""

    score: int = 0
    combo: int = 1
    combo_timer: float = 0.0
    lives: int = field(default_factory=lambda: config.LIVES)
    wave: int = 1


def add_score(stats: RunStats, points: int) -> None:
    """Add raw points to the score (no combo math)."""
    stats.score += max(0, int(points))


def collect_cell(stats: RunStats, base_value: int = config.CELL_VALUE) -> int:
    """Register a cell collection. Returns points gained (base x current combo)."""
    gained = base_value * stats.combo
    stats.score += gained
    stats.combo = min(stats.combo + 1, config.COMBO_CAP)
    stats.combo_timer = config.COMBO_WINDOW
    return gained


def tick_combo(stats: RunStats, dt: float) -> None:
    """Advance the combo window; reset the multiplier when it lapses."""
    if stats.combo_timer <= 0.0:
        return
    stats.combo_timer -= dt
    if stats.combo_timer <= 0.0:
        stats.combo = 1


def lose_life(stats: RunStats) -> bool:
    """Register a death. Returns True when the run is over (0 lives left)."""
    stats.lives = max(0, stats.lives - 1)
    stats.combo = 1
    stats.combo_timer = 0.0
    return stats.lives <= 0


def wave_clear_bonus(wave: int, time_remaining: float) -> int:
    """Score bonus for clearing a wave, scaling with wave and remaining time."""
    return (
        config.WAVE_CLEAR_BONUS_BASE * wave
        + int(max(0.0, time_remaining)) * config.TIME_BONUS_PER_SECOND
    )
