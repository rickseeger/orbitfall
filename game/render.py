"""Pygame drawing: star, drone, cells, asteroids, gate, trails, particles.

Rendering consumes game state and never mutates it (DESIGN.md section 9).
Neon glow uses additive blending (pygame.BLEND_ADD) onto a reusable layer.

The renderer reads a plain `game` object (duck-typed) so it never imports the
main loop module -- no circular dependency. All geometry is procedural.
"""

from __future__ import annotations

import math
import random

import pygame

from game import config
from game.entities import Vec2

__all__ = ["Renderer"]


def _lerp_color(a, b, t: float):
    t = max(0.0, min(1.0, t))
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
    )


class Renderer:
    """Owns pre-rendered surfaces and draws one full frame per call."""

    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.world = pygame.Surface((width, height))
        self.glow = pygame.Surface((width, height))  # opaque; BLEND_ADD layer
        self.starfield = self._make_starfield()
        self.star_gradient = self._make_star_gradient(160)
        self._star_cache: dict[int, pygame.Surface] = {}
        self._font_small = pygame.font.Font(None, 22)
        self._font = pygame.font.Font(None, 30)
        self._font_big = pygame.font.Font(None, 72)
        self._font_title = pygame.font.Font(None, 120)

    # -- pre-rendered helpers ------------------------------------------------
    def _make_starfield(self) -> list[tuple[float, float, int, int]]:
        rng = random.Random(config.STARFIELD_SEED)
        points = []
        for _ in range(config.STARFIELD_COUNT):
            x = rng.uniform(0, self.width)
            y = rng.uniform(0, self.height)
            size = 1 if rng.random() < 0.75 else 2
            bright = rng.randint(40, 160)
            points.append((x, y, size, bright))
        return points

    def _make_star_gradient(self, size: int) -> pygame.Surface:
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        c = size / 2.0
        maxd = size / 2.0
        core = config.COLOR_STAR_CORE
        edge = config.COLOR_STAR_EDGE
        for y in range(size):
            for x in range(size):
                d = math.hypot(x - c, y - c) / maxd
                if d <= 1.0:
                    col = _lerp_color(core, edge, min(1.0, d * 1.15))
                    alpha = int(255 * (1.0 - d) ** 2)
                    surf.set_at((x, y), (*col, alpha))
        return surf

    def _star_surface(self, radius: int) -> pygame.Surface:
        radius = max(4, radius)
        if radius not in self._star_cache:
            self._star_cache[radius] = pygame.transform.smoothscale(
                self.star_gradient, (radius * 2, radius * 2)
            )
        return self._star_cache[radius]

    # -- frame ---------------------------------------------------------------
    def draw(self, game, dt: float) -> None:
        screen = game.screen
        # screen shake offset (affects the world only, not the HUD)
        shake = game.shake
        ox = oy = 0
        if shake > 0.1:
            ox = random.uniform(-shake, shake)
            oy = random.uniform(-shake, shake)

        self.world.fill(config.COLOR_BACKGROUND)
        self._draw_starfield()
        self._draw_star(game)
        self._draw_cells(game)
        self._draw_asteroids(game)
        self._draw_gate(game)
        self._draw_trail(game)
        self._draw_ship(game)
        self._draw_particles(game)
        self._apply_glow(game)

        screen.blit(self.world, (int(ox), int(oy)))
        self._draw_hud(game)
        self._draw_overlay(game)

    # -- world elements ------------------------------------------------------
    def _draw_starfield(self) -> None:
        for x, y, size, bright in self.starfield:
            self.world.set_at(
                (int(x), int(y)),
                (bright, bright, bright),
            )

    def _draw_star(self, game) -> None:
        star = game.star
        flicker = 1.0 + 0.035 * math.sin(game.time * 13.0) + 0.015 * math.sin(game.time * 31.0 + 1.3)
        r = max(4, int(star.surface_radius * flicker))
        scaled = self._star_surface(r)
        self.world.blit(scaled, (int(star.pos.x - r), int(star.pos.y - r)))

        # additive halo
        halo = pygame.draw.circle(
            self.glow, (60, 20, 10), (int(star.pos.x), int(star.pos.y)), int(star.surface_radius * 2.4)
        )

    def _draw_ship(self, game) -> None:
        drone = game.drone
        if not drone.alive:
            return
        # blink while invulnerable
        if drone.invuln > 0.0 and int(game.time * 12) % 2 == 0:
            return

        direction = Vec2.from_angle(drone.heading)
        perp = direction.perp()
        pos = drone.pos
        size = drone.radius + 4.0
        nose = pos + direction * size
        back_l = pos - direction * size * 0.6 + perp * size * 0.5
        back_r = pos - direction * size * 0.6 - perp * size * 0.5
        pygame.draw.polygon(
            self.world,
            config.COLOR_SHIP,
            [nose.to_tuple(), back_l.to_tuple(), back_r.to_tuple()],
        )
        # heading indicator line
        pygame.draw.line(
            self.world,
            config.COLOR_SHIP,
            pos.to_tuple(),
            nose.to_tuple(),
            2,
        )

        if drone.thrusting:
            tail = pos - direction * size * 0.6
            flame = pos - direction * (size * 1.6 + random.uniform(0, 4))
            pygame.draw.line(
                self.world,
                config.COLOR_SHIP_GLOW,
                tail.to_tuple(),
                flame.to_tuple(),
                3,
            )
            pygame.draw.circle(
                self.glow, (30, 90, 140), (int(pos.x), int(pos.y)), int(size * 1.6)
            )

    def _draw_cells(self, game) -> None:
        for cell in game.cells:
            if cell.collected:
                continue
            pos = (int(cell.pos.x), int(cell.pos.y))
            r = int(cell.radius)
            pygame.draw.circle(self.world, config.COLOR_CELL, pos, r)
            pygame.draw.circle(self.world, (255, 240, 180), pos, max(1, r - 2))
            pulse = 1.0 + 0.15 * math.sin(game.time * 4.0 + cell.pos.x * 0.1)
            pygame.draw.circle(
                self.glow, (70, 45, 10), pos, int(cell.radius * 3.2 * pulse)
            )

    def _draw_asteroids(self, game) -> None:
        for asteroid in game.asteroids:
            rng = random.Random(asteroid.seed)
            verts = []
            n = 7
            for i in range(n):
                angle = asteroid.angle + 2.0 * math.pi * i / n
                rr = asteroid.radius * rng.uniform(0.78, 1.12)
                x = asteroid.center.x + asteroid.orbit_radius * math.cos(asteroid.angle)
                y = asteroid.center.y + asteroid.orbit_radius * math.sin(asteroid.angle)
                verts.append(
                    (x + math.cos(angle) * rr, y + math.sin(angle) * rr)
                )
            pygame.draw.polygon(self.world, config.COLOR_ASTEROID, verts, 0)
            pygame.draw.polygon(self.world, (190, 200, 220), verts, 1)

    def _draw_gate(self, game) -> None:
        gate = game.gate
        if not gate.active:
            return
        pos = (int(gate.pos.x), int(gate.pos.y))
        pulse = 1.0 + 0.08 * math.sin(game.time * 6.0)
        radius = int(gate.radius * 1.9 * pulse)
        # outer ring
        pygame.draw.circle(self.world, config.COLOR_GATE, pos, radius, 2)
        # rotating dashed segments
        for k in range(3):
            a = gate.angle + k * (2.0 * math.pi / 3.0)
            p1 = (
                gate.pos.x + math.cos(a) * radius,
                gate.pos.y + math.sin(a) * radius,
            )
            p2 = (
                gate.pos.x + math.cos(a + 0.6) * radius,
                gate.pos.y + math.sin(a + 0.6) * radius,
            )
            pygame.draw.line(self.world, (255, 160, 230), p1, p2, 4)
        pygame.draw.circle(self.glow, (60, 10, 45), pos, radius + 8)

    def _draw_trail(self, game) -> None:
        trail = game.trail
        n = len(trail)
        if n < 2:
            return
        for i in range(n - 1):
            t = i / max(1, n - 1)
            alpha = int(160 * t)
            if alpha <= 0:
                continue
            color = (*config.COLOR_TRAIL, alpha)
            surf = pygame.Surface((4, 4), pygame.SRCALPHA)
            surf.fill(color)
            a = trail[i]
            b = trail[i + 1]
            pygame.draw.line(
                self.world, config.COLOR_TRAIL, a.to_tuple(), b.to_tuple(), 2
            )

    def _draw_particles(self, game) -> None:
        for p in game.particles:
            frac = p.life / max(1e-6, p.max_life)
            col = _lerp_color(p.color, (0, 0, 0), 1.0 - frac)
            size = max(1, int(p.size * frac))
            pos = (int(p.pos.x), int(p.pos.y))
            pygame.draw.circle(self.world, col, pos, size)
            pygame.draw.circle(self.glow, (col[0] // 4, col[1] // 4, col[2] // 4), pos, size + 3)

    def _apply_glow(self, game) -> None:
        self.world.blit(self.glow, (0, 0), special_flags=pygame.BLEND_ADD)
        self.glow.fill((0, 0, 0))

    # -- HUD / overlays ------------------------------------------------------
    def _draw_hud(self, game) -> None:
        screen = game.screen
        hud = config.COLOR_HUD
        self._text(screen, self._font_small, f"SCORE {game.stats.score:07d}", (12, 8), hud)
        self._text(screen, self._font_small, f"HI {game.high_score:07d}", (12, 30), (170, 180, 210))

        wave_txt = f"WAVE {game.wave}"
        self._text(screen, self._font, wave_txt, (self.width - 12, 8), hud, anchor="right")
        # wave timer with color warning when low
        tcolor = config.COLOR_WARN if game.wave_time_left <= 10.0 else hud
        self._text(screen, self._font_small, f"TIME {max(0, game.wave_time_left):4.1f}", (self.width - 12, 34), tcolor, anchor="right")

        # combo multiplier
        if game.stats.combo > 1:
            self._text(
                screen,
                self._font_big,
                f"x{game.stats.combo}",
                (self.width // 2, 60),
                config.COLOR_CELL,
                anchor="center",
            )

        # lives as small ship glyphs
        for i in range(game.stats.lives):
            cx = 16 + i * 20
            cy = self.height - 16
            pygame.draw.polygon(
                screen, config.COLOR_SHIP, [(cx, cy - 8), (cx - 6, cy + 6), (cx + 6, cy + 6)]
            )

        # impulse meter
        mx = 12
        my = self.height - 34
        for i in range(game.impulse_max):
            full = i < int(game.impulse_charges)
            frac = game.impulse_charges - int(game.impulse_charges) if i == int(game.impulse_charges) else (1.0 if full else 0.0)
            if full:
                frac = 1.0
            rect = pygame.Rect(mx + i * 22, my, 18, 10)
            pygame.draw.rect(screen, (40, 40, 70), rect, 0)
            if frac > 0.0:
                fill = pygame.Rect(rect.x, rect.y, int(rect.w * frac), rect.h)
                pygame.draw.rect(screen, (90, 220, 255), fill, 0)
            pygame.draw.rect(screen, (120, 140, 180), rect, 1)

        # telegraph warnings
        if game.pulse_state == "telegraph":
            self._text(screen, self._font_big, "GRAVITY PULSE", (self.width // 2, self.height - 70), config.COLOR_WARN, anchor="center")
        elif game.nova_state == "telegraph":
            self._text(screen, self._font_big, "NOVA SURGE", (self.width // 2, self.height - 70), config.COLOR_WARN, anchor="center")

        # transient banner (wave clear / new wave)
        if game.banner_timer > 0.0:
            self._text(screen, self._font_big, game.banner_text, (self.width // 2, self.height // 2 - 80), config.COLOR_GATE, anchor="center")

    def _draw_overlay(self, game) -> None:
        screen = game.screen
        phase = game.phase.name

        if phase == "TITLE":
            self._fade(screen, 0.55)
            self._text(screen, self._font_title, config.TITLE, (self.width // 2, self.height // 2 - 110), config.COLOR_SHIP, anchor="center")
            self._text(screen, self._font, "the last drone of the solar rig", (self.width // 2, self.height // 2 - 60), config.COLOR_HUD, anchor="center")
            self._text(screen, self._font, f"HIGH SCORE  {game.high_score:07d}", (self.width // 2, self.height // 2 + 10), config.COLOR_CELL, anchor="center")
            self._text(screen, self._font_big, "PRESS ENTER TO LAUNCH", (self.width // 2, self.height // 2 + 90), config.COLOR_SHIP, anchor="center")
            self._text(screen, self._font_small, "A/D or Left/Right rotate   W/Up/Space thrust   Shift/Ctrl impulse   P pause", (self.width // 2, self.height - 40), (150, 165, 200), anchor="center")
            self._text(screen, self._font_small, "collect cells, then fly through the gate before the star takes you", (self.width // 2, self.height - 14), (120, 130, 160), anchor="center")

        elif phase == "GAMEOVER":
            self._fade(screen, 0.7)
            self._text(screen, self._font_title, "GAME OVER", (self.width // 2, self.height // 2 - 100), config.COLOR_WARN, anchor="center")
            self._text(screen, self._font, f"SCORE  {game.stats.score:07d}", (self.width // 2, self.height // 2 - 20), config.COLOR_HUD, anchor="center")
            if game.new_high:
                self._text(screen, self._font, "NEW HIGH SCORE!", (self.width // 2, self.height // 2 + 20), config.COLOR_CELL, anchor="center")
            else:
                self._text(screen, self._font, f"HIGH SCORE  {game.high_score:07d}", (self.width // 2, self.height // 2 + 20), config.COLOR_CELL, anchor="center")
            self._text(screen, self._font_big, "PRESS ENTER TO RESTART", (self.width // 2, self.height // 2 + 90), config.COLOR_SHIP, anchor="center")

        elif phase == "PAUSED":
            self._fade(screen, 0.5)
            self._text(screen, self._font_title, "PAUSED", (self.width // 2, self.height // 2 - 40), config.COLOR_HUD, anchor="center")
            self._text(screen, self._font, "P or Esc to resume", (self.width // 2, self.height // 2 + 20), config.COLOR_HUD, anchor="center")

    # -- primitives ----------------------------------------------------------
    def _fade(self, screen, alpha: float) -> None:
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, int(255 * alpha)))
        screen.blit(overlay, (0, 0))

    def _text(self, screen, font, text: str, pos, color, anchor: str = "left") -> None:
        surf = font.render(text, True, color)
        rect = surf.get_rect()
        if anchor == "right":
            rect.topright = pos
        elif anchor == "center":
            rect.center = pos
        else:
            rect.topleft = pos
        screen.blit(surf, rect)
