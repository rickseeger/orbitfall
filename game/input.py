"""Logical-action -> key mapping, with optional rebinding (DESIGN.md sec 6).

The input layer maps logical actions (rotate_left, thrust, impulse, ...) to
keys so remapping is data-only. Bindings are persisted to the XDG data dir as
JSON (canonical key names) and can be overridden without touching game code.

Key names are canonical lower-case pygame constants: 'left', 'a', 'space',
'lshift', 'rctrl', 'kp_enter', ... (K_LEFT -> 'left', K_a -> 'a').

Public API:
    ACTIONS
    default_bindings() -> dict[str, list[str]]
    InputMap, save_bindings(), load_bindings()
"""

from __future__ import annotations

import json
from pathlib import Path

import pygame

from game.persistence import data_dir

__all__ = [
    "ACTIONS",
    "default_bindings",
    "InputMap",
    "save_bindings",
    "load_bindings",
]

# Logical actions the game understands.
ACTIONS = (
    "rotate_left",
    "rotate_right",
    "thrust",
    "impulse",
    "pause",
    "confirm",
)

_BINDINGS_FILE = "bindings.json"


def _build_key_maps() -> tuple[dict[str, int], dict[int, str]]:
    """Map canonical names <-> pygame keycodes from the K_* constants."""
    name_to_code: dict[str, int] = {}
    for attr, value in pygame.__dict__.items():
        if attr.startswith("K_") and isinstance(value, int):
            name_to_code.setdefault(attr[2:].lower(), value)
    code_to_name = {v: k for k, v in name_to_code.items()}
    return name_to_code, code_to_name


_NAME_TO_CODE, _CODE_TO_NAME = _build_key_maps()


def default_bindings() -> dict[str, list[str]]:
    """Default logical-action -> key-name mappings (DESIGN.md section 6)."""
    return {
        "rotate_left": ["left", "a"],
        "rotate_right": ["right", "d"],
        "thrust": ["up", "w", "space"],
        "impulse": ["lshift", "rshift", "lctrl", "rctrl"],
        "pause": ["p", "escape"],
        "confirm": ["return", "kp_enter"],
    }


def key_code(name: str) -> int:
    """Convert a canonical key name to a keycode (unknown -> -1)."""
    return _NAME_TO_CODE.get(name.lower(), -1)


class InputMap:
    """Resolves held/edge key presses to logical actions."""

    def __init__(self, bindings: dict[str, list[str]] | None = None) -> None:
        self.bindings: dict[str, set[int]] = {}
        self.set_bindings(bindings or default_bindings())

    def set_bindings(self, bindings: dict[str, list[str]]) -> None:
        """Replace the whole mapping from canonical key names."""
        self.bindings = {
            action: {key_code(name) for name in names if key_code(name) >= 0}
            for action, names in bindings.items()
            if action in ACTIONS
        }

    def resolve(self, action: str, keycode: int) -> bool:
        """Whether `keycode` is bound to `action`."""
        codes = self.bindings.get(action)
        return codes is not None and keycode in codes

    def rebind(self, action: str, key_names: list[str]) -> None:
        if action in ACTIONS:
            self.bindings[action] = {
                key_code(n) for n in key_names if key_code(n) >= 0
            }

    def to_names(self) -> dict[str, list[str]]:
        """Serialize current bindings back to canonical names (for persistence)."""
        out: dict[str, list[str]] = {}
        for action in ACTIONS:
            codes = self.bindings.get(action, set())
            out[action] = [
                _CODE_TO_NAME[code]
                for code in sorted(codes)
                if code in _CODE_TO_NAME
            ]
        return out


def bindings_path(path: Path | None = None) -> Path:
    """Path to the bindings file (inside a data directory)."""
    return (path or data_dir()) / _BINDINGS_FILE


def save_bindings(imap: InputMap, path: Path | None = None) -> None:
    """Persist bindings; `path` is a directory (created on demand)."""
    target = bindings_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(imap.to_names()), encoding="utf-8")


def load_bindings(path: Path | None = None) -> dict[str, list[str]] | None:
    """Load bindings; None when absent/corrupt (caller falls back to defaults)."""
    target = bindings_path(path)
    try:
        raw = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(raw, dict):
        return None
    out: dict[str, list[str]] = {}
    for action in ACTIONS:
        names = raw.get(action)
        if isinstance(names, list) and all(isinstance(n, str) for n in names):
            out[action] = names
    return out if out else None
