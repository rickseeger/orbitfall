"""Entity data classes: drone, cells, asteroids, gate, star (DESIGN.md sec 9).

Pure data shapes (dataclasses) — no behavior. Node 3 defines the fields and
any per-entity helpers. Import-safe today so the package structure is proven.
"""

from __future__ import annotations

# TODO(node 3): define dataclasses for Drone, Cell, Asteroid, JumpGate, Star,
# and Particle. Intended public names:
#   Drone, Cell, Asteroid, JumpGate, Star, Particle

__all__: list[str] = []
