"""Wave / difficulty generators (DESIGN.md sections 7 and 16).

Pure functions of wave number N and an RNG seed -> deterministic spawn data.
Difficulty parameters are centralized in game/config.py. Node 3 owns this.

Intended public API (node 3):
    spawn_wave(n, seed) -> WaveSpawn
"""

from __future__ import annotations

__all__: list[str] = []
