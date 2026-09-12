"""Core audio helpers for Audio Battle."""

from __future__ import annotations

import math


def clamp_pan(pan: float) -> float:
    """Clamp pan value to [-1.0, 1.0]."""
    return max(-1.0, min(1.0, pan))


def stereo_gains(pan: float) -> tuple[float, float]:
    """Return equal-power stereo gains for pan in [-1.0, 1.0]."""
    p = clamp_pan(pan)
    # Map [-1, 1] to [0, pi/2]
    angle = (p + 1.0) * (math.pi / 4.0)
    return math.cos(angle), math.sin(angle)
