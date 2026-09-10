# ORBITFALL — Installation and Playing Guide

Everything you need to install and play ORBITFALL on an ordinary Linux laptop,
from a clean start. On Windows, see [WINDOWS.md](WINDOWS.md) instead. These steps were run and verified against this repository on
2026-09-10 (Ubuntu 26.04, Python 3.14.4).

ORBITFALL is a single-screen neon-vector score-attack arcade game. You pilot the
last drone of a solar-harvesting rig around a star collapsing into a gravity
well: collect energy cells, dodge asteroids, and fly through the jump gate
before the star's surface catches you.

---

## 1. Prerequisites

- A Linux desktop with a graphical session (X11 or Wayland). The game opens a
  960×540 window and is keyboard-only.
- Python 3.10 or newer (developed and tested on 3.14).
- `pip` and `venv` for Python. On Debian/Ubuntu these need the `python3-venv`
  package (it provides the `ensurepip` module that `python3 -m venv` uses):

  ```sh
  sudo apt update
  sudo apt install python3 python3-venv
  ```

  `sudo apt install` prompts **Y/n** for confirmation before it installs.
  For an unattended or scripted setup, add `-y`:
  `sudo apt install -y python3 python3-venv`.

  Without `python3-venv`, creating a virtual environment fails with
  "ensurepip is not available".
- Git to fetch the code (or download the repository ZIP from GitHub).

Nothing else. `pygame-ce` — the single runtime dependency — bundles SDL2 as a
wheel, so there are no system SDL libraries, no GPU, and no other packages to
install. All graphics and audio are procedural; there are no image or sound
assets.

## 2. Get the code

```sh
git clone https://github.com/rickseeger/orbitfall.git
cd orbitfall
```

(SSH alternative: `git clone git@github.com:rickseeger/orbitfall.git`)

## 3. Set up a virtual environment and install (recommended)

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install .
```

- `python3 -m venv .venv` creates an isolated environment in `.venv` (run once).
- `source .venv/bin/activate` activates it (run once per terminal session).
- `pip install .` downloads `pygame-ce` and installs the `orbitfall` command
  into the environment (run once).

Verified clean install: `pip install .` resolves the project's `pygame-ce>=2.5.8`
dependency and installs `orbitfall 0.1.0` and `pygame-ce 2.5.8` (SDL 2.32.10).

## 4. Play

With the environment active:

```sh
orbitfall
```

Or, from the repository root, without activating:

```sh
.venv/bin/orbitfall
```

No-install alternative (still requires `pygame-ce` to be importable in the
active interpreter — e.g. after `pip install pygame-ce`, or with the `.venv`
above, which `run.sh` detects automatically):

```sh
./run.sh
```

The `orbitfall` command works from any directory; `./run.sh` must be run from
the repository.

### Controls

| Action              | Keys                                    |
|---------------------|-----------------------------------------|
| Rotate left         | Left arrow / A                          |
| Rotate right        | Right arrow / D                         |
| Thrust              | Up arrow / W / Space                    |
| Impulse (dodge)     | Left/Right Shift or Left/Right Ctrl     |
| Pause               | P / Esc                                 |
| Confirm / restart   | Enter (Return or keypad Enter)          |

### How to play

You fly the last drone of a solar-harvesting rig around a star collapsing into
a gravity well. The star's gravity constantly accelerates you inward, so you
hold an orbit by balancing thrust, rotation, and the impulse dodge against the
pull.

Each wave:

1. Collect every energy cell scattered around the star. Collecting a cell
   raises your combo (collect quickly to keep the multiplier alive) and refills
   part of your impulse meter.
2. Once the last cell is collected, the jump gate opens at the outer edge of the
   arena. Fly through it before the wave timer runs out to clear the wave.
3. The next wave is harder: more cells, more and faster asteroids, a smaller
   arena, and (from wave 4) gravity pulses and (from wave 6) nova surges.

Hitting the star or an asteroid costs a life; you start with three. After a hit
you are briefly invulnerable and respawn on a safe tangent orbit. Lose all three
lives and the run is over — your score and high score are shown, and Enter
starts another run.

Scoring: 100 points per cell × your current combo (combo caps at ×8), plus a
wave-clear bonus that scales with wave number and time remaining, and a small
bonus for grazing close past an asteroid. The high score is saved to a
per-user, platform data directory — `~/.local/share/orbitfall/highscore.json`
on Linux (honouring `$XDG_DATA_HOME`), `~/Library/Application Support/orbitfall/`
on macOS, and `%LOCALAPPDATA%\orbitfall\` on Windows.

## 5. Verify it works

Headless smoke checks — no display required; each runs the game for a fixed
number of frames and exits cleanly:

```sh
orbitfall --headless --frames 60          # title screen
orbitfall --headless --start --frames 180 # playing state
```

Run the automated test suite (77 tests, 100% line coverage on the pure-logic
core):

```sh
pip install pytest pytest-cov
python -m pytest
```

## 6. Alternative: uv

If you use [uv](https://docs.astral.sh/uv/):

```sh
uv sync
uv run orbitfall
```

Or create a pip-seeded environment with uv, then install with pip:

```sh
uv venv .venv --seed
source .venv/bin/activate
pip install .
```

## 7. Troubleshooting

- `python3 -m venv .venv` fails with "ensurepip is not available" → install the
  venv support package: `sudo apt install python3-venv`, then recreate the
  environment.
- `orbitfall: command not found` → the virtual environment isn't active, or
  `pip install .` hasn't been run in it. Either `source .venv/bin/activate`
  first, or run `.venv/bin/orbitfall` directly.
- "No available video device" / no window opens → you are on a machine without
  a display (for example over SSH). Run the game on a local desktop session.
  `--headless` is only for smoke checks, not for actual play.
- No sound (or audio init fails on a machine with no sound card) → run with the
  dummy audio driver to play silently: `SDL_AUDIODRIVER=dummy orbitfall`. On a
  normal laptop with PulseAudio or PipeWire running, audio works out of the box.
- The line `pygame-ce 2.5.8 (SDL 2.32.10, Python 3.14.4)` printed at startup is
  just pygame's banner, not an error.
