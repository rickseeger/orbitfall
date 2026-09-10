"""Procedural SFX synthesis (DESIGN.md section 3).

Synthesizes raw PCM buffers with stdlib array/math (no numpy, no audio files)
and feeds them to pygame.mixer.Sound(buffer=...). The buffers are generated to
match the mixer's *actual* negotiated format, so they work on both real audio
and the dummy driver used in headless CI.

Public API:
    ensure_mixer() -> None
    AudioBank (class with .play_cell(combo), .start_thrust(), ...)
"""

from __future__ import annotations

import array
import math
import random

import pygame

from game import config

__all__ = ["ensure_mixer", "AudioBank"]

_SAMPLE_RATE = 44100


def ensure_mixer() -> None:
    """Initialize the mixer (stereo 16-bit @ 44.1 kHz) if not already up."""
    if pygame.mixer.get_init() is None:
        pygame.mixer.init(frequency=_SAMPLE_RATE, size=-16, channels=2)


def _format() -> tuple[int, int, int]:
    ensure_mixer()
    freq, size, channels = pygame.mixer.get_init()  # type: ignore[assignment]
    return freq, size, channels


def _build(fn, dur: float, volume: float = 1.0) -> pygame.mixer.Sound:
    """Turn a sample function fn(t)->[-1,1] into a mixer Sound."""
    freq, size, channels = _format()
    n = int(freq * dur)
    array_code = "h" if size < 0 else "H"
    buf = array.array(array_code)
    amp = (1 << (abs(size) - 1)) - 1
    for i in range(n):
        t = i / freq
        v = fn(t) * volume
        v = -1.0 if v < -1.0 else (1.0 if v > 1.0 else v)
        sample = int(v * amp)
        for _ in range(channels):
            buf.append(sample)
    return pygame.mixer.Sound(buffer=buf.tobytes())


def _cell_collect(combo: int) -> pygame.mixer.Sound:
    base = 440.0 * (1.0 + 0.12 * max(0, min(combo - 1, 7)))

    def fn(t: float) -> float:
        f = base * (1.0 + 0.6 * min(t / 0.09, 1.0))
        env = math.exp(-t * 22.0)
        return math.sin(2.0 * math.pi * f * t) * env

    return _build(fn, 0.18, 0.8)


def _thrust() -> pygame.mixer.Sound:
    rnd = random.Random(1234)

    def fn(t: float) -> float:
        wobble = 0.6 + 0.4 * math.sin(2.0 * math.pi * 1.3 * t)
        tone = math.sin(2.0 * math.pi * 55.0 * t) * 0.6
        noise = (rnd.random() * 2.0 - 1.0) * 0.4
        return (tone + noise) * wobble * 0.6

    return _build(fn, 0.5, 0.7)


def _impulse() -> pygame.mixer.Sound:
    rnd = random.Random(999)

    def fn(t: float) -> float:
        env = math.exp(-t * 14.0)
        sweep = math.sin(2.0 * math.pi * (300.0 + 900.0 * t) * t) * 0.4
        noise = (rnd.random() * 2.0 - 1.0) * 0.6
        return (sweep + noise) * env

    return _build(fn, 0.4, 0.85)


def _explosion() -> pygame.mixer.Sound:
    rnd = random.Random(7)

    def fn(t: float) -> float:
        env = math.exp(-t * 5.0)
        tone = math.sin(2.0 * math.pi * (220.0 - 180.0 * min(t / 0.5, 1.0)) * t) * 0.5
        noise = (rnd.random() * 2.0 - 1.0) * 0.8
        return (tone + noise) * env

    return _build(fn, 0.6, 0.9)


def _gate_open() -> pygame.mixer.Sound:
    def fn(t: float) -> float:
        if t < 0.14:
            tt, f = t, 660.0
        else:
            tt, f = t - 0.14, 880.0
        env = math.exp(-tt * 18.0)
        return math.sin(2.0 * math.pi * f * tt) * env

    return _build(fn, 0.55, 0.7)


def _wave_clear() -> pygame.mixer.Sound:
    notes = [523.25, 659.25, 783.99, 1046.50]
    step = 0.11

    def fn(t: float) -> float:
        i = min(int(t / step), len(notes) - 1)
        tt = t - i * step
        env = math.exp(-tt * 10.0)
        return math.sin(2.0 * math.pi * notes[i] * tt) * env

    return _build(fn, step * len(notes) + 0.25, 0.65)


def _graze() -> pygame.mixer.Sound:
    def fn(t: float) -> float:
        env = math.exp(-t * 40.0)
        return math.sin(2.0 * math.pi * 1200.0 * t) * env

    return _build(fn, 0.09, 0.5)


class AudioBank:
    """Pre-built SFX + a looping thrust rumble, all procedural."""

    def __init__(self) -> None:
        ensure_mixer()
        self.thrust = _thrust()
        self.impulse = _impulse()
        self.explosion = _explosion()
        self.gate_open = _gate_open()
        self.wave_clear = _wave_clear()
        self.graze = _graze()
        self._thrust_on = False

    def play_cell(self, combo: int) -> None:
        _cell_collect(combo).play()

    def play_impulse(self) -> None:
        self.impulse.play()

    def play_explosion(self) -> None:
        self.explosion.play()

    def play_gate_open(self) -> None:
        self.gate_open.play()

    def play_wave_clear(self) -> None:
        self.wave_clear.play()

    def play_graze(self) -> None:
        self.graze.play()

    def set_thrust(self, on: bool) -> None:
        if on and not self._thrust_on:
            self.thrust.play(loops=-1)
            self._thrust_on = True
        elif not on and self._thrust_on:
            self.thrust.stop()
            self._thrust_on = False
