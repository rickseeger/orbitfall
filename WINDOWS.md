# ORBITFALL — Windows Install and Run Guide

Everything you need to install and play ORBITFALL on a Windows 10/11 machine,
from a clean start. These steps follow the same game as the Linux guide
(see [INSTALL.md](INSTALL.md)) but use Windows commands and paths.

ORBITFALL is a single-screen neon-vector score-attack arcade game. You pilot the
last drone of a solar-harvesting rig around a star collapsing into a gravity
well: collect energy cells, dodge asteroids, and fly through the jump gate
before the star's surface catches you. It is keyboard-only and opens a 960×540
window.

---

## 1. Prerequisites

- Windows 10 or 11.
- Python 3.10 or newer (we recommend 3.11 or later; verified against 3.14).
- Git, to fetch the code — or just download the repository as a ZIP from GitHub.

Nothing else. The single runtime dependency, `pygame-ce`, bundles SDL2 as a
prebuilt wheel, so it is `pip`-installable on Windows with no extra system
dependencies, no Visual Studio build tools, and no GPU. All graphics and audio
are procedural; there are no image or sound assets to download.

## 2. Install Python

1. Download the latest installer from <https://www.python.org/downloads/windows/>
   (choose the 64-bit installer, Python 3.11 or newer).
2. Run the installer.
3. On the first screen, tick **"Add python.exe to PATH"** (important — this
   makes `python` and `pip` available from any terminal).
4. Click **Install Now**, then let the installer finish.

Verify the install by opening a new PowerShell or Command Prompt window:

```powershell
python --version
```

You should see something like `Python 3.12.x`. If instead you get
"python is not recognized", see the Troubleshooting section below.

> If `python` is not recognized but the `py` launcher is installed, you can use
> `py` instead of `python` throughout this guide.

## 3. Get the code

With Git (in PowerShell):

```powershell
git clone https://github.com/rickseeger/orbitfall.git
cd orbitfall
```

Or, without Git: download the repository ZIP from GitHub
(Code → Download ZIP), extract it, and open a terminal in the extracted folder.

## 4. Set up a virtual environment and install

Recommended — this keeps the game and its dependency isolated from the rest of
your system:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install .
```

- `python -m venv .venv` creates an isolated environment in `.venv` (run once).
- `.venv\Scripts\activate` activates it (run once per terminal window).
- `pip install .` downloads `pygame-ce` and installs the `orbitfall` command
  into the environment (run once). This is the same single command as on
  Linux; `pygame-ce` installs cleanly from prebuilt wheels on Windows with no
  extra system dependencies.

To uninstall cleanly later, just delete the `orbitfall` folder and the `.venv`
folder inside it — nothing is installed system-wide.

### Alternative: just the dependency (run from source, no install)

If you only want to play from the repository without installing the package:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install pygame-ce
```

Then run from the repository root with `python -m game.main` (see below).

## 5. Run the game

With the virtual environment active, from the repository root, any of these
work:

```powershell
orbitfall
```

or

```powershell
python -m game.main
```

or (only if you used `pip install .`, so the `orbitfall` script is on PATH)

```powershell
.venv\Scripts\orbitfall.exe
```

The `orbitfall` command works from any directory; `python -m game.main` must be
run from the repository root.

### Controls

| Action              | Keys                                |
|---------------------|-------------------------------------|
| Rotate left         | Left arrow / A                      |
| Rotate right        | Right arrow / D                     |
| Thrust              | Up arrow / W / Space                |
| Impulse (dodge)     | Left/Right Shift or Left/Right Ctrl |
| Pause               | P / Esc                             |
| Confirm / restart   | Enter (Return or keypad Enter)      |

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
bonus for grazing close past an asteroid.

## 6. Where your high score is saved (Windows)

The game stores its data (high score and key bindings) in a per-user, platform
location — not in the game folder and not in a Linux-only path:

```
%LOCALAPPDATA%\orbitfall\highscore.json
%LOCALAPPDATA%\orbitfall\bindings.json
```

(If `LOCALAPPDATA` is unset, it falls back to `%APPDATA%`, then
`%USERPROFILE%\AppData\Local`.) You can see the exact folder by opening
PowerShell and typing `echo $env:LOCALAPPDATA\orbitfall`.

## 7. Verify it works

Headless smoke checks — no window needed; each runs the game for a fixed number
of frames and exits cleanly:

```powershell
python -m game.main --headless --frames 60            # title screen
python -m game.main --headless --start --frames 180   # playing state
```

Run the automated test suite (optional; needs pytest):

```powershell
pip install pytest pytest-cov
python -m pytest
```

## 8. Troubleshooting

- **`python` is not recognized** → Python was installed without "Add python.exe
  to PATH". Re-run the Python installer, choose **Modify**, and tick
  **"Add python.exe to PATH"**, or use the `py` launcher instead.
- **`orbitfall` is not recognized** → the virtual environment isn't active, or
  you skipped `pip install .`. Run `.venv\Scripts\activate` first, or use
  `python -m game.main` from the repository root instead.
- **`pip` is not recognized** → same cause as the `python` PATH issue; re-add
  Python to PATH. You can also run `python -m pip install ...` to use pip via
  Python.
- **Execution policy blocks `activate`** (PowerShell) → in PowerShell, the
  activation script may be blocked by the execution policy. Run
  `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`, or
  activate with the batch file in Command Prompt: `.venv\Scripts\activate.bat`.
- **A window opens but no sound** → run with the dummy audio driver to play
  silently: `SDL_AUDIODRIVER=dummy python -m game.main`. On a normal Windows
  desktop with working audio, sound works out of the box.

---

For the Linux install guide, see [INSTALL.md](INSTALL.md).
