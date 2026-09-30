"""Act I - the hook, the velocity field, and Newton's law in disguise."""

from __future__ import annotations
import numpy as np
from manim import *

import theme as T
from common import (Caption, FieldMovie, body, card, div_equation, frames,
                    full_equation, kicker, meta, rule, title)


# ==========================================================================
def section(scene, part, headline, hold=1.5):
    """A part title: small label, big line, hairline. Then it gets out of the way."""
    k = kicker(part, color=T.INK_SOFT)
    h = title(headline, size=T.T_H1, width=11.8)
    ln = rule(width=max(h.width, 5.0) + 1.2)
    g = VGroup(k, h, ln).arrange(DOWN, buff=0.42).move_to(ORIGIN)
    scene.play(FadeIn(k, shift=UP * 0.2), run_time=0.6)
    scene.play(FadeIn(h, shift=UP * 0.22), run_time=0.75)
    scene.play(Create(ln), run_time=0.6)
    scene.wait(hold)
    scene.play(FadeOut(g, shift=UP * 0.3), run_time=0.7)


# ==========================================================================
class S01Title(Scene):
    """Cold open: the answer first, the question afterwards."""

    def construct(self):
        m = meta("street")
        # crop the wide channel down to a 16:9 window so it can fill the frame
        half = int(m["ny"] * 16 / 9)
        x0 = int(m["cx"] - 0.22 * half)
        mv = FieldMovie(frames("street", "dye"), T.GLOW_LUT,
                        crop=(x0, x0 + half, 0, m["ny"]), fps=30, start=60,
                        loop=False)
        mv.img.height = 8.35
        mv.img.set_opacity(0.0)
        self.add(mv)
        mv.play(rate=0.85)

        self.play(mv.img.animate.set_opacity(0.30), run_time=2.6, rate_func=smooth)

        k = kicker("an introduction from zero", color=T.INK_SOFT)
        name = Text("N A V I E R – S T O K E S", font_size=74, weight="MEDIUM",
                    color=T.INK)
        if name.width > 12.4:
            name.scale(12.4 / name.width)
        ln = rule(width=name.width * 0.94, color=T.RULE, stroke=1.8)
        sub = body("the rule obeyed by every flowing thing", size=T.T_H2,
                   color=T.INK_SOFT)
        stack = VGroup(k, name, ln, sub).arrange(DOWN, buff=0.46).move_to(UP * 0.55)

        self.play(FadeIn(k, shift=UP * 0.2), run_time=0.8)
        self.play(LaggedStart(*[FadeIn(ch, shift=UP * 0.18) for ch in name],
                              lag_ratio=0.035), run_time=1.9)
        self.play(Create(ln), run_time=0.9)
        self.play(FadeIn(sub, shift=UP * 0.16), run_time=0.8)
        self.wait(2.2)

        eq = full_equation(font_size=40).to_edge(DOWN, buff=0.85)
        self.play(FadeIn(eq, shift=UP * 0.2), run_time=1.1)
        self.wait(3.0)

        self.play(FadeOut(stack, shift=UP * 0.25), FadeOut(eq, shift=DOWN * 0.2),
                  mv.img.animate.set_opacity(0.95), run_time=1.6)
        self.wait(2.4)
        self.play(mv.img.animate.set_opacity(0.0), run_time=1.4)
        mv.freeze()
        self.wait(0.3)


