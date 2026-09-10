"""Game state machine and score/combo/lives logic (pure, DESIGN.md sec 9).

States: title / playing / paused / gameover. Score, combo and lives transitions
live here with no rendering or wall-clock dependency. Node 3 owns this.

Intended public API (node 3):
    GameState, transition(state, event), apply_score(...)
"""

from __future__ import annotations

__all__: list[str] = []
