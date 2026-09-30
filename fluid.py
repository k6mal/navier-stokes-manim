"""
A small but honest 2-D incompressible Navier-Stokes solver.

Discretisation
--------------
Staggered ("MAC") grid.  Pressure lives at cell centres, the x-velocity on
vertical faces and the y-velocity on horizontal faces.  That is the layout
that makes the discrete divergence and the discrete gradient exact adjoints
of one another, which is what keeps the projection step clean.

      v[i, j+1]
   +-----^-----+
   |           |
u[i,j] >  p  > u[i+1,j]
   |           |
   +-----^-----+
      v[i, j]

Time stepping is the classic fractional step (Chorin projection):

    1.  u*        = u^n + dt * ( -(u.grad)u + nu*lap(u) + f )      [SSP-RK3]
    2.  lap(p)    = div(u*) / dt                                   [sparse LU]
    3.  u^{n+1}   = u* - dt * grad(p)                              [now div-free]

Convection uses centred differences (second order, non-dissipative) so that
vortices stay crisp instead of smearing out; SSP-RK3 is used for the time
integration because its stability region covers a chunk of the imaginary
axis, which is exactly what centred convection needs.

Everything is in grid units: h = 1.  So lengths are measured in cells and the
Reynolds number is Re = U * D / nu.
"""

from __future__ import annotations

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from scipy.ndimage import maximum_filter, minimum_filter


