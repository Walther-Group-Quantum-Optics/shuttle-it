"""Chapter 3 UI: Barrier Challenge."""

from __future__ import annotations

import ipywidgets as widgets
import numpy as np

from backend.quantum import START_CENTER, START_WIDTH, TARGET_CENTER, simulate_quantum
from .common import (
    CYAN,
    GOLD,
    MUTED,
    NAVY,
    NAVY_2,
    animation_to_html,
    chapter_screen,
    image_uri,
    make_quantum_animation,
    make_quantum_controls,
    make_quantum_plan_plot,
    primary_button,
    secondary_button,
    story_page,
)

CONTROL_POINTS = 8
BARRIER = (3.0, 0.5, 0.20)  # center, width, height


def start_chapter_3(game):
    default_centers = np.linspace(START_CENTER, TARGET_CENTER, CONTROL_POINTS)
    default_widths = np.full(CONTROL_POINTS, START_WIDTH)

    state = {
        "centers": default_centers.copy(),
        "widths": default_widths.copy(),
        "last_result": None,
        "last_score": 0.0,
        "best_score": 0.0,
        "final_score": 0.0,
    }

    def screen_1():
        story_page(
            game,
            chapter=3,
            chapter_title="BARRIER CHALLENGE",
            image="chapter3/last-challenge.png",
            eyebrow="ONE LAST CHALLENGE",
            title="Your professor isn’t done with you yet.",
            text=f"""
            You’ve learned how to trap an atom with light.<br><br>
            You’ve learned how to move it.<br><br>
            And you’ve successfully shuttled it to a target.<br><br>
            Your professor looks at the class.<br><br>
            <span style="color:{MUTED};font-style:italic;">“Good. Now let’s make things interesting.”</span>
            """,
            on_back=None,
            on_next=screen_2,
            next_text="WHAT'S THE CHALLENGE? →",
        )

    def screen_2():
        story_page(
            game,
            chapter=3,
            chapter_title="BARRIER CHALLENGE",
            image="chapter3/barrier.png",
            eyebrow="SOMETHING’S IN THE WAY",
            title="This time, the path isn’t clear.",
            text=f"""
            A <b>barrier</b> now stands between your atom and its destination.<br><br>
            You still control the optical trap.<br><br>
            But now you’ll need to figure out how to move the atom <b>past the barrier</b> and into the target region.<br><br>
            <span style="color:{MUTED};font-style:italic;">Same controls. Much harder journey.</span>
            """,
            on_back=screen_1,
            on_next=screen_3,
            next_text="SHOW ME THE BARRIER →",
        )

    def screen_3():
        story_page(
            game,
            chapter=3,
            chapter_title="BARRIER CHALLENGE",
            image="chapter3/final-experiment.png",
            eyebrow="THE FINAL EXPERIMENT",
            title="How much can you deliver?",
            text=f"""
            There’s no passing score this time.<br><br>
            Your goal is simple:<br><br>
            <b>Get as much of the atom as possible past the barrier and into the target.</b><br><br>
            Change the trap’s position and width however you like.<br><br>
            Experiment. Refine your strategy. Try again.<br><br>
            <span style="color:{MUTED};font-style:italic;">Every bit that reaches the target counts.</span>
            """,
            on_back=screen_2,
            on_next=show_controls,
            next_text="START EXPERIMENTING →",
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
            centers, widths = center_values(), width_values()
            state["centers"] = centers.copy()
            state["widths"] = widths.copy()
            controls["update_labels"]()
            graph.value = make_quantum_plan_plot(
                centers,
                widths,
                barrier=BARRIER,
                title="Your barrier-crossing plan",
            )

        def changed(_):
            if not updating["active"]:
                render()

        for slider in center_sliders + width_sliders:
            slider.observe(changed, names="value")
        render()

        run = primary_button("RUN EXPERIMENT ▶", width="205px")
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

        def run_experiment(_):
            run.disabled = True
            centers, widths = center_values(), width_values()
            state["centers"] = centers.copy()
            state["widths"] = widths.copy()
            message.value = f'<div style="width:100%;min-height:26px;display:flex;align-items:center;justify-content:center;color:{MUTED};font-size:12px;font-weight:700;">Running your quantum simulation...</div>'

            try:
                result = simulate_quantum(centers, widths, barrier=BARRIER)
                score = 100.0 * result["target_probability"]
                state["last_result"] = result
                state["last_score"] = score
                state["best_score"] = max(state["best_score"], score)
                animation = make_quantum_animation(result, barrier=BARRIER)
                show_watch(result, animation)
            except Exception as error:
                run.disabled = False
                message.value = f'<div style="min-height:26px;display:flex;align-items:center;justify-content:center;color:{NAVY};font-size:11px;"><b>Simulation error:</b>&nbsp;{error}</div>'

        reset.on_click(do_reset)
        run.on_click(run_experiment)

        heading = widgets.HTML(
            f'<div style="text-align:center;color:{NAVY};font-size:21px;font-weight:900;">CROSS THE BARRIER'
            f'<div style="margin-top:3px;color:{MUTED};font-size:12px;font-weight:500;">Deliver as much of the atom as you can.</div></div>',
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
        back.on_click(lambda _: screen_3())
        game.show(chapter_screen(game, 3, "BARRIER CHALLENGE", content, widgets.HBox([back])))

    def show_watch(result, animation=None):
        if animation is None:
            animation = make_quantum_animation(result, barrier=BARRIER)

        animation_widget = widgets.HTML(
            value=animation_to_html(animation, max_width=860, max_height=350),
            layout=widgets.Layout(width="900px", height="355px", overflow="hidden"),
        )
        header = widgets.HTML(
            f'<div style="text-align:center;color:{NAVY};font-size:21px;font-weight:900;">WATCH THE ATOM'
            f'<div style="margin-top:3px;color:{MUTED};font-size:12px;font-weight:500;">Can your trap carry it through the barrier?</div></div>'
        )
        content = widgets.VBox(
            [header, animation_widget],
            layout=widgets.Layout(width="100%", height="100%", align_items="center", justify_content="space-between", overflow="hidden"),
        )
        back = secondary_button("← CHANGE CONTROLS", width="205px")
        back.on_click(lambda _: show_controls())
        score_button = primary_button("SEE YOUR SCORE →", width="190px")
        score_button.on_click(lambda _: screen_4())
        footer = widgets.HBox([back, score_button], layout=widgets.Layout(width="100%", justify_content="space-between", align_items="center", overflow="hidden"))
        game.show(chapter_screen(game, 3, "BARRIER CHALLENGE", content, footer))

    def screen_4():
        score = state["last_score"]
        image = widgets.HTML(
            f"""
            <div style="width:400px;height:390px;display:flex;align-items:center;justify-content:center;">
                <img src="{image_uri('chapter3/score.png')}"
                     style="max-width:100%;max-height:100%;display:block;object-fit:contain;">
            </div>
            """
        )
        text = widgets.HTML(
            f"""
            <div style="width:445px;color:{NAVY};padding:25px 30px;box-sizing:border-box;
                        border:2px solid rgba(172,201,230,.70);border-radius:25px;">
                <div style="color:{GOLD};font-size:10px;font-weight:900;letter-spacing:2px;">YOUR SCORE</div>
                <div style="margin-top:10px;font-size:30px;line-height:1.18;font-weight:900;">
                    You delivered <span style="color:{CYAN};">{score:.1f}%</span>
                </div>
                <div style="margin-top:22px;color:{NAVY_2};font-size:15px;line-height:1.6;">
                    That’s how much of the atom made it safely into the destination region.<br><br>
                    Satisfied?<br><br>
                    You can keep experimenting and try to push your score higher…<br><br>
                    or see how you compare with everyone else.
                </div>
            </div>
            """
        )
        content = widgets.HBox([image, text], layout=widgets.Layout(width="100%", height="100%", justify_content="center", align_items="center", overflow="hidden"))

        retry = secondary_button("TRY AGAIN", width="145px")
        retry.on_click(lambda _: show_controls())
        happy = primary_button("I'M HAPPY WITH MY SCORE →", width="245px")

        def accept(_):
            state["final_score"] = state["best_score"]
            screen_5()

        happy.on_click(accept)
        footer = widgets.HBox([retry, happy], layout=widgets.Layout(width="100%", justify_content="space-between", align_items="center", overflow="hidden"))
        game.show(chapter_screen(game, 3, "BARRIER CHALLENGE", content, footer))

    def screen_5():
        story_page(
            game,
            chapter=3,
            chapter_title="BARRIER CHALLENGE",
            image="chapter3/surprise.png",
            eyebrow="ONE MORE SURPRISE",
            title="Your professor made it a competition.",
            text="""
            Throughout the experiment, everyone has been trying to solve the same problem.<br><br>
            And your professor has been keeping track of the best results.<br><br>
            There’s a <b>class leaderboard</b> waiting for you.<br><br>
            Think your score belongs on it?
            """,
            on_back=screen_4,
            on_next=screen_6,
            next_text="SEE THE LEADERBOARD →",
        )

    def screen_6():
        score = state["final_score"]
        leaderboard = widgets.HTML(
            f"""
            <div style="width:700px;margin:0 auto;text-align:center;color:{NAVY};">
                <div style="color:{GOLD};font-size:10px;font-weight:900;letter-spacing:3px;">THE LEADERBOARD</div>
                <div style="margin-top:8px;font-size:31px;font-weight:900;">How do you stack up?</div>
                <div style="width:520px;margin:22px auto 0;border:2px solid rgba(172,201,230,.70);border-radius:25px;overflow:hidden;background:white;">
                    <div style="padding:12px 25px;font-size:17px;font-weight:900;border-bottom:1px solid #e6eef6;">🥇 1. Maya — 98.7%</div>
                    <div style="padding:12px 25px;font-size:17px;font-weight:900;border-bottom:1px solid #e6eef6;">🥈 2. Alex — 97.4%</div>
                    <div style="padding:12px 25px;font-size:17px;font-weight:900;border-bottom:1px solid #e6eef6;">🥉 3. Sam — 95.9%</div>
                    <div style="padding:12px 25px;font-size:17px;font-weight:900;border-bottom:1px solid #e6eef6;">4. Jordan — 94.2%</div>
                    <div style="padding:12px 25px;color:{MUTED};font-size:16px;font-weight:800;">5. ??? — Can you beat them?</div>
                </div>
                <div style="margin-top:17px;font-size:17px;font-weight:900;">
                    Your score: <span style="color:{CYAN};font-size:23px;">{score:.1f}%</span>
                </div>
                <div style="margin-top:6px;color:{MUTED};font-size:13px;font-style:italic;">Want to put your result on the board?</div>
            </div>
            """
        )
        private = secondary_button("KEEP IT PRIVATE", width="170px")
        private.on_click(lambda _: screen_7_private())
        submit = primary_button("SUBMIT MY SCORE →", width="200px")
        submit.on_click(lambda _: screen_7_submit())
        footer = widgets.HBox([private, submit], layout=widgets.Layout(width="100%", justify_content="space-between", align_items="center", overflow="hidden"))
        game.show(chapter_screen(game, 3, "BARRIER CHALLENGE", leaderboard, footer))

    def screen_7_submit():
        score = state["final_score"]
        content = widgets.HTML(
            f"""
            <div style="width:100%;height:100%;display:flex;align-items:center;justify-content:center;gap:60px;">
                <div style="width:330px;height:330px;display:flex;align-items:center;justify-content:center;
                            border:2px solid rgba(172,201,230,.70);border-radius:25px;background:white;">
                    <img src="{image_uri('chapter3/leaderboard-qr.png')}"
                         style="width:270px;height:270px;object-fit:contain;display:block;">
                </div>
                <div style="width:390px;color:{NAVY};">
                    <div style="color:{GOLD};font-size:10px;font-weight:900;letter-spacing:3px;">SUBMIT YOUR SCORE</div>
                    <div style="margin-top:10px;font-size:31px;font-weight:900;">Claim your spot.</div>
                    <div style="margin-top:22px;color:{NAVY_2};font-size:15px;line-height:1.6;">
                        Scan the QR code with your phone to submit your score to the leaderboard.
                    </div>
                    <div style="margin-top:24px;font-size:16px;font-weight:900;">
                        Your score: <span style="color:{CYAN};font-size:22px;">{score:.1f}%</span>
                    </div>
                    <div style="margin-top:15px;color:{MUTED};font-size:13px;font-style:italic;">Submission is completely optional.</div>
                </div>
            </div>
            """
        )
        back = secondary_button("← LEADERBOARD", width="155px")
        back.on_click(lambda _: screen_6())
        finish = primary_button("FINISH →", width="150px")
        finish.on_click(lambda _: finish_chapter())
        footer = widgets.HBox([back, finish], layout=widgets.Layout(width="100%", justify_content="space-between", align_items="center", overflow="hidden"))
        game.show(chapter_screen(game, 3, "BARRIER CHALLENGE", content, footer))

    def screen_7_private():
        story_page(
            game,
            chapter=3,
            chapter_title="BARRIER CHALLENGE",
            image="chapter3/private.png",
            eyebrow="SCORE KEPT PRIVATE",
            title="Challenge complete.",
            text=f"""
            You made it past the barrier and found your own way to shuttle the atom to its destination.<br><br>
            Leaderboard or not, you’ve completed your final experiment.<br><br>
            <span style="color:{MUTED};font-style:italic;">Not bad for your first day in the quantum lab.</span>
            """,
            on_back=screen_6,
            on_next=finish_chapter,
            next_text="FINISH →",
        )

    def finish_chapter():
        game.complete_chapter(3)
        game.show_final_screen()

    screen_1()
