"""Entry point and loop wiring for ORBITFALL (DESIGN.md section 9).

Owns the playable core loop: title -> play -> collect -> gate -> escalate ->
death -> game over -> restart, with a fixed-timestep symplectic-Euler
simulation (1/120 s) and a render accumulator at 60 FPS. Headless runs use the
SDL dummy drivers so CI and smoke checks need no display.
"""

from __future__ import annotations

import argparse
import math
import os
import random
import sys
from collections import deque

import pygame

from game import config
from game import input as game_input
from game import persistence
from game import physics
from game import state
from game import waves
from game.audio import AudioBank
from game.entities import Drone, Particle, Vec2
from game.render import Renderer

__all__ = ["main", "Game"]


class Game:
    """The full simulation and loop wiring (title/play/pause/gameover)."""

    def __init__(self, seed: int | None = None, start: bool = False) -> None:
        pygame.init()
        pygame.mixer.init(frequency=44100, size=-16, channels=2)
        self.screen = pygame.display.set_mode(
            (config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
        )
        pygame.display.set_caption(config.TITLE)
        self.clock = pygame.time.Clock()
        self.renderer = Renderer(config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
        self.audio = AudioBank()

        self.seed = seed if seed is not None else random.randrange(1 << 30)
        self.rng = random.Random(self.seed)
        self.high_score = persistence.load_high_score()

        bindings = game_input.load_bindings() or game_input.default_bindings()
        self.input_map = game_input.InputMap(bindings)

        # render-facing state
        self.time = 0.0
        self.frames = 0
        self.shake = 0.0
        self.banner_text = ""
        self.banner_timer = 0.0
        self.new_high = False
        self.impulse_max = config.IMPULSE_CHARGES

        # run state
        self.phase = state.GamePhase.TITLE
        self.stats = state.RunStats()
        self.wave = 1
        self.impulse_charges = float(config.IMPULSE_CHARGES)
        self.impulse_recharge = 0.0
        self.particles: list[Particle] = []
        self.trail: deque[Vec2] = deque(maxlen=config.TRAIL_LENGTH)
        self._between_waves = False
        self._between_waves_timer = 0.0
        self._grazed: set[int] = set()

        # world objects
        self.drone = Drone()
        self.star = waves.make_star(1)
        self.cells = []
        self.asteroids = []
        self.gate = None
        self.shell_radius = config.SHELL_RADIUS_INITIAL
        self.time_limit = config.WAVE_TIME_BASE
        self.wave_time_left = config.WAVE_TIME_BASE
        self.pulse_state = "idle"
        self.nova_state = "idle"
        self.pulse_timer = 0.0
        self.nova_timer = 0.0
        self.pulse_enabled = False
        self.nova_enabled = False
        self.next_pulse_in = float("inf")
        self.next_nova_in = float("inf")

        self._spawn_wave(1)
        self._place_drone()

        if start:
            self._start_run()

    # ------------------------------------------------------------------ run
    def run(self, frames: int | None = None) -> int:
        accumulator = 0.0
        running = True
        while running:
            frame_dt = self.clock.tick(config.FPS) / 1000.0
            frame_dt = min(frame_dt, 0.25)

            running = self._handle_events()
            actions = self._held_actions()

            accumulator += frame_dt
            while accumulator >= config.FIXED_DT:
                self._step(config.FIXED_DT, actions)
                accumulator -= config.FIXED_DT

            self.renderer.draw(self, frame_dt)
            pygame.display.flip()
            self.frames += 1

            if frames is not None and self.frames >= frames:
                running = False

        pygame.quit()
        return 0

    # ---------------------------------------------------------------- input
    def _handle_events(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type != pygame.KEYDOWN:
                continue
            key = event.key
            if self.input_map.resolve("pause", key):
                self._toggle_pause()
            elif self.input_map.resolve("confirm", key):
                if self.phase in (state.GamePhase.TITLE, state.GamePhase.GAMEOVER):
                    self._start_run()
                elif self.phase == state.GamePhase.PAUSED:
                    self._resume()
            elif self.input_map.resolve("impulse", key):
                self._fire_impulse()
        return True

    def _held_actions(self) -> dict[str, bool]:
        pressed = pygame.key.get_pressed()
        actions: dict[str, bool] = {}
        for action in ("thrust", "rotate_left", "rotate_right"):
            codes = self.input_map.bindings.get(action, set())
            actions[action] = any(pressed[code] for code in codes)
        return actions

    def _toggle_pause(self) -> None:
        if self.phase == state.GamePhase.PLAYING:
            self.phase = state.GamePhase.PAUSED
            self.audio.set_thrust(False)
            self.drone.thrusting = False
        elif self.phase == state.GamePhase.PAUSED:
            self._resume()

    def _resume(self) -> None:
        self.phase = state.GamePhase.PLAYING

    # ------------------------------------------------------------- run state
    def _start_run(self) -> None:
        self.stats = state.RunStats()
        self.wave = 1
        self.impulse_charges = float(config.IMPULSE_CHARGES)
        self.impulse_recharge = 0.0
        self.time = 0.0
        self.shake = 0.0
        self.particles = []
        self.trail.clear()
        self.new_high = False
        self._between_waves = False
        self.rng = random.Random(self.seed)
        self._spawn_wave(1)
        self._place_drone()
        self.phase = state.GamePhase.PLAYING

    def _spawn_wave(self, n: int) -> None:
        wave_seed = self.rng.randrange(1 << 30)
        spawn = waves.spawn_wave(n, wave_seed)
        self.wave = n
        self.cells = spawn.cells
        self.asteroids = spawn.asteroids
        self.gate = spawn.gate
        self.gate.active = False
        self.shell_radius = spawn.shell_radius
        self.time_limit = spawn.time_limit
        self.wave_time_left = spawn.time_limit
        self.star = waves.make_star(n)
        self.pulse_enabled = spawn.gravity_pulse
        self.nova_enabled = spawn.nova
        self.pulse_state = "idle"
        self.nova_state = "idle"
        self.pulse_timer = 0.0
        self.nova_timer = 0.0
        self.next_pulse_in = (
            config.GRAVITY_PULSE_INTERVAL_BASE if self.pulse_enabled else float("inf")
        )
        self.next_nova_in = (
            config.NOVA_INTERVAL_BASE if self.nova_enabled else float("inf")
        )
        self._grazed = set()
        self.banner_text = f"WAVE {n}"
        self.banner_timer = 1.6

    def _place_drone(self) -> None:
        r = self.shell_radius * config.RESPAWN_RADIUS_FRACTION
        self.drone = Drone()
        self.drone.pos = self.star.pos + Vec2(0.0, -r)
        v = physics.circular_orbit_speed(r)
        tangent = physics.orbit_tangent(self.star.pos, self.drone.pos, 1.0)
        self.drone.vel = tangent * v
        self.drone.heading = tangent.angle_deg()
        self.drone.alive = True
        self.drone.invuln = config.INVULN_TIME
        self.trail.clear()
        # The outer shell radius can exceed the window's vertical half-extent,
        # so clamp the spawn point on-screen too.
        self.drone.pos, self.drone.vel = physics.contain_on_screen(
            self.drone.pos, self.drone.vel
        )

    def _respawn(self) -> None:
        self._place_drone()

    def _fire_impulse(self) -> None:
        if self.phase != state.GamePhase.PLAYING or not self.drone.alive:
            return
        if self.impulse_charges < 1.0:
            return
        self.impulse_charges -= 1.0
        self.drone.vel = self.drone.vel + physics.heading_vec(
            self.drone.heading
        ) * config.IMPULSE_DELTA_V
        self.audio.play_impulse()
        self._spawn_particles(self.drone.pos, config.COLOR_SHIP_GLOW, config.PARTICLE_IMPULSE_COUNT, 140.0)
        self.shake += 2.0

    # ----------------------------------------------------------- fixed step
    def _step(self, dt: float, actions: dict[str, bool]) -> None:
        if self.phase != state.GamePhase.PLAYING:
            return
        self.time += dt
        self._update_banner(dt)
        self.shake = min(14.0, self.shake * config.SHAKE_DECAY)
        state.tick_combo(self.stats, dt)

        if self._between_waves:
            self._between_waves_timer -= dt
            if self._between_waves_timer <= 0.0:
                self._between_waves = False
                self.wave += 1
                self._spawn_wave(self.wave)
                self._respawn()
            return

        self._update_pulse(dt)
        self._update_nova(dt)
        self._recharge_impulse(dt)
        self._update_drone(dt, actions)
        self._update_asteroids(dt)
        self._update_particles(dt)
        if self.gate is not None:
            self.gate.angle += dt * 1.6

        # wave countdown
        self.wave_time_left -= dt
        if self.wave_time_left <= 0.0:
            self._die("the star caught you")
            self.wave_time_left = self.time_limit

        self._handle_collisions()

        self.trail.append(self.drone.pos.copy())

    def _update_banner(self, dt: float) -> None:
        if self.banner_timer > 0.0:
            self.banner_timer = max(0.0, self.banner_timer - dt)

    def _recharge_impulse(self, dt: float) -> None:
        if self.impulse_charges < float(self.impulse_max):
            self.impulse_recharge += dt
            while (
                self.impulse_recharge >= config.IMPULSE_RECHARGE
                and self.impulse_charges < float(self.impulse_max)
            ):
                self.impulse_recharge -= config.IMPULSE_RECHARGE
                self.impulse_charges += 1.0

    def _update_drone(self, dt: float, actions: dict[str, bool]) -> None:
        d = self.drone
        if d.invuln > 0.0:
            d.invuln = max(0.0, d.invuln - dt)
        d.thrusting = bool(actions.get("thrust"))
        self.audio.set_thrust(d.thrusting)

        if actions.get("rotate_left"):
            d.heading -= config.ROTATION_RATE * dt
        if actions.get("rotate_right"):
            d.heading += config.ROTATION_RATE * dt

        rel = self.star.pos - d.pos
        accel = physics.gravity_vector(rel, config.GRAVITY_G * self.star.gravity_mult)
        if d.thrusting:
            accel = accel + physics.heading_vec(d.heading) * config.THRUST_ACCEL
        d.pos, d.vel = physics.integrate(d.pos, d.vel, accel, dt)
        d.pos, d.vel = physics.contain_on_screen(d.pos, d.vel)

    def _update_asteroids(self, dt: float) -> None:
        for a in self.asteroids:
            a.angle += a.angular_vel * dt

    def _update_particles(self, dt: float) -> None:
        for p in self.particles:
            p.vel *= 0.92
            p.pos += p.vel * dt
            p.life -= dt
        self.particles = [p for p in self.particles if p.life > 0.0]

    def _update_pulse(self, dt: float) -> None:
        if not self.pulse_enabled:
            return
        if self.pulse_state == "idle":
            self.next_pulse_in -= dt
            if self.next_pulse_in <= 0.0:
                self.pulse_state = "telegraph"
                self.pulse_timer = config.GRAVITY_PULSE_TELEGRAPH
        elif self.pulse_state == "telegraph":
            self.pulse_timer -= dt
            if self.pulse_timer <= 0.0:
                self.pulse_state = "active"
                self.pulse_timer = config.GRAVITY_PULSE_DURATION
                self.star.gravity_mult = config.GRAVITY_PULSE_MULT
        elif self.pulse_state == "active":
            self.pulse_timer -= dt
            if self.pulse_timer <= 0.0:
                self.pulse_state = "idle"
                self.star.gravity_mult = 1.0
                self.next_pulse_in = max(
                    3.0,
                    config.GRAVITY_PULSE_INTERVAL_BASE
                    - (self.wave - config.GRAVITY_PULSE_FROM_WAVE) * 0.5,
                )

    def _update_nova(self, dt: float) -> None:
        if not self.nova_enabled:
            return
        if self.nova_state == "idle":
            self.next_nova_in -= dt
            if self.next_nova_in <= 0.0:
                self.nova_state = "telegraph"
                self.nova_timer = config.NOVA_TELEGRAPH
        elif self.nova_state == "telegraph":
            self.nova_timer -= dt
            if self.nova_timer <= 0.0:
                self.nova_state = "active"
                self.nova_timer = config.NOVA_DURATION
                self.star.kill_radius = waves.star_kill_radius(self.wave) * config.NOVA_MULT
        elif self.nova_state == "active":
            self.nova_timer -= dt
            if self.nova_timer <= 0.0:
                self.nova_state = "idle"
                self.star.kill_radius = waves.star_kill_radius(self.wave)
                self.next_nova_in = max(
                    6.0,
                    config.NOVA_INTERVAL_BASE - (self.wave - config.NOVA_FROM_WAVE),
                )

    # ----------------------------------------------------------- collisions
    def _handle_collisions(self) -> None:
        d = self.drone
        if not d.alive:
            return

        # star
        if d.invuln <= 0.0 and d.pos.distance(self.star.pos) <= self.star.kill_radius:
            self._die("the star")
            return

        # asteroids (collision + graze)
        for a in self.asteroids:
            apos = self._asteroid_pos(a)
            dist = d.pos.distance(apos)
            if d.invuln <= 0.0 and dist <= d.radius + a.radius:
                self._die("an asteroid")
                return
            if (
                a.seed not in self._grazed
                and d.radius + a.radius < dist <= d.radius + a.radius + config.GRAZE_MARGIN
            ):
                self._grazed.add(a.seed)
                state.add_score(self.stats, config.GRAZE_BONUS)
                self.audio.play_graze()

        # cells
        for c in self.cells:
            if c.collected:
                continue
            if d.pos.distance(c.pos) <= d.radius + c.radius:
                c.collected = True
                state.collect_cell(self.stats)
                self.impulse_charges = min(
                    float(self.impulse_max),
                    self.impulse_charges + config.IMPULSE_REFILL_ON_COLLECT,
                )
                self.audio.play_cell(self.stats.combo)
                self._spawn_particles(c.pos, config.COLOR_CELL, config.PARTICLE_COLLECT_COUNT, 120.0)
                self.shake += 1.5

        # gate activation
        if all(c.collected for c in self.cells) and self.gate is not None and not self.gate.active:
            self.gate.active = True
            self.audio.play_gate_open()
            self.banner_text = "GATE OPEN"
            self.banner_timer = 1.4
            self._spawn_particles(self.gate.pos, config.COLOR_GATE, 24, 120.0)

        # gate crossing
        if self.gate is not None and self.gate.active:
            if d.pos.distance(self.gate.pos) <= d.radius + self.gate.radius:
                self._clear_wave()

    @staticmethod
    def _asteroid_pos(a) -> Vec2:
        return a.center + Vec2(
            math.cos(a.angle) * a.orbit_radius, math.sin(a.angle) * a.orbit_radius
        )

    def _die(self, reason: str) -> None:
        self.shake += 9.0
        self._spawn_particles(self.drone.pos, config.COLOR_SHIP, config.PARTICLE_DEATH_COUNT, 260.0)
        self.audio.play_explosion()
        self.audio.set_thrust(False)
        self.drone.alive = False
        game_over = state.lose_life(self.stats)
        if game_over:
            self._game_over()
        else:
            self._respawn()

    def _game_over(self) -> None:
        self.phase = state.GamePhase.GAMEOVER
        self.new_high = self.stats.score > self.high_score
        if self.new_high:
            self.high_score = self.stats.score
            persistence.save_high_score(self.high_score)
        self.audio.set_thrust(False)
        self.drone.thrusting = False

    def _clear_wave(self) -> None:
        bonus = state.wave_clear_bonus(self.wave, self.wave_time_left)
        state.add_score(self.stats, bonus)
        self.audio.play_wave_clear()
        self.banner_text = f"WAVE {self.wave} CLEAR  +{bonus}"
        self.banner_timer = 1.8
        self._spawn_particles(self.gate.pos, config.COLOR_GATE, config.PARTICLE_GATE_COUNT, 180.0)
        self.shake += 3.0
        self._between_waves = True
        self._between_waves_timer = 1.2
        self.audio.set_thrust(False)
        self.drone.thrusting = False

    # ------------------------------------------------------------- particles
    def _spawn_particles(self, pos: Vec2, color, count: int, speed: float) -> None:
        for _ in range(count):
            ang = random.uniform(0.0, 2.0 * math.pi)
            vel = Vec2(math.cos(ang), math.sin(ang)) * random.uniform(20.0, speed)
            life = random.uniform(0.3, 0.8)
            self.particles.append(
                Particle(
                    pos=pos.copy(),
                    vel=vel,
                    life=life,
                    max_life=life,
                    color=color,
                    size=random.uniform(1.5, 3.5),
                )
            )



def main(argv: list[str] | None = None) -> int:
    """Run ORBITFALL. Returns a process exit code."""
    args = _parse_args(argv)

    if args.headless:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

    game = Game(seed=args.seed, start=args.start)
    return game.run(frames=args.frames)


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
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="RNG seed for a deterministic run (default: random).",
    )
    parser.add_argument(
        "--start",
        action="store_true",
        help="Skip the title screen and start the run immediately (for CI).",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    sys.exit(main())
