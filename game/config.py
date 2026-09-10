"""Central tunables for ORBITFALL.

This module is the single source of truth for every game-feel and difficulty
constant (DESIGN.md sections 7 and 16). Node 3 wires gameplay around these;
playtest tuning edits happen here and nowhere else.
"""

from __future__ import annotations

# ---- Window & timing -----------------------------------------------------
WINDOW_WIDTH = 960
WINDOW_HEIGHT = 540
FPS = 60                     # render frame rate
FIXED_DT = 1.0 / 120.0       # physics timestep (s); symplectic Euler

# ---- Title ----------------------------------------------------------------
TITLE = "ORBITFALL"

# ---- Neon-on-dark palette (DESIGN.md section 3) --------------------------
COLOR_BACKGROUND = (10, 10, 24)      # near-black deep indigo #0a0a18
COLOR_STAR_CORE = (255, 140, 40)     # amber -> red core (tuned in render.py)
COLOR_SHIP = (60, 220, 255)          # cyan dart / triangle
COLOR_CELL = (255, 200, 80)          # warm amber/gold orbs
COLOR_ASTEROID = (150, 160, 180)     # cool gray polygons
COLOR_GATE = (255, 60, 200)          # magenta ring

# ---- Physics (DESIGN.md section 5.1) -------------------------------------
GRAVITY_G = 900.0            # TODO(node 3): tune inverse-square strength
THRUST_ACCEL = 600.0         # px/s^2 along heading
ROTATION_RATE = 240.0        # deg/s

# ---- Impulse (the snappy dodge tool) -------------------------------------
IMPULSE_DELTA_V = 180.0      # px/s instant velocity delta
IMPULSE_CHARGES = 3
IMPULSE_RECHARGE = 2.0       # s per charge

# ---- Combo / score --------------------------------------------------------
COMBO_WINDOW = 2.0           # s to keep the multiplier alive
COMBO_CAP = 8

# ---- Lives / respawn ------------------------------------------------------
LIVES = 3
STAR_KILL_RADIUS = 40.0      # px; grows per wave

# ---- Arena ----------------------------------------------------------------
SHELL_RADIUS_INITIAL = 300.0  # px, outer shell
SHELL_RADIUS_FLOOR = 180.0    # px, tightest arena
CELL_RADIUS = 6.0
ASTEROID_RADIUS_MIN = 10.0
ASTEROID_RADIUS_MAX = 18.0

# ---- Waves / difficulty (DESIGN.md section 7) -----------------------------
WAVE_TIME_BASE = 45.0
WAVE_TIME_STEP = 1.5         # seconds subtracted per wave
WAVE_TIME_FLOOR = 20.0
CELLS_BASE = 5
CELLS_PER_WAVE = 2           # cells = 5 + 2N
CELLS_CAP = 25
ASTEROIDS_PER_WAVE = 1       # asteroids = N
ASTEROIDS_CAP = 8
GRAVITY_PULSE_MULT = 1.4
GRAVITY_PULSE_DURATION = 1.5   # s
GRAVITY_PULSE_FROM_WAVE = 4
NOVA_MULT = 1.8
NOVA_DURATION = 2.0           # s
NOVA_FROM_WAVE = 6            # SHOULD (stretch)
