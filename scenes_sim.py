"""Act III - turning the symbols into arithmetic, and watching the answer move."""

from __future__ import annotations
import numpy as np
from manim import *

import theme as T
from common import (Caption, FieldMovie, body, card, div_equation, frames,
                    full_equation, kicker, meta, rule, title)
from scenes_intro import section


def step_card(n, name, detail, color):
    num = Text(n, font_size=26, color=color, weight="BOLD")
    ttl = Text(name, font_size=34, color=T.INK, weight="MEDIUM")
    det = body(detail, size=0.24, color=T.INK_SOFT, width=3.0)
    inner = VGroup(num, ttl, det).arrange(DOWN, buff=0.22)
    box = RoundedRectangle(corner_radius=0.16, width=3.55, height=2.25,
                           fill_color=T.BG_SOFT, fill_opacity=1.0,
                           stroke_color=T.RULE, stroke_width=1.6).move_to(inner)
    return VGroup(box, inner)


# ==========================================================================
class S07Solve(Scene):
    """No formula exists, so we grind it out one small step at a time."""

    def construct(self):
        cap = Caption(self)
        section(self, "part six", "Making it actually move")

        # ---- there is no formula ---------------------------------------
        quad = MathTex(r"ax^{2}+bx+c=0", font_size=48, color=T.INK_SOFT)
        sol = MathTex(r"x=\frac{-b\pm\sqrt{b^{2}-4ac}}{2a}", font_size=48, color=T.INK)
        tick = Text("a formula has existed for centuries", font_size=26,
                    color=T.C_FORCE)
        left = VGroup(quad, sol, tick).arrange(DOWN, buff=0.42).move_to(UP * 1.35)
        self.play(FadeIn(quad, shift=UP * 0.15), run_time=0.7)
        self.play(FadeIn(sol, shift=UP * 0.15), run_time=0.8)
        self.play(FadeIn(tick), run_time=0.5)
        cap.say("Some equations hand you a formula. You put the numbers in, "
                "the answer comes out.", hold=2.3)

        eqs = full_equation(font_size=44)
        qm = Text("no such formula is known", font_size=26, color=T.C_ADVECT)
        right = VGroup(eqs, qm).arrange(DOWN, buff=0.5).move_to(DOWN * 1.55)
        self.play(FadeIn(eqs, shift=UP * 0.15), run_time=0.9)
        self.play(FadeIn(qm), run_time=0.6)
        cap.say("This one does not. For almost any real situation, nobody can write "
                "the answer down.", hold=2.8, color=T.C_ADVECT)
        cap.say("So we stop looking for a formula, and do arithmetic instead.",
                hold=2.0, weight="MEDIUM")
        self.play(FadeOut(left), FadeOut(right), run_time=0.8)

        # ---- chop space into boxes -------------------------------------
        m = meta("street")
        GW, GH = 11.6, 4.85
        frame = Rectangle(width=GW, height=GH, stroke_color=T.RULE,
                          stroke_width=2.0).move_to(UP * 0.45)
        NCX, NCY = 24, 10
        grid = VGroup()
        for i in range(1, NCX):
            x = frame.get_left()[0] + GW * i / NCX
            grid.add(Line([x, frame.get_bottom()[1], 0], [x, frame.get_top()[1], 0],
                          stroke_color=T.RULE, stroke_width=1.3, stroke_opacity=0.8))
        for j in range(1, NCY):
            y = frame.get_bottom()[1] + GH * j / NCY
            grid.add(Line([frame.get_left()[0], y, 0], [frame.get_right()[0], y, 0],
                          stroke_color=T.RULE, stroke_width=1.3, stroke_opacity=0.8))

        self.play(Create(frame), run_time=0.8)
        self.play(LaggedStart(*[Create(l) for l in grid], lag_ratio=0.012), run_time=1.8)
        cap.say("Chop the space into little boxes.", hold=1.4)

        cyl = Circle(radius=0.52, fill_color=T.BG, fill_opacity=1,
                     stroke_color=T.INK_SOFT, stroke_width=2.2)
        cyl.move_to(frame.get_left() + RIGHT * GW * 0.24 + UP * 0.0)
        cyl.move_to([frame.get_left()[0] + GW * 0.24, frame.get_center()[1], 0])

        cells = VGroup()
        for i in range(NCX):
            for j in range(NCY):
                x = frame.get_left()[0] + GW * (i + 0.5) / NCX
                y = frame.get_bottom()[1] + GH * (j + 0.5) / NCY
                p = np.array([x, y, 0.0])
                if np.linalg.norm(p - cyl.get_center()) < 0.62:
                    continue
                dx = x - cyl.get_center()[0]
                dy = y - cyl.get_center()[1]
                r2 = max(dx * dx + dy * dy, 0.5)
                vx = 1.0 - 0.55 * (dx * dx - dy * dy) / (r2 * r2) * 1.4
                vy = -1.1 * dx * dy / (r2 * r2) * 1.4
                mag = np.hypot(vx, vy)
                d = np.array([vx, vy, 0.0]) / max(mag, 1e-9)
                s = 0.105 + 0.095 * min(mag, 1.6)
                cells.add(Arrow(p - d * s, p + d * s, buff=0, color=T.C_TIME,
                                stroke_width=2.9, tip_length=0.10,
                                max_tip_length_to_length_ratio=0.5).set_opacity(0.85))

        self.play(FadeIn(cyl), run_time=0.5)
        self.play(LaggedStart(*[GrowArrow(a) for a in cells], lag_ratio=0.004),
                  run_time=2.2)
        n_cells = m["nx"] * m["ny"]
        cap.say(f"Keep one arrow in each. The simulation you are about to see uses "
                f"{n_cells:,} of them.", hold=2.8)
        self.play(FadeOut(VGroup(frame, grid, cells, cyl)), run_time=0.9)

        # ---- the loop ---------------------------------------------------
        cards = VGroup(
            step_card("STEP 1", "CARRY", "slide everything along the arrows", T.C_ADVECT),
            step_card("STEP 2", "PUSH", "add pressure, friction and gravity", T.C_PRESS),
            step_card("STEP 3", "FIX", "squeeze nothing: undo any compression", T.C_DIV),
        ).arrange(RIGHT, buff=0.7).move_to(UP * 0.75)

        arrows = VGroup(*[
            Arrow(cards[i].get_right() + RIGHT * 0.08, cards[i + 1].get_left() - RIGHT * 0.08,
                  buff=0.0, color=T.RULE, stroke_width=3.5,
                  max_tip_length_to_length_ratio=0.35)
            for i in range(2)])
        back = VMobject(stroke_color=T.RULE, stroke_width=3.0)
        back.set_points_smoothly([
            cards[2].get_bottom() + DOWN * 0.1,
            cards[2].get_bottom() + DOWN * 0.95,
            cards[0].get_bottom() + DOWN * 0.95,
            cards[0].get_bottom() + DOWN * 0.1])
        tip = Triangle(fill_color=T.RULE, fill_opacity=1, stroke_width=0).scale(0.11)
        tip.rotate(PI / 2).move_to(cards[0].get_bottom() + DOWN * 0.18)
        clocklbl = body("then move the clock on a little, and go round again",
                        size=0.27, color=T.INK_SOFT).move_to(DOWN * 2.2)

        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.2) for c in cards],
                              lag_ratio=0.25), run_time=1.6)
        self.play(*[GrowArrow(a) for a in arrows], run_time=0.7)
        self.play(Create(back), FadeIn(tip), FadeIn(clocklbl), run_time=1.0)
        cap.say("Three moves, over and over.", hold=1.6)

        for cycle in range(3):
            for i, c in enumerate(cards):
                glow = SurroundingRectangle(c, color=[T.C_ADVECT, T.C_PRESS, T.C_DIV][i],
                                            buff=0.02, stroke_width=3.0, corner_radius=0.17)
                self.play(Create(glow), run_time=0.22)
                self.play(FadeOut(glow), run_time=0.18)
        cap.say("Do it thousands of times over, and the fluid moves.", hold=2.2)
        self.play(FadeOut(VGroup(cards, arrows, back, tip, clocklbl)), run_time=0.9)
        cap.clear(0.3)

        # ---- the real thing ---------------------------------------------
        mv = FieldMovie(frames("street", "dye"), T.GLOW_LUT, fps=30, loop=False)
        mv.img.width = 13.7
        mv.img.move_to(UP * 0.25)
        obst = mv.obstacle(m, fill_color=T.BG, stroke_color=T.INK_SOFT, stroke_width=2.0)
        mv.img.set_opacity(0.0)
        self.add(mv, obst)
        obst.set_opacity(0.0)
        mv.play(rate=1.0)
        self.play(mv.img.animate.set_opacity(1.0), obst.animate.set_opacity(1.0),
                  run_time=1.8)
        cap.say("Here it is. Smoke blown from the left, past a round post.", hold=3.2)
        self.wait(3.0)
        cap.say("Nothing in this picture was drawn by hand.", hold=3.0, weight="MEDIUM")
        self.wait(3.5)
        cap.say("Every curl is the equation, worked out one small step at a time.",
                hold=3.4)
        self.wait(2.5)

        # switch to the spin view
        mv2 = FieldMovie(frames("street", "vort"), T.VORTICITY_LUT, fps=30,
                         loop=False, start=int(mv._t * mv.fps))
        mv2.img.width = 13.7
        mv2.img.move_to(UP * 0.25)
        mv2.img.set_opacity(0.0)
        self.add(mv2)
        mv2.play(rate=1.0)
        obst.set_z_index(5)
        mv2.img.set_z_index(1)
        cap.say("The same flow again, coloured by which way it is turning.", hold=0.9)
        self.play(mv2.img.animate.set_opacity(1.0), run_time=1.6)
        self.remove(mv)
        mv.freeze()
        self.wait(2.6)

        # omega = dv/dx - du/dy, so POSITIVE is anticlockwise, and signed_to_u8
        # sends positive to the warm half of the map.  Sample the map itself at a
        # typical vortex strength rather than hard-coding its extreme ends, which
        # only ever show up in the thin layer on the cylinder surface.
        def swatch(signed):
            i = int(np.clip(signed * 0.5 + 0.5, 0, 1) * 255)
            return rgb_to_color(T.VORTICITY_LUT[i] / 255.0)

        legend = VGroup(
            VGroup(Dot(radius=0.11, color=swatch(+0.45)),
                   body("anticlockwise", size=0.24, color=T.INK_SOFT)).arrange(RIGHT, buff=0.22),
            VGroup(Dot(radius=0.11, color=swatch(-0.45)),
                   body("clockwise", size=0.24, color=T.INK_SOFT)).arrange(RIGHT, buff=0.22),
        ).arrange(RIGHT, buff=0.85).move_to(UP * 3.45)
        self.play(FadeIn(legend, shift=DOWN * 0.1), run_time=0.8)
        cap.say("The post sheds a spinning blob, first from one side, then the other, "
                "for ever.", hold=3.4)
        self.wait(2.0)

        name = body("a von Kármán vortex street", size=T.T_H2, color=T.C_HILITE,
                    weight="MEDIUM").move_to(UP * 3.42)
        self.play(FadeOut(legend), run_time=0.5)
        self.play(FadeIn(name, shift=DOWN * 0.12), run_time=0.9)
        cap.say("It has a name. And you can find the very same pattern in satellite "
                "photographs of cloud behind an island.", hold=4.0)
        self.wait(2.0)
        self.play(FadeOut(name), FadeOut(obst), mv2.img.animate.set_opacity(0.0),
                  run_time=1.4)
        mv2.freeze()
        cap.clear()
        self.wait(0.3)