# ==========================================================================
class S02Field(Scene):
    """Drop the molecules. Keep the arrows."""

    def construct(self):
        cap = Caption(self)
        section(self, "part one", "What a fluid looks like to physics")

        # ---- a box of jittering molecules -----------------------------
        BOX_W, BOX_H = 8.4, 4.1
        box = RoundedRectangle(corner_radius=0.16, width=BOX_W, height=BOX_H,
                               stroke_color=T.RULE, stroke_width=2.0,
                               fill_color=T.BG_SOFT, fill_opacity=0.5)
        box.move_to(UP * 0.12)

        rng = np.random.default_rng(11)
        n = 265
        home = np.stack([rng.uniform(-BOX_W / 2 + .22, BOX_W / 2 - .22, n),
                         rng.uniform(-BOX_H / 2 + .22, BOX_H / 2 - .22, n)], axis=1)
        home += np.array([box.get_center()[0], box.get_center()[1]])
        freq = rng.uniform(1.1, 2.9, (n, 2))
        phase = rng.uniform(0, 2 * np.pi, (n, 2))
        dots = VGroup(*[Dot(np.array([p[0], p[1], 0.0]), radius=0.041,
                            color=T.C_TIME).set_opacity(0.9) for p in home])

        clock = ValueTracker(0.0)

        def jiggle(g):
            t = clock.get_value()
            off = 0.075 * np.sin(freq * t * 2 * np.pi + phase)
            for d, h, o in zip(g, home, off):
                d.move_to(np.array([h[0] + o[0], h[1] + o[1], 0.0]))

        self.play(Create(box), run_time=0.9)
        self.play(LaggedStart(*[FadeIn(d, scale=0.4) for d in dots],
                              lag_ratio=0.002), run_time=1.6)
        dots.add_updater(jiggle)
        self.add(dots)
        self.play(clock.animate.set_value(3.0), run_time=3.0, rate_func=linear)

        cap.say("A glass of water holds roughly ten trillion trillion molecules.", hold=2.2)
        cap.say("Nobody is going to follow them one at a time.", hold=2.0)
        cap.say("So physics asks a different question.", hold=1.6)

        # ---- one point, one arrow --------------------------------------
        self.play(clock.animate.set_value(5.0), run_time=2.0, rate_func=linear)
        dots.clear_updaters()

        probe = np.array([box.get_center()[0] - 1.6, box.get_center()[1] + 0.5, 0.0])
        ring = Circle(radius=0.22, stroke_color=T.C_HILITE, stroke_width=3.0).move_to(probe)
        self.play(Create(ring), dots.animate.set_opacity(0.28), run_time=0.8)
        cap.say("At this one spot, right now: which way is the fluid going, and how fast?",
                hold=2.2)

        one = Arrow(probe, probe + np.array([1.15, 0.42, 0.0]), buff=0,
                    color=T.C_HILITE, stroke_width=6, max_tip_length_to_length_ratio=0.3)
        self.play(GrowArrow(one), run_time=0.9)
        self.wait(1.2)

        # ---- ask it everywhere ------------------------------------------
        def swirl(x, y, t=0.0):
            """Two gentle counter-rotating eddies, drifting with t."""
            cx, cy = box.get_center()[0], box.get_center()[1]
            dx, dy = x - cx, y - cy
            a = np.array([-(dy - 0.5), (dx + 1.9 + 0.45 * np.sin(t))])
            b = np.array([(dy + 0.7), -(dx - 1.9 - 0.45 * np.sin(t))])
            v = 0.55 * a / (1 + 0.16 * (dx + 1.9) ** 2 + 0.16 * (dy - 0.5) ** 2) \
                + 0.55 * b / (1 + 0.16 * (dx - 1.9) ** 2 + 0.16 * (dy + 0.7) ** 2)
            return float(v[0]), float(v[1])

        xs = np.linspace(box.get_left()[0] + 0.42, box.get_right()[0] - 0.42, 13)
        ys = np.linspace(box.get_bottom()[1] + 0.38, box.get_top()[1] - 0.38, 7)

        def make_field(t, color=T.C_TIME, opacity=1.0):
            g = VGroup()
            for x in xs:
                for y in ys:
                    vx, vy = swirl(x, y, t)
                    mag = np.hypot(vx, vy)
                    d = np.array([vx, vy, 0.0]) / max(mag, 1e-9)
                    s = 0.20 + 0.30 * min(mag, 1.4) / 1.4
                    p = np.array([x, y, 0.0])
                    g.add(Arrow(p - d * s, p + d * s, buff=0, color=color,
                                stroke_width=3.4, tip_length=0.13,
                                max_tip_length_to_length_ratio=0.42).set_opacity(opacity))
            return g

        field = make_field(0.0)
        cap.say("Ask it everywhere.", hold=0.9)
        self.play(FadeOut(dots), FadeOut(one), FadeOut(ring),
                  LaggedStart(*[GrowArrow(a) for a in field], lag_ratio=0.006),
                  run_time=2.4)
        self.wait(0.6)

        cap.say("That picture is the whole state of the fluid. It is called a velocity field.",
                hold=2.3)

        lab = MathTex(r"\vec v(x,\,y,\,t)", font_size=54, color=T.C_TIME)
        gloss = body("the arrow at position (x, y), at time t", size=T.T_SMALL,
                     color=T.INK_SOFT)
        labg = VGroup(lab, gloss).arrange(DOWN, buff=0.28)
        labg.next_to(box, UP, buff=0.42)
        self.play(FadeIn(labg, shift=UP * 0.18), run_time=0.9)
        self.wait(1.6)

        # ---- and it changes ---------------------------------------------
        cap.say("And it changes. Every instant, every arrow, everywhere at once.", hold=1.4)
        for t in (1.5, 3.0, 4.6):
            self.play(Transform(field, make_field(t)), run_time=2.0, rate_func=smooth)
        self.wait(0.5)

        cap.say("Navier–Stokes is the rule that decides what the next picture is.",
                hold=2.6, weight="MEDIUM")
        self.play(FadeOut(VGroup(box, field, labg)), run_time=0.9)
        cap.clear()
        self.wait(0.3)


