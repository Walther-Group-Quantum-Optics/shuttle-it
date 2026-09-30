"""Shared frontend machinery for Shuttle it!.

Only UI mechanisms used by more than one chapter belong here. Chapter-specific
story and experiment logic stays in the chapter modules.
"""

from __future__ import annotations

import base64
import os
import tempfile
from functools import lru_cache
from io import BytesIO
from pathlib import Path

import ipywidgets as widgets
import matplotlib.pyplot as plt
import numpy as np
from IPython.display import HTML, display
from matplotlib.animation import FuncAnimation, PillowWriter

from backend.quantum import (
    START_CENTER,
    START_WIDTH,
    TARGET_CENTER,
    TARGET_LEFT,
    TARGET_RIGHT,
    TOTAL_TIME,
    TRAP_DEPTH,
    barrier_potential,
    interpolate_controls,
)

# ---------------------------------------------------------------------------
# Shared visual constants
# ---------------------------------------------------------------------------

GAME_W = 1100
GAME_H = 619
GAME_RADIUS = 28
GAME_WIDTH = f"{GAME_W}px"
GAME_HEIGHT = f"{GAME_H}px"

NAVY = "#20385e"
NAVY_2 = "#405f86"
CYAN = "#00dbe7"
CYAN_DARK = "#00c5d1"
GOLD = "#d99b10"
WHITE = "#ffffff"
MUTED = "#87a2c3"
LOCK_BG = "#eee8dd"
LOCK_TEXT = "#878787"
WARNING_BG = "#fff4e8"
WARNING_BORDER = "#f2a33a"
WARNING_TEXT = "#ad5c00"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = PROJECT_ROOT / "assets"


def asset_path(path: str) -> Path:
    """Return the absolute path to an asset."""

    return ASSET_ROOT / path


@lru_cache(maxsize=128)
def image_uri(path: str) -> str:
    """Return a data URI for an image asset, cached after first use."""

    file_path = asset_path(path)
    data = file_path.read_bytes()
    suffix = file_path.suffix.lower()
    mime = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".svg": "image/svg+xml",
    }.get(suffix, "application/octet-stream")
    encoded = base64.b64encode(data).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def read_asset_text(path: str) -> str:
    return asset_path(path).read_text(encoding="utf-8")


def install_css():
    """Install the game stylesheet in the current notebook output."""

    css = (ASSET_ROOT / "style.css").read_text(encoding="utf-8")
    display(HTML(f"<style>{css}</style>"))


def primary_button(text, width="180px", height="45px", font_size="15px"):
    button = widgets.Button(
        description=text,
        layout=widgets.Layout(
            width=width,
            height=height,
            min_height=height,
            max_height=height,
            overflow="hidden",
        ),
    )
    button.style.button_color = CYAN
    button.style.text_color = WHITE
    button.style.font_weight = "900"
    button.style.font_size = font_size
    button.add_class("pill-button")
    button.add_class("primary-button")
    return button


def secondary_button(text, width="135px", height="41px"):
    button = widgets.Button(
        description=text,
        layout=widgets.Layout(
            width=width,
            height=height,
            min_height=height,
            max_height=height,
            overflow="hidden",
        ),
    )
    button.style.button_color = "#f4f8fc"
    button.style.text_color = NAVY
    button.style.font_weight = "800"
    button.add_class("pill-button")
    button.add_class("secondary-button")
    return button


def chapter_topbar(game, chapter_number, chapter_title):
    back = secondary_button("‹  CHAPTERS", width="128px", height="39px")
    back.on_click(lambda _: game.show_chapters())

    title = widgets.HTML(
        f"""
        <div style="text-align:center;">
            <div style="color:{CYAN};font-size:10px;font-weight:900;letter-spacing:3px;">
                CHAPTER {chapter_number}
            </div>
            <div style="margin-top:2px;color:{NAVY};font-size:22px;font-weight:900;">
                {chapter_title}
            </div>
        </div>
        """
    )

    spacer = widgets.Box(layout=widgets.Layout(width="128px"))

    return widgets.HBox(
        [back, title, spacer],
        layout=widgets.Layout(
            width="100%",
            height="61px",
            padding="9px 24px 0 24px",
            box_sizing="border-box",
            align_items="center",
            justify_content="space-between",
            overflow="hidden",
        ),
    )


