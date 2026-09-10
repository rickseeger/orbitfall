"""Pygame drawing: star, drone, cells, asteroids, gate, trails, particles.

Rendering consumes game state and never mutates it (DESIGN.md section 9).
Neon glow uses additive blending (pygame.BLEND_ADD). Node 3 owns this.

Intended public API (node 3):
    draw_scene(surface, state) -> None
"""

from __future__ import annotations

__all__: list[str] = []
