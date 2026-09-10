"""Pytest configuration: force headless SDL so tests run anywhere (incl. CI)."""

import os

# Must be set before pygame is imported anywhere, so do it at collection time.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
