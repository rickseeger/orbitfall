"""Central tunables for ORBITFALL.

This module is the single source of truth for every game-feel and difficulty
constant (DESIGN.md sections 7 and 16). Playtest tuning edits happen here and
nowhere else. Values are expected to shift during playtest tuning.
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
COLOR_STAR_EDGE = (200, 30, 30)      # outer edge of the star's radial gradient
COLOR_SHIP = (60, 220, 255)          # cyan dart / triangle
COLOR_SHIP_GLOW = (40, 160, 220)     # engine / halo glow
COLOR_CELL = (255, 200, 80)          # warm amber/gold orbs
COLOR_ASTEROID = (150, 160, 180)     # cool gray polygons
COLOR_GATE = (255, 60, 200)          # magenta ring
COLOR_TRAIL = (50, 150, 200)         # motion-trail cyan
COLOR_HUD = (210, 225, 255)          # HUD text / accents
COLOR_WARN = (255, 90, 90)           # warnings (timer low, pulse telegraph)
COLOR_STARFIELD = (140, 150, 200)    # dim starfield points

# ---- Physics (DESIGN.md section 5.1) -------------------------------------
# Gravity is inverse-square: a = G / r^2 (softened below SOFTENING_RADIUS).
# Tuned so the pull at the outer shell (~300 px) is mild (~33 px/s^2) but
# grows steeply toward the star; near the kill radius it exceeds thrust and
# becomes lethal. (G = 3.0e6 -> 33 px/s^2 at 300 px, 833 px/s^2 at 60 px.)
GRAVITY_G = 3_000_000.0
THRUST_ACCEL = 600.0         # px/s^2 along heading
ROTATION_RATE = 240.0        # deg/s
SOFTENING_RADIUS = 20.0      # px; gravity linearized below this (no singularity)

# ---- Impulse (the snappy dodge tool) -------------------------------------
IMPULSE_DELTA_V = 180.0      # px/s instant velocity delta
IMPULSE_CHARGES = 3
IMPULSE_RECHARGE = 2.0       # s per charge
IMPULSE_REFILL_ON_COLLECT = 0.5  # fraction of a charge refilled per cell

# ---- Combo / score --------------------------------------------------------
COMBO_WINDOW = 2.0           # s to keep the multiplier alive
COMBO_CAP = 8
CELL_VALUE = 100             # base score per energy cell
GRAZE_BONUS = 25             # SHOULD: near-miss asteroid bonus
GRAZE_MARGIN = 14.0          # px beyond collision radius that still counts
WAVE_CLEAR_BONUS_BASE = 100  # bonus scales with wave number
TIME_BONUS_PER_SECOND = 10   # per remaining second at wave clear

# ---- Lives / respawn ------------------------------------------------------
LIVES = 3
STAR_KILL_RADIUS = 40.0      # px; grows per wave
STAR_RADIUS_PER_WAVE = 2.0   # kill-radius growth per wave
STAR_KILL_RADIUS_CAP = 64.0
INVULN_TIME = 2.0            # s of post-death invulnerability
RESPAWN_RADIUS_FRACTION = 0.9  # respawn at this fraction of the shell radius

# ---- Arena ----------------------------------------------------------------
SHELL_RADIUS_INITIAL = 300.0  # px, outer shell
SHELL_RADIUS_FLOOR = 180.0    # px, tightest arena
SHELL_SHRINK_PER_WAVE = 20.0  # px smaller each wave
CELL_RADIUS = 6.0
CELL_MIN_ORBIT_RADIUS = 80.0  # cells never spawn closer to the star than this
ASTEROID_RADIUS_MIN = 10.0
ASTEROID_RADIUS_MAX = 18.0
DRONE_RADIUS = 8.0
GATE_RADIUS = 20.0

# ---- Waves / difficulty (DESIGN.md section 7) -----------------------------
WAVE_TIME_BASE = 45.0
WAVE_TIME_STEP = 1.5         # seconds subtracted per wave
WAVE_TIME_FLOOR = 20.0
CELLS_BASE = 5
CELLS_PER_WAVE = 2           # cells = 5 + 2N
CELLS_CAP = 25
ASTEROIDS_PER_WAVE = 1       # asteroids = N
ASTEROIDS_CAP = 8
ASTEROID_BASE_OMEGA = 0.7    # rad/s base orbit rate (outer shell)
ASTEROID_SPEED_STEP = 0.05   # orbit speed scales by (1 + step*N)
GRAVITY_PULSE_MULT = 1.4
GRAVITY_PULSE_DURATION = 1.5   # s
GRAVITY_PULSE_TELEGRAPH = 0.8  # s warning before the pulse hits
GRAVITY_PULSE_FROM_WAVE = 4
GRAVITY_PULSE_INTERVAL_BASE = 9.0   # s between pulses (scales down per wave)
NOVA_MULT = 1.8
NOVA_DURATION = 2.0           # s
NOVA_TELEGRAPH = 1.0          # s warning before the nova surge
NOVA_FROM_WAVE = 6            # SHOULD (stretch)
NOVA_INTERVAL_BASE = 14.0     # s between nova surges

# ---- Visual / audio -------------------------------------------------------
TRAIL_LENGTH = 24            # recent positions drawn as a fading line
STAR_SURFACE_RADIUS = 26.0   # visual core radius (smaller than kill radius)
STAR_SURFACE_PER_WAVE = 1.5  # visual growth per wave
STARFIELD_COUNT = 150        # static background points
STARFIELD_SEED = 20260908    # deterministic starfield layout
PARTICLE_COLLECT_COUNT = 12
PARTICLE_DEATH_COUNT = 48
PARTICLE_IMPULSE_COUNT = 10
PARTICLE_GATE_COUNT = 40
SHAKE_DECAY = 0.88           # multiplicative per-frame shake falloff
