"""Unit tests for high-score persistence (DESIGN.md section 11)."""

import json
import os
import sys
from pathlib import Path

from game import persistence


def test_round_trip(tmp_path):
    persistence.save_high_score(4321, path=tmp_path)
    assert persistence.load_high_score(path=tmp_path) == 4321


def test_load_missing_returns_zero(tmp_path):
    assert persistence.load_high_score(path=tmp_path) == 0


def test_load_corrupt_json_returns_zero(tmp_path):
    persistence.high_score_path(tmp_path).write_text("{ not json !!!", encoding="utf-8")
    assert persistence.load_high_score(path=tmp_path) == 0


def test_load_non_numeric_returns_zero(tmp_path):
    persistence.high_score_path(tmp_path).write_text(
        json.dumps({"high_score": "abc"}), encoding="utf-8"
    )
    assert persistence.load_high_score(path=tmp_path) == 0


def test_save_clamps_negative(tmp_path):
    persistence.save_high_score(-5, path=tmp_path)
    assert persistence.load_high_score(path=tmp_path) == 0


def test_save_creates_directory(tmp_path):
    nested = tmp_path / "a" / "b" / "c"
    persistence.save_high_score(77, path=nested)
    assert persistence.load_high_score(path=nested) == 77


def test_high_score_path_defaults_to_data_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    assert persistence.high_score_path() == persistence.data_dir() / "highscore.json"


# ---- cross-platform data-dir resolution -----------------------------------
# The resolver must pick the conventional per-user location on every platform,
# never a Linux-only path. These simulate each platform by patching sys.platform
# and the relevant environment variables.


def test_data_dir_windows_prefers_localappdata(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local"))
    monkeypatch.delenv("APPDATA", raising=False)
    assert persistence.data_dir() == Path(tmp_path) / "local" / "orbitfall"


def test_data_dir_windows_falls_back_to_appdata(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    monkeypatch.setenv("APPDATA", str(tmp_path / "roaming"))
    assert persistence.data_dir() == Path(tmp_path) / "roaming" / "orbitfall"


def test_data_dir_windows_defaults_under_profile(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    monkeypatch.delenv("APPDATA", raising=False)
    expected = Path(os.path.expanduser("~")) / "AppData" / "Local" / "orbitfall"
    assert persistence.data_dir() == expected


def test_data_dir_macos_application_support(monkeypatch):
    monkeypatch.setattr(sys, "platform", "darwin")
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    expected = (
        Path(os.path.expanduser("~")) / "Library" / "Application Support" / "orbitfall"
    )
    assert persistence.data_dir() == expected


def test_data_dir_linux_defaults_to_xdg(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    expected = Path(os.path.expanduser("~")) / ".local" / "share" / "orbitfall"
    assert persistence.data_dir() == expected
