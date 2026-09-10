"""Unit tests for high-score persistence (DESIGN.md section 11)."""

import json

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
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    assert persistence.high_score_path() == persistence.data_dir() / "highscore.json"