# ==========================================================================
class S08Reynolds(Scene):
    """One dial, three different worlds."""

    def construct(self):
        cap = Caption(self, y=-3.45, width=12.2)
        section(self, "part seven", "One number changes everything")

        re = MathTex(r"\mathrm{Re}", "=", r"\frac{\rho\, v\, L}{\mu}",
                     font_size=70).move_to(UP * 1.35)
        re[0].set_color(T.C_HILITE)
        gloss = body("speed  ×  size  ÷  stickiness", size=T.T_H2, color=T.INK_SOFT)
        gloss.next_to(re, DOWN, buff=0.7)
        self.play(FadeIn(re, shift=UP * 0.2), run_time=1.0)
        cap.say("Hidden inside the equation is a single dial.", hold=1.8)
        self.play(FadeIn(gloss, shift=UP * 0.15), run_time=0.8)
        cap.say("It goes by Reynolds number: how fast, how big, how thick.", hold=2.4)
        cap.say("It is the only thing the fluid really cares about.", hold=2.2)
        self.play(FadeOut(re), FadeOut(gloss), run_time=0.8)

        # ---- three panels, same physical clock --------------------------
        m = meta("reynolds")
        CROP = (52, 612, 24, 126)
        rows = [("syrup", "thick like syrup", 6), ("water", "water", 90),
                ("fast", "water, moving faster", 420)]
        PW = 9.15
        movies, labels, obsts = [], VGroup(), VGroup()
        for k, (name, human, Re) in enumerate(rows):
            # 560 frames over the ~36 s the panels are up, once through
            mv = FieldMovie(frames("reynolds", f"{name}_dye"), T.GLOW_LUT,
                            crop=CROP, fps=15.5, loop=False)
            mv.img.width = PW
            mv.img.move_to([2.1, 2.1 - k * 2.1, 0])
            ob = Circle(radius=m["r"] * mv.cell(), fill_color=T.BG, fill_opacity=1,
                        stroke_color=T.INK_SOFT, stroke_width=1.6)
            ob.move_to(mv.point(m["cx"], m["cy"]))
            lab = VGroup(
                body(human, size=0.28, color=T.INK, width=3.8),
                MathTex(rf"\mathrm{{Re}} \approx {Re}", font_size=34, color=T.C_HILITE),
            ).arrange(DOWN, buff=0.22)
            lab.move_to([-4.95, 2.1 - k * 2.1, 0])
            mv.img.set_opacity(0.0); ob.set_opacity(0.0)
            movies.append(mv); labels.add(lab); obsts.add(ob)
            self.add(mv, ob)
            mv.play(rate=1.0)

        self.play(*[mvv.img.animate.set_opacity(1.0) for mvv in movies],
                  *[o.animate.set_opacity(1.0) for o in obsts],
                  LaggedStart(*[FadeIn(l, shift=RIGHT * 0.2) for l in labels],
                              lag_ratio=0.2),
                  run_time=1.8)
        cap.say("Same post. Same equations. Same puffs of smoke, released on the "
                "same clock.", hold=3.4)
        self.wait(2.0)
        cap.say("Only the dial is different.", hold=2.6, weight="MEDIUM")
        self.wait(1.5)

        hl = SurroundingRectangle(movies[0].img, color=T.C_VISC, buff=0.07,
                                  stroke_width=2.4, corner_radius=0.06)
        self.play(Create(hl), run_time=0.6)
        cap.say("Thick and slow: the fluid slides round the post and closes up neatly "
                "behind it.", hold=3.4)
        self.play(Transform(hl, SurroundingRectangle(movies[1].img, color=T.C_ADVECT,
                                                     buff=0.07, stroke_width=2.4,
                                                     corner_radius=0.06)), run_time=0.8)
        cap.say("Thinner: it can no longer keep up, and starts letting go in lumps.",
                hold=3.4)
        self.play(Transform(hl, SurroundingRectangle(movies[2].img, color=T.C_HILITE,
                                                     buff=0.07, stroke_width=2.4,
                                                     corner_radius=0.06)), run_time=0.8)
        cap.say("Faster still: the lumps come quicker and start to break up.", hold=3.4)
        self.play(FadeOut(hl), run_time=0.6)

        cap.say("This is why a small model in a wind tunnel can stand in for a real "
                "aeroplane.", hold=3.2)
        cap.say("Match the number, and you match the flow.", hold=2.8, weight="MEDIUM")

        self.play(*[mvv.img.animate.set_opacity(0.0) for mvv in movies],
                  FadeOut(labels), FadeOut(obsts), run_time=1.3)
        for mvv in movies:
            mvv.freeze()
        cap.clear()
        self.wait(0.3)
