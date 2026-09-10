"""Unit tests for the logical-action -> key mapping (DESIGN.md section 11)."""

import pygame

from game import input as game_input


def test_default_bindings_resolve():
    im = game_input.InputMap()
    assert im.resolve("rotate_left", pygame.K_LEFT)
    assert im.resolve("rotate_left", pygame.K_a)
    assert im.resolve("rotate_right", pygame.K_RIGHT)
    assert im.resolve("rotate_right", pygame.K_d)
    assert im.resolve("thrust", pygame.K_UP)
    assert im.resolve("thrust", pygame.K_w)
    assert im.resolve("thrust", pygame.K_SPACE)
    assert im.resolve("impulse", pygame.K_LSHIFT)
    assert im.resolve("impulse", pygame.K_LCTRL)
    assert im.resolve("pause", pygame.K_p)
    assert im.resolve("pause", pygame.K_ESCAPE)
    assert im.resolve("confirm", pygame.K_RETURN)
    assert im.resolve("confirm", pygame.K_KP_ENTER)


def test_default_bindings_reject_unbound_keys():
    im = game_input.InputMap()
    assert not im.resolve("thrust", pygame.K_b)
    assert not im.resolve("rotate_left", pygame.K_x)


def test_rebind_changes_mapping():
    im = game_input.InputMap()
    im.rebind("thrust", ["k"])
    assert im.resolve("thrust", pygame.K_k)
    assert not im.resolve("thrust", pygame.K_SPACE)


def test_to_names_round_trips():
    im = game_input.InputMap()
    names = im.to_names()
    im2 = game_input.InputMap(names)
    assert im2.bindings == im.bindings


def test_save_and_load_bindings(tmp_path):
    im = game_input.InputMap()
    im.rebind("thrust", ["k"])
    game_input.save_bindings(im, path=tmp_path)
    loaded = game_input.load_bindings(path=tmp_path)
    assert loaded["thrust"] == ["k"]


def test_load_missing_returns_none(tmp_path):
    assert game_input.load_bindings(path=tmp_path) is None


def test_unknown_action_not_resolved():
    im = game_input.InputMap()
    assert not im.resolve("does_not_exist", pygame.K_LEFT)
