"""Real smoke tests: the ORBITFALL package imports and pygame boots headlessly."""

import importlib

import pygame

SKELETON_MODULES = [
    "game",
    "game.config",
    "game.entities",
    "game.physics",
    "game.waves",
    "game.state",
    "game.persistence",
    "game.input",
    "game.audio",
    "game.render",
    "game.main",
]


def test_skeleton_package_imports():
    """Every module in the declared package structure imports cleanly."""
    for name in SKELETON_MODULES:
        assert importlib.import_module(name) is not None


def test_version_and_config():
    import game
    from game import config

    assert isinstance(game.__version__, str) and game.__version__
    assert config.WINDOW_WIDTH == 960
    assert config.WINDOW_HEIGHT == 540


def test_pygame_initializes_headlessly():
    """pygame-ce boots on the dummy drivers and draws with additive blend."""
    pygame.init()
    try:
        # SDL must be on the dummy video driver in headless CI/local runs.
        assert pygame.display.get_driver() == "dummy"

        screen = pygame.display.set_mode((320, 240))
        assert screen.get_size() == (320, 240)

        # Mixer + font subsystems initialize with the dummy audio driver and
        # bundled dejavu fonts (see STACK_VERIFICATION.md).
        pygame.mixer.init()
        assert pygame.mixer.get_init() is not None
        pygame.font.init()
        assert pygame.font.get_fonts()  # bundled fonts present

        # Draw + additive blend smoke (the neon-glow foundation).
        surf = pygame.Surface((16, 16))
        surf.fill((0, 0, 0))
        glow = pygame.Surface((16, 16), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 255, 255, 128), (8, 8), 4)
        surf.blit(glow, (0, 0), special_flags=pygame.BLEND_ADD)
    finally:
        pygame.quit()


def test_main_runs_headlessly_and_exits(tmp_path, monkeypatch):
    """The real entry point runs a fixed number of frames headless and exits 0."""
    from game import main as mainmod

    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    rc = mainmod.main(["--headless", "--frames", "90", "--start", "--seed", "1"])
    assert rc == 0
