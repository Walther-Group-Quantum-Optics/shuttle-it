"""1D quantum transport backend for Shuttle it!.

This module contains the complete numerical model used by both quantum
chapters. Chapter 2 calls :func:`simulate_quantum` with no barrier. Chapter 3
passes a Gaussian barrier tuple ``(center, width, height)``.

Units
-----
The game uses dimensionless units with ħ = 1 and m = 1.
"""

from __future__ import annotations

from functools import lru_cache

import numpy as np
from scipy.interpolate import PchipInterpolator
from scipy.integrate import trapezoid
from scipy.linalg import solve_banded
from scipy.sparse import diags
from scipy.sparse.linalg import eigsh

# ---------------------------------------------------------------------------
# Physical/game constants that define the quantum experiment itself.
# They live in the backend so the solver and frontend cannot silently disagree.
# ---------------------------------------------------------------------------

START_CENTER = -3.5
START_WIDTH = 1.0
TRAP_DEPTH = -1.0

TARGET_LEFT = 5.0
TARGET_RIGHT = 10.0
TARGET_CENTER = 0.5 * (TARGET_LEFT + TARGET_RIGHT)

TOTAL_TIME = 20.0
DEFAULT_NT = 500
DEFAULT_XMIN = -40.0
DEFAULT_XMAX = 40.0
DEFAULT_NX = 2500

ABSORBER_START = 15.0
ABSORBER_STRENGTH = 0.001


def _prepare_controls(center_points, width_points):
    """Validate controls and enforce the fixed initial trap."""

    centers = np.asarray(center_points, dtype=float).copy()
    widths = np.asarray(width_points, dtype=float).copy()

    if centers.ndim != 1 or widths.ndim != 1:
        raise ValueError("center_points and width_points must be 1D arrays.")
    if len(centers) != len(widths):
        raise ValueError("center_points and width_points must have equal length.")
    if len(centers) < 2:
        raise ValueError("At least two quantum control points are required.")
    if not np.all(np.isfinite(centers)) or not np.all(np.isfinite(widths)):
        raise ValueError("Quantum controls must contain only finite values.")
    if np.any(widths <= 0):
        raise ValueError("Trap widths must be positive.")

    centers[0] = START_CENTER
    widths[0] = START_WIDTH
    return centers, widths


def interpolate_controls(center_points, width_points, t, total_time: float = TOTAL_TIME):
    """Interpolate the user controls onto arbitrary times using PCHIP.

    The first point is always forced to the physical initial trap state.

    Returns
    -------
    (mu, sigma): tuple[np.ndarray, np.ndarray]
        Trap center and width evaluated at ``t``.
    """

    centers, widths = _prepare_controls(center_points, width_points)
    t = np.asarray(t, dtype=float)

    if total_time <= 0:
        raise ValueError("total_time must be positive.")
    if np.any(t < -1e-12) or np.any(t > total_time + 1e-12):
        raise ValueError("Interpolation times must lie inside [0, total_time].")

    control_times = np.linspace(0.0, total_time, len(centers))
    mu_function = PchipInterpolator(control_times, centers)
    sigma_function = PchipInterpolator(control_times, widths)

    mu = np.asarray(mu_function(t), dtype=float)
    sigma = np.maximum(np.asarray(sigma_function(t), dtype=float), 0.1)
    return mu, sigma


def trap_potential(x, center, width):
    """Attractive Gaussian optical trap."""

    x = np.asarray(x, dtype=float)
    width = float(width)
    if width <= 0:
        raise ValueError("Trap width must be positive.")

    return TRAP_DEPTH * np.exp(-((x - float(center)) ** 2) / (2.0 * width**2))


def barrier_potential(x, barrier=None):
    """Return the fixed Gaussian barrier, or zero when ``barrier`` is None.

    ``barrier`` is the tuple ``(center, width, height)``.
    """

    x = np.asarray(x, dtype=float)

    if barrier is None:
        return np.zeros_like(x)

    if len(barrier) != 3:
        raise ValueError("barrier must be (center, width, height).")

    center, width, height = map(float, barrier)

    if width <= 0:
        raise ValueError("Barrier width must be positive.")
    if height < 0:
        raise ValueError("Barrier height must be nonnegative.")

    return height * np.exp(-((x - center) ** 2) / (2.0 * width**2))


def absorbing_potential(
    x,
    start: float = ABSORBER_START,
    strength: float = ABSORBER_STRENGTH,
):
    """Symmetric positive absorber profile used as ``-i V_abs``."""

    x = np.asarray(x, dtype=float)

    if start <= 0:
        raise ValueError("Absorber start must be positive.")
    if strength < 0:
        raise ValueError("Absorber strength must be nonnegative.")

    V_abs = np.zeros_like(x)
    right = x > start
    left = x < -start

    V_abs[right] = strength * (np.cosh(x[right] - start) - 1.0)
    V_abs[left] = strength * (np.cosh(-x[left] - start) - 1.0)
    return V_abs


@lru_cache(maxsize=8)
def _cached_initial_state(xmin: float, xmax: float, Nx: int):
    """Compute and cache the prepared ground state for a numerical grid.

    The returned arrays must never be mutated directly by callers. Public
    :func:`initial_ground_state` returns copies.
    """

    x = np.linspace(float(xmin), float(xmax), int(Nx))
    dx = x[1] - x[0]
    N_inner = len(x) - 2

    V0 = trap_potential(x, START_CENTER, START_WIDTH)[1:-1]

    kinetic_diag = 1.0 / dx**2
    kinetic_off = -1.0 / (2.0 * dx**2)

    H0 = diags(
        [
            kinetic_off * np.ones(N_inner - 1),
            kinetic_diag * np.ones(N_inner) + V0,
            kinetic_off * np.ones(N_inner - 1),
        ],
        offsets=[-1, 0, 1],
        format="csc",
    )

    _, vectors = eigsh(H0, k=1, which="SA")
    psi_inner = vectors[:, 0].astype(complex)
    psi_inner /= np.sqrt(np.sum(np.abs(psi_inner) ** 2) * dx)

    psi = np.zeros(len(x), dtype=complex)
    psi[1:-1] = psi_inner
    return x, psi


