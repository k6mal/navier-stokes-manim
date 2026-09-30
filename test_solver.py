import time
import numpy as np
from fluid import Fluid2D, disc_mask

NX, NY, D = 400, 200, 28
solid = disc_mask(NX, NY, 100, NY / 2 + 0.5, D / 2)
Re = 200.0
sim = Fluid2D(NX, NY, nu=D / Re, solid=solid, mode="channel", u_in=1.0)
print(f"unknowns = {sim._n_unknown}")

t0 = time.time()
sim.step(0.4)
print(f"first step (warm-up): {time.time()-t0:.3f}s")

t0 = time.time()
N = 60
for k in range(N):
    sim.step(0.4)
dt_step = (time.time() - t0) / N
print(f"per step: {dt_step*1000:.1f} ms  ->  3000 steps = {dt_step*3000:.0f} s")
print(f"max |div| after project = {np.abs(sim.divergence()).max():.2e}")
print(f"max |u| = {np.abs(sim.u).max():.3f}   KE = {sim.kinetic_energy():.1f}")
