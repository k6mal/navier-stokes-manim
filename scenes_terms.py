"""Act II - reading the equation, one term at a time."""

from __future__ import annotations
import numpy as np
from manim import *

import theme as T
from common import (Caption, body, card, div_equation, full_equation, IDX,
                    kicker, rule, spotlight, title)
from scenes_intro import section


def term_card(symbol, name, color, font_size=64, width=5.4):
    """A big coloured symbol with its plain-English name underneath."""
    sym = MathTex(symbol, font_size=font_size, color=color)
    nm = body(name, size=T.T_SMALL, color=T.INK_SOFT, width=width)
    return VGroup(sym, nm).arrange(DOWN, buff=0.3)


# ==========================================================================
class S04Acceleration(Scene):
    """The left-hand side: what 'acceleration' means for something that flows."""

    def construct(self):
        cap = Caption(self)
        section(self, "part three", "The left side: acceleration")

        eq = full_equation(font_size=44).move_to(UP * 3.05)
        self.play(FadeIn(eq, shift=DOWN * 0.15), run_time=0.9)
        self.play(*spotlight(eq, ["rho", "lp", "dt", "plus1", "adv", "rp"]), run_time=0.8)
        self.wait(0.5)

        # ------------------------------------------------------ d v / d t
        self.play(*spotlight(eq, ["dt"]), run_time=0.8)
        tc = term_card(r"\frac{\partial \vec v}{\partial t}",
                       "how the arrow here changes", T.C_TIME).move_to(UP * 1.75)
        self.play(FadeIn(tc, shift=UP * 0.2), run_time=0.8)
        cap.say("Stand still at one spot and stare at the arrow there.", hold=1.5)

        clock = ValueTracker(0.0)
        PROBE = np.array([-0.35, -1.25, 0.0])

        def vfield(x, y, t):
            ang = 0.85 * np.sin(0.62 * t + 0.34 * x) + 0.55 * np.cos(0.47 * t - 0.42 * y)
            mag = 1.0 + 0.42 * np.sin(0.75 * t + 0.3 * x - 0.22 * y)
            return np.array([np.cos(ang), np.sin(ang), 0.0]) * mag

        gx = np.linspace(-5.0, 4.3, 8)
        gy = np.linspace(-2.6, 0.1, 4)

        def backdrop():
            t = clock.get_value()
            g = VGroup()
            for x in gx:
                for y in gy:
                    p = np.array([x, y, 0.0])
                    if np.linalg.norm(p - PROBE) < 0.85:
                        continue
                    d = vfield(x, y, t) * 0.34
                    g.add(Arrow(p - d, p + d, buff=0, color=T.C_TIME, stroke_width=2.6,
                                tip_length=0.11,
                                max_tip_length_to_length_ratio=0.45).set_opacity(0.26))
            return g

        probe_arrow = always_redraw(lambda: Arrow(
            PROBE, PROBE + vfield(PROBE[0], PROBE[1], clock.get_value()) * 1.15,
            buff=0, color=T.C_TIME, stroke_width=7,
            max_tip_length_to_length_ratio=0.28))
        ring = Circle(radius=0.26, stroke_color=T.C_HILITE, stroke_width=2.4).move_to(PROBE)
        post = Dot(PROBE, radius=0.075, color=T.C_HILITE)

        bg = always_redraw(backdrop)
        self.play(FadeIn(bg), run_time=0.8)
        self.play(FadeIn(post), Create(ring), run_time=0.5)
        self.add(probe_arrow)
        self.play(clock.animate.set_value(6.5), run_time=6.5, rate_func=linear)
        cap.say("That rate of change, at a fixed point in space, is this term.", hold=1.6)
        self.play(clock.animate.set_value(10.5), run_time=4.0, rate_func=linear)
        self.remove(bg, probe_arrow)
        self.play(FadeOut(VGroup(post, ring)), FadeOut(tc), run_time=0.7)

        # ------------------------------------------------- (v . grad) v
        self.play(*spotlight(eq, ["adv"]), run_time=0.8)
        cap.say("But a blob of fluid does not stay at one spot. It gets carried off.",
                hold=1.9, color=T.C_ADVECT)

        X0, X1, MID = -5.7, 5.7, -0.55

        def half_width(x):
            """Wide, then squeezed in the middle, then wide again."""
            return 1.72 - 1.06 * np.exp(-((x - 0.2) / 2.5) ** 2)

        xs_wall = np.linspace(X0, X1, 220)
        top = VMobject(stroke_color=T.RULE, stroke_width=3)
        top.set_points_smoothly([np.array([x, half_width(x) + MID, 0]) for x in xs_wall])
        bot = VMobject(stroke_color=T.RULE, stroke_width=3)
        bot.set_points_smoothly([np.array([x, -half_width(x) + MID, 0]) for x in xs_wall])
        pipe = VGroup(top, bot)

        field = VGroup()
        for x in np.linspace(X0 + 0.5, X1 - 0.5, 17):
            h = half_width(x)
            speed = 1.72 / h
            dh = (half_width(x + 0.02) - half_width(x - 0.02)) / 0.04
            for f in (-0.62, 0.0, 0.62):
                y = f * h
                vx, vy = speed, speed * dh * f
                mag = np.hypot(vx, vy)
                d = np.array([vx, vy, 0.0]) / mag
                s = 0.10 + 0.20 * mag
                p = np.array([x, y + MID, 0.0])
                field.add(Arrow(p - d * s, p + d * s, buff=0, color=T.C_TIME,
                                stroke_width=3.2, tip_length=0.12,
                                max_tip_length_to_length_ratio=0.45).set_opacity(0.6))

        self.play(Create(pipe), run_time=1.1)
        self.play(LaggedStart(*[GrowArrow(a) for a in field], lag_ratio=0.01), run_time=1.6)
        frozen = body("these arrows never change", size=T.T_SMALL,
                      color=T.INK_SOFT).move_to([0, 1.75, 0])
        self.play(FadeIn(frozen, shift=UP * 0.12), run_time=0.6)
        cap.say("Here is a steady flow. Nothing in this picture changes with time.", hold=2.0)

        parcel = Dot(np.array([X0 + 0.3, MID, 0.0]), radius=0.13, color=T.C_ADVECT)
        halo = Circle(radius=0.27, stroke_color=T.C_ADVECT, stroke_width=2.5,
                      stroke_opacity=0.55)
        halo.add_updater(lambda m: m.move_to(parcel))
        sp_lab = body("speed", size=0.26, color=T.C_ADVECT)
        sp_num = DecimalNumber(1.0, num_decimal_places=2, font_size=40, color=T.C_ADVECT)
        readout = VGroup(sp_lab, sp_num).arrange(RIGHT, buff=0.22)
        readout.add_updater(lambda m: m.next_to(parcel, UP, buff=0.5))
        sp_num.add_updater(lambda d: d.set_value(
            1.72 / half_width(float(np.clip(parcel.get_center()[0], X0, X1)))))

        self.play(FadeIn(parcel), FadeIn(halo), FadeIn(readout), run_time=0.5)

        # travel at the speed the flow actually dictates: fast where it is narrow
        xs_p = np.linspace(X0 + 0.3, X1 - 0.3, 400)
        v_p = 1.72 / half_width(xs_p)
        t_cum = np.concatenate([[0.0], np.cumsum(np.diff(xs_p) / v_p[:-1])])
        t_cum /= t_cum[-1]
        par = np.linspace(0.0, 1.0, 400)
        path = VMobject()
        path.set_points_smoothly([np.array([x, MID, 0]) for x in xs_p[::8]])
        self.play(MoveAlongPath(parcel, path), run_time=5.4,
                  rate_func=lambda a: float(np.interp(a, t_cum, par)))
        halo.clear_updaters(); readout.clear_updaters(); sp_num.clear_updaters()
        cap.say("And yet the blob accelerates — only because it moved somewhere faster.",
                hold=2.5, color=T.C_ADVECT, weight="MEDIUM")
        self.play(FadeOut(VGroup(parcel, halo, readout, field, pipe, frozen)), run_time=0.8)

        # ---- the nonlinearity ------------------------------------------
        big = MathTex(r"\bigl(", r"\vec v", r"\cdot\nabla", r"\bigr)", r"\vec v",
                      font_size=100, color=T.C_ADVECT).move_to(UP * 1.25)
        self.play(FadeIn(big, scale=0.9), run_time=0.9)
        cap.say("Look closely at what this term is made of.", hold=1.4)

        v1 = SurroundingRectangle(big[1], color=T.C_HILITE, buff=0.09,
                                  stroke_width=2.4, corner_radius=0.06)
        v2 = SurroundingRectangle(big[4], color=T.C_HILITE, buff=0.09,
                                  stroke_width=2.4, corner_radius=0.06)
        self.play(Create(v1), Create(v2), run_time=0.8)
        cap.say("The velocity, multiplied by itself.", hold=1.7, color=T.C_HILITE)

        loop = VGroup(
            body("the flow decides where things are carried", size=T.T_BODY),
            body("where things are carried decides the flow", size=T.T_BODY),
        ).arrange(DOWN, buff=0.36).move_to(DOWN * 0.75)
        self.play(FadeIn(loop[0], shift=UP * 0.15), run_time=0.7)
        self.wait(1.2)
        self.play(FadeIn(loop[1], shift=UP * 0.15), run_time=0.7)
        self.wait(1.7)

        word = body("this loop is called NONLINEARITY", size=T.T_H2,
                    color=T.C_ADVECT, weight="MEDIUM").move_to(DOWN * 2.15)
        self.play(FadeIn(word, shift=UP * 0.18), run_time=0.8)
        cap.say("It is why fluids can churn — and why nobody has cracked these equations.",
                hold=2.9, weight="MEDIUM")
        self.play(FadeOut(VGroup(big, v1, v2, loop, word)), FadeOut(eq), run_time=0.9)
        cap.clear()
        self.wait(0.3)


