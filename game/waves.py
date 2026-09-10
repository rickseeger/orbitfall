"""Wave / difficulty generators (DESIGN.md sections 7 and 16).

Pure functions of wave number N and an RNG seed -> deterministic spawn data.
Difficulty parameters are centralized in game/config.py. No pygame import.

Public API:
    cells_count(n) -> int
    asteroids_count(n) -> int
    shell_radius(n) -> float
    time_limit(n) -> float
    star_kill_radius(n) -> float
    asteroid_orbit_speed(n, orbit_radius) -> float
    spawn_wave(n, seed, center) -> WaveSpawn
"""

from __future__ import annotations

import math
import random

from game import config
from game.entities import Asteroid, Cell, JumpGate, Star, Vec2, WaveSpawn

__all__ = [
    "cells_count",
    "asteroids_count",
    "shell_radius",
    "time_limit",
    "star_kill_radius",
    "asteroid_orbit_speed",
    "spawn_wave",
]


def cells_count(n: int) -> int:
    """Number of energy cells in wave n: 5 + 2n, capped at 25."""
    return min(config.CELLS_BASE + config.CELLS_PER_WAVE * n, config.CELLS_CAP)


def asteroids_count(n: int) -> int:
    """Number of asteroids in wave n: n, capped at 8."""
    return min(config.ASTEROIDS_PER_WAVE * n, config.ASTEROIDS_CAP)


def shell_radius(n: int) -> float:
    """Outer-shell radius for wave n, shrinking to a floor."""
    r = config.SHELL_RADIUS_INITIAL - config.SHELL_SHRINK_PER_WAVE * (n - 1)
    return max(r, config.SHELL_RADIUS_FLOOR)


def time_limit(n: int) -> float:
    """Seconds allowed to clear wave n, floored at 20."""
    t = config.WAVE_TIME_BASE - config.WAVE_TIME_STEP * (n - 1)
    return max(t, config.WAVE_TIME_FLOOR)


def star_kill_radius(n: int) -> float:
    """Star's lethal radius for wave n (grows, capped)."""
    r = config.STAR_KILL_RADIUS + config.STAR_RADIUS_PER_WAVE * (n - 1)
    return min(r, config.STAR_KILL_RADIUS_CAP)


def asteroid_orbit_speed(n: int, orbit_radius: float) -> float:
    """Base angular rate (rad/s) for an asteroid orbit in wave n.

    Scales a natural orbital rate by (1 + 0.05*n) per DESIGN.md section 7.
    """
    natural = math.sqrt(config.GRAVITY_G) / (orbit_radius ** 1.5)
    return config.ASTEROID_BASE_OMEGA * (1.0 + config.ASTEROID_SPEED_STEP * n)


def spawn_wave(n: int, seed: int, center: Vec2 | None = None) -> WaveSpawn:
    """Deterministically lay out one wave (cells, asteroids, gate).

    The gate is placed on the outer shell at a fixed angle (opposite the
    first cell) and activates only after all cells are collected.
    """
    center = center or Vec2(config.WINDOW_WIDTH / 2, config.WINDOW_HEIGHT / 2)
    rng = random.Random(seed)
    n = max(1, int(n))

    radius = shell_radius(n)
    limit = time_limit(n)
    kill_r = star_kill_radius(n)

    # ---- cells: static, on a band between the star and the shell ----------
    inner = max(config.CELL_MIN_ORBIT_RADIUS, kill_r + config.CELL_RADIUS + 24.0)
    outer = radius - config.CELL_RADIUS - 12.0
    if outer < inner + 24.0:
        outer = inner + 24.0

    cells: list[Cell] = []
    cell_angles = [2.0 * math.pi * i / cells_count(n) for i in range(cells_count(n))]
    for angle in cell_angles:
        # jitter the angle slightly and pick a random radius in the band
        a = angle + rng.uniform(-0.35, 0.35) * (2.0 * math.pi / cells_count(n))
        r = rng.uniform(inner, outer)
        pos = center + Vec2(math.cos(a) * r, math.sin(a) * r)
        cells.append(Cell(pos=pos, radius=config.CELL_RADIUS))

    # ---- asteroids: fixed circular orbits --------------------------------
    asteroids: list[Asteroid] = []
    for _ in range(asteroids_count(n)):
        a_r = rng.uniform(inner, outer)
        a_angle = rng.uniform(0.0, 2.0 * math.pi)
        omega = asteroid_orbit_speed(n, a_r) * rng.uniform(0.8, 1.2)
        if rng.random() < 0.5:
            omega = -omega
        a_radius = rng.uniform(config.ASTEROID_RADIUS_MIN, config.ASTEROID_RADIUS_MAX)
        asteroids.append(
            Asteroid(
                center=center,
                orbit_radius=a_r,
                angle=a_angle,
                angular_vel=omega,
                radius=a_radius,
                seed=rng.randrange(1 << 30),
            )
        )

    # ---- gate: outer shell, opposite the first cell ----------------------
    gate_angle = (cell_angles[0] + math.pi) % (2.0 * math.pi)
    gate_pos = center + Vec2(math.cos(gate_angle) * radius, math.sin(gate_angle) * radius)
    gate = JumpGate(pos=gate_pos, radius=config.GATE_RADIUS)

    return WaveSpawn(
        wave=n,
        shell_radius=radius,
        time_limit=limit,
        cells=cells,
        asteroids=asteroids,
        gate=gate,
        gravity_pulse=(n >= config.GRAVITY_PULSE_FROM_WAVE),
        nova=(n >= config.NOVA_FROM_WAVE),
    )


def make_star(n: int, center: Vec2 | None = None) -> Star:
    """Build a Star with the correct kill/surface radii for wave n."""
    center = center or Vec2(config.WINDOW_WIDTH / 2, config.WINDOW_HEIGHT / 2)
    kill = star_kill_radius(n)
    surface = min(config.STAR_SURFACE_RADIUS + config.STAR_SURFACE_PER_WAVE * (n - 1),
                  kill - 6.0)
    return Star(pos=center, kill_radius=kill, surface_radius=surface)
