"""Chapter 2 UI: Quantum Lab."""

from __future__ import annotations

from io import BytesIO

import ipywidgets as widgets
import matplotlib.pyplot as plt
import numpy as np

from backend.quantum import (
    START_CENTER,
    START_WIDTH,
    TARGET_CENTER,
    TOTAL_TIME,
    TRAP_DEPTH,
    simulate_quantum,
)
from .common import (
    CYAN,
    GOLD,
    MUTED,
    NAVY,
    NAVY_2,
    animation_to_html,
    chapter_screen,
    make_quantum_animation,
    make_quantum_controls,
    make_quantum_plan_plot,
    primary_button,
    secondary_button,
    story_page,
)

CONTROL_POINTS = 8
PASS_THRESHOLD = 0.85


def _warmup_preview_png(center, width):
    x = np.linspace(-8, 12, 700)
    potential = TRAP_DEPTH * np.exp(-((x - center) ** 2) / (2.0 * width**2))

    # The density vertical placement is schematic; only its horizontal response
    # is physical in this teaching preview.
    atom_width = .42 + .48 * width
    density = np.exp(-((x - center) ** 2) / (2.0 * atom_width**2))
    density /= max(float(density.max()), 1e-12)
    baseline = -.93
    density_visual = baseline + .43 * density
    visible = density > .003

    fig, ax = plt.subplots(figsize=(7.0, 2.4), dpi=105)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.fill_between(x, 0, potential, alpha=.07)
    ax.plot(x, potential, linewidth=3, label="Optical trap")
    ax.fill_between(x, baseline, density_visual, where=visible, alpha=.30)
    ax.plot(x, np.where(visible, density_visual, np.nan), linewidth=2.3, label="Atom")
    ax.axhline(0, linewidth=1, alpha=.15)
    ax.axvline(center, linestyle="--", linewidth=1, alpha=.20)
    ax.text(center, -1.075, "CENTER", ha="center", va="top", color=MUTED, fontsize=8, fontweight="bold")
    ax.set_xlim(-8, 12)
    ax.set_ylim(-1.18, .18)
    ax.set_yticks([])
    ax.set_xlabel("Position", color=NAVY)
    ax.tick_params(colors=NAVY)
    ax.grid(axis="x", alpha=.07)
    ax.legend(loc="upper right", frameon=False, fontsize=9)
    for spine in ax.spines.values():
        spine.set_color("#d5e1ed")
    plt.tight_layout(pad=.6)

    buffer = BytesIO()
    fig.savefig(buffer, format="png", facecolor="white", bbox_inches="tight", pad_inches=.04)
    plt.close(fig)
    return buffer.getvalue()


