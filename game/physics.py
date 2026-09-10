"""Pure-math simulation core: integrator, gravity, collision resolution.

Per DESIGN.md section 9 this module must stay pure and deterministic: no
pygame import, no wall-clock, no rendering — so it is fully unit-testable in
headless CI. Node 3 owns the implementation.

Intended public API (node 3):
    gravity_accel(radius, G) -> float
    step(body, dt) -> None        # symplectic (semi-implicit) Euler
    collide_circle(a, b) -> bool
"""

from __future__ import annotations

__all__: list[str] = []