# ==========================================================================
class S05Forces(Scene):
    """The right-hand side: the three pushes, and the rule about squeezing."""

    def construct(self):
        cap = Caption(self)
        section(self, "part four", "The right side: the pushes")

        eq = full_equation(font_size=44).move_to(UP * 3.05)
        self.play(FadeIn(eq, shift=DOWN * 0.15), run_time=0.9)

        # ----------------------------------------------------- pressure
        self.play(*spotlight(eq, ["press"]), run_time=0.8)
        tc = term_card(r"-\,\nabla p", "pressure pushes", T.C_PRESS).move_to(UP * 2.0)
        self.play(FadeIn(tc, shift=UP * 0.2), run_time=0.8)
        cap.say("Pressure is how hard the fluid is being squeezed.", hold=1.8)

        # a pressure hill on the left, a hollow on the right
        W, H, NC, NR = 10.4, 3.0, 52, 15
        CENTER = np.array([0.0, -0.85, 0.0])

        def pressure(x, y):
            return (np.exp(-((x + 3.4) / 3.0) ** 2 - (y / 1.25) ** 2)
                    - np.exp(-((x - 3.4) / 3.0) ** 2 - (y / 1.25) ** 2))

        cw, ch = W / NC, H / NR
        pmap = VGroup()
        for i in range(NC):
            for j in range(NR):
                x = -W / 2 + (i + 0.5) * cw
                y = -H / 2 + (j + 0.5) * ch
                idx = int(np.clip(pressure(x, y) * 0.5 + 0.5, 0, 1) * 255)
                sq = Rectangle(width=cw * 1.03, height=ch * 1.03,
                               fill_color=rgb_to_color(T.PRESSURE_LUT[idx] / 255.0),
                               fill_opacity=1.0, stroke_width=0)
                sq.move_to(CENTER + np.array([x, y, 0.0]))
                pmap.add(sq)

        self.play(FadeIn(pmap), run_time=1.0)
        hi = body("SQUEEZED", size=0.27, color=T.BG, weight="BOLD")
        hi.move_to(CENTER + LEFT * 3.4 + UP * 1.0)
        lo = body("FREE", size=0.27, color=T.BG, weight="BOLD")
        lo.move_to(CENTER + RIGHT * 3.4 + UP * 1.0)
        self.play(FadeIn(hi), FadeIn(lo), run_time=0.6)
        cap.say("Fluid always slides from where it is squeezed toward where it is free.",
                hold=2.1)

        downhill = VGroup()
        for x in np.linspace(-4.0, 4.0, 11):
            for y in (-0.95, -0.32, 0.32):
                g = -(pressure(x + 0.05, y) - pressure(x - 0.05, y)) / 0.1
                if abs(g) < 0.015:
                    continue
                s = 0.14 + 1.05 * abs(g)
                d = np.array([np.sign(g), 0.0, 0.0])
                p = CENTER + np.array([x, y, 0.0])
                downhill.add(Arrow(p - d * s, p + d * s, buff=0, color=T.INK,
                                   stroke_width=3.6, tip_length=0.14,
                                   max_tip_length_to_length_ratio=0.4).set_opacity(0.92))
        self.play(LaggedStart(*[GrowArrow(a) for a in downhill], lag_ratio=0.025),
                  run_time=1.7)
        cap.say("The triangle asks 'which way does pressure climb'. The minus sign "
                "sends the fluid the other way.", hold=2.8)
        self.play(FadeOut(VGroup(pmap, hi, lo, downhill, tc)), run_time=0.8)

        # ---------------------------------------------------- viscosity
        self.play(*spotlight(eq, ["visc"]), run_time=0.8)
        tc = term_card(r"\mu\,\nabla^{2}\vec v", "internal friction", T.C_VISC).move_to(UP * 2.0)
        self.play(FadeIn(tc, shift=UP * 0.2), run_time=0.8)
        cap.say("Fluids rub against themselves. A fast layer drags a slow one along.",
                hold=2.1)

        AXIS_X, NL = -3.9, 13
        ys = np.linspace(-2.25, 0.35, NL) + 0.05
        rough = np.array([0.30, 1.55, 0.45, 2.35, 0.70, 2.95, 1.00, 2.60, 0.60,
                          2.05, 0.45, 1.30, 0.28])
        # settle towards a proper laminar profile carrying the same total flow
        smoothp = np.exp(-((np.arange(NL) - (NL - 1) / 2) / 4.2) ** 2)
        smoothp *= rough.sum() / smoothp.sum()

        prof = ValueTracker(0.0)
        axis = Line([AXIS_X, ys[0] - 0.25, 0], [AXIS_X, ys[-1] + 0.25, 0],
                    color=T.RULE, stroke_width=2.4)

        def layers():
            a = prof.get_value()
            vals = rough * (1 - a) + smoothp * a
            g = VGroup()
            tips = []
            for y, val in zip(ys, vals):
                tip = AXIS_X + max(val, 0.05) * 1.55
                tips.append(np.array([tip, y, 0.0]))
                g.add(Arrow([AXIS_X, y, 0], [tip, y, 0], buff=0, color=T.C_VISC,
                            stroke_width=5, max_tip_length_to_length_ratio=0.3,
                            tip_length=0.16))
            curve = VMobject(stroke_color=T.C_HILITE, stroke_width=3)
            curve.set_points_smoothly(tips)
            g.add(curve)
            return g

        lay = always_redraw(layers)
        self.play(Create(axis), FadeIn(lay), run_time=0.9)
        self.wait(1.1)
        cap.say("Left alone, friction irons the differences out.", hold=1.0)
        self.play(prof.animate.set_value(1.0), run_time=3.4, rate_func=smooth)
        self.wait(0.7)

        mu = MathTex(r"\mu", font_size=70, color=T.C_VISC)
        mug = VGroup(
            body("water: small", size=0.27, color=T.INK_SOFT),
            body("honey: large", size=0.27, color=T.INK_SOFT),
        ).arrange(DOWN, buff=0.24)
        mublk = VGroup(mu, mug).arrange(DOWN, buff=0.34).move_to([3.5, -0.95, 0])
        self.play(FadeIn(mublk, shift=UP * 0.12), run_time=0.9)
        cap.say("Mu is the stickiness. Water is runny. Honey is not.", hold=2.1)
        # swap the live-redrawn group for a static copy so it can be faded out
        settled = layers()
        self.remove(lay)
        self.add(settled)
        self.play(FadeOut(VGroup(mublk, tc, axis, settled)), run_time=0.8)

        # ------------------------------------------------------- forces
        self.play(*spotlight(eq, ["force"]), run_time=0.8)
        tc = term_card(r"\vec f", "everything else pushing", T.C_VISC if False else T.C_FORCE)
        tc.move_to(UP * 1.85)
        self.play(FadeIn(tc, shift=UP * 0.2), run_time=0.8)
        items = VGroup(*[body(s, size=T.T_BODY, color=T.INK_SOFT)
                         for s in ("gravity", "a pump", "a fan", "the spin of the Earth")])
        items.arrange(DOWN, buff=0.42).move_to(DOWN * 1.1)
        self.play(LaggedStart(*[FadeIn(i, shift=RIGHT * 0.2) for i in items],
                              lag_ratio=0.3), run_time=1.8)
        cap.say("And whatever else happens to be shoving the fluid around.", hold=1.9)
        self.play(FadeOut(VGroup(tc, items)), run_time=0.7)

        # -------------------------------------------- incompressibility
        self.play(*spotlight(eq, []), run_time=0.7)
        deq = div_equation(font_size=62).move_to(UP * 1.95)
        self.play(FadeIn(deq, shift=UP * 0.2), run_time=0.9)
        cap.say("One more rule, and it is a short one.", hold=1.3, color=T.C_DIV)
        cap.say("You cannot squash water. Squeeze a litre and you still have a litre.",
                hold=2.1)

        boxm = Square(side_length=2.1, stroke_color=T.C_DIV, stroke_width=2.6,
                      fill_color=T.BG_SOFT, fill_opacity=0.55).move_to(DOWN * 0.85)
        ins = VGroup(
            Arrow(boxm.get_left() + LEFT * 1.3, boxm.get_left(), buff=0.05,
                  color=T.C_DIV, stroke_width=6, max_tip_length_to_length_ratio=0.3),
            Arrow(boxm.get_bottom() + DOWN * 0.95, boxm.get_bottom(), buff=0.05,
                  color=T.C_DIV, stroke_width=5, max_tip_length_to_length_ratio=0.3),
        )
        outs = VGroup(
            Arrow(boxm.get_right(), boxm.get_right() + RIGHT * 1.3, buff=0.05,
                  color=T.C_DIV, stroke_width=6, max_tip_length_to_length_ratio=0.3),
            Arrow(boxm.get_top(), boxm.get_top() + UP * 0.95, buff=0.05,
                  color=T.C_DIV, stroke_width=5, max_tip_length_to_length_ratio=0.3),
        )
        inl = body("what flows in", size=0.28, color=T.INK_SOFT).next_to(boxm, LEFT, buff=1.5)
        outl = body("must flow out", size=0.28, color=T.INK_SOFT).next_to(boxm, RIGHT, buff=1.5)
        self.play(Create(boxm), run_time=0.6)
        self.play(LaggedStart(*[GrowArrow(a) for a in ins], lag_ratio=0.2),
                  FadeIn(inl), run_time=1.0)
        self.play(LaggedStart(*[GrowArrow(a) for a in outs], lag_ratio=0.2),
                  FadeIn(outl), run_time=1.0)
        cap.say("Whatever flows into any little box has to flow straight back out of it.",
                hold=2.5)
        self.wait(0.3)
        self.play(FadeOut(VGroup(boxm, ins, outs, inl, outl, deq)), FadeOut(eq), run_time=0.9)
        cap.clear()
        self.wait(0.3)


