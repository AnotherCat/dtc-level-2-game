from typing import TYPE_CHECKING

from arcade import View, draw_text, set_viewport, start_render
from arcade.color import WHITE

from static_values import HEIGHT, WIDTH

if TYPE_CHECKING:
    from main import GameWindow


class GameWonView(View):
    """View to show when game is won"""

    def __init__(self) -> None:
        """This is run once when we switch to this view"""
        super().__init__()

        self.window.set_mouse_visible(True)
        # Make the mouse visible
        self.window: "GameWindow"

        # Value to show next to winning
        self.value = ""
        self.clock: float = 0

    def setup(self) -> None:
        # Reset the viewport, necessary if we have a scrolling game and we need
        # to reset the viewport back to the start so we can see what we draw.
        set_viewport(0, WIDTH - 1, 0, HEIGHT - 1)
        self.value = ""
        self.clock = 0

    def on_draw(self) -> None:
        """Draw this view"""
        start_render()
        draw_text(
            "You won!",
            WIDTH / 2,
            HEIGHT / 2,
            WHITE,
            font_size=50,
            anchor_x="center",
        )
        draw_text(
            self.value,
            WIDTH / 2,
            HEIGHT / 2 - 100,
            WHITE,
            font_size=20,
            anchor_x="center",
        )
        draw_text(
            "Click to play again",
            WIDTH / 2,
            HEIGHT - 75,
            WHITE,
            font_size=20,
            anchor_x="center",
        )

    def on_update(self, delta_time: float):
        self.clock += delta_time / 2
        if self.clock > 0.5 and self.clock < 2.0:
            self.value = "\n\nFound a communicator, attempting to contact base..."
        elif self.clock > 2.0:
            self.value = "\n\nGot a signal! Looks like they're on their way"

    def on_mouse_press(
        self, _x: float, _y: float, _button: int, _modifiers: int
    ) -> None:
        """If the user presses the mouse button, re-start the game."""
        game_view = self.window.game_view
        game_view.setup()
        self.window.show_view(game_view)
