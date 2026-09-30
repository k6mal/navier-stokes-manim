"""Shared look-and-feel: palette, type, and the colour maps for the fields."""

from __future__ import annotations
import numpy as np

# --------------------------------------------------------------------------
# palette
# --------------------------------------------------------------------------
BG        = "#0A0E17"     # deep navy-black, the ground for everything
BG_SOFT   = "#141A28"     # panels / cards
INK       = "#EAF0FA"     # primary text
INK_SOFT  = "#9AA6BD"     # secondary text
RULE      = "#2A3347"     # hairlines

# one colour per idea, used consistently from first mention to final equation
C_TIME    = "#6FD3F7"     # d v / d t      -- "how it changes here"
C_ADVECT  = "#FF7A8A"     # (v . grad) v   -- "the flow carries itself"
C_PRESS   = "#FFC24B"     # -grad p        -- "pushed from squeezed to free"
C_VISC    = "#A78BFA"     # mu lap v       -- "internal friction"
C_FORCE   = "#4ADE9B"     # f              -- "outside pushes"
C_DIV     = "#F49CE8"     # div v = 0      -- "no room to squeeze"
C_HILITE  = "#FFD166"

FONT = "Inter"

# type scale (manim units)
T_TITLE, T_H1, T_H2, T_BODY, T_SMALL = 1.05, 0.62, 0.48, 0.40, 0.31


# --------------------------------------------------------------------------
# colour maps
#
# Built as anchor lists and interpolated in linear-light so the ramps do not
# go muddy in the middle.  Zero maps to the page background, which makes the
# still fluid disappear and the moving fluid glow.
# --------------------------------------------------------------------------
def _hex(c: str) -> np.ndarray:
    c = c.lstrip("#")
    return np.array([int(c[i:i + 2], 16) for i in (0, 2, 4)], dtype=float) / 255.0


def _ramp(anchors, n=256) -> np.ndarray:
    """anchors: [(position 0..1, '#rrggbb'), ...] -> (n, 3) float array."""
    pos = np.array([a[0] for a in anchors])
    cols = np.stack([_hex(a[1]) for a in anchors])
    lin = cols ** 2.2                                   # to linear light
    x = np.linspace(0, 1, n)
    out = np.stack([np.interp(x, pos, lin[:, k]) for k in range(3)], axis=1)
    return np.clip(out ** (1 / 2.2), 0, 1)              # back to sRGB


def _lut(anchors, n=256) -> np.ndarray:
    return (_ramp(anchors, n) * 255).astype(np.uint8)


# vorticity: cool anticlockwise / warm clockwise, background at zero
VORTICITY_LUT = _lut([
    (0.00, "#B8F4FF"), (0.12, "#5AD9F5"), (0.27, "#1E86D6"),
    (0.40, "#123A73"), (0.50, BG),
    (0.60, "#5C1A2E"), (0.73, "#C33B4A"), (0.88, "#FF9147"), (1.00, "#FFE9B0"),
])

# speed / dye: a single warm glow out of the background
GLOW_LUT = _lut([
    (0.00, BG), (0.18, "#1B2A52"), (0.40, "#2E6FC4"),
    (0.62, "#49C6E8"), (0.82, "#B7F0D8"), (1.00, "#FFFFFF"),
])

# smoke plume: heat
FLAME_LUT = _lut([
    (0.00, BG), (0.16, "#2A1633"), (0.36, "#7A1E5C"),
    (0.58, "#D6403F"), (0.78, "#FF9A2E"), (0.93, "#FFE07A"), (1.00, "#FFFDF2"),
])

# pressure: low = cool, high = warm, mid = background
PRESSURE_LUT = _lut([
    (0.00, "#3FD0C9"), (0.28, "#176F84"), (0.50, BG),
    (0.72, "#8E5A17"), (1.00, "#FFD27A"),
])


def signed_to_u8(field: np.ndarray, limit: float, gamma: float = 0.62) -> np.ndarray:
    """Map a signed field to 0..255 centred on 128.

    `gamma` < 1 lifts the weak values, so vortices stay visible long after
    viscosity has eaten most of their strength - the picture then shows the
    structure of the flow rather than just its loudest moment.
    """
    x = np.clip(field / limit, -1.0, 1.0)
    x = np.sign(x) * np.abs(x) ** gamma
    return np.clip((x * 0.5 + 0.5) * 255.0, 0, 255).astype(np.uint8)


def unsigned_to_u8(field: np.ndarray, limit: float, gamma: float = 0.75) -> np.ndarray:
    x = np.clip(field / limit, 0.0, 1.0) ** gamma
    return np.clip(x * 255.0, 0, 255).astype(np.uint8)


def colorize(u8: np.ndarray, lut: np.ndarray) -> np.ndarray:
    """(nx, ny) uint8 -> (ny, nx, 3) uint8, already flipped for screen order."""
    return lut[u8].transpose(1, 0, 2)[::-1]
