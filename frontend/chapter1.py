"""Chapter 1 UI: Tea Rescue."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from io import BytesIO

import ipywidgets as widgets
import matplotlib.pyplot as plt
import numpy as np

from backend.tea import simulate_tea
from .common import (
    CYAN,
    GOLD,
    MUTED,
    NAVY,
    NAVY_2,
    WARNING_BG,
    WARNING_BORDER,
    WARNING_TEXT,
    chapter_screen,
    primary_button,
    read_asset_text,
    secondary_button,
    story_page,
)

TEA_CONTROL_POINTS = 10
DEFAULT_SPEED = 1.15
TEA_LEVEL_Y = 145
SLOSH_WARNING_THRESHOLD = 0.09
SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)


def _speed_plot_png(speed_points):
    values = np.asarray(speed_points, dtype=float)
    controls = np.arange(1, len(values) + 1)
    dense_x = np.linspace(1, len(values), 300)
    dense_v = np.interp(dense_x, controls, values)

    fig, ax = plt.subplots(figsize=(6.0, 1.85), dpi=110)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.plot(dense_x, dense_v, color=CYAN, linewidth=3)
    ax.scatter(controls, values, color=GOLD, s=42, zorder=5)
    ax.set_xlim(1, len(values))
    ax.set_ylim(0, 2.6)
    ax.set_xticks(controls)
    ax.set_xlabel("Journey", color=NAVY)
    ax.set_ylabel("Speed", color=NAVY)
    ax.tick_params(colors=NAVY, labelsize=8)
    ax.grid(alpha=.10)
    for spine in ax.spines.values():
        spine.set_color("#cadbed")
    plt.tight_layout(pad=.6)

    buffer = BytesIO()
    fig.savefig(buffer, format="png", facecolor="white", bbox_inches="tight", pad_inches=.04)
    plt.close(fig)
    return buffer.getvalue()


def _tea_watch_svg(speed_points):
    result = simulate_tea(speed_points)
    tea_t, tea_x, tea_q = result["t"], result["x"], result["q"]
    duration = max(float(tea_t[-1] - tea_t[0]), 1e-6)

    frame_indices = np.linspace(0, len(tea_t) - 1, 90).astype(int)
    x_anim = tea_x[frame_indices]
    q_anim = tea_q[frame_indices]

    warning_mask = np.abs(q_anim) > SLOSH_WARNING_THRESHOLD
    warning_mask = np.convolve(warning_mask.astype(int), np.ones(5, dtype=int), mode="same") > 0
    warning_values = ";".join("1" if active else "0" for active in warning_mask)

    stage_w, stage_h = 1000, 385
    journey_left, journey_right = 120, 880
    axis_y = 305
    cup_w, cup_h, cup_y = 235, 165, 72

    if np.isclose(tea_x[0], tea_x[-1]):
        progress = np.linspace(0, 1, len(x_anim))
    else:
        progress = (x_anim - tea_x[0]) / (tea_x[-1] - tea_x[0])
    progress = np.clip(progress, 0, 1)
    cup_x_positions = journey_left + progress * (journey_right - journey_left) - cup_w / 2

    slosh = np.clip(150.0 * q_anim, -44.0, 44.0)
    fill_paths, surface_paths = [], []
    for displacement in slosh:
        y_left = TEA_LEVEL_Y + displacement
        y_right = TEA_LEVEL_Y - displacement
        fill_paths.append(
            f"M140 {y_left:.2f} Q280 {TEA_LEVEL_Y:.2f} 420 {y_right:.2f} L420 350 L140 350 Z"
        )
        surface_paths.append(
            f"M150 {y_left:.2f} Q280 {TEA_LEVEL_Y:.2f} 410 {y_right:.2f}"
        )

    cup_root = ET.fromstring(read_asset_text("chapter1/tea-cup.svg"))
    tea_fill = cup_root.find(f".//{{{SVG_NS}}}path[@id='teaFill']")
    tea_surface = cup_root.find(f".//{{{SVG_NS}}}path[@id='teaSurface']")
    if tea_fill is None or tea_surface is None:
        raise ValueError("chapter1/tea-cup.svg must contain #teaFill and #teaSurface paths.")

    tea_fill.set("d", fill_paths[0])
    tea_surface.set("d", surface_paths[0])

    fill_animation = ET.SubElement(tea_fill, f"{{{SVG_NS}}}animate")
    fill_animation.attrib.update(
        attributeName="d",
        dur=f"{duration:.4f}s",
        repeatCount="indefinite",
        calcMode="linear",
        values=";".join(fill_paths),
    )
    surface_animation = ET.SubElement(tea_surface, f"{{{SVG_NS}}}animate")
    surface_animation.attrib.update(
        attributeName="d",
        dur=f"{duration:.4f}s",
        repeatCount="indefinite",
        calcMode="linear",
        values=";".join(surface_paths),
    )

    cup_root.set("width", str(cup_w))
    cup_root.set("height", str(cup_h))
    cup_root.set("viewBox", "0 0 600 420")
    cup_svg = ET.tostring(cup_root, encoding="unicode")

    translation_values = ";".join(f"{xpos:.2f} {cup_y:.2f}" for xpos in cup_x_positions)
    journey_positions = np.linspace(journey_left, journey_right, TEA_CONTROL_POINTS)
    markers = "".join(
        f"""
        <circle cx="{xpos:.2f}" cy="{axis_y}" r="7" fill="{CYAN}" stroke="white" stroke-width="3"/>
        <text x="{xpos:.2f}" y="{axis_y + 28}" text-anchor="middle" font-family="Arial"
              font-size="16" font-weight="800" fill="{NAVY}">{i}</text>
        """
        for i, xpos in enumerate(journey_positions, start=1)
    )

    return f"""
    <div style="width:100%;height:100%;display:flex;align-items:center;justify-content:center;overflow:hidden;background:white;">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {stage_w} {stage_h}"
           style="width:930px;height:360px;display:block;overflow:hidden;background:white;">
        <g opacity="0">
          <rect x="370" y="14" width="260" height="44" rx="22" fill="{WARNING_BG}"
                stroke="{WARNING_BORDER}" stroke-width="2"/>
          <text x="500" y="42" text-anchor="middle" font-family="Arial" font-size="16"
                font-weight="900" fill="{WARNING_TEXT}">⚠ TEA SLOSHING!</text>
          <animate attributeName="opacity" dur="{duration:.4f}s" repeatCount="indefinite"
                   calcMode="discrete" values="{warning_values}"/>
        </g>
        <line x1="{journey_left}" y1="{axis_y}" x2="{journey_right}" y2="{axis_y}"
              stroke="{NAVY}" stroke-width="4" stroke-linecap="round" opacity=".22"/>
        <text x="{journey_left}" y="{axis_y - 20}" text-anchor="middle" font-family="Arial"
              font-size="11" font-weight="800" fill="{MUTED}">START</text>
        <text x="{journey_right}" y="{axis_y - 20}" text-anchor="middle" font-family="Arial"
              font-size="11" font-weight="800" fill="{MUTED}">YOU</text>
        {markers}
        <text x="{stage_w / 2}" y="{axis_y + 58}" text-anchor="middle" font-family="Arial"
              font-size="13" font-weight="800" letter-spacing="3" fill="{MUTED}">JOURNEY</text>
        <g transform="translate({cup_x_positions[0]:.2f} {cup_y:.2f})">
          <animateTransform attributeName="transform" type="translate" dur="{duration:.4f}s"
                            repeatCount="indefinite" calcMode="linear" values="{translation_values}"/>
          {cup_svg}
        </g>
      </svg>
    </div>
    """


def start_chapter_1(game):
    state = {"baseline_seen": False, "changed_seen": False, "last_speed_points": None}

    sliders = [
        widgets.FloatSlider(
            value=DEFAULT_SPEED,
            min=.2,
            max=2.4,
            step=.1,
            description=str(i + 1),
            readout_format=".1f",
            continuous_update=False,
            style={"description_width": "15px"},
            layout=widgets.Layout(width="165px"),
        )
        for i in range(TEA_CONTROL_POINTS)
    ]
    for slider in sliders:
        slider.add_class("tea-slider")

    speed_plot = widgets.Image(format="png", layout=widgets.Layout(width="660px", height="200px"))
    tea_watch = widgets.HTML(value="", layout=widgets.Layout(width="960px", height="380px", overflow="hidden"))
    message = widgets.HTML()
    updating = {"active": False}

    def values():
        return np.array([slider.value for slider in sliders], dtype=float)

    def constant(v):
        return np.ptp(v) < 1e-10

    def render_plot():
        speed_plot.value = _speed_plot_png(values())

    def refresh_message():
        v = values()
        if not state["baseline_seen"]:
            text, color = "<b>STEP 1:</b> Keep all ten speeds equal and run the experiment.", GOLD
        elif constant(v):
            text, color = "<b>STEP 2:</b> Change some speed points so your sister speeds up and slows down.", CYAN
        else:
            text, color = "Great — now run this motion.", CYAN
        message.value = (
            f'<div style="width:730px;padding:8px 15px;border-radius:18px;border-left:4px solid {color};'
            f'color:{NAVY};font-size:13px;">{text}</div>'
        )

    def slider_changed(_):
        if updating["active"]:
            return
        render_plot()
        refresh_message()

    for slider in sliders:
        slider.observe(slider_changed, names="value")

    def screen_1():
        story_page(
            game,
            chapter=1,
            chapter_title="TEA RESCUE",
            image="chapter1/student-worried.png",
            eyebrow="THE NIGHT BEFORE THE PHYSICS FINAL",
            title="Physics is winning.",
            text="""
            Tomorrow is your high-school physics final.<br><br>
            You've been studying for hours, but nothing seems to be making sense.<br><br>
            You're exhausted, stressed, and overwhelmed.
            """,
            on_back=None,
            on_next=screen_2,
        )

    def screen_2():
        story_page(
            game,
            chapter=1,
            chapter_title="TEA RESCUE",
            image="chapter1/sister-shocked.png",
            eyebrow="YOUR SISTER WALKS IN",
            title="She gets worried.",
            text="""
            Your sister comes to check on you and immediately sees how badly you're struggling.<br><br>
            She decides that you clearly need something to help you relax.
            """,
            on_back=screen_1,
            on_next=screen_3,
        )

    def screen_3():
        story_page(
            game,
            chapter=1,
            chapter_title="TEA RESCUE",
            image="chapter1/sister-bringing-tea.png",
            eyebrow="A CUP OF TEA",
            title="Your sister wants to cheer you up.",
            text=f"""
            You’ve had a stressful day, so she’s bringing you a cup of tea.<br><br>
            She doesn’t want to spill a drop and make you even more stressed.<br><br>
            You decide to help her by controlling her speed along the journey.<br><br>
            <b>Can you keep the tea from sloshing and get it to you safely?</b><br><br>
            <span style="color:{MUTED};font-style:italic;">Try different ways of moving and watch what happens.</span>
            """,
            on_back=screen_2,
            on_next=show_controls,
            next_text="START EXPERIMENT →",
        )

    def show_controls():
        render_plot()
        refresh_message()

        run = primary_button("RUN AGAIN ▶" if state["baseline_seen"] else "RUN EXPERIMENT ▶", width="190px")
        reset = secondary_button("RESET", width="105px")

        def do_reset(_):
            updating["active"] = True
            for slider in sliders:
                slider.value = DEFAULT_SPEED
            updating["active"] = False
            render_plot()
            refresh_message()

        def run_experiment(_):
            v = values()
            if not state["baseline_seen"] and not constant(v):
                message.value = f'<div style="width:730px;padding:8px 15px;border-left:4px solid {GOLD};color:{NAVY};">Run the steady-speed example first.</div>'
                return

            state["last_speed_points"] = v.copy()
            if constant(v):
                state["baseline_seen"] = True
            else:
                state["changed_seen"] = True
            tea_watch.value = _tea_watch_svg(v)
            show_watch()

        reset.on_click(do_reset)
        run.on_click(run_experiment)

        content = widgets.VBox(
            [
                widgets.HTML(
                    f'<div style="text-align:center;color:{NAVY};font-size:21px;font-weight:900;">HOW SHOULD SHE MOVE?'
                    f'<div style="margin-top:2px;color:{MUTED};font-size:12px;font-weight:500;">Choose her speed at 10 moments.</div></div>'
                ),
                widgets.HBox(sliders[:5], layout=widgets.Layout(justify_content="center")),
                widgets.HBox(sliders[5:], layout=widgets.Layout(justify_content="center")),
                widgets.Box([speed_plot], layout=widgets.Layout(width="100%", height="200px", justify_content="center", align_items="center", overflow="hidden")),
                message,
                widgets.HBox([run, widgets.Box(layout=widgets.Layout(width="12px")), reset], layout=widgets.Layout(justify_content="center", overflow="hidden")),
            ],
            layout=widgets.Layout(width="100%", height="100%", align_items="center", justify_content="space-between", overflow="hidden"),
        )

        back = secondary_button("← BACK")
        back.on_click(lambda _: screen_3())
        game.show(chapter_screen(game, 1, "TEA RESCUE", content, widgets.HBox([back])))

    def show_watch():
        content = widgets.VBox(
            [
                widgets.HTML(
                    f'<div style="text-align:center;color:{NAVY};font-size:21px;font-weight:900;">WATCH THE TEA'
                    f'<div style="margin-top:3px;color:{MUTED};font-size:12px;font-weight:500;">Watch how the tea responds as the cup moves through the journey.</div></div>'
                ),
                widgets.Box([tea_watch], layout=widgets.Layout(width="100%", height="410px", justify_content="center", align_items="center", overflow="hidden")),
            ],
            layout=widgets.Layout(width="100%", height="100%", align_items="center", overflow="hidden"),
        )

        back = secondary_button("← CHANGE MOTION", width="165px")
        back.on_click(lambda _: show_controls())
        nxt = primary_button("WHAT HAPPENED? →" if state["changed_seen"] else "CHANGE THE SPEED →", width="195px")
        nxt.on_click(lambda _: show_discovery() if state["changed_seen"] else show_controls())
        footer = widgets.HBox([back, nxt], layout=widgets.Layout(width="100%", justify_content="space-between", align_items="center", overflow="hidden"))
        game.show(chapter_screen(game, 1, "TEA RESCUE", content, footer))

    def show_discovery():
        content = widgets.HTML(
            f"""
            <div style="width:100%;height:100%;display:flex;align-items:center;justify-content:center;">
              <div style="width:760px;margin:0 auto;text-align:center;color:{NAVY};">
                <div style="font-size:28px;font-weight:900;">What happened?</div>
                <div style="margin-top:26px;display:flex;justify-content:center;gap:30px;">
                  <div style="width:330px;height:205px;padding:25px 22px;box-sizing:border-box;border:2px solid {CYAN};border-radius:25px;display:flex;flex-direction:column;justify-content:center;">
                    <div style="color:{CYAN};font-size:18px;font-weight:900;">STEADY SPEED</div>
                    <div style="margin-top:24px;font-size:14px;line-height:1.55;">The cup was moving, but its speed wasn't changing.</div>
                    <div style="margin-top:25px;font-size:14px;font-weight:900;">The tea stayed calm.</div>
                  </div>
                  <div style="width:330px;height:205px;padding:25px 22px;box-sizing:border-box;border:2px solid {GOLD};border-radius:25px;display:flex;flex-direction:column;justify-content:center;">
                    <div style="color:{GOLD};font-size:18px;font-weight:900;">CHANGING SPEED</div>
                    <div style="margin-top:24px;font-size:14px;line-height:1.55;">When your sister sped up or slowed down, the tea responded.</div>
                    <div style="margin-top:25px;font-size:14px;font-weight:900;">The tea began to slosh.</div>
                  </div>
                </div>
                <div style="width:690px;margin:28px auto 0;color:{NAVY};font-size:18px;font-weight:900;line-height:1.5;">
                  Motion itself wasn't the problem.<br><span style="color:{CYAN};">Changing the motion disturbed what was inside.</span>
                </div>
              </div>
            </div>
            """,
            layout=widgets.Layout(width="100%", height="100%", overflow="hidden"),
        )
        back = secondary_button("← EXPERIMENT")
        back.on_click(lambda _: show_controls())
        nxt = primary_button("CONTINUE STORY →", width="190px")
        nxt.on_click(lambda _: screen_6())
        footer = widgets.HBox([back, nxt], layout=widgets.Layout(width="100%", justify_content="space-between", align_items="center"))
        game.show(chapter_screen(game, 1, "TEA RESCUE", content, footer))

    def screen_6():
        story_page(
            game,
            chapter=1,
            chapter_title="TEA RESCUE",
            image="chapter1/sister-happy.png",
            eyebrow="TEA DELIVERED",
            title="Success!",
            text="""
            Your sister makes it across safely with the tea.<br><br>
            No spill. No disaster.<br><br>
            And now you finally have something warm to help you relax.
            """,
            on_back=show_discovery,
            on_next=screen_7,
        )

    def screen_7():
        def finish():
            game.complete_chapter(1)
            game.unlock_chapter(2)
            game.show_chapters()

        story_page(
            game,
            chapter=1,
            chapter_title="TEA RESCUE",
            image="chapter1/student-relaxed.png",
            eyebrow="A LITTLE LATER...",
            title="Much better.",
            text="""
            The tea helps you relax.<br><br>
            You clear your head and finally return to studying calmly.<br><br>
            Maybe you can survive this physics exam after all.
            """,
            on_back=screen_6,
            on_next=finish,
            next_text="FINISH CHAPTER →",
        )

    screen_1()