# ==========================================================================
class S06Assemble(Scene):
    """All of it, at once, in plain English."""

    def construct(self):
        cap = Caption(self)
        section(self, "part five", "The whole thing, in plain English")

        eq = full_equation(font_size=58).move_to(UP * 2.35)
        self.play(FadeIn(eq, shift=UP * 0.2), run_time=1.2)
        self.wait(0.7)

        # two staggered rails of labels, so nothing ever collides
        glosses = [
            ("dt", "how the flow\nchanges here", T.C_TIME, 1.05),
            ("adv", "the flow\ncarries itself", T.C_ADVECT, -0.15),
            ("press", "pushed toward\nlower pressure", T.C_PRESS, 1.05),
            ("visc", "rubbed smooth\nby friction", T.C_VISC, -0.15),
            ("force", "gravity and\nthe rest", T.C_FORCE, 1.05),
        ]
        tags = VGroup()
        for key, txt, col, yrail in glosses:
            part = eq[IDX[key]]
            t = body(txt, size=0.27, color=col, width=2.55)
            t.move_to([part.get_center()[0], yrail, 0])
            t.shift(RIGHT * np.clip(0 - abs(t.get_center()[0]), -99, 0) * 0)
            leg = Line(part.get_bottom() + DOWN * 0.1,
                       [part.get_center()[0], t.get_top()[1] + 0.1, 0],
                       color=col, stroke_width=1.3, stroke_opacity=0.55)
            tags.add(VGroup(leg, t))

        # keep every label inside the frame
        for g in tags:
            over = g[1].get_right()[0] - 6.7
            if over > 0:
                g[1].shift(LEFT * over)
            under = -6.7 - g[1].get_left()[0]
            if under > 0:
                g[1].shift(RIGHT * under)

        self.play(LaggedStart(*[FadeIn(t, shift=UP * 0.12) for t in tags],
                              lag_ratio=0.2), run_time=2.3)
        self.wait(1.5)

        deq = div_equation(font_size=48).move_to(DOWN * 1.35)
        dgloss = body("and nothing gets squashed", size=0.28, color=T.C_DIV)
        dgloss.next_to(deq, DOWN, buff=0.3)
        self.play(FadeIn(deq, shift=UP * 0.15), FadeIn(dgloss, shift=UP * 0.1), run_time=0.9)
        self.wait(1.6)

        cap.say("Read it out loud: mass times acceleration equals the sum of the pushes.",
                hold=2.7, weight="MEDIUM")
        cap.say("Every wave, every gust, every swirl of cream in coffee is in there.",
                hold=2.7)
        self.play(FadeOut(tags), FadeOut(dgloss), run_time=0.8)
        self.play(eq.animate.scale(0.9).move_to(UP * 0.5),
                  deq.animate.scale(0.9).move_to(DOWN * 0.85), run_time=1.0)
        self.wait(1.3)
        self.play(FadeOut(eq), FadeOut(deq), run_time=0.9)
        cap.clear()
        self.wait(0.3)
