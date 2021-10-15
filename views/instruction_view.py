from typing import TYPE_CHECKING

from arcade import View, draw_text, set_background_color, set_viewport, start_render
from arcade.color import WHITE
from arcade.csscolor import DARK_SLATE_BLUE

from static_values import HEIGHT, WIDTH

if TYPE_CHECKING:
    from main import GameWindow


class InstructionView(View):
    window: "GameWindow"

    def on_show(self) -> None:
        """This is run once when we switch to this view"""
        set_background_color(DARK_SLATE_BLUE)

        self.window.set_mouse_visible(True)
        # Make the mouse visible

    def setup(self) -> None:
        # Reset the viewport, necessary if we have a scrolling game and we need
        # to reset the viewport back to the start so we can see what we draw.
        set_viewport(0, WIDTH - 1, 0, HEIGHT - 1)

    def on_draw(self) -> None:
        """Draw this view"""
        start_render()
        draw_text(
            "Instructions Screen",
            WIDTH / 2,
            HEIGHT / 2,
            WHITE,
            font_size=50,
            anchor_x="center",
        )
        draw_text(
            "The aim is to collect as many batteries as possible",
            WIDTH / 2,
            HEIGHT / 2 - 40,
            WHITE,
            font_size=20,
            anchor_x="center",
        )
        draw_text(
            "Click to advance",
            WIDTH / 2,
            HEIGHT / 2 - 75,
            WHITE,
            font_size=20,
            anchor_x="center",
        )

    def on_mouse_press(
        self, _x: float, _y: float, _button: int, _modifiers: int
    ) -> None:
        """If the user presses the mouse button, start the game."""
        game_view = self.window.game_view
        game_view.setup()
        self.window.show_view(game_view)
