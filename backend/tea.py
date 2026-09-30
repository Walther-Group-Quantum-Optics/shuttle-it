"""Classical tea-sloshing backend for Shuttle it!.

The frontend supplies a small number of speed control points. This module
interpolates the speed profile and solves a damped driven oscillator for the
tea displacement. It has no UI dependencies.
"""

from __future__ import annotations

import numpy as np
from scipy.integrate import cumulative_trapezoid, solve_ivp
from scipy.interpolate import PchipInterpolator


def simulate_tea(
    speed_points,
    T: float = 6.0,
    x0: float = -4.0,
    omega: float = 3.2,
    gamma: float = 0.08,
    N: int = 600,
):
    """Simulate the cup motion and tea slosh.

    Parameters
    ----------
    speed_points:
        Speed values at equally spaced control times.
    T:
        Total journey duration.
    x0:
        Initial cup position.
    omega:
        Natural slosh frequency.
    gamma:
        Damping coefficient.
    N:
        Number of output time samples.

    Returns
    -------
    dict
        Keys: ``t``, ``x``, ``v``, ``a``, ``q``.
    """

    speed_points = np.asarray(speed_points, dtype=float)

    if speed_points.ndim != 1 or len(speed_points) < 2:
        raise ValueError("speed_points must be a 1D array with at least 2 values.")
    if not np.all(np.isfinite(speed_points)):
        raise ValueError("speed_points must contain only finite values.")
    if T <= 0:
        raise ValueError("T must be positive.")
    if N < 3:
        raise ValueError("N must be at least 3.")
    if omega <= 0:
        raise ValueError("omega must be positive.")
    if gamma < 0:
        raise ValueError("gamma must be nonnegative.")

    t = np.linspace(0.0, T, N)
    control_times = np.linspace(0.0, T, len(speed_points))

    speed_function = PchipInterpolator(control_times, speed_points)
    acceleration_function = speed_function.derivative()

    v = np.asarray(speed_function(t), dtype=float)
    a = np.asarray(acceleration_function(t), dtype=float)
    x = x0 + cumulative_trapezoid(v, t, initial=0.0)

    def rhs(time, y):
        q, qdot = y
        forcing = float(acceleration_function(time))
        return (
            qdot,
            -2.0 * gamma * qdot - omega**2 * q - forcing,
        )

    solution = solve_ivp(
        rhs,
        (0.0, T),
        (0.0, 0.0),
        t_eval=t,
        rtol=1e-8,
        atol=1e-10,
    )

    if not solution.success:
        raise RuntimeError(f"Tea simulation failed: {solution.message}")

    q = np.asarray(solution.y[0], dtype=float)

    return {
        "t": t,
        "x": x,
        "v": v,
        "a": a,
        "q": q,
    }
