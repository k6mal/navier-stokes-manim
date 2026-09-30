"""Shared scaffolding for the scenes: defaults, captions, and field playback."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from manim import *

import theme as T

CACHE = Path(__file__).parent / "cache"

config.background_color = T.BG
Text.set_default(font=T.FONT, color=T.INK)
MathTex.set_default(color=T.INK)
Tex.set_default(color=T.INK)


# --------------------------------------------------------------------------
# cached simulation data
# --------------------------------------------------------------------------
def meta(name: str) -> dict:
    return json.loads((CACHE / f"{name}.json").read_text())


def frames(name: str, key: str) -> np.ndarray:
    """Memory-mapped (n_frames, nx, ny) uint8 stack."""
    return np.load(CACHE / f"{name}__{key}.npy", mmap_mode="r")


class FieldMovie(Group):
    """An ImageMobject that plays a cached scalar field through a colour map.

    The frame index is driven off wall-clock animation time, so the fluid keeps
    moving at a steady rate no matter what else is being animated on top of it.
    Cell coordinates can be turned into scene points with `point()`, which is
    how a clean circle gets laid exactly over the staircased obstacle.
    """

    def __init__(self, stack, lut, width=None, height=None, crop=None,
                 fps=30.0, loop=True, start=0, opacity=1.0, smooth=True):
        super().__init__()
        self.stack, self.lut, self.fps, self.loop = stack, lut, fps, loop
        self.smooth = smooth
        n, nx, ny = stack.shape
        x0, x1, y0, y1 = crop if crop else (0, nx, 0, ny)
        self.x0, self.x1, self.y0, self.y1 = x0, x1, y0, y1
        self._i = -1
        self._t = float(start) / fps

        self.img = ImageMobject(self._rgb(start))
        self.img.set_resampling_algorithm(RESAMPLING_ALGORITHMS["cubic"])
        if width is not None:
            self.img.width = width
        if height is not None:
            self.img.height = height
        self.img.set_opacity(opacity)
        self.add(self.img)
        self._i = start

    # -- data ------------------------------------------------------------
    def _clamp(self, i):
        n = self.stack.shape[0]
        return int(i) % n if self.loop else int(min(max(i, 0), n - 1))

    def _window(self, i):
        return np.asarray(self.stack[self._clamp(i), self.x0:self.x1, self.y0:self.y1])

    def _rgb(self, t):
        """Colour the field at fractional frame `t`.

        The cached frames are usually played back slower than they were
        captured, so neighbouring frames get blended.  Without this the
        motion steps visibly instead of flowing.
        """
        i0 = int(np.floor(t))
        a = float(t - i0)
        if not self.smooth or a < 0.02:
            return T.colorize(self._window(i0), self.lut)
        s0 = self._window(i0).astype(np.float32)
        s1 = self._window(i0 + 1).astype(np.float32)
        blend = np.clip(s0 + (s1 - s0) * a, 0, 255).astype(np.uint8)
        return T.colorize(blend, self.lut)

    def set_frame(self, t):
        self._i = self._clamp(t)
        self.img.pixel_array[:, :, :3] = self._rgb(t)

    # -- playback --------------------------------------------------------
    def play(self, rate=1.0):
        """Start advancing the movie in real time; rate scales the speed."""
        def upd(m, dt):
            self._t += dt * rate
            self.set_frame(self._t * self.fps)
        self.img.add_updater(upd)
        return self

    def freeze(self):
        self.img.clear_updaters()
        return self

    # -- geometry --------------------------------------------------------
    def point(self, xc, yc):
        """Cell coordinate -> scene point."""
        left, right = self.img.get_left()[0], self.img.get_right()[0]
        bot, top = self.img.get_bottom()[1], self.img.get_top()[1]
        fx = (xc - self.x0) / (self.x1 - self.x0)
        fy = (yc - self.y0) / (self.y1 - self.y0)
        return np.array([left + fx * (right - left), bot + fy * (top - bot), 0.0])

    def cell(self):
        """Size of one simulation cell, in scene units."""
        return self.img.width / (self.x1 - self.x0)

    def obstacle(self, m, **kw):
        """A crisp circle sitting exactly where the solver's disc sits."""
        style = dict(radius=m["r"] * self.cell(), fill_opacity=1.0,
                     fill_color=T.BG, stroke_color=T.RULE, stroke_width=2.0)
        style.update(kw)
        return Circle(**style).move_to(self.point(m["cx"], m["cy"]))


# --------------------------------------------------------------------------
# typography helpers
# --------------------------------------------------------------------------
def body(txt, size=T.T_BODY, color=T.INK, weight="NORMAL", width=11.4):
    t = Text(txt, font_size=size * 100, color=color, weight=weight,
             line_spacing=0.85)
    if t.width > width:
        t.scale(width / t.width)
    return t


def title(txt, size=T.T_H1, color=T.INK, weight="MEDIUM", width=12.6):
    return body(txt, size=size, color=color, weight=weight, width=width)


def kicker(txt, color=T.INK_SOFT):
    """Small all-caps label with generous tracking."""
    t = Text(" ".join(txt.upper()), font_size=T.T_SMALL * 78,
             color=color, weight="MEDIUM")
    return t


class Caption:
    """The bottom line of narration. Cross-fades between statements."""

    def __init__(self, scene, y=-3.18, width=11.4, size=T.T_BODY):
        self.scene, self.y, self.width, self.size = scene, y, width, size
        self.cur = None

    def _make(self, txt, color, weight):
        t = body(txt, size=self.size, color=color, weight=weight, width=self.width)
        return t.move_to([0, self.y + t.height / 2 - 0.2, 0])

    def say(self, txt, hold=1.9, color=T.INK, weight="NORMAL", fade=0.5):
        new = self._make(txt, color, weight)
        anims = [FadeIn(new, shift=UP * 0.16)]
        if self.cur is not None:
            anims.append(FadeOut(self.cur, shift=UP * 0.16))
        self.scene.play(*anims, run_time=fade)
        self.cur = new
        if hold:
            self.scene.wait(hold)
        return new

    def clear(self, fade=0.45):
        if self.cur is not None:
            self.scene.play(FadeOut(self.cur, shift=UP * 0.16), run_time=fade)
            self.cur = None


