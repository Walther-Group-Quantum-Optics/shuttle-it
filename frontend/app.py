"""Top-level application shell and navigation for Shuttle it!."""

from __future__ import annotations

import ipywidgets as widgets
from IPython.display import clear_output, display

from .common import (
    CYAN,
    GOLD,
    GAME_HEIGHT,
    GAME_WIDTH,
    LOCK_BG,
    LOCK_TEXT,
    MUTED,
    NAVY,
    image_uri,
    install_css,
    primary_button,
    secondary_button,
)
from .chapter1 import start_chapter_1
from .chapter2 import start_chapter_2
from .chapter3 import start_chapter_3


class Game:
    """Own the small amount of state that exists above individual chapters."""

    def __init__(self):
        self.player_name = ""
        self.chapter_unlocked = [True, False, False]
        self.chapter_completed = [False, False, False]
        self.chapter_just_unlocked = [False, False, False]

        self.output = widgets.Output(
            layout=widgets.Layout(
                width=GAME_WIDTH,
                height=GAME_HEIGHT,
                min_width=GAME_WIDTH,
                max_width=GAME_WIDTH,
                min_height=GAME_HEIGHT,
                max_height=GAME_HEIGHT,
                margin="0px",
                padding="0px",
                overflow="hidden",
            )
        )
        self.output.add_class("shuttle-output")

        self.frame = widgets.Box(
            [self.output],
            layout=widgets.Layout(
                width=GAME_WIDTH,
                height=GAME_HEIGHT,
                min_width=GAME_WIDTH,
                max_width=GAME_WIDTH,
                min_height=GAME_HEIGHT,
                max_height=GAME_HEIGHT,
                margin="0px",
                padding="0px",
                overflow="hidden",
            ),
        )
        self.frame.add_class("shuttle-game")

    def show(self, widget):
        widget.add_class("game-screen")
        with self.output:
            clear_output(wait=True)
            display(widget)

    def complete_chapter(self, chapter_number: int):
        self.chapter_completed[chapter_number - 1] = True

    def unlock_chapter(self, chapter_number: int):
        index = chapter_number - 1
        if not self.chapter_unlocked[index]:
            self.chapter_unlocked[index] = True
            self.chapter_just_unlocked[index] = True

    def reset(self):
        self.player_name = ""
        self.chapter_unlocked[:] = [True, False, False]
        self.chapter_completed[:] = [False, False, False]
        self.chapter_just_unlocked[:] = [False, False, False]

    def launch(self):
        install_css()
        display(self.frame)
        self.show_landing()
        return self

    # ------------------------------------------------------------------
    # Landing
    # ------------------------------------------------------------------

    def show_landing(self):
        name_input = widgets.Text(
            placeholder="What is your name?",
            layout=widgets.Layout(width="600px", height="66px"),
        )
        name_input.add_class("name-entry")

        message = widgets.HTML("", layout=widgets.Layout(height="22px"))
        start = primary_button("Game on!", width="400px", height="72px", font_size="23px")

        def start_game(_=None):
            value = name_input.value.strip()
            if not value:
                message.value = (
                    f'<div style="color:{NAVY};text-align:center;font-size:13px;font-weight:700;">'
                    "Tell me your name first!</div>"
                )
                return
            self.player_name = value
            self.show_chapters()

        start.on_click(start_game)

        body = widgets.VBox(
            [
                widgets.HTML(
                    f"""
                    <div style="text-align:center;color:{NAVY};font-size:55px;font-weight:900;letter-spacing:-2px;">
                        Welcome to Shuttle <span style="color:{CYAN};">it!</span>
                    </div>
                    """
                ),
                widgets.Box(layout=widgets.Layout(height="54px")),
                name_input,
                message,
                widgets.Box(layout=widgets.Layout(height="17px")),
                start,
            ],
            layout=widgets.Layout(
                width="100%",
                height="100%",
                align_items="center",
                justify_content="center",
                overflow="hidden",
            ),
        )
        self.show(body)

    # ------------------------------------------------------------------
    # Chapter selection
    # ------------------------------------------------------------------

    def _chapter_card(self, chapter_number, subtitle, description):
        index = chapter_number - 1
        unlocked = self.chapter_unlocked[index]
        color = CYAN if unlocked else GOLD

        badge = widgets.HTML(
            f"""
            <div style="width:66px;height:66px;display:flex;align-items:center;justify-content:center;
                        border-radius:50%;background:{color};color:white;font-size:30px;font-weight:900;
                        box-shadow:0 4px 12px rgba(32,56,94,.12);position:relative;z-index:20;">
                {chapter_number}
            </div>
            """
        )

        heading = widgets.HTML(
            f"""
            <div style="text-align:center;color:{NAVY};">
                <div style="font-size:22px;font-weight:900;">CHAPTER {chapter_number}</div>
                <div style="margin-top:4px;font-size:13px;font-weight:500;letter-spacing:4px;">{subtitle}</div>
            </div>
            """
        )

        lock_overlay = ""
        if not unlocked:
            lock_overlay = f"""
            <div style="position:absolute;inset:0;z-index:4;background:rgba(255,255,255,.40);"></div>
            <img src="{image_uri('common/lock.png')}"
                 style="position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);
                        width:82px;height:82px;object-fit:contain;z-index:5;">
            """

        image = widgets.HTML(
            f"""
            <div style="width:100%;height:154px;position:relative;overflow:hidden;border-radius:12px;background:white;">
                <img src="{image_uri(f'chapter{chapter_number}/card.png')}"
                     style="position:absolute;inset:0;width:100%;height:100%;display:block;object-fit:cover;object-position:center;">
                {lock_overlay}
            </div>
            """
        )

        desc = widgets.HTML(
            f"""
            <div style="height:52px;display:flex;align-items:center;justify-content:center;padding:0 8px;
                        box-sizing:border-box;color:{NAVY};text-align:center;font-size:14px;line-height:1.35;">
                {description}
            </div>
            """
        )

        if unlocked:
            action = primary_button("PLAY  ▶", width="100%", height="50px", font_size="18px")
            if chapter_number == 1:
                action.on_click(lambda _: start_chapter_1(self))
            elif chapter_number == 2:
                action.on_click(lambda _: start_chapter_2(self))
            else:
                action.on_click(lambda _: start_chapter_3(self))
        else:
            action = widgets.Button(
                description=f"COMPLETE CHAPTER {chapter_number - 1} TO UNLOCK",
                disabled=True,
                layout=widgets.Layout(width="100%", height="50px", overflow="hidden"),
            )
            action.style.button_color = LOCK_BG
            action.style.text_color = LOCK_TEXT
            action.style.font_size = "10px"
            action.style.font_weight = "700"
            action.add_class("pill-button")
            action.add_class("locked-button")

        card_body = widgets.VBox(
            [
                widgets.Box(layout=widgets.Layout(height="30px")),
                heading,
                widgets.Box(layout=widgets.Layout(height="12px")),
                image,
                desc,
                action,
            ],
            layout=widgets.Layout(
                width="300px",
                height="394px",
                padding="0 14px 14px 14px",
                border=f"2px solid {color}",
                margin="-31px 0 0 0",
                overflow="hidden",
            ),
        )
        card_body.add_class("chapter-card-body")
        if not unlocked:
            card_body.add_class("chapter-card-locked")

        return widgets.VBox(
            [badge, card_body],
            layout=widgets.Layout(width="300px", height="430px", align_items="center", overflow="visible"),
        )

    def _unlock_celebration(self, chapter_number):
        emojis = ["🎉", "✨", "🥳", "🎊", "⭐", "🎉", "✨", "🎊", "🥳"]
        emoji_html = "".join(f'<span class="unlock-emoji">{emoji}</span>' for emoji in emojis)
        celebration = widgets.HTML(
            value=f"""
            <div class="unlock-celebration">
                <div class="unlock-banner">🎉 Chapter {chapter_number} unlocked!</div>
                {emoji_html}
            </div>
            """,
            layout=widgets.Layout(
                width="100%",
                height="100%",
                min_width="100%",
                min_height="100%",
                margin="0px",
                padding="0px",
                overflow="hidden",
            ),
        )
        celebration.add_class("unlock-overlay-widget")
        return celebration

    def show_chapters(self):
        unlocked_now = [i for i, value in enumerate(self.chapter_just_unlocked) if value]

        logo = widgets.HTML(
            f"""
            <div style="padding-top:22px;text-align:center;color:{NAVY};font-size:49px;
                        line-height:1;font-weight:900;letter-spacing:-2px;">
                Shuttle <span style="color:{CYAN};">it!</span>
            </div>
            """
        )

        chapters = widgets.HBox(
            [
                self._chapter_card(1, "TEA RESCUE", "One goal: don’t spill!"),
                widgets.Box(layout=widgets.Layout(width="28px")),
                self._chapter_card(2, "QUANTUM LAB", "Steer the atom with light<br>and bring it home!"),
                widgets.Box(layout=widgets.Layout(width="28px")),
                self._chapter_card(3, "BARRIER CHALLENGE", "Navigate the bump and<br>bring the atom home!"),
            ],
            layout=widgets.Layout(
                width="100%",
                height="475px",
                padding="39px 20px 0 20px",
                box_sizing="border-box",
                justify_content="center",
                align_items="flex-start",
                overflow="visible",
            ),
        )

        base_page = widgets.VBox(
            [logo, chapters],
            layout=widgets.Layout(width="100%", height="100%", overflow="hidden"),
        )
        base_page.add_class("chapters-base-layer")

        children = [base_page]
        if unlocked_now:
            children.append(self._unlock_celebration(unlocked_now[0] + 1))

        screen = widgets.Box(
            children,
            layout=widgets.Layout(width="100%", height="100%", overflow="hidden"),
        )
        screen.add_class("chapters-screen")

        for index in unlocked_now:
            self.chapter_just_unlocked[index] = False

        self.show(screen)

    # ------------------------------------------------------------------
    # Whole-game ending
    # ------------------------------------------------------------------

    def show_final_screen(self):
        image = widgets.HTML(
            f"""
            <div style="width:390px;height:360px;display:flex;align-items:center;justify-content:center;">
                <img src="{image_uri('chapter3/final.png')}"
                     style="width:100%;height:100%;object-fit:contain;display:block;">
            </div>
            """
        )

        text = widgets.HTML(
            f"""
            <div style="width:460px;color:{NAVY};">
                <div style="color:{CYAN};font-size:12px;font-weight:900;letter-spacing:4px;">SHUTTLE IT!</div>
                <div style="margin-top:10px;font-size:34px;line-height:1.15;font-weight:900;">
                    From tea to quantum atoms.
                </div>
                <div style="margin-top:22px;color:#405f86;font-size:15px;line-height:1.65;">
                    You started by discovering what makes a cup of tea slosh.<br><br>
                    Then you stepped into a quantum lab, learned to control atoms with light,
                    and used an optical trap to move them through increasingly difficult challenges.<br><br>
                    You’ve completed <b>Shuttle it!</b>
                </div>
            </div>
            """
        )

        play_again = primary_button("PLAY AGAIN ↻", width="200px", height="48px")

        def restart(_):
            self.reset()
            self.show_landing()

        play_again.on_click(restart)

        screen = widgets.VBox(
            [
                widgets.Box(layout=widgets.Layout(height="20px")),
                widgets.HBox(
                    [image, text],
                    layout=widgets.Layout(
                        width="100%", height="500px", justify_content="center", align_items="center", overflow="hidden"
                    ),
                ),
                widgets.HBox(
                    [play_again],
                    layout=widgets.Layout(width="100%", justify_content="center", overflow="hidden"),
                ),
            ],
            layout=widgets.Layout(width="100%", height="100%", align_items="center", overflow="hidden"),
        )
        self.show(screen)


def launch_game():
    """Create and launch a fresh Shuttle it! game; return it for debugging."""

    return Game().launch()