# --------------------------------------------------------------------------
# interpolation helper used by the semi-Lagrangian scalar transport
# --------------------------------------------------------------------------
def _bilerp(field: np.ndarray, x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Sample `field` (cell-centred, shape (nx, ny)) at fractional cell coords."""
    nx, ny = field.shape
    x = np.clip(x, 0.0, nx - 1.001)
    y = np.clip(y, 0.0, ny - 1.001)
    i0 = x.astype(np.int64)
    j0 = y.astype(np.int64)
    i1 = i0 + 1
    j1 = j0 + 1
    fx = x - i0
    fy = y - j0
    return (
        field[i0, j0] * (1 - fx) * (1 - fy)
        + field[i1, j0] * fx * (1 - fy)
        + field[i0, j1] * (1 - fx) * fy
        + field[i1, j1] * fx * fy
    )


class Fluid2D:
    """Incompressible NS on a rectangle, optionally with solid obstacles.

    Parameters
    ----------
    nx, ny : grid size in cells.
    nu     : kinematic viscosity, in cells^2 / time.
    solid  : bool array (nx, ny), True where the cell is a solid wall.
    mode   : "channel" -> inflow left, outflow right, free-slip top/bottom.
             "box"     -> free-slip on all four walls.
    u_in   : inflow speed used by "channel".
    """

    def __init__(self, nx, ny, nu, solid=None, mode="channel", u_in=1.0):
        self.nx, self.ny = int(nx), int(ny)
        self.nu = float(nu)
        self.mode = mode
        self.u_in = float(u_in)

        self.solid = (
            np.zeros((self.nx, self.ny), dtype=bool) if solid is None else solid.astype(bool)
        )
        self.fluid = ~self.solid

        # velocities on faces
        self.u = np.zeros((self.nx + 1, self.ny))
        self.v = np.zeros((self.nx, self.ny + 1))
        if mode == "channel":
            self.u[:] = self.u_in

        # faces that touch a solid cell are frozen at zero (no-slip, staircased)
        self.u_solid = np.zeros_like(self.u, dtype=bool)
        self.v_solid = np.zeros_like(self.v, dtype=bool)
        self.u_solid[1:-1, :] = self.solid[:-1, :] | self.solid[1:, :]
        self.v_solid[:, 1:-1] = self.solid[:, :-1] | self.solid[:, 1:]
        self.u_solid[0, :] |= self.solid[0, :]
        self.u_solid[-1, :] |= self.solid[-1, :]
        self.v_solid[:, 0] |= self.solid[:, 0]
        self.v_solid[:, -1] |= self.solid[:, -1]

        # passive scalars that ride along with the flow
        self.dye = np.zeros((self.nx, self.ny))
        self.temp = np.zeros((self.nx, self.ny))
        self.buoyancy = 0.0          # body force  f_y = buoyancy * temp
        self.gravity = 0.0

        self._build_poisson()
        self._apply_velocity_bcs()

    # ------------------------------------------------------------------
    # pressure Poisson operator
    # ------------------------------------------------------------------
    def _build_poisson(self):
        """Assemble lap(p) for the fluid cells and factorise it once.

        Neumann (dp/dn = 0) wherever the normal velocity is already known -
        solid walls, the inflow plane, the free-slip walls.  Dirichlet p = 0
        at the outflow, which also pins the otherwise-free additive constant.
        In "box" mode there is no outflow, so one cell is pinned by hand.
        """
        nx, ny = self.nx, self.ny
        fluid = self.fluid

        index = -np.ones((nx, ny), dtype=np.int64)
        n_unknown = int(fluid.sum())
        index[fluid] = np.arange(n_unknown)

        ii, jj = np.nonzero(fluid)
        centre = index[ii, jj]
        diag = np.zeros(n_unknown)
        rows, cols = [], []

        dirichlet = {"left": False, "right": self.mode == "channel",
                     "bottom": False, "top": False}

        for di, dj, side in ((-1, 0, "left"), (1, 0, "right"),
                             (0, -1, "bottom"), (0, 1, "top")):
            ni, nj = ii + di, jj + dj
            inside = (ni >= 0) & (ni < nx) & (nj >= 0) & (nj < ny)

            # neighbour is a fluid cell -> a real off-diagonal coupling
            link = np.zeros_like(inside)
            link[inside] = fluid[ni[inside], nj[inside]]
            diag[centre[link]] -= 1.0
            rows.append(centre[link])
            cols.append(index[ni[link], nj[link]])

            # neighbour is outside the domain on a Dirichlet wall -> p_ghost = 0
            if dirichlet[side]:
                diag[centre[~inside]] -= 1.0
            # everything else (solid neighbour, Neumann wall) contributes nothing

        rows.append(np.arange(n_unknown))
        cols.append(np.arange(n_unknown))
        data = [np.ones(len(r)) for r in rows[:-1]] + [diag]

        A = sp.coo_matrix(
            (np.concatenate(data), (np.concatenate(rows), np.concatenate(cols))),
            shape=(n_unknown, n_unknown),
        ).tocsr()

        if self.mode != "channel":
            # no Dirichlet anywhere: pin a single cell so the system is regular
            A = A.tolil()
            A.rows[0], A.data[0] = [0], [1.0]
            A = A.tocsr()
            self._pinned = True
        else:
            self._pinned = False

        self._index = index
        self._n_unknown = n_unknown
        self._solve_poisson = spla.factorized(A.tocsc())

    # ------------------------------------------------------------------
    # boundary conditions
    # ------------------------------------------------------------------
    def _apply_velocity_bcs(self):
        u, v = self.u, self.v
        if self.mode == "channel":
            u[0, :] = self.u_in                 # inflow
            u[-1, :] = u[-2, :]                 # outflow, zero gradient
            # keep the books balanced: what goes in must come out
            flux_in = u[0, :].sum()
            flux_out = u[-1, :].sum()
            if abs(flux_out) > 1e-12:
                u[-1, :] *= flux_in / flux_out
            else:
                u[-1, :] = self.u_in
            v[0, :] = 0.0
            v[-1, :] = v[-2, :]
        else:
            u[0, :] = 0.0
            u[-1, :] = 0.0
        v[:, 0] = 0.0                            # free-slip floor / ceiling
        v[:, -1] = 0.0
        u[self.u_solid] = 0.0
        v[self.v_solid] = 0.0

    def _pad_u(self):
        """u with one ghost layer all round, filled to honour the BCs."""
        p = np.empty((self.nx + 3, self.ny + 2))
        p[1:-1, 1:-1] = self.u
        if self.mode == "channel":
            p[0, 1:-1] = self.u_in               # uniform inflow
            p[-1, 1:-1] = self.u[-1, :]          # outflow, zero gradient
        else:
            # free-slip wall: the normal velocity is odd about the wall
            p[0, 1:-1] = -self.u[1, :]
            p[-1, 1:-1] = -self.u[-2, :]
        p[:, 0] = p[:, 1]                        # free-slip: du/dy = 0
        p[:, -1] = p[:, -2]
        return p

    def _pad_v(self):
        p = np.empty((self.nx + 2, self.ny + 3))
        p[1:-1, 1:-1] = self.v
        if self.mode == "channel":
            p[0, 1:-1] = -self.v[0, :]           # v = 0 across the inflow plane
            p[-1, 1:-1] = self.v[-1, :]          # outflow, zero gradient
        else:
            # free-slip wall: the tangential velocity is even about the wall
            p[0, 1:-1] = self.v[0, :]
            p[-1, 1:-1] = self.v[-1, :]
        p[:, 0] = -p[:, 1]                       # v = 0 on the floor / ceiling
        p[:, -1] = -p[:, -2]
        return p

    # ------------------------------------------------------------------
    # the right-hand side:  -(u.grad)u + nu*lap(u) + f
    # ------------------------------------------------------------------
    def _rhs(self):
        up, vp = self._pad_u(), self._pad_v()

        # ---- x-momentum, evaluated on the u faces -----------------------
        uc = up[1:-1, 1:-1]
        dudx = (up[2:, 1:-1] - up[:-2, 1:-1]) * 0.5
        dudy = (up[1:-1, 2:] - up[1:-1, :-2]) * 0.5
        # v averaged from the four surrounding v faces onto the u face
        v_at_u = 0.25 * (vp[:-1, 1:-2] + vp[1:, 1:-2] + vp[:-1, 2:-1] + vp[1:, 2:-1])
        lap_u = (up[2:, 1:-1] + up[:-2, 1:-1] + up[1:-1, 2:] + up[1:-1, :-2] - 4.0 * uc)
        du = -(uc * dudx + v_at_u * dudy) + self.nu * lap_u

        # ---- y-momentum, evaluated on the v faces -----------------------
        vc = vp[1:-1, 1:-1]
        dvdx = (vp[2:, 1:-1] - vp[:-2, 1:-1]) * 0.5
        dvdy = (vp[1:-1, 2:] - vp[1:-1, :-2]) * 0.5
        u_at_v = 0.25 * (up[1:-2, :-1] + up[2:-1, :-1] + up[1:-2, 1:] + up[2:-1, 1:])
        lap_v = (vp[2:, 1:-1] + vp[:-2, 1:-1] + vp[1:-1, 2:] + vp[1:-1, :-2] - 4.0 * vc)
        dv = -(u_at_v * dvdx + vc * dvdy) + self.nu * lap_v

        if self.buoyancy or self.gravity:
            t_at_v = np.zeros_like(self.v)
            t_at_v[:, 1:-1] = 0.5 * (self.temp[:, :-1] + self.temp[:, 1:])
            t_at_v[:, 0] = self.temp[:, 0]
            t_at_v[:, -1] = self.temp[:, -1]
            dv += self.buoyancy * t_at_v - self.gravity

        du[self.u_solid] = 0.0
        dv[self.v_solid] = 0.0
        return du, dv

    # ------------------------------------------------------------------
    # projection: strip off the part of the field that has any divergence
    # ------------------------------------------------------------------
    def divergence(self):
        d = (self.u[1:, :] - self.u[:-1, :]) + (self.v[:, 1:] - self.v[:, :-1])
        d[self.solid] = 0.0
        return d

    def project(self, dt):
        self._apply_velocity_bcs()
        rhs = (self.divergence() / dt)[self.fluid]
        if self._pinned:
            rhs = rhs - rhs.mean()
            rhs[0] = 0.0

        p = np.zeros((self.nx, self.ny))
        p[self.fluid] = self._solve_poisson(rhs)
        self.p = p

        # u <- u - dt * grad(p), only across faces between two fluid cells
        inner_u = self.fluid[:-1, :] & self.fluid[1:, :]
        self.u[1:-1, :][inner_u] -= dt * (p[1:, :] - p[:-1, :])[inner_u]
        inner_v = self.fluid[:, :-1] & self.fluid[:, 1:]
        self.v[:, 1:-1][inner_v] -= dt * (p[:, 1:] - p[:, :-1])[inner_v]
        if self.mode == "channel":
            self.u[-1, :] -= dt * (0.0 - p[-1, :])      # Dirichlet ghost at outflow
        self._apply_velocity_bcs()

    # ------------------------------------------------------------------
    # scalar transport: semi-Lagrangian, i.e. "where did this parcel come from?"
    # ------------------------------------------------------------------
    def _advect_scalar(self, s, dt, inflow_value=None, maccormack=True):
        """Trace each cell backwards down the flow and read off what was there.

        Plain semi-Lagrangian is rock solid but smears a dye pattern into mush
        after a few hundred steps, because every step interpolates.  The
        MacCormack correction runs the same transport forwards again, measures
        how far it missed, and subtracts half that error - then clamps the
        result to the values actually available upstream so the sharpening can
        never invent a new maximum and blow up.
        """
        nx, ny = self.nx, self.ny
        gx, gy = np.meshgrid(np.arange(nx), np.arange(ny), indexing="ij")
        uc = 0.5 * (self.u[:-1, :] + self.u[1:, :])
        vc = 0.5 * (self.v[:, :-1] + self.v[:, 1:])

        # midpoint rule for the departure point
        um = _bilerp(uc, gx - 0.5 * dt * uc, gy - 0.5 * dt * vc)
        vm = _bilerp(vc, gx - 0.5 * dt * uc, gy - 0.5 * dt * vc)
        xd, yd = gx - dt * um, gy - dt * vm
        out = _bilerp(s, xd, yd)

        if maccormack:
            back = _bilerp(out, gx + dt * um, gy + dt * vm)
            lo = _bilerp(minimum_filter(s, size=3, mode="nearest"), xd, yd)
            hi = _bilerp(maximum_filter(s, size=3, mode="nearest"), xd, yd)
            out = np.clip(out + 0.5 * (s - back), lo, hi)

        if inflow_value is not None:
            out[0, :] = inflow_value
        out[self.solid] = 0.0
        return out

    # ------------------------------------------------------------------
    def step(self, dt, dye_inflow=None, temp_inflow=None):
        """Advance the whole state by dt."""
        u0, v0 = self.u.copy(), self.v.copy()

        # SSP-RK3 on convection + diffusion, then a single projection
        du, dv = self._rhs()
        self.u, self.v = u0 + dt * du, v0 + dt * dv
        self._apply_velocity_bcs()

        du, dv = self._rhs()
        self.u = 0.75 * u0 + 0.25 * (self.u + dt * du)
        self.v = 0.75 * v0 + 0.25 * (self.v + dt * dv)
        self._apply_velocity_bcs()

        du, dv = self._rhs()
        self.u = (u0 + 2.0 * (self.u + dt * du)) / 3.0
        self.v = (v0 + 2.0 * (self.v + dt * dv)) / 3.0

        self.project(dt)

        if self.dye is not None:
            self.dye = self._advect_scalar(self.dye, dt, dye_inflow)
        if self.buoyancy:
            self.temp = self._advect_scalar(self.temp, dt, temp_inflow)

    # ------------------------------------------------------------------
    # diagnostics / things worth drawing
    # ------------------------------------------------------------------
    def vorticity(self):
        """curl of u, at cell centres:  omega = dv/dx - du/dy."""
        uc = 0.5 * (self.u[:-1, :] + self.u[1:, :])
        vc = 0.5 * (self.v[:, :-1] + self.v[:, 1:])
        dvdx = np.gradient(vc, axis=0)
        dudy = np.gradient(uc, axis=1)
        w = dvdx - dudy
        w[self.solid] = 0.0
        return w

    def speed(self):
        uc = 0.5 * (self.u[:-1, :] + self.u[1:, :])
        vc = 0.5 * (self.v[:, :-1] + self.v[:, 1:])
        return np.hypot(uc, vc)

    def velocity_at(self, x, y):
        """Cell-centred velocity sampled at fractional cell coordinates."""
        uc = 0.5 * (self.u[:-1, :] + self.u[1:, :])
        vc = 0.5 * (self.v[:, :-1] + self.v[:, 1:])
        return _bilerp(uc, x, y), _bilerp(vc, x, y)

    def kinetic_energy(self):
        return 0.5 * float((self.speed() ** 2)[self.fluid].sum())


# --------------------------------------------------------------------------
def disc_mask(nx, ny, cx, cy, radius):
    x, y = np.meshgrid(np.arange(nx) + 0.5, np.arange(ny) + 0.5, indexing="ij")
    return (x - cx) ** 2 + (y - cy) ** 2 < radius ** 2