def initial_ground_state(
    xmin: float = DEFAULT_XMIN,
    xmax: float = DEFAULT_XMAX,
    Nx: int = DEFAULT_NX,
):
    """Return ``(x, psi0)`` for the prepared optical-trap ground state."""

    if xmax <= xmin:
        raise ValueError("xmax must exceed xmin.")
    if Nx < 5:
        raise ValueError("Nx must be at least 5.")

    x, psi = _cached_initial_state(float(xmin), float(xmax), int(Nx))
    return x.copy(), psi.copy()


def target_probability(density, x):
    """Integrate probability density inside the destination region."""

    density = np.asarray(density, dtype=float)
    x = np.asarray(x, dtype=float)

    if density.shape != x.shape:
        raise ValueError("density and x must have the same shape.")

    mask = (x >= TARGET_LEFT) & (x <= TARGET_RIGHT)
    if np.count_nonzero(mask) < 2:
        return 0.0

    value = trapezoid(density[mask], x[mask])
    return float(np.clip(value, 0.0, 1.0))


def simulate_quantum(
    center_points,
    width_points,
    barrier=None,
    T: float = TOTAL_TIME,
    Nt: int = DEFAULT_NT,
    xmin: float = DEFAULT_XMIN,
    xmax: float = DEFAULT_XMAX,
    Nx: int = DEFAULT_NX,
):
    """Run the 1D Crank–Nicolson quantum shuttle simulation.

    Parameters
    ----------
    center_points, width_points:
        User controls at equally spaced times. The first control is forced to
        ``START_CENTER`` and ``START_WIDTH``.
    barrier:
        Optional ``(center, width, height)`` Gaussian barrier. ``None`` gives
        the Chapter 2 experiment; a tuple gives Chapter 3.
    T, Nt, xmin, xmax, Nx:
        Numerical grid parameters.

    Returns
    -------
    dict
        ``t``, ``x``, ``density``, ``mu``, ``sigma``, ``barrier``,
        ``target_probability``, ``survival_probability``, ``center_points``,
        and ``width_points``.
    """

    centers, widths = _prepare_controls(center_points, width_points)

    if T <= 0:
        raise ValueError("T must be positive.")
    if Nt < 3:
        raise ValueError("Nt must be at least 3.")
    if xmax <= xmin:
        raise ValueError("xmax must exceed xmin.")
    if Nx < 5:
        raise ValueError("Nx must be at least 5.")

    x, psi = initial_ground_state(xmin=xmin, xmax=xmax, Nx=Nx)
    t = np.linspace(0.0, T, Nt)
    dx = x[1] - x[0]
    dt = t[1] - t[0]

    control_times = np.linspace(0.0, T, len(centers))
    mu_function = PchipInterpolator(control_times, centers)
    sigma_function = PchipInterpolator(control_times, widths)

    mu_t = np.asarray(mu_function(t), dtype=float)
    sigma_t = np.maximum(np.asarray(sigma_function(t), dtype=float), 0.1)

    V_barrier = barrier_potential(x, barrier)
    V_abs = absorbing_potential(x)

    N_inner = Nx - 2
    kinetic_diag = 1.0 / dx**2
    kinetic_off = -1.0 / (2.0 * dx**2)

    A_off = 1j * dt * kinetic_off / 2.0
    B_off = -1j * dt * kinetic_off / 2.0

    density_history = np.empty((Nt, Nx), dtype=np.float32)
    density_history[0] = np.abs(psi) ** 2

    for n in range(Nt - 1):
        # Midpoint Hamiltonian gives second-order time accuracy.
        t_mid = 0.5 * (t[n] + t[n + 1])
        mu_mid = float(mu_function(t_mid))
        sigma_mid = max(float(sigma_function(t_mid)), 0.1)

        V_total = (
            trap_potential(x, mu_mid, sigma_mid)
            + V_barrier
            - 1j * V_abs
        )

        H_diag = kinetic_diag + V_total[1:-1]
        A_diag = 1.0 + 1j * dt * H_diag / 2.0
        B_diag = 1.0 - 1j * dt * H_diag / 2.0

        current = psi[1:-1]
        rhs = B_diag * current
        rhs[1:] += B_off * current[:-1]
        rhs[:-1] += B_off * current[1:]

        ab = np.zeros((3, N_inner), dtype=complex)
        ab[0, 1:] = A_off
        ab[1, :] = A_diag
        ab[2, :-1] = A_off

        next_inner = solve_banded((1, 1), ab, rhs, check_finite=False)

        psi.fill(0.0)
        psi[1:-1] = next_inner

        # Do not renormalize. Norm loss is the intended absorber loss.
        density_history[n + 1] = np.abs(psi) ** 2

    final_density = np.abs(psi) ** 2
    score = target_probability(final_density, x)
    survival = float(trapezoid(final_density, x))

    return {
        "t": t,
        "x": x,
        "density": density_history,
        "mu": mu_t,
        "sigma": sigma_t,
        "barrier": V_barrier,
        "target_probability": score,
        "survival_probability": survival,
        "center_points": centers,
        "width_points": widths,
    }
