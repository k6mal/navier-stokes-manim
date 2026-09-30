"""Act IV - chaos, the open question, and why any of it matters."""

from __future__ import annotations
import numpy as np
from manim import *

import theme as T
from common import (Caption, FieldMovie, body, card, div_equation, frames,
                    full_equation, kicker, meta, rule, title)
from scenes_intro import section


def swirl_glyph(radius, color, turns=1.55, width=3.0, clockwise=False):
    """A little curl of arc with an arrowhead: 'something spinning, this big'."""
    a = Arc(radius=radius, start_angle=0.0,
            angle=(-1 if clockwise else 1) * turns * PI,
            stroke_color=color, stroke_width=width)
    a.add_tip(tip_length=min(0.22, radius * 0.75))
    return a


# ==========================================================================
class S09Chaos(Scene):
    """Two runs of the same laws, split by a hair."""

    def construct(self):
        cap = Caption(self, y=-3.4)
        section(self, "part eight", "Two futures")

        m = meta("plume")
        trace = m["separation"]
        eps_pct = m["eps"] * 100.0

        PH, PX = 4.9, 2.45
        # 660 cached frames stretched over the ~46 s the panels are up,
        # played once only: the whole point is that it never repeats
        left = FieldMovie(frames("plume", "a"), T.FLAME_LUT, fps=14.2, loop=False)
        right = FieldMovie(frames("plume", "b"), T.FLAME_LUT, fps=14.2, loop=False)
        for mv, x in ((left, -PX), (right, PX)):
            mv.img.height = PH
            mv.img.move_to([x, 0.35, 0])
            mv.img.set_opacity(0.0)
            self.add(mv)

        la = body("simulation A", size=0.28, color=T.INK_SOFT).move_to([-PX, 3.2, 0])
        lb = body("simulation B", size=0.28, color=T.INK_SOFT).move_to([PX, 3.2, 0])

        left.play(rate=1.0)
        right.play(rate=1.0)
        self.play(left.img.animate.set_opacity(1.0), right.img.animate.set_opacity(1.0),
                  FadeIn(la), FadeIn(lb), run_time=1.6)
        cap.say("Two simulations of hot smoke rising. Watch them side by side.", hold=2.2)
        cap.say("Same equations. Same computer. Same everything —", hold=2.0)

        diff_lab = body("difference between them", size=0.26, color=T.INK_SOFT)
        diff_num = DecimalNumber(0.0, num_decimal_places=2, unit=r"\%",
                                 font_size=44, color=T.C_HILITE)
        readout = VGroup(diff_lab, diff_num).arrange(RIGHT, buff=0.34)
        readout.move_to([0.0, -2.65, 0])

        def follow(d):
            i = int(np.clip(left._i, 0, len(trace) - 1))
            d.set_value(min(trace[i], 1.0) * 100.0)
        diff_num.add_updater(follow)

        self.play(FadeIn(readout, shift=UP * 0.15), run_time=0.8)
        cap.say(f"— except that one was started {eps_pct:.2f}% warmer at the source.",
                hold=2.8)
        cap.say(f"One part in {int(round(1/m['eps'])):,}. Less than you could ever "
                f"measure in a real room.", hold=3.0)

        # the beats below are placed against the measured separation curve:
        # ~6% here, ~10% at "look again", ~14% at "not the same any more"
        cap.say("For now, the two are the same picture.", hold=3.0)
        self.wait(5.0)
        cap.say("Look again.", hold=2.5)
        self.wait(5.0)
        cap.say("They are not the same any more.", hold=3.0, weight="MEDIUM",
                color=T.C_HILITE)
        self.wait(4.0)

        diff_num.clear_updaters()
        cap.say("Nothing random happened. Every single step was fixed in advance.",
                hold=2.8)
        cap.say("The difference simply grew — doubling, and doubling, and doubling.",
                hold=3.0)
        cap.say("This is chaos. It is the reason a forecast is good for days, and "
                "worthless for months.", hold=3.4, weight="MEDIUM")
        self.wait(1.0)
        self.play(left.img.animate.set_opacity(0.0), right.img.animate.set_opacity(0.0),
                  FadeOut(VGroup(la, lb, readout)), run_time=1.3)
        left.freeze(); right.freeze()
        cap.clear()
        self.wait(0.3)