# ==========================================================================
class S03Newton(Scene):
    """It is F = ma, applied to a blob that will not hold still."""

    def construct(self):
        cap = Caption(self)
        section(self, "part two", "You already know the physics")

        fma = MathTex("F", "=", "m", "a", font_size=110).move_to(UP * 0.7)
        fma[0].set_color(T.C_FORCE)
        fma[2].set_color(T.INK)
        fma[3].set_color(T.C_TIME)
        self.play(FadeIn(fma, scale=0.92), run_time=1.0)
        cap.say("Newton, 1687. Push a thing, and it speeds up.", hold=1.9)

        # a block getting shoved
        ground = Line(LEFT * 5.8 + DOWN * 2.1, RIGHT * 5.8 + DOWN * 2.1,
                      color=T.RULE, stroke_width=2)
        blk = RoundedRectangle(corner_radius=0.12, width=1.25, height=1.25,
                               fill_color=T.BG_SOFT, fill_opacity=1,
                               stroke_color=T.RULE, stroke_width=2)
        blk.move_to(LEFT * 4.3 + DOWN * 1.42)
        push = Arrow(LEFT * 6.0 + DOWN * 1.42, LEFT * 4.95 + DOWN * 1.42, buff=0,
                     color=T.C_FORCE, stroke_width=8, max_tip_length_to_length_ratio=0.32)
        push.add_updater(lambda a: a.next_to(blk, LEFT, buff=0.08))
        self.play(Create(ground), FadeIn(blk), GrowArrow(push), run_time=0.8)
        self.play(blk.animate.shift(RIGHT * 8.6), run_time=2.6,
                  rate_func=lambda t: t ** 2)
        push.clear_updaters()
        self.play(FadeOut(blk), FadeOut(push), FadeOut(ground), run_time=0.6)

        cap.say("Push harder and it speeds up more. Make it heavier and it speeds up less.",
                hold=2.2)

        # rearrange to mass x acceleration = the pushes
        fma2 = MathTex("m", "a", "=", "F", font_size=110).move_to(UP * 0.95)
        fma2[0].set_color(T.INK); fma2[1].set_color(T.C_TIME); fma2[3].set_color(T.C_FORCE)
        self.play(TransformMatchingTex(fma, fma2), run_time=1.2)

        # labels sit on their own rail, joined to their symbol by a hairline
        spec = [(fma2[0], "mass", T.INK_SOFT, -4.1),
                (fma2[1], "acceleration", T.C_TIME, -0.9),
                (fma2[3], "the sum of the pushes", T.C_FORCE, 3.6)]
        tags = VGroup()
        for sym, txt, col, xpos in spec:
            w = body(txt, size=T.T_SMALL, color=col, width=4.0)
            w.move_to([xpos, -0.75, 0])
            leg = Line(sym.get_bottom() + DOWN * 0.1, w.get_top() + UP * 0.12,
                       color=T.RULE, stroke_width=1.4)
            tags.add(VGroup(leg, w))
        self.play(LaggedStart(*[FadeIn(t, shift=UP * 0.12) for t in tags],
                              lag_ratio=0.25), run_time=1.3)
        cap.say("Now stop applying it to a block, and apply it to a thimbleful of water.",
                hold=2.4)

        self.play(FadeOut(tags), fma2.animate.scale(0.5).to_edge(UP, buff=0.7),
                  run_time=1.2)
        cap.clear()

        # ---- the three swaps --------------------------------------------
        rows = [
            (r"m \;\longrightarrow\; \rho",
             "mass becomes density — how much stuff is packed into the blob", T.INK),
            (r"a \;\longrightarrow\; \frac{\partial \vec v}{\partial t} + (\vec v\cdot\nabla)\,\vec v",
             "acceleration becomes how the blob's own arrow changes", T.C_TIME),
            (r"F \;\longrightarrow\; -\nabla p \;+\; \mu\nabla^{2}\vec v \;+\; \vec f",
             "the pushes become pressure, friction and gravity", T.C_FORCE),
        ]
        blocks = VGroup()
        for tex, words_, col in rows:
            mt = MathTex(tex, font_size=44, color=col)
            wd = body(words_, size=T.T_SMALL, color=T.INK_SOFT, width=8.6)
            blocks.add(VGroup(mt, wd).arrange(DOWN, buff=0.26))
        blocks.arrange(DOWN, buff=0.62).move_to(DOWN * 0.55)

        for blk_ in blocks:
            self.play(FadeIn(blk_, shift=UP * 0.18), run_time=0.8)
            self.wait(1.45)
        self.wait(0.9)
        group = blocks

        # ---- and there it is ---------------------------------------------
        eq = full_equation(font_size=54).move_to(DOWN * 0.3)
        self.play(FadeOut(group, shift=DOWN * 0.3), FadeOut(fma2, shift=UP * 0.2),
                  run_time=0.9)
        self.play(FadeIn(eq, shift=UP * 0.25), run_time=1.4)
        self.wait(1.4)

        deq = div_equation(font_size=44).next_to(eq, DOWN, buff=0.85)
        self.play(FadeIn(deq, shift=UP * 0.18), run_time=0.9)
        cap.say("That is the whole thing. Everything that follows is just reading it out loud.",
                hold=2.8, weight="MEDIUM")
        self.play(FadeOut(eq), FadeOut(deq), run_time=0.9)
        cap.clear()
        self.wait(0.3)