def start_chapter_2(game):
    default_centers = np.linspace(START_CENTER, TARGET_CENTER, CONTROL_POINTS)
    default_widths = np.full(CONTROL_POINTS, START_WIDTH)

    state = {
        "warm_center_changed": False,
        "warm_width_changed": False,
        "centers": default_centers.copy(),
        "widths": default_widths.copy(),
        "last_result": None,
    }

    def screen_1():
        story_page(
            game,
            chapter=2,
            chapter_title="QUANTUM LAB",
            image="chapter2/new-chapter.png",
            eyebrow="A NEW CHAPTER",
            title="You made it to university.",
            text=f"""
            You graduated high school—and against all odds, you decided to pursue <b>physics</b>.<br><br>
            Today is your first day in the quantum physics lab.<br><br>
            You have no idea what your professor has planned for you.<br><br>
            <span style="color:{MUTED};font-style:italic;">Time to find out what quantum physics actually looks like.</span>
            """,
            on_back=None,
            on_next=screen_2,
            next_text="ENTER THE LAB →",
        )

    def screen_2():
        story_page(
            game,
            chapter=2,
            chapter_title="QUANTUM LAB",
            image="chapter2/quantum-lab.png",
            eyebrow="WELCOME TO THE QUANTUM LAB",
            title="Things are different down here.",
            text=f"""
            Your professor starts with a warning:<br><br>
            Atoms aren’t tiny balls sitting at one exact position.<br><br>
            Instead, their quantum state can spread out through space—more like a <b>wave</b> than a point particle.<br><br>
            That means moving an atom isn’t quite like moving an ordinary object.<br><br>
            <span style="color:{MUTED};font-style:italic;">So... how do you get hold of something that behaves like a wave?</span>
            """,
            on_back=screen_1,
            on_next=screen_3,
            next_text="KEEP LISTENING →",
        )

    def screen_3():
        story_page(
            game,
            chapter=2,
            chapter_title="QUANTUM LAB",
            image="chapter2/catching-atom.png",
            eyebrow="CATCHING AN ATOM",
            title="Your professor has a trick.",
            text=f"""
            <div style="color:{CYAN};font-size:22px;font-weight:900;margin-bottom:14px;">Light.</div>
            With carefully arranged laser light, you can create regions that hold atoms in place.<br><br>
            This is called an <b>optical trap</b>.<br><br>
            Move the trap, and you may be able to bring the atom along with it.<br><br>
            <span style="color:{MUTED};font-style:italic;">Your professor smiles. “Want to try?”</span>
            """,
            on_back=screen_2,
            on_next=screen_4,
            next_text="SHOW ME THE TRAP →",
        )

    def screen_4():
        story_page(
            game,
            chapter=2,
            chapter_title="QUANTUM LAB",
            image="chapter2/meet-trap.png",
            eyebrow="MEET YOUR TRAP",
            title="This one has two controls.",
            text=f"""
            Today, you’ll work with a <b>Gaussian optical trap</b>.<br><br>
            You only need to get familiar with two things:<br><br>
            <b>Center</b> — where the trap is.<br><br>
            <b>Width</b> — how wide or narrow the trap is.<br><br>
            Change either one, and the atom may respond.<br><br>
            <span style="color:{MUTED};font-style:italic;">Before moving anything for real, you need to learn your controls.</span>
            """,
            on_back=screen_3,
            on_next=screen_5,
            next_text="START TRAINING →",
        )

    def screen_5():
        story_page(
            game,
            chapter=2,
            chapter_title="QUANTUM LAB",
            image="chapter2/warmup.png",
            eyebrow="WARM-UP EXPERIMENT",
            title="Get a feel for the trap.",
            text=f"""
            Your professor gives you a simple experiment.<br><br>
            Move the <b>center</b> of the trap.<br><br>
            Change its <b>width</b>.<br><br>
            Then watch carefully what happens to the atom.<br><br>
            There’s no destination yet. No score. Just experiment.<br><br>
            <span style="color:{MUTED};font-style:italic;">Play with the controls and see how the atom responds.</span>
            """,
            on_back=screen_4,
            on_next=show_warmup,
            next_text="RUN THE EXPERIMENT →",
        )

    def show_warmup():
        center_slider = widgets.FloatSlider(
            value=START_CENTER,
            min=-6,
            max=10,
            step=.2,
            description="Center",
            continuous_update=False,
            readout_format=".1f",
            style={"description_width": "60px"},
            layout=widgets.Layout(width="430px"),
        )
        width_slider = widgets.FloatSlider(
            value=START_WIDTH,
            min=.45,
            max=2.3,
            step=.05,
            description="Width",
            continuous_update=False,
            readout_format=".2f",
            style={"description_width": "60px"},
            layout=widgets.Layout(width="430px"),
        )
        center_slider.add_class("quantum-slider")
        width_slider.add_class("quantum-slider")

        preview = widgets.Image(format="png", layout=widgets.Layout(width="700px", height="245px"))
        status = widgets.HTML()
        finish = primary_button("FINISH TRAINING →", width="190px")
        finish.disabled = True

        def render():
            preview.value = _warmup_preview_png(center_slider.value, width_slider.value)
            center_done = state["warm_center_changed"]
            width_done = state["warm_width_changed"]
            finish.disabled = not (center_done and width_done)
            status.value = f"""
            <div style="color:{NAVY};font-size:13px;text-align:center;">
                <span style="color:{CYAN if center_done else MUTED};font-weight:900;">{'✓' if center_done else '○'} Move the center</span>
                &nbsp;&nbsp;&nbsp;&nbsp;
                <span style="color:{CYAN if width_done else MUTED};font-weight:900;">{'✓' if width_done else '○'} Change the width</span>
            </div>
            """

        def center_changed(_):
            if not np.isclose(center_slider.value, START_CENTER):
                state["warm_center_changed"] = True
            render()

        def width_changed(_):
            if not np.isclose(width_slider.value, START_WIDTH):
                state["warm_width_changed"] = True
            render()

        center_slider.observe(center_changed, names="value")
        width_slider.observe(width_changed, names="value")
        finish.on_click(lambda _: screen_6())
        render()

        heading = widgets.HTML(
            f'<div style="text-align:center;color:{NAVY};font-size:21px;font-weight:900;">PLAY WITH THE TRAP'
            f'<div style="margin-top:3px;color:{MUTED};font-size:12px;font-weight:500;">Change both controls before finishing training.</div></div>'
        )
        content = widgets.VBox(
            [heading, center_slider, width_slider, preview, status, finish],
            layout=widgets.Layout(width="100%", height="100%", align_items="center", justify_content="space-between", overflow="hidden"),
        )
        back = secondary_button("← BACK")
        back.on_click(lambda _: screen_5())
        game.show(chapter_screen(game, 2, "QUANTUM LAB", content, widgets.HBox([back])))

    def screen_6():
        story_page(
            game,
            chapter=2,
            chapter_title="QUANTUM LAB",
            image="chapter2/training-complete.png",
            eyebrow="TRAINING COMPLETE",
            title="You’ve got the controls.",
            text=f"""
            You’ve seen how changing the trap can change what happens to the atom.<br><br>
            Your professor decides you’re ready for something harder.<br><br>
            This time, you won’t just experiment with the trap.<br><br>
            You’ll use it to <b>take the atom somewhere</b>.<br><br>
            <span style="color:{MUTED};font-style:italic;">Your first real quantum lab challenge is about to begin.</span>
            """,
            on_back=show_warmup,
            on_next=screen_7,
            next_text="ACCEPT THE CHALLENGE →",
        )

    def screen_7():
        story_page(
            game,
            chapter=2,
            chapter_title="QUANTUM LAB",
            image="chapter2/first-shuttle.png",
            eyebrow="YOUR FIRST SHUTTLE",
            title="Guide the atom with light and reach the target!",
            text=f"""
            A target region appears on the other side of the lab.<br><br>
            Your job is to control the optical trap and <b>shuttle the atom into it</b>.<br><br>
            You can move the trap’s center and adjust its width along the journey.<br><br>
            How you get there is up to you.<br><br>
            <span style="color:{MUTED};font-style:italic;">Get at least <b style="color:{CYAN};">85% of the atom</b> into the target region to complete the experiment.</span>
            """,
            on_back=screen_6,
            on_next=show_controls,
            next_text="START THE CHALLENGE →",
        )

    def show_controls():
        controls = make_quantum_controls(state["centers"], state["widths"])
        center_sliders = controls["center_sliders"]
        width_sliders = controls["width_sliders"]
        center_values = controls["center_values"]
        width_values = controls["width_values"]

        graph = widgets.Image(format="png", layout=widgets.Layout(width="775px", height="260px", overflow="hidden"))
        message = widgets.HTML("", layout=widgets.Layout(width="100%", min_height="26px", overflow="visible"))
        updating = {"active": False}

        def render():
            centers = center_values()
            widths = width_values()
            state["centers"] = centers.copy()
            state["widths"] = widths.copy()
            controls["update_labels"]()
            graph.value = make_quantum_plan_plot(centers, widths, title="Your trap plan")

        def changed(_):
            if not updating["active"]:
                render()

        for slider in center_sliders + width_sliders:
            slider.observe(changed, names="value")
        render()

        run = primary_button("RUN SHUTTLE ▶", width="190px")
        reset = secondary_button("RESET", width="105px")

        def do_reset(_):
            updating["active"] = True
            for i in range(CONTROL_POINTS):
                center_sliders[i].value = float(default_centers[i])
                width_sliders[i].value = float(default_widths[i])
            updating["active"] = False
            state["centers"] = default_centers.copy()
            state["widths"] = default_widths.copy()
            render()

        def run_simulation(_):
            run.disabled = True
            centers, widths = center_values(), width_values()
            state["centers"], state["widths"] = centers.copy(), widths.copy()
            message.value = f'<div style="width:100%;min-height:26px;display:flex;align-items:center;justify-content:center;color:{MUTED};font-size:12px;font-weight:700;">Running your quantum simulation...</div>'
            try:
                result = simulate_quantum(centers, widths)
                state["last_result"] = result
                animation = make_quantum_animation(result)
                show_watch(result, animation)
            except Exception as error:
                run.disabled = False
                message.value = f'<div style="min-height:26px;display:flex;align-items:center;justify-content:center;color:{NAVY};font-size:11px;"><b>Quantum simulation error:</b>&nbsp;{error}</div>'

        reset.on_click(do_reset)
        run.on_click(run_simulation)

        heading = widgets.HTML(
            f'<div style="text-align:center;color:{NAVY};font-size:21px;font-weight:900;">PROGRAM THE SHUTTLE'
            f'<div style="margin-top:3px;color:{MUTED};font-size:12px;font-weight:500;">Choose the trap center and width at 8 moments.</div></div>',
            layout=widgets.Layout(height="42px"),
        )
        center_title = widgets.HTML(f'<div style="text-align:center;color:{CYAN};font-size:12px;font-weight:900;letter-spacing:2px;">TRAP CENTER</div>', layout=widgets.Layout(height="15px"))
        width_title = widgets.HTML(f'<div style="text-align:center;color:{GOLD};font-size:12px;font-weight:900;letter-spacing:2px;">TRAP WIDTH</div>', layout=widgets.Layout(height="15px"))
        graph_box = widgets.Box([graph], layout=widgets.Layout(width="100%", height="260px", justify_content="center", align_items="center", overflow="hidden"))
        buttons = widgets.HBox([run, widgets.Box(layout=widgets.Layout(width="12px")), reset], layout=widgets.Layout(height="45px", justify_content="center", align_items="center", overflow="hidden"))
        content = widgets.VBox(
            [heading, center_title, controls["centers_row"], width_title, controls["widths_row"], graph_box, message, buttons],
            layout=widgets.Layout(width="100%", height="100%", align_items="center", justify_content="space-between", overflow="hidden"),
        )
        back = secondary_button("← BACK")
        back.on_click(lambda _: screen_7())
        game.show(chapter_screen(game, 2, "QUANTUM LAB", content, widgets.HBox([back])))

    def show_watch(result, animation=None):
        if animation is None:
            animation = make_quantum_animation(result)

        probability = result["target_probability"]
        animation_widget = widgets.HTML(
            value=animation_to_html(animation),
            layout=widgets.Layout(width="900px", height="355px", overflow="hidden"),
        )
        header = widgets.HTML(
            f'<div style="text-align:center;color:{NAVY};font-size:21px;font-weight:900;">WATCH THE ATOM'
            f'<div style="margin-top:3px;color:{MUTED};font-size:12px;font-weight:500;">Watch the probability cloud respond to your moving trap.</div></div>'
        )
        score_color = CYAN if probability >= PASS_THRESHOLD else GOLD
        score = widgets.HTML(
            f'<div style="padding:9px 20px;border-radius:9999px;border:2px solid {score_color};color:{NAVY};font-size:14px;font-weight:800;">'
            f'In target: <span style="color:{score_color};font-size:18px;font-weight:900;">{100 * probability:.1f}%</span></div>'
        )
        content = widgets.VBox(
            [header, animation_widget, score],
            layout=widgets.Layout(width="100%", height="100%", align_items="center", justify_content="space-between", overflow="hidden"),
        )
        back = secondary_button("← CHANGE CONTROLS", width="205px")
        back.on_click(lambda _: show_controls())
        result_button = primary_button("SEE RESULT →", width="180px")
        result_button.on_click(lambda _: screen_8_success() if probability >= PASS_THRESHOLD else screen_8_fail())
        footer = widgets.HBox([back, result_button], layout=widgets.Layout(width="100%", justify_content="space-between", align_items="center", overflow="hidden"))
        game.show(chapter_screen(game, 2, "QUANTUM LAB", content, footer))

    def screen_8_fail():
        probability = state["last_result"]["target_probability"]
        story_page(
            game,
            chapter=2,
            chapter_title="QUANTUM LAB",
            image="chapter2/failed.png",
            eyebrow="NOT QUITE THERE",
            title="The atom didn’t make it.",
            text=f"""
            Some of the atom reached the destination—but not enough.<br><br>
            You delivered <b style="color:{GOLD};">{100 * probability:.1f}%</b> into the target region.<br><br>
            Change how you move the trap and try again.<br><br>
            <span style="color:{MUTED};font-style:italic;">Watch the atom closely. Your controls are telling you something.</span>
            """,
            on_back=lambda: show_watch(state["last_result"]),
            on_next=show_controls,
            next_text="TRY AGAIN →",
        )

    def screen_8_success():
        probability = state["last_result"]["target_probability"]

        def finish():
            game.complete_chapter(2)
            game.unlock_chapter(3)
            game.show_chapters()

        story_page(
            game,
            chapter=2,
            chapter_title="QUANTUM LAB",
            image="chapter2/success.png",
            eyebrow="TARGET REACHED",
            title="You shuttled your first atom!",
            text=f"""
            At least <b>85% of the atom</b> made it into the destination region.<br><br>
            Your result: <b style="color:{CYAN};">{100 * probability:.1f}%</b><br><br>
            You used light to trap a quantum particle, control its motion, and guide it where you wanted it to go.<br><br>
            Not bad for your first day in the lab.<br><br>
            <span style="color:{MUTED};font-style:italic;">Your professor already has something harder in mind...</span>
            """,
            on_back=lambda: show_watch(state["last_result"]),
            on_next=finish,
            next_text="FINISH CHAPTER →",
        )

    screen_1()
