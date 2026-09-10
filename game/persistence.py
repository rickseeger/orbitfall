"""High-score save/load: JSON in a per-user, platform data directory.

Round-trip save/load plus corrupt-file handling are unit-tested. The data dir
is resolved per platform so the game runs the same way on Linux, macOS, and
Windows (no Linux-only assumptions):

- Linux/other POSIX: $XDG_DATA_HOME (default ~/.local/share)
- macOS: ~/Library/Application Support
- Windows: %LOCALAPPDATA% (fallback %APPDATA%, then ~\\AppData\\Local)

The resolver is stdlib-only (no platformdirs dependency); it keys off
sys.platform and reads the conventional per-user environment variables.

Public API:
    data_dir() -> Path
    high_score_path() -> Path
    load_high_score(path=None) -> int
    save_high_score(score, path=None) -> None
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

__all__ = ["data_dir", "high_score_path", "load_high_score", "save_high_score"]

_APP_DIR = "orbitfall"
_SCORE_FILE = "highscore.json"


def _data_home() -> str:
    """Resolve the per-user data home directory for the current platform."""
    if sys.platform == "win32":
        # Save data is machine-local rather than roamed: prefer LOCALAPPDATA,
        # then the roaming APPDATA, then the conventional default under the
        # user profile.
        return (
            os.environ.get("LOCALAPPDATA")
            or os.environ.get("APPDATA")
            or os.path.join(os.path.expanduser("~"), "AppData", "Local")
        )
    if sys.platform == "darwin":
        return os.path.join(
            os.path.expanduser("~"), "Library", "Application Support"
        )
    # Linux and other POSIX systems follow the XDG Base Directory spec.
    return os.environ.get("XDG_DATA_HOME") or os.path.join(
        os.path.expanduser("~"), ".local", "share"
    )


def data_dir() -> Path:
    """Per-user data directory for ORBITFALL (created on demand by writers)."""
    return Path(_data_home()) / _APP_DIR


def high_score_path(path: Path | None = None) -> Path:
    return (path or data_dir()) / _SCORE_FILE


def load_high_score(path: Path | None = None) -> int:
    """Read the persisted high score; 0 on missing/corrupt/invalid files."""
    target = high_score_path(path)
    try:
        raw = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return 0
    if isinstance(raw, dict):
        value = raw.get("high_score", 0)
    else:
        value = raw
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return 0
    return max(0, int(value))


def save_high_score(score: int, path: Path | None = None) -> None:
    """Persist a high score, creating the data directory as needed."""
    target = high_score_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {"high_score": max(0, int(score))}
    target.write_text(json.dumps(payload), encoding="utf-8")
