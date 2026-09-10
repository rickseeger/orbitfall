"""Entity data classes: drone, cells, asteroids, gate, star (DESIGN.md sec 9).

Pure data shapes (dataclasses) with a minimal 2D vector type. No pygame import
here, so physics/waves/state stay unit-testable in headless CI.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

__all__ = [
    "Vec2",
    "Drone",
    "Cell",
    "Asteroid",
    "JumpGate",
    "Star",
    "Particle",
    "WaveSpawn",
]


class Vec2:
    """Minimal immutable-by-convention 2D vector (pure Python, no pygame)."""

    __slots__ = ("x", "y")

    def __init__(self, x: float = 0.0, y: float = 0.0) -> None:
        self.x = float(x)
        self.y = float(y)

    @classmethod
    def from_angle(cls, degrees: float) -> "Vec2":
        r = math.radians(degrees)
        return cls(math.cos(r), math.sin(r))

    def copy(self) -> "Vec2":
        return Vec2(self.x, self.y)

    def __add__(self, o: "Vec2") -> "Vec2":
        return Vec2(self.x + o.x, self.y + o.y)

    def __sub__(self, o: "Vec2") -> "Vec2":
        return Vec2(self.x - o.x, self.y - o.y)

    def __mul__(self, s: float) -> "Vec2":
        return Vec2(self.x * s, self.y * s)

    __rmul__ = __mul__

    def __truediv__(self, s: float) -> "Vec2":
        return Vec2(self.x / s, self.y / s)

    def __neg__(self) -> "Vec2":
        return Vec2(-self.x, -self.y)

    def __iadd__(self, o: "Vec2") -> "Vec2":
        self.x += o.x
        self.y += o.y
        return self

    def __isub__(self, o: "Vec2") -> "Vec2":
        self.x -= o.x
        self.y -= o.y
        return self

    def __imul__(self, s: float) -> "Vec2":
        self.x *= s
        self.y *= s
        return self

    def length_sq(self) -> float:
        return self.x * self.x + self.y * self.y

    def length(self) -> float:
        return math.hypot(self.x, self.y)

    def distance(self, o: "Vec2") -> float:
        return math.hypot(self.x - o.x, self.y - o.y)

    def normalized(self) -> "Vec2":
        length = self.length()
        if length == 0.0:
            return Vec2(0.0, 0.0)
        return Vec2(self.x / length, self.y / length)

    def dot(self, o: "Vec2") -> float:
        return self.x * o.x + self.y * o.y

    def perp(self) -> "Vec2":
        """Rotate 90 degrees clockwise on screen (y-down convention)."""
        return Vec2(self.y, -self.x)

    def angle_deg(self) -> float:
        return math.degrees(math.atan2(self.y, self.x))

    def to_tuple(self) -> tuple[float, float]:
        return (self.x, self.y)

    def __iter__(self):
        return iter((self.x, self.y))

    def __repr__(self) -> str:
        return f"Vec2({self.x:.3f}, {self.y:.3f})"


@dataclass
class Drone:
    """The player's craft. Heading is in degrees (0 = right, + = clockwise)."""

    pos: Vec2 = field(default_factory=Vec2)
    vel: Vec2 = field(default_factory=Vec2)
    heading: float = -90.0
    radius: float = 8.0
    alive: bool = True
    invuln: float = 0.0        # seconds of invulnerability remaining
    thrusting: bool = False


@dataclass
class Cell:
    """A static energy-cell collectible."""

    pos: Vec2 = field(default_factory=Vec2)
    radius: float = 6.0
    collected: bool = False


@dataclass
class Asteroid:
    """A rock on a fixed circular orbit around the star."""

    center: Vec2 = field(default_factory=Vec2)   # star center (shared)
    orbit_radius: float = 200.0
    angle: float = 0.0          # radians, current orbit position
    angular_vel: float = 0.5    # rad/s (may be negative)
    radius: float = 12.0
    seed: int = 0               # deterministic polygon shape


@dataclass
class JumpGate:
    """The escape gate; only active once every cell is collected."""

    pos: Vec2 = field(default_factory=Vec2)
    radius: float = 20.0
    angle: float = 0.0          # rotating dash segment phase
    active: bool = False


@dataclass
class Star:
    """The collapsing gravity well."""

    pos: Vec2 = field(default_factory=Vec2)
    kill_radius: float = 40.0
    surface_radius: float = 26.0   # visual core (smaller than kill radius)
    gravity_mult: float = 1.0      # scaled by gravity pulses


@dataclass
class Particle:
    """A short-lived visual particle (consumed by render.py)."""

    pos: Vec2 = field(default_factory=Vec2)
    vel: Vec2 = field(default_factory=Vec2)
    life: float = 0.5
    max_life: float = 0.5
    color: tuple[int, int, int] = (255, 255, 255)
    size: float = 2.0


@dataclass
class WaveSpawn:
    """Deterministic spawn data for one wave (returned by waves.spawn_wave)."""

    wave: int
    shell_radius: float
    time_limit: float
    cells: list[Cell]
    asteroids: list[Asteroid]
    gate: JumpGate
    gravity_pulse: bool
    nova: bool
