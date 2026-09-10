# ORBITFALL — Game Design Document

| Field        | Value                                              |
|--------------|----------------------------------------------------|
| Project      | ORBITFALL                                          |
| Tree / Node  | G0 / node 1 (Design)                               |
| Status       | Draft for review — source of truth for nodes 2–4   |
| Version      | 1.0                                                |
| Date         | 2026-09-08                                         |
| Author       | G (Hermes worker session)                          |

## 1. Executive Summary

ORBITFALL is a small, polished, single-screen 2D physics arcade game for Linux.
You pilot the last drone of a solar-harvesting rig around a star that is
collapsing into a gravity well. The star constantly pulls you inward. You must
collect energy cells scattered in orbit — each one staves off the nova and
refills your escape drive — and then fly out through a jump gate to the next,
harder orbital shell before the star's surface catches you.

The design favors depth, responsiveness, and interesting gameplay over content
volume: a single elegant mechanic — orbital motion under gravity plus a snappy
"impulse" dodge — produces a high skill ceiling and emergent play from a small,
deterministic, fully testable rule set.

## 2. Genre & Positioning

- Genre: 2D physics arcade / score-attack (single-screen, endless wave survival).
- Player count: 1.
- Session length: 3–15 minutes per run (short "one more try" loops).
- Touchstones: Super Hexagon (one mechanic, extreme polish, escalating
  intensity), VVVVVV (gravity as core movement), twin-stick arcade feel distilled
  to a single pilot.

Why this genre fits the mission: score-attack arcade games are the smallest
genre that can still be "complete and polished" rather than a programming demo.
They require a tight core loop, excellent game feel, and a difficulty curve, but
no large content pipeline (levels, narrative, art assets).

## 3. Aesthetic: Visual Style & Audio

Visual style: minimalist neon-on-dark, geometric vector art, high contrast, with
additive glow and motion trails. All graphics are procedural (drawn from
primitives); there are no external image assets, which guarantees palette
consistency and removes an asset pipeline.