# --------------------------------------------------------------------------
# the equation, built once so every scene colours it identically
# --------------------------------------------------------------------------
EQ_PARTS = [
    (r"\rho", T.INK),
    (r"\Bigl(", T.INK_SOFT),
    (r"\frac{\partial \vec v}{\partial t}", T.C_TIME),
    (r"+", T.INK_SOFT),
    (r"(\vec v\cdot\nabla)\,\vec v", T.C_ADVECT),
    (r"\Bigr)", T.INK_SOFT),
    (r"=", T.INK),
    (r"-\,\nabla p", T.C_PRESS),
    (r"+", T.INK_SOFT),
    (r"\mu\,\nabla^{2}\vec v", T.C_VISC),
    (r"+", T.INK_SOFT),
    (r"\vec f", T.C_FORCE),
]

# indices into the MathTex above, by name
IDX = {"rho": 0, "lp": 1, "dt": 2, "plus1": 3, "adv": 4, "rp": 5,
       "eq": 6, "press": 7, "plus2": 8, "visc": 9, "plus3": 10, "force": 11}


def full_equation(font_size=52, dim=False):
    eq = MathTex(*[p for p, _ in EQ_PARTS], font_size=font_size)
    for i, (_, c) in enumerate(EQ_PARTS):
        eq[i].set_color(T.INK_SOFT if dim else c)
    return eq


def div_equation(font_size=44, dim=False):
    eq = MathTex(r"\nabla\cdot\vec v", "=", "0", font_size=font_size)
    eq[0].set_color(T.INK_SOFT if dim else T.C_DIV)
    eq[1].set_color(T.INK_SOFT)
    eq[2].set_color(T.INK_SOFT if dim else T.C_DIV)
    return eq


def spotlight(eq, keep, others_opacity=0.22):
    """Return animations that dim every part of `eq` except the named ones."""
    keep = {IDX[k] for k in keep}
    anims = []
    for i, (_, c) in enumerate(EQ_PARTS):
        if i in keep:
            anims.append(eq[i].animate.set_color(c).set_opacity(1.0))
        else:
            anims.append(eq[i].animate.set_opacity(others_opacity))
    return anims


# --------------------------------------------------------------------------
# small drawing utilities
# --------------------------------------------------------------------------
def rule(width=11.0, color=T.RULE, stroke=1.6):
    return Line(LEFT * width / 2, RIGHT * width / 2, stroke_width=stroke, color=color)


def card(mob, pad=0.38, color=T.BG_SOFT, stroke=T.RULE, radius=0.18, opacity=1.0):
    box = RoundedRectangle(
        corner_radius=radius,
        width=mob.width + 2 * pad, height=mob.height + 2 * pad,
        fill_color=color, fill_opacity=opacity, stroke_color=stroke, stroke_width=1.4,
    ).move_to(mob)
    return VGroup(box, mob)


def arrow_field(func, x_range, y_range, length=0.42, color=T.C_TIME,
                stroke=3.0, max_tip=0.16, opacity=1.0):
    """A tidy grid of little arrows sampling a velocity function."""
    g = VGroup()
    for x in x_range:
        for y in y_range:
            vx, vy = func(x, y)
            m = np.hypot(vx, vy)
            if m < 1e-6:
                continue
            d = np.array([vx, vy, 0.0]) / m
            s = length * min(1.0, m)
            a = Arrow(
                start=np.array([x, y, 0.0]) - d * s / 2,
                end=np.array([x, y, 0.0]) + d * s / 2,
                buff=0, stroke_width=stroke, color=color,
                max_tip_length_to_length_ratio=0.38, tip_length=min(max_tip, s * 0.42),
            )
            a.set_opacity(opacity)
            g.add(a)
    return g


class ParcelTrail(VGroup):
    """A dot that rides a velocity field and leaves a fading tail behind it."""

    def __init__(self, pos, vel_func, color=T.C_ADVECT, radius=0.075,
                 tail=26, speed=1.0, bounds=None):
        super().__init__()
        self.vel_func, self.speed, self.bounds = vel_func, speed, bounds
        self.pos = np.array([pos[0], pos[1], 0.0], dtype=float)
        self.history = [self.pos.copy()]
        self.tail_len = tail
        self.dot = Dot(self.pos, radius=radius, color=color)
        self.trail = VMobject(stroke_color=color, stroke_width=3.2, stroke_opacity=0.5)
        self.trail.set_points_as_corners([self.pos, self.pos])
        self.add(self.trail, self.dot)

    def advance(self, dt):
        vx, vy = self.vel_func(self.pos[0], self.pos[1])
        self.pos = self.pos + np.array([vx, vy, 0.0]) * dt * self.speed
        if self.bounds is not None:
            x0, x1, y0, y1 = self.bounds
            if not (x0 <= self.pos[0] <= x1 and y0 <= self.pos[1] <= y1):
                self.pos = np.array(self.history[0])
                self.history = [self.pos.copy()]
        self.history.append(self.pos.copy())
        self.history = self.history[-self.tail_len:]
        self.dot.move_to(self.pos)
        if len(self.history) > 1:
            self.trail.set_points_as_corners(self.history)

    def updater(self):
        return lambda m, dt: self.advance(dt)
