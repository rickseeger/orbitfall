# ORBITFALL

A single-screen neon-vector score-attack arcade game. You pilot the last drone
of a solar-harvesting rig around a star collapsing into a gravity well: collect
energy cells, dodge asteroids, and fly through the jump gate before the star's
surface catches you.

- Design & spec: [DESIGN.md](DESIGN.md)
- Stack verification: [STACK_VERIFICATION.md](STACK_VERIFICATION.md)

## Requirements

- Python 3.10 or newer (developed and verified on 3.14)
- `pygame-ce` — the single runtime dependency (bundles SDL2; no system
  packages or GPU required)

No other runtime dependencies. Audio is synthesized in pure Python (stdlib
`array`/`math`); all graphics are procedural — there are no image or audio
assets.

## Install

Create a virtual environment, then install the package:

```sh
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install .
```

This installs `pygame-ce` and the `orbitfall` console command.

Or with [uv](https://docs.astral.sh/uv/):

```sh
uv sync
```

## Play

```sh
orbitfall
```

Controls (see DESIGN.md section 6):

| Action          | Keys                          |
|-----------------|-------------------------------|
| Rotate left     | Left / A                      |
| Rotate right    | Right / D                     |
| Thrust          | Up / W / Space                |
| Impulse         | Shift / Ctrl                  |
| Pause           | P / Esc                       |
| Confirm/restart | Enter                         |

If you'd rather not install, run straight from the source tree (`pygame-ce`
must still be installed in the active environment):

```sh
./run.sh
```

## Develop / test

Install the dev tooling (adds pytest) and run the test suite:

```sh
uv sync --dev
uv run pytest
```

Or with pip:

```sh
pip install -e . pytest
python -m pytest
```

Tests run headless automatically — the test config forces SDL's dummy video and
audio drivers — so they work in CI and on servers without a display. To run
headless manually:

```sh
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy pytest
```

Coverage is enforced at >=90% line coverage on the pure-logic core
(`physics`, `waves`, `state`) in CI:

```sh
pytest --cov=game.physics --cov=game.waves --cov=game.state --cov-fail-under=90
```

CI runs the same suite on every push to `main`
([.github/workflows/ci.yml](.github/workflows/ci.yml)).

## Project layout

```
game/            the ORBITFALL package
  config.py      every tunable constant (single source of truth)
  entities.py    data classes (drone, cells, asteroids, gate, star)
  physics.py     pure-math integrator, gravity, collisions (no pygame)
  waves.py       deterministic wave/difficulty generators
  state.py       game state machine + score/combo/lives
  persistence.py high-score save/load (XDG data dir)
  input.py       logical-action -> key mapping
  audio.py       procedural SFX synthesis
  render.py      pygame drawing + additive glow
  main.py        loop wiring / entry point
tests/           pytest suite (headless)
```

> Status: complete and playable (G0 node 3). Full gameplay loop, visuals,
> audio, difficulty escalation, and an automated test suite are implemented.
> The launch command `orbitfall` (or `./run.sh`) opens the game directly.