def chapter_screen(game, chapter_number, chapter_title, content, footer=None):
    if footer is None:
        footer = widgets.Box()

    body = widgets.Box(
        [content],
        layout=widgets.Layout(
            width="100%",
            height="500px",
            padding="8px 24px",
            box_sizing="border-box",
            justify_content="center",
            align_items="center",
            overflow="hidden",
        ),
    )

    footer_box = widgets.Box(
        [footer],
        layout=widgets.Layout(
            width="100%",
            height="58px",
            padding="4px 24px 8px 24px",
            box_sizing="border-box",
            overflow="hidden",
        ),
    )

    return widgets.VBox(
        [chapter_topbar(game, chapter_number, chapter_title), body, footer_box],
        layout=widgets.Layout(width="100%", height="100%", overflow="hidden"),
    )


def story_page(
    game,
    *,
    chapter,
    chapter_title,
    image,
    eyebrow,
    title,
    text,
    on_back,
    on_next,
    next_text="CONTINUE →",
):
    """Render the shared two-column story layout."""

    image_widget = widgets.HTML(
        f"""
        <div style="width:405px;height:415px;display:flex;align-items:center;justify-content:center;">
            <img src="{image_uri(image)}"
                 style="max-width:100%;max-height:100%;display:block;object-fit:contain;">
        </div>
        """
    )

    panel = widgets.HTML(
        f"""
        <div style="width:445px;padding:29px 32px;box-sizing:border-box;
                    border:2px solid rgba(172,201,230,.70);border-radius:25px;
                    background:white;color:{NAVY};">
            <div style="color:{GOLD};font-size:10px;font-weight:900;letter-spacing:2px;">
                {eyebrow}
            </div>
            <div style="margin-top:10px;font-size:29px;line-height:1.18;font-weight:900;">
                {title}
            </div>
            <div style="margin-top:18px;color:{NAVY_2};font-size:15px;line-height:1.58;">
                {text}
            </div>
        </div>
        """
    )

    content = widgets.HBox(
        [image_widget, widgets.Box(layout=widgets.Layout(width="20px")), panel],
        layout=widgets.Layout(
            width="100%",
            height="100%",
            justify_content="center",
            align_items="center",
            overflow="hidden",
        ),
    )

    back = secondary_button("← BACK")
    if on_back is None:
        back.disabled = True
    else:
        back.on_click(lambda _: on_back())

    nxt = primary_button(next_text, width="225px")
    nxt.on_click(lambda _: on_next())

    footer = widgets.HBox(
        [back, nxt],
        layout=widgets.Layout(
            width="100%",
            justify_content="space-between",
            align_items="center",
            overflow="hidden",
        ),
    )

    game.show(chapter_screen(game, chapter, chapter_title, content, footer))


def make_quantum_controls(center_start_values, width_start_values):
    """Build the shared 8-point center/width control rows.

    The first point is disabled in the UI and is also hard-enforced when values
    are read, matching the backend's safety check.
    """

    centers0 = np.asarray(center_start_values, dtype=float).copy()
    widths0 = np.asarray(width_start_values, dtype=float).copy()

    if len(centers0) != len(widths0):
        raise ValueError("Center and width controls must have equal length.")
    if len(centers0) < 2:
        raise ValueError("At least two control points are required.")

    centers0[0] = START_CENTER
    widths0[0] = START_WIDTH

    center_sliders = []
    center_labels = []
    width_sliders = []
    width_labels = []

    for i in range(len(centers0)):
        fixed = i == 0

        center_slider = widgets.FloatSlider(
            value=float(centers0[i]),
            min=-5.0,
            max=10.0,
            step=.25,
            description="",
            readout=False,
            continuous_update=False,
            disabled=fixed,
            layout=widgets.Layout(width="116px", height="25px", overflow="hidden"),
        )
        center_slider.add_class("quantum-slider")
        if fixed:
            center_slider.add_class("fixed-control")

        width_slider = widgets.FloatSlider(
            value=float(widths0[i]),
            min=.5,
            max=2.0,
            step=.05,
            description="",
            readout=False,
            continuous_update=False,
            disabled=fixed,
            layout=widgets.Layout(width="116px", height="25px", overflow="hidden"),
        )
        width_slider.add_class("quantum-slider")
        if fixed:
            width_slider.add_class("fixed-control")

        center_labels.append(
            widgets.HTML(layout=widgets.Layout(width="116px", height="23px", overflow="hidden"))
        )
        width_labels.append(
            widgets.HTML(layout=widgets.Layout(width="116px", height="23px", overflow="hidden"))
        )
        center_sliders.append(center_slider)
        width_sliders.append(width_slider)

    def center_values():
        values = np.array([slider.value for slider in center_sliders], dtype=float)
        values[0] = START_CENTER
        return values

    def width_values():
        values = np.array([slider.value for slider in width_sliders], dtype=float)
        values[0] = START_WIDTH
        return values

    def update_labels():
        centers = center_values()
        widths = width_values()

        for i in range(len(center_sliders)):
            fixed = i == 0
            point_text = "1&nbsp;🔒" if fixed else str(i + 1)
            opacity = ".48" if fixed else "1"

            center_labels[i].value = f"""
            <div style="width:116px;display:flex;justify-content:space-between;align-items:center;
                        padding:0 2px;box-sizing:border-box;color:{NAVY};opacity:{opacity};font-size:12px;">
                <b>{point_text}</b><span>{centers[i]:.1f}</span>
            </div>
            """
            width_labels[i].value = f"""
            <div style="width:116px;display:flex;justify-content:space-between;align-items:center;
                        padding:0 2px;box-sizing:border-box;color:{NAVY};opacity:{opacity};font-size:12px;">
                <b>{point_text}</b><span>{widths[i]:.2f}</span>
            </div>
            """

    center_controls = [
        widgets.VBox(
            [center_labels[i], center_sliders[i]],
            layout=widgets.Layout(width="120px", height="46px", align_items="center", overflow="hidden"),
        )
        for i in range(len(center_sliders))
    ]
    width_controls = [
        widgets.VBox(
            [width_labels[i], width_sliders[i]],
            layout=widgets.Layout(width="120px", height="46px", align_items="center", overflow="hidden"),
        )
        for i in range(len(width_sliders))
    ]

    centers_row = widgets.HBox(
        center_controls,
        layout=widgets.Layout(
            width="100%", height="46px", justify_content="center", align_items="center", overflow="hidden"
        ),
    )
    widths_row = widgets.HBox(
        width_controls,
        layout=widgets.Layout(
            width="100%", height="46px", justify_content="center", align_items="center", overflow="hidden"
        ),
    )

    update_labels()

    return {
        "center_sliders": center_sliders,
        "width_sliders": width_sliders,
        "center_values": center_values,
        "width_values": width_values,
        "update_labels": update_labels,
        "centers_row": centers_row,
        "widths_row": widths_row,
    }


