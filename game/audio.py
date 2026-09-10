"""Procedural SFX synthesis (DESIGN.md section 3).

Synthesizes raw PCM buffers with stdlib array/math (no numpy, no audio files)
and feeds them to pygame.mixer.Sound(buffer=...). Node 3 owns this.

Intended public API (node 3):
    blip(freq) -> Sound, thrust_rumble(...), impulse(), explosion(), ...
"""

from __future__ import annotations

__all__: list[str] = []
