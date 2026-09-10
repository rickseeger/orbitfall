"""Entry point and loop wiring for ORBITFALL (DESIGN.md section 9).

Node 2 ships a runnable stub that opens a window, draws the neon background,
and exits cleanly when the window is closed (or ESC is pressed). Node 3
replaces this placeholder loop with the real fixed-timestep game loop.
"""

from __future__ import annotations

import argparse
import os
import sys

import pygame

from game import config

__all__ = ["main"]


def main(argv: list[str] | None = None) -> int:
    """Run ORBITFALL. Returns a process exit code."""
    args = _parse_args(argv)

    if args.headless:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

    pygame.init()
    try:
        screen = pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
        pygame.display.set_caption(config.TITLE)
        clock = pygame.time.Clock()

        # Placeholder loop (node 2): render the neon background and a small
        # ship marker, then run until the window closes or ESC is pressed.
        frames = 0
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False

            screen.fill(config.COLOR_BACKGROUND)
            pygame.draw.circle(
                screen,
                config.COLOR_SHIP,
                (config.WINDOW_WIDTH // 2, config.WINDOW_HEIGHT // 2),
                8,
            )
            pygame.display.flip()
            clock.tick(config.FPS)

            frames += 1
            if args.frames is not None and frames >= args.frames:
                running = False
    finally:
        pygame.quit()

    return 0


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="orbitfall", description=config.TITLE)
    parser.add_argument(
        "--frames",
        type=int,
        default=None,
        help="Exit after N frames (used by smoke checks and headless CI).",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Force SDL dummy video/audio drivers (no display required).",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    sys.exit(main())