def make_quantum_plan_plot(center_points, width_points, barrier=None, title="Your trap plan"):
    """Render the planning graph used by Chapters 2 and 3."""

    centers = np.asarray(center_points, dtype=float).copy()
    widths = np.asarray(width_points, dtype=float).copy()
    centers[0] = START_CENTER
    widths[0] = START_WIDTH

    control_times = np.linspace(0.0, TOTAL_TIME, len(centers))
    dense_time = np.linspace(0.0, TOTAL_TIME, 400)
    mu, sigma = interpolate_controls(centers, widths, dense_time, TOTAL_TIME)

    lower = mu - 2.0 * sigma
    upper = mu + 2.0 * sigma

    fig, ax = plt.subplots(figsize=(7.65, 2.65), dpi=110)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    ax.axhspan(TARGET_LEFT, TARGET_RIGHT, alpha=.16)
    ax.axhline(TARGET_CENTER, linestyle="--", linewidth=1.7, alpha=.45)
    ax.text(.35, TARGET_CENTER + .35, "TARGET REGION", color=NAVY_2, fontsize=8, fontweight="bold")

    if barrier is not None:
        barrier_center, barrier_width, _ = barrier
        ax.axhspan(barrier_center - barrier_width, barrier_center + barrier_width, alpha=.20)
        ax.axhline(barrier_center, linestyle=":", linewidth=2, alpha=.60)
        ax.text(.35, barrier_center + .18, "BARRIER", color=GOLD, fontsize=8, fontweight="900")

    ax.fill_between(
        dense_time,
        lower,
        upper,
        alpha=.17,
        label=r"Trap span  $\mu(t)\pm2\sigma(t)$",
    )
    ax.plot(dense_time, mu, linewidth=3, label=r"Center  $\mu(t)$")
    ax.scatter(control_times[1:], centers[1:], s=46, zorder=7, label="Your controls")
    ax.scatter([control_times[0]], [centers[0]], s=78, marker="s", zorder=8, label="Fixed start")

    ax.set_xlim(0, TOTAL_TIME)
    ax.set_ylim(-10, 14)
    ax.set_xlabel("Time", color=NAVY, fontsize=9)
    ax.set_ylabel("Position", color=NAVY, fontsize=9)
    ax.set_title(title, color=NAVY, fontsize=13, fontweight="bold", pad=5)
    ax.tick_params(colors=NAVY, labelsize=8)
    ax.grid(alpha=.10)

    for spine in ax.spines.values():
        spine.set_color("#cbdbea")

    ax.legend(loc="lower right", frameon=False, fontsize=7.0, ncol=2)
    fig.subplots_adjust(left=.11, right=.985, top=.86, bottom=.20)

    buffer = BytesIO()
    fig.savefig(buffer, format="png", facecolor="white", bbox_inches="tight", pad_inches=.04)
    plt.close(fig)
    return buffer.getvalue()


