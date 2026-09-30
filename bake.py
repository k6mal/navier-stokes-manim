"""Run the simulations once, cache the frames, so rendering stays fast.

Each dataset is stored as uint8 arrays of shape (n_frames, nx, ny) plus a
small JSON sidecar describing the geometry, so the scenes can lay a clean
circle exactly over the staircased obstacle.

    python bake.py street
    python bake.py reynolds
    python bake.py plume
    python bake.py all
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

from fluid import Fluid2D, disc_mask
from theme import signed_to_u8, unsigned_to_u8

CACHE = Path(__file__).parent / "cache"
CACHE.mkdir(exist_ok=True)


def _save(name: str, arrays: dict, meta: dict) -> None:
    for key, arr in arrays.items():
        np.save(CACHE / f"{name}__{key}.npy", arr)
    (CACHE / f"{name}.json").write_text(json.dumps(meta, indent=2))
    total = sum(a.nbytes for a in arrays.values()) / 1e6
    print(f"  saved {name}: {list(arrays)}  {total:.0f} MB  {meta['frames']} frames")


def _bar(k, n, t0, every=500):
    if k % every == 0:
        el = time.time() - t0
        eta = el / max(k, 1) * (n - k)
        print(f"    {k:6d}/{n}   {el:5.0f}s in, ~{eta:4.0f}s left", flush=True)


def _lanes(ny, count, width, lo=0.14, hi=0.86):
    """Evenly spaced soft stripes of dye across the inlet."""
    lanes = np.zeros(ny)
    for c in np.linspace(lo, hi, count) * ny:
        lanes += np.exp(-0.5 * ((np.arange(ny) - c) / width) ** 2)
    return np.clip(lanes, 0, 1)


# ==========================================================================
# 1. flow past a cylinder -> the von Karman vortex street
# ==========================================================================
def bake_street(frames=1050, capture_every=3):
    NX, NY, D = 880, 368, 56
    CX, CY = 210.0, NY / 2
    Re, DT = 260.0, 0.36

    solid = disc_mask(NX, NY, CX, CY, D / 2)
    sim = Fluid2D(NX, NY, nu=D / Re, solid=solid, mode="channel", u_in=1.0)
    lanes = _lanes(NY, 11, 2.2)

    print("  spinning up until the wake finds its rhythm...", flush=True)
    t0 = time.time()
    spin = 4500
    probe = []
    for k in range(spin):
        if k < 90:                      # break the symmetry once, then let go
            sim.v[int(CX) - 34:int(CX) + 34, :] += 0.04
        sim.step(DT, dye_inflow=0.0)
        probe.append(sim.v[int(CX + 3 * D), int(CY)])
        _bar(k, spin, t0, 750)

    sig = np.array(probe[-2200:]); sig = sig - sig.mean()
    cr = np.where((sig[:-1] < 0) & (sig[1:] >= 0))[0]
    period = float(np.mean(np.diff(cr))) * DT if len(cr) > 2 else float("nan")
    print(f"  shedding period ~{period:.0f} time units   St ~{D/period:.3f}", flush=True)

    print("  letting the dye wind into the wake...", flush=True)
    t0 = time.time()
    for k in range(1200):
        sim.step(DT, dye_inflow=lanes)
        _bar(k, 1200, t0, 400)

    print("  capturing...", flush=True)
    vort = np.empty((frames, NX, NY), dtype=np.uint8)
    dye = np.empty((frames, NX, NY), dtype=np.uint8)
    t0 = time.time()
    for f in range(frames):
        for _ in range(capture_every):
            sim.step(DT, dye_inflow=lanes)
        # gamma 0.72: lifts the weak downstream vortices without also
        # lifting the faint channel-scale shear into a background wash
        vort[f] = signed_to_u8(sim.vorticity(), 0.40, gamma=0.72)
        dye[f] = unsigned_to_u8(sim.dye, 0.95, gamma=0.80)
        _bar(f, frames, t0, 200)

    _save("street", {"vort": vort, "dye": dye},
          dict(nx=NX, ny=NY, cx=CX, cy=CY, r=D / 2, dt=DT, Re=Re, D=D,
               frames=frames, capture_every=capture_every, period=period))


# ==========================================================================
# 2. the same obstacle, three thicknesses -> one number changes everything
# ==========================================================================
def bake_reynolds(frames=560):
    NX, NY, D = 640, 150, 20
    CX, CY = 130.0, NY / 2
    DT_FRAME = 1.2                      # identical *physical* time per frame
    PULSE = 26.0                        # dye released in dashes, so steady flow still reads as moving

    runs = [("syrup", 6.0), ("water", 90.0), ("fast", 420.0)]
    out, meta_runs = {}, []
    lanes = _lanes(NY, 9, 1.5)

    for name, Re in runs:
        nu = D / Re
        dt = min(0.32, 2.1 / (8.0 * nu))
        sub = max(1, int(round(DT_FRAME / dt)))
        dt = DT_FRAME / sub
        print(f"  {name}: Re={Re:g}  nu={nu:.3f}  dt={dt:.4f}  {sub} steps/frame", flush=True)

        solid = disc_mask(NX, NY, CX, CY, D / 2)
        sim = Fluid2D(NX, NY, nu=nu, solid=solid, mode="channel", u_in=1.0)

        t, t0 = 0.0, time.time()
        spin = int(560 / dt)                       # about one flush of the domain
        for k in range(spin):
            if t < 40:
                sim.v[int(CX) - 14:int(CX) + 14, :] += 0.05 * dt
            pulse = 1.0 if (t % PULSE) < 0.5 * PULSE else 0.0
            sim.step(dt, dye_inflow=lanes * pulse)
            t += dt
            _bar(k, spin, t0, 2000)

        dyes = np.empty((frames, NX, NY), dtype=np.uint8)
        vors = np.empty((frames, NX, NY), dtype=np.uint8)
        for f in range(frames):
            for _ in range(sub):
                pulse = 1.0 if (t % PULSE) < 0.5 * PULSE else 0.0
                sim.step(dt, dye_inflow=lanes * pulse)
                t += dt
            dyes[f] = unsigned_to_u8(sim.dye, 0.9, gamma=0.8)
            vors[f] = signed_to_u8(sim.vorticity(), 0.5, gamma=0.55)
        out[f"{name}_dye"], out[f"{name}_vort"] = dyes, vors
        meta_runs.append(dict(name=name, Re=Re, nu=nu, dt=dt, sub=sub))
        print(f"    done in {time.time()-t0:.0f}s", flush=True)

    _save("reynolds", out,
          dict(nx=NX, ny=NY, cx=CX, cy=CY, r=D / 2, frames=frames,
               dt_frame=DT_FRAME, runs=meta_runs))


# ==========================================================================
# 3. two plumes, forked by one part in ten thousand -> two different futures
#
# Both are advanced in the same loop with the same forcing, so the ONLY
# difference between them is the epsilon applied to the source temperature.
# This plume is only weakly chaotic - the separation doubles about every
# 120 time units - so the run has to be long enough for one part in ten
# thousand to become one part in one.
# ==========================================================================
def bake_plume(frames=660, capture_every=6):
    NX, NY = 240, 340
    NU, DT, BUOY = 0.0012, 0.12, 0.012
    EPS = 1e-4
    SPIN = 3600                      # by here the two are still identical to the eye

    hot = np.zeros((NX, NY)); hot[disc_mask(NX, NY, NX / 2, 22, 13)] = 1.0
    ink = np.zeros((NX, NY)); ink[disc_mask(NX, NY, NX / 2, 22, 10)] = 0.92
    xs = np.arange(NX)[:, None]

    def wobble(t):
        return (0.30 * np.sin(0.055 * t) + 0.22 * np.sin(0.131 * t + 1.3)
                + 0.16 * np.sin(0.207 * t + 2.7))

    def make():
        s_ = Fluid2D(NX, NY, nu=NU, mode="box")
        s_.buoyancy = BUOY
        return s_

    A, B = make(), make()
    a_img = np.empty((frames, NX, NY), dtype=np.uint8)
    b_img = np.empty((frames, NX, NY), dtype=np.uint8)

    t, k, t0 = 0.0, 0, time.time()
    total = SPIN + frames * capture_every
    trace = []

    def separation():
        d = np.sqrt(((A.v - B.v) ** 2).mean())
        r = np.sqrt((A.v ** 2).mean())
        return float(d / max(r, 1e-30))

    def advance():
        nonlocal t, k
        w = wobble(t)
        amp = 1.0 + 0.45 * np.sin(xs * 0.27 + 0.072 * t) * w
        for sim, scale in ((A, 1.0), (B, 1.0 + EPS)):
            sim.temp = np.maximum(sim.temp, hot * amp * scale)
            sim.dye = np.maximum(sim.dye, ink)
            sim.u[:, :30] += 0.010 * w * DT
            sim.step(DT)
        t += DT; k += 1
        if k % 900 == 0:
            print(f"    {k:6d}/{total}  t={t:6.0f}  separation={separation():.2e}  "
                  f"[{time.time()-t0:.0f}s]", flush=True)

    print(f"  running both plumes in lockstep, epsilon = {EPS:g}", flush=True)
    for _ in range(SPIN):
        advance()
    for f in range(frames):
        for _ in range(capture_every):
            advance()
        a_img[f] = unsigned_to_u8(A.dye, 1.0, gamma=0.72)
        b_img[f] = unsigned_to_u8(B.dye, 1.0, gamma=0.72)
        trace.append(separation())

    final = float(np.abs(a_img[-1].astype(int) - b_img[-1].astype(int)).mean())
    print(f"  final mean pixel difference: {final:.2f}/255", flush=True)
    _save("plume", {"a": a_img, "b": b_img},
          dict(nx=NX, ny=NY, nu=NU, dt=DT, buoyancy=BUOY, eps=EPS, spin=SPIN,
               frames=frames, capture_every=capture_every,
               t_start=SPIN * DT, t_end=t, separation=trace,
               dt_frame=capture_every * DT,
               final_pixel_diff=final))


# ==========================================================================
JOBS = {"street": bake_street, "reynolds": bake_reynolds, "plume": bake_plume}

if __name__ == "__main__":
    wanted = sys.argv[1:] or ["all"]
    if wanted == ["all"]:
        wanted = list(JOBS)
    for w in wanted:
        print(f"[bake] {w}", flush=True)
        t = time.time()
        JOBS[w]()
        print(f"[bake] {w} finished in {time.time()-t:.0f}s\n", flush=True)