- Background: near-black deep indigo (#0a0a18) with a procedurally generated
  static starfield (dim points; subtle parallax in a later pass).
- Star: radial gradient amber→red core (pre-rendered radial surface) with
  animated surface flicker and a soft additive glow halo.
- Ship: small cyan dart/triangle with a heading indicator and engine glow.
- Cells: warm amber/gold glowing orbs (additive core + halo).
- Asteroids: cool gray geometric polygons with slow rotation.
- Jump gate: magenta ring with dashed rotating segments; pulses when active.
- Juice (game feel, all achievable with pygame): motion trail (recent positions
  drawn as a fading line), screen shake (impact/near-miss/death), particle
  bursts (cell collect, explosion), flash + trail on impulse, UI easing.
  Optional subtle chromatic-offset glow (draw sprite 2–3× with small offsets +
  additive blend).

Audio: fully procedural, no audio assets.
- SFX (MUST): cell collect (rising blip, pitch tracks combo), thrust (low rumble,
  volume tracks input), impulse (whoosh), explosion/death (noise burst +
  descending tone), gate open (two-tone chime), wave clear (ascending arpeggio).
  Synthesized in pure Python (stdlib array/math) into raw PCM buffers fed to
  pygame.mixer.Sound(buffer=...) — no numpy, no sample files.
- Music (SHOULD): optional short looping ambient pad, generated offline and
  bundled; omitted for scope if time is short.

## 4. Core Gameplay Loop

Per wave:

1. Spawn — wave N places a constellation of energy cells along orbital shells,
   plus a set of asteroids moving on their own circular orbits (and, from later
   waves, gravity pulses and nova surges).
2. Orbit & collect — the star's gravity continuously accelerates the drone
   toward the star; the player counters with thrust and corrective impulses to
   hold an orbit and gather every cell.
3. Escape — once all cells are collected, a jump gate appears at the outer edge
   of the shell. Fly through it within the wave's time limit to clear the wave.
4. Escalate — the next wave is strictly harder (more cells, faster/more
   asteroids, tighter shells, gravity pulses, nova surges, larger star radius).

Death & retry: hitting the star or an asteroid costs a life and briefly makes the
drone invulnerable, respawning it on a safe tangent orbit. Three lives lost →
game over → high-score entry → restart. Score accumulates across the run; the
high score persists to disk.

## 5. Mechanics (Detailed)

### 5.1 Movement & physics
- Gravity: inverse-square inward acceleration a = G / r^2 toward the star center,
  softened only below a small radius; the star's kill radius is larger than the
  softening radius, so the integrator never approaches the singularity in
  practice.
- Thrust: constant acceleration along the drone's heading while thrust is held.
- Rotation: heading turns at a fixed angular rate (left/right).
- Impulse (the responsive, high-skill tool): an instant velocity delta along the
  current heading, drawn from a small rechargeable meter. Impulses make the game
  feel snappy rather than floaty, and chaining them is the core of advanced play
  (slingshots, quick orbit corrections, gate dives).
- Integrator: symplectic (semi-implicit) Euler at a fixed 1/120 s timestep with a
  render accumulator. The simulation is deterministic given a fixed RNG seed and
  input, which makes it testable and replayable.
- Containment: the drone is clamped to the playfield at a fixed inset
  (`BOUNDARY_MARGIN`) from each window edge, with any outward velocity zeroed,
  so neither gravity, thrust, nor impulse can strand the ship off-screen.

### 5.2 Energy cells
- Static collectibles; circle collision with the drone.
- On collect: score (base × current combo), small impulse-meter refill, a
  particle burst, and a pitch-rising blip.
- Combo: collecting cells within a combo window (≈2.0 s) increments the
  multiplier (cap ×8); missing the window resets it.

### 5.3 Asteroids
- Move on fixed circular orbits at per-wave radii and speeds (deterministic from
  the wave seed).
- Circle collision with the drone costs a life. Passing close to an asteroid
  (within a small margin) awards a "graze" bonus (SHOULD) to reward risk.

### 5.4 Jump gate
- Appears only after all cells in the wave are collected, on the outer shell.
- Crossing it clears the wave (score bonus scales with wave and time remaining),
  plays the wave-clear arpeggio, and starts the next wave after a short beat.

### 5.5 Gravity pulses (introduced wave 4)
- Telegraphed (≈0.8 s warning), then the gravity multiplier ramps to ≈×1.4 for
  ≈1.5 s. The telegraph keeps it fair; skilled players pre-correct their orbit.

### 5.6 Nova surge (introduced wave 6, SHOULD)
- Telegraphed (≈1.0 s), then the star's kill radius briefly expands to ≈1.8× for
  ≈2.0 s, forcing the player toward the outer shell.

### 5.7 Lives, respawn, score
- 3 lives. On death: screen shake, particle explosion, brief invulnerability,
  respawn on a safe tangent with velocity matched to a local circular orbit.
- Score = cell value × combo + wave-clear bonus + graze bonuses. High score
  persisted to disk (XDG data dir), shown on title and game-over screens.

## 6. Controls

- Rotate left / right: Left/Right arrows (also A/D).
- Thrust: Up arrow / W / Space.
- Impulse: Shift / Ctrl.
- Pause: P / Esc. Confirm / restart: Enter.

Keys are rebindable (SHOULD) via a config file; the input layer maps logical
actions to keys so remapping is data-only.

## 7. Difficulty & Escalation

All difficulty parameters are pure functions of wave number N (deterministic),
centralized in config.py:

- Cells: 5 + 2N (cap 25).
- Asteroids: N (cap 8); orbit speeds ≈ ×(1 + 0.05N).
- Shell radius: shrinks each wave to a floor (~180 px), tightening the arena.
- Wave time limit: 45 − 1.5(N−1) s, floor 20 s.
- Gravity pulses from wave 4 (frequency/intensity scale); nova from wave 6
  (SHOULD).

The curve is validated by playtest AC-7; because it is deterministic it can be
tuned without re-architecting.

## 8. Technology Stack (with rationale)

- Language: Python 3 (≥3.10; verified on 3.14).
- Engine: pygame-ce (community edition) — a single pip install, open-source,
  wraps SDL2, software 2D rendering (no GPU requirement), cross-platform. Chosen
  over classic pygame for active maintenance and current-Python wheels.
- Rendering: pygame Surfaces + pygame.draw primitives + BLEND_ADD for glow. No
  shaders or textures required.
- Audio: pygame.mixer; SFX synthesized in stdlib Python to raw PCM buffers.
- Tests: pytest.
- Packaging: pyproject.toml; `pip install .` provides an `orbitfall` entry point;
  `./run.sh` for a no-install run. Optional single-file binary via PyInstaller
  (SHOULD, stretch).
- CI: GitHub Actions running pytest on ubuntu-latest (set up in node 2).

Rationale vs. alternatives:
- Not Godot/Unity — editor-centric, heavier than needed for a single-screen 2D
  game, and harder to unit-test pure logic in headless CI.
- Not JS/Electron — large dependency footprint; conflicts with "ordinary Linux
  laptop, no heavy dependencies."
- Not raw C/SDL — more build friction and slower iteration; a single developer
  reaches polish faster in Python.
- Not terminal curses — insufficient visual fidelity for the neon aesthetic and
  no easy audio; fails the "polished game" bar.

Verification performed (2026-09-08, this server): pygame-ce 2.5.8 installed on
Python 3.14.4 (SDL 2.32.10); display, mixer, and font subsystems initialize;
primitive drawing and additive blend confirmed; a stdlib-synthesized PCM buffer
constructed a valid pygame.mixer.Sound; pytest 9.1.1 available. Full log:
STACK_VERIFICATION.md.

## 9. Architecture & Module Separation (for testability)

- game/entities.py — data classes: drone, cells, asteroids, gate, star.
- game/physics.py — integrator, gravity, collision resolution (pure math; no
  pygame import).
- game/waves.py — wave/difficulty generators (pure functions of wave N + RNG seed
  → deterministic spawn data).
- game/state.py — game state machine (title/playing/paused/gameover) +
  score/combo/lives (pure logic).
- game/persistence.py — high-score save/load (JSON in XDG data dir).
- game/input.py — logical-action → key mapping + rebinding.
- game/audio.py — procedural SFX synthesis.
- game/render.py — pygame drawing: star, drone, cells, asteroids, gate, trails,
  particles, shake.
- game/main.py — loop wiring: fixed timestep + accumulator, input poll, update,
  render.
- game/config.py — every tunable constant (single source of truth for tuning).
- tests/ — pytest suite for the pure-logic modules.

The rule that makes testing possible: physics, waves, and state are pure and
deterministic, with no rendering or wall-clock dependencies. Rendering and audio
consume the game state; they never mutate it.

## 10. Feature Scope (MoSCoW)

MUST (shipped):
- Core loop (orbit → collect → gate → escalate); gravity, thrust, impulse
  (+recharge); cells + combo; asteroids; jump gate; lives/respawn; score +
  high-score persistence; pause; difficulty escalation (cells/asteroids/shell/
  time); gravity pulses (wave 4+); juice (trail, shake, particles, flash); SFX;
  title / game-over / pause screens; tests + CI; install + README.

SHOULD (if time allows, before polish freeze):
- Nova surge (wave 6+); graze (near-miss) bonus; ambient music; rebindable keys;
  PyInstaller single binary; shake-intensity setting.

WON'T (explicitly out of scope):
- Multiplayer, level editor, procedural world/story, controller support, online
  leaderboards, mid-run save/resume, localization, mobile/console ports.

## 11. Automated Test Plan (which logic units get tests)

1. physics — integrator conserves energy within tolerance for a circular orbit
   over N steps; no NaN/runaway over long integration; collision detection
   correct for inside/tangent/outside cases.
2. waves — deterministic spawn data given a seed; monotonic difficulty (each
   parameter non-decreasing across waves); counts within caps.
3. state — score/combo/lives transitions; combo window timing; wave-clear
   condition (all cells collected + gate crossed); game-over on zero lives.
4. persistence — round-trip save/load; corrupt-file handling; data-directory
   creation.
5. input — action→key mapping; rebinding persistence.

Coverage bar: ≥90% line coverage on physics, waves, and state (the pure-logic
core), enforced in CI. Rendering/audio are intentionally excluded from the
coverage bar (they are thin and exercised by the playtest).

## 12. Definition of Done ("playable and complete")

ORBITFALL is done when ALL of the following hold:

1. Install & launch — `pip install .` (or `./run.sh`) then `orbitfall` opens a
   window on a reference Linux laptop (Ubuntu 24.04, integrated GPU, 8 GB RAM)
   with no missing-dependency errors.
2. Full session — a player can go title → play → collect cells → clear ≥3 waves →
   die → see game over with score → restart, entirely by keyboard, with no manual
   intervention.
3. Performance — sustained 60 FPS with the maximum wave population (P95 frame
   time ≤ 20 ms); stable memory over 30 minutes.
4. Stability — 30-minute continuous playtest with zero crashes, soft-locks, or
   NaN/teleport glitches.
5. Mechanics complete — every MUST feature present and functioning (Section 10).
6. Juice/polish — trails, shake, particles, near-miss/death feedback, UI
   transitions, and SFX for all key events.
7. Automated tests — the Section 11 suite passes in CI; ≥90% coverage on the
   pure-logic core.
8. Human playtest — the Section 14 protocol is run and its pass criteria
   (AC-5/6/7) are met.

## 13. Acceptance Criteria (measurable gates)

- AC-1 Launch: fresh install on a clean Ubuntu 24.04 VM reaches the title screen
  in <5 s.
- AC-2 Session: 3/3 scripted playthroughs reach wave 3+ without a crash.
- AC-3 Performance: 60 FPS sustained for 5 min at full population (P95 frame time
  ≤ 20 ms).
- AC-4 Tests: pytest suite green in CI; ≥90% coverage on physics/waves/state.
- AC-5 Fun: ≥5 external playtesters, ≥10 min each; median "I had fun" ≥4/5 and
  median "controls felt responsive" ≥4/5; ≥4/5 would play again.
- AC-6 Visual coherence: median "visuals felt consistent and polished" ≥4/5; zero
  critical readability bugs reported.
- AC-7 Difficulty: median "difficulty was fair but challenging" ≥4/5; no report
  of first-wave impossibility.

## 14. Human Playtest Protocol

- Recruit ≥5 playtesters of varied skill (may include Rick + others).
- First run watch-only (no coaching); then open play.
- Minimum 10 minutes per playtester.
- Collect: session length, waves reached, deaths, and a short Likert
  questionnaire (1–5): fun, responsiveness, fairness, visual polish,
  would-play-again, plus free-text comments.
- Log every observed bug; any crash or soft-lock is a blocking failure until
  fixed.
- Acceptance per AC-5/6/7.

## 15. Risks & Mitigations

- Orbital motion feels floaty/frustrating → the impulse tool provides snap;
  gravity tuned mild; early playtest; all constants in config.py.
- pygame-ce unavailable on a given Python → verified on 3.14 today; fallback to
  classic pygame or pin Python 3.12 in a venv/PyInstaller.
- Scope creep → MoSCoW (Section 10) + explicit WON'T list; escalation defined as
  data, not new features.
- Difficulty tuning → deterministic curve + AC-7 playtest gate.

## 16. Tunables (single source of truth, initial values)

Window 960×540 logical; fixed dt 1/120 s; gravity G (tuned); thrust ≈600 px/s²;
rotation ≈240 deg/s; impulse Δv ≈180 px/s, 3 charges, 2.0 s/charge recharge,
partial refill on collect; combo window ≈2.0 s, cap ×8; lives 3; star kill-radius
≈40 px (grows/wave); shell radius ≈300→180 px; cell radius ≈6 px; asteroid radius
≈10–18 px; wave time 45 − 1.5(N−1) s (floor 20 s); cells 5+2N (cap 25); asteroids
N (cap 8); gravity pulse ×1.4 / 1.5 s (wave 4+); nova ×1.8 / 2.0 s (wave 6+,
SHOULD). All values live in config.py and are expected to shift during playtest
tuning.
