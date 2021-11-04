from typing import TYPE_CHECKING

from arcade import View, draw_text, set_viewport, start_render
from arcade.color import WHITE

from static_values import HEIGHT, START_LEVEL, WIDTH

if TYPE_CHECKING:
    from main import GameWindow


class GameOverView(View):
    """View to show when game is over"""

    def __init__(self) -> None:
        """This is run once when we switch to this view"""
        super().__init__()

        self.window.set_mouse_visible(True)
        # Make the mouse visible
        self.window: "GameWindow"

        # Store this so all progress is not lost
        self.current_level: int

    def setup(self, current_level: int = START_LEVEL) -> None:
        # Reset the viewport, necessary if we have a scrolling game and we need
        # to reset the viewport back to the start so we can see what we draw.
        set_viewport(0, WIDTH - 1, 0, HEIGHT - 1)
        self.current_level = current_level

    def on_draw(self) -> None:
        """Draw this view"""
        start_render()
        draw_text(
            "Game Over", WIDTH / 2, HEIGHT / 2, WHITE, font_size=50, anchor_x="center"
        )
        draw_text(
            "Click to restart",
            WIDTH / 2,
            HEIGHT - 75,
            WHITE,
            font_size=20,
            anchor_x="center",
        )

    def on_mouse_press(
        self, _x: float, _y: float, _button: int, _modifiers: int
    ) -> None:
        """If the user presses the mouse button, re-start the game."""
        game_view = self.window.game_view
        game_view.setup(self.current_level)
        self.window.show_view(game_view)
