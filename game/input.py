"""Logical-action -> key mapping, with optional rebinding (DESIGN.md sec 6).

The input layer maps logical actions (rotate_left, thrust, impulse, ...) to
keys so remapping is data-only. Node 3 owns this.

Intended public API (node 3):
    InputMap, default_bindings(), resolve(action, key) -> bool
"""

from __future__ import annotations

__all__: list[str] = []
