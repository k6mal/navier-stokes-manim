import time
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from fluid import Fluid2D, disc_mask

NX, NY, D = 480, 220, 28
CX, CY = 110, NY / 2
solid = disc_mask(NX, NY, CX, CY, D / 2)
sim = Fluid2D(NX, NY, nu=D / 200.0, solid=solid, mode="channel", u_in=1.0)

DT = 0.4
t0 = time.time()
for k in range(3000):
    # a brief nudge to break the perfect up/down symmetry, then let physics run
    if k < 60:
        sim.v[CX - 20:CX + 20, :] += 0.05
    sim.step(DT)
    if k % 500 == 0:
        w = sim.vorticity()
        print(f"step {k:5d}  t={k*DT:7.1f}  |w|max={np.abs(w).max():.3f}  "
              f"v_rms={np.sqrt((sim.v**2).mean()):.4f}  {time.time()-t0:.0f}s")

w = sim.vorticity()
fig, ax = plt.subplots(figsize=(14, 6.5), dpi=110)
lim = 0.35
ax.imshow(w.T, origin="lower", cmap="RdBu_r", vmin=-lim, vmax=lim, interpolation="bilinear")
ax.add_patch(plt.Circle((CX, CY), D / 2, color="k"))
ax.set_axis_off()
fig.tight_layout(pad=0)
fig.savefig("/private/tmp/claude-501/-Users-mohammedkamal/53f14616-29a3-4519-854b-ca791f53bf20/scratchpad/street.png")
print("saved")
