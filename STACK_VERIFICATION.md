# ORBITFALL — Technology Stack Verification

Evidence that the chosen stack (Python 3.14 + pygame-ce + pytest) actually
builds and runs on the target platform, so that nodes 2 and 3 do not inherit an
unbuildable foundation.

Date: 2026-09-08
Host: this server (Linux 7.0.0-31-generic, x86_64)

## What was tested

A clean virtualenv was created with uv and Python 3.14.4, then pygame-ce was
installed from PyPI. The following were exercised headlessly
(SDL_VIDEODRIVER=dummy, SDL_AUDIODRIVER=dummy):

1. pygame import + version + SDL version.
2. display, mixer, and font subsystem initialization.
3. Core 2D drawing primitives (circle, polygon, line) on a Surface.
4. Additive blending (BLEND_ADD) for the neon-glow visual style.
5. Procedural SFX synthesis: a 440 Hz sine wave was generated with stdlib
   array/math and turned into a pygame.mixer.Sound via buffer= (no numpy, no
   audio files).
6. pytest availability.

## Results

- pygame-ce 2.5.8 (SDL 2.32.10, Python 3.14.4) installed with a single
  `uv pip install pygame-ce` (no build step, no system packages required).
- display init ok: True
- mixer init ok: True
- font init ok: True
- System fonts detected (bundled with the SDL_ttf / pygame-ce wheel), e.g.
  dejavusansmono, freesans, dejavusans — sufficient for the UI.
- draw/blend ok (primitives + BLEND_ADD glow confirmed).
- Sound built from raw bytes: ok (stdlib-synthesized PCM accepted by mixer).
- pytest 9.1.1 installed and importable.

## Conclusion

The full visual + audio + test pipeline claimed in DESIGN.md (Section 8) is
achievable on an ordinary Linux host with no GPU beyond basics, no proprietary
SDK, and a single pip dependency (pygame-ce) plus stdlib-only SFX synthesis.

Notes for node 2/3:
- Pin `pygame-ce>=2.5.8` in pyproject.toml.
- The dummy audio driver reports a nominal mixer format; fine-tuning the exact
  mixer sample format for synthesized SFX is an implementation detail in
  game/audio.py, not a design risk.