# ==========================================================================
class S10Prize(Scene):
    """The bit nobody can do."""

    def construct(self):
        cap = Caption(self)
        section(self, "part nine", "The million-dollar question")

        # ---- the cascade -------------------------------------------------
        cap.say("Look at what a big swirl does when it is left alone.", hold=1.8)
        # one swirl, then two, then four: a branching ladder down the scales
        rows_spec = [(1, 1.05, 2.45, 0.0), (2, 0.60, 0.95, 1.85),
                     (4, 0.34, -0.30, 3.45), (8, 0.19, -1.25, 4.45),
                     (16, 0.105, -1.95, 4.95)]
        rows, links, centres = VGroup(), VGroup(), []
        for k, (n, r, y, spread) in enumerate(rows_spec):
            xs = np.linspace(-spread, spread, n) if n > 1 else np.array([0.0])
            row = VGroup()
            here = []
            for i, x in enumerate(xs):
                row.add(swirl_glyph(r, T.C_ADVECT, width=max(1.2, 3.4 * r),
                                    clockwise=bool(i % 2)).move_to([x, y, 0]))
                here.append(np.array([x, y, 0.0]))
            rows.add(row)
            if k > 0:
                lk = VGroup()
                for i, c in enumerate(here):
                    par = centres[i // 2]
                    lk.add(Line(par + DOWN * rows_spec[k - 1][1] * 0.55,
                                c + UP * r * 0.9, color=T.C_ADVECT,
                                stroke_width=1.2, stroke_opacity=0.28))
                links.add(lk)
            centres = here

        self.play(FadeIn(rows[0], scale=0.85), run_time=0.9)
        self.play(Rotate(rows[0], PI * 0.9), run_time=1.6, rate_func=linear)
        cap.say("It buckles, and breaks into smaller ones.", hold=1.4)
        for k in range(1, len(rows)):
            self.play(FadeIn(links[k - 1]),
                      LaggedStart(*[FadeIn(s, scale=0.7) for s in rows[k]],
                                  lag_ratio=0.06), run_time=0.85)
        self.wait(0.8)

        dots = body(". . .", size=0.5, color=T.INK_SOFT).move_to([0, -2.72, 0])
        self.play(FadeIn(dots), run_time=0.5)
        cap.say("Each swirl hands its energy to smaller swirls. Down and down.",
                hold=2.6)
        cap.say("At the very bottom, friction finally turns the motion into warmth.",
                hold=2.6)
        self.play(FadeOut(rows), FadeOut(links), FadeOut(dots), run_time=0.9)

        # ---- the question --------------------------------------------------
        q = body("Does that ladder always have a bottom?", size=T.T_H1,
                 color=T.INK, weight="MEDIUM").move_to(UP * 1.4)
        self.play(FadeIn(q, shift=UP * 0.2), run_time=1.0)
        self.wait(2.2)

        sub = body("Could a swirl become infinitely small\nand infinitely fast — "
                   "in a finite amount of time?", size=T.T_H2, color=T.C_ADVECT)
        sub.move_to(DOWN * 0.45)
        self.play(FadeIn(sub, shift=UP * 0.15), run_time=1.0)
        cap.say("If it could, the equation would hand back infinity.", hold=2.6)

        word = body("a singularity", size=T.T_H2, color=T.C_HILITE,
                    weight="MEDIUM").move_to(DOWN * 2.1)
        self.play(FadeIn(word, shift=UP * 0.15), run_time=0.8)
        cap.say("And at that instant it would stop describing anything at all.",
                hold=2.8)
        self.play(FadeOut(VGroup(q, sub, word)), run_time=0.9)
        cap.clear(0.4)

        # ---- the honest caveat ---------------------------------------------
        flat = VGroup(
            body("In two dimensions", size=T.T_H2, color=T.C_TIME, weight="MEDIUM"),
            body("flat, like every picture in this video —\nthis was settled long ago. "
                 "Nothing ever blows up.", size=T.T_BODY, color=T.INK_SOFT, width=9.0),
        ).arrange(DOWN, buff=0.34).move_to(UP * 1.5)
        self.play(FadeIn(flat, shift=UP * 0.18), run_time=1.0)
        self.wait(2.8)

        solid = VGroup(
            body("In three dimensions", size=T.T_H2, color=T.C_ADVECT, weight="MEDIUM"),
            body("the world you actually live in —\nnobody knows.",
                 size=T.T_BODY, color=T.INK_SOFT, width=9.0),
        ).arrange(DOWN, buff=0.34).move_to(DOWN * 1.35)
        self.play(FadeIn(solid, shift=UP * 0.18), run_time=1.0)
        cap.say("The extra dimension lets a vortex stretch itself thinner and spin "
                "faster. Nobody can prove where that stops.", hold=4.2)
        self.wait(0.8)
        self.play(FadeOut(flat), FadeOut(solid), run_time=0.9)
        cap.clear(0.4)

        # ---- the prize -------------------------------------------------------
        amount = Text("$1,000,000", font_size=88, color=T.C_PRESS, weight="MEDIUM")
        who = body("Clay Mathematics Institute", size=T.T_H2, color=T.INK)
        when = body("posed in 2000  ·  still unclaimed", size=T.T_BODY, color=T.INK_SOFT)
        prize = VGroup(amount, who, when).arrange(DOWN, buff=0.45)
        box = RoundedRectangle(corner_radius=0.22, width=prize.width + 2.4,
                               height=prize.height + 1.7, fill_color=T.BG_SOFT,
                               fill_opacity=1.0, stroke_color=T.RULE, stroke_width=1.6)
        grp = VGroup(box, prize.move_to(box)).move_to(UP * 0.35)
        self.play(FadeIn(box, scale=0.95), run_time=0.8)
        self.play(FadeIn(amount, shift=UP * 0.2), run_time=0.9)
        self.play(FadeIn(who), FadeIn(when), run_time=0.8)
        cap.say("One of seven problems chosen to define the century's unfinished "
                "mathematics. Six are still open.", hold=3.8)
        self.wait(1.2)
        cap.say("Prove that the equations always behave — or find the one case where "
                "they do not.", hold=3.4, weight="MEDIUM")
        self.wait(0.8)
        self.play(FadeOut(grp), run_time=0.9)
        cap.clear()
        self.wait(0.3)


# ==========================================================================
class S11Outro(Scene):
    """Where it all shows up, and a last look."""

    def construct(self):
        cap = Caption(self)
        m = meta("street")
        mv = FieldMovie(frames("street", "vort"), T.VORTICITY_LUT, fps=30,
                        start=100, loop=False)
        mv.img.height = 8.05          # overfills the frame: no letterbox bars
        mv.img.move_to(ORIGIN)
        mv.img.set_opacity(0.0)
        self.add(mv)
        mv.play(rate=0.7)

        items = ["every weather forecast", "every aeroplane wing",
                 "blood through a heart valve", "the currents under the ocean",
                 "gas falling into a new star"]
        lines = VGroup(*[body(s, size=T.T_H2, color=T.INK) for s in items])
        lines.arrange(DOWN, buff=0.5).move_to(UP * 0.35)

        self.play(mv.img.animate.set_opacity(0.2), run_time=1.6)
        for ln in lines:
            self.play(FadeIn(ln, shift=UP * 0.16), run_time=0.55)
            self.wait(0.75)
        self.wait(1.4)
        cap.say("All of it runs on the same handful of symbols.", hold=2.8,
                weight="MEDIUM")
        self.play(FadeOut(lines, shift=UP * 0.25), run_time=1.0)

        eq = full_equation(font_size=56).move_to(UP * 0.55)
        deq = div_equation(font_size=42).next_to(eq, DOWN, buff=0.75)
        self.play(mv.img.animate.set_opacity(0.32), FadeIn(eq, shift=UP * 0.2),
                  run_time=1.4)
        self.play(FadeIn(deq, shift=UP * 0.15), run_time=0.8)
        cap.say("Symbols we use every day, and have never quite proved.", hold=3.2)
        self.wait(1.0)
        self.play(FadeOut(eq), FadeOut(deq), run_time=1.0)
        cap.clear(0.6)

        self.play(mv.img.animate.set_opacity(0.95), run_time=1.6)
        self.wait(3.0)

        end = Text("N A V I E R – S T O K E S", font_size=56, weight="MEDIUM",
                   color=T.INK)
        if end.width > 11.0:
            end.scale(11.0 / end.width)
        ln = rule(width=end.width * 0.92)
        tag = body("still open", size=T.T_H2, color=T.INK_SOFT)
        endg = VGroup(end, ln, tag).arrange(DOWN, buff=0.45)
        shade = Rectangle(width=16, height=9, fill_color=T.BG, fill_opacity=0.0,
                          stroke_width=0)
        self.add(shade)
        self.play(shade.animate.set_opacity(0.72), FadeIn(endg, shift=UP * 0.15),
                  run_time=1.8)
        self.wait(2.6)
        self.play(FadeOut(endg), shade.animate.set_opacity(1.0),
                  mv.img.animate.set_opacity(0.0), run_time=2.0)
        mv.freeze()
        self.wait(0.6)