def make_quantum_animation(result, barrier=None, title=None):
    """Build the shared quantum animation for Chapters 2 and 3."""

    t = np.asarray(result["t"])
    x = np.asarray(result["x"])
    density = np.asarray(result["density"])
    center_t = np.asarray(result["mu"])
    width_t = np.asarray(result["sigma"])

    if barrier is None:
        barrier_curve = np.zeros_like(x)
        title = title or "Shuttling the atom"
    else:
        barrier_curve = np.asarray(result.get("barrier", barrier_potential(x, barrier)))
        title = title or "Crossing the barrier"

    frames = np.linspace(0, len(t) - 1, min(85, len(t))).astype(int)
    global_density_max = max(float(np.max(density)), 1e-12)
    density_baseline = -0.93

    fig, ax = plt.subplots(figsize=(8.5, 3.45), dpi=100)
    fig.patch.set_facecolor("white")
    fig.subplots_adjust(left=.11, right=.985, top=.84, bottom=.22)

    def update(frame):
        ax.clear()
        ax.set_facecolor("white")

        rho = density[frame]
        mu = float(center_t[frame])
        sigma = float(width_t[frame])
        V_trap = TRAP_DEPTH * np.exp(-((x - mu) ** 2) / (2.0 * sigma**2))

        rho_scaled = rho / global_density_max
        density_visual = density_baseline + .43 * rho_scaled
        visible = rho_scaled > .002
        density_line = np.where(visible, density_visual, np.nan)

        ax.axvspan(TARGET_LEFT, TARGET_RIGHT, alpha=.10)
        target_label_y = .34 if barrier is not None else .15
        ax.text(TARGET_CENTER, target_label_y, "TARGET", ha="center", color=CYAN, fontsize=10, fontweight="900")

        ax.fill_between(x, 0, V_trap, alpha=.07)
        ax.plot(x, V_trap, linewidth=3, label="Optical trap")

        if barrier is not None:
            center, _, height = barrier
            ax.fill_between(x, 0, barrier_curve, alpha=.18)
            ax.plot(x, barrier_curve, linewidth=2.5, label="Barrier")
            ax.text(center, height + .05, "BARRIER", ha="center", color=GOLD, fontsize=9, fontweight="900")

        ax.fill_between(x, density_baseline, density_visual, where=visible, alpha=.30)
        ax.plot(x, density_line, linewidth=2.3, label="Atom")

        ax.axhline(0, linewidth=1, alpha=.15)
        ax.axvline(mu, linestyle="--", linewidth=1, alpha=.16)
        ax.set_xlim(-8, 12)
        ymax = max(.40, barrier[2] * 1.5) if barrier is not None else .22
        ax.set_ylim(-1.18, ymax)
        ax.set_yticks([])
        ax.set_xlabel("Position", color=NAVY, fontsize=10, labelpad=7)
        ax.tick_params(colors=NAVY)
        ax.grid(axis="x", alpha=.06)
        ax.set_title(title, color=NAVY, fontsize=15, fontweight="bold", pad=7)
        ax.legend(loc="upper left", frameon=False, fontsize=8 if barrier is not None else 9)

        for spine in ax.spines.values():
            spine.set_color("#d5e1ed")

    animation = FuncAnimation(fig, update, frames=frames, interval=65, blit=False)
    plt.close(fig)
    return animation


def animation_to_html(animation, max_width=860, max_height=350, fps=17):
    """Render a Matplotlib animation to an inline GIF HTML block."""

    temp_file = tempfile.NamedTemporaryFile(suffix=".gif", delete=False)
    path = temp_file.name
    temp_file.close()

    try:
        animation.save(path, writer=PillowWriter(fps=fps), dpi=85)
        data = Path(path).read_bytes()
    finally:
        if os.path.exists(path):
            os.remove(path)

    encoded = base64.b64encode(data).decode("ascii")
    return f"""
    <div style="width:100%;height:100%;display:flex;align-items:center;justify-content:center;overflow:hidden;">
        <img src="data:image/gif;base64,{encoded}"
             style="max-width:{max_width}px;max-height:{max_height}px;width:auto;height:auto;display:block;object-fit:contain;">
    </div>
    """
