from typing import TYPE_CHECKING, Callable, NamedTuple, Optional, Union

from arcade import (
    View,
    draw_text,
    set_background_color,
    set_viewport,
    start_render,
    SpriteList,
)
from arcade.color import WHITE
from arcade.csscolor import DARK_SLATE_BLUE
from arcade.sprite import Sprite

from static_values import HEIGHT, WIDTH

if TYPE_CHECKING:
    from main import GameWindow


class PageTuple(NamedTuple):
    title: str
    message: Union[str, Callable[..., None]]
    sprite_generator: Optional[Callable[..., SpriteList]]


def draw_gameplay_page_message() -> None:
    base_width = WIDTH / 2 - 300
    base_height = HEIGHT / 2 + 100
    draw_text(
        ("Various items you'll encounter:"),
        base_width,
        base_height,
        WHITE,
        font_size=18,
    )
    draw_text(
        (" - Allows you to jump higher, must be close to the centre of the board"),
        base_width + 35,
        base_height - 50,
        WHITE,
        font_size=18,
        anchor_y="bottom",
    )
    draw_text(
        (" - Touching this means instant death"),
        base_width + 35,
        base_height - 50 * 2,
        WHITE,
        font_size=18,
    )


def generate_gameplay_sprites() -> SpriteList:
    sprite_list = SpriteList()
    spring_board = Sprite("./assets/intro_single_sprites/spring_board.png", scale=0.25)
    spring_board.center_x = (WIDTH / 2 - 300) + spring_board.width / 2
    spring_board.center_y = HEIGHT / 2 + 100 - 40
    sprite_list.append(spring_board)
    spike = Sprite("./assets/intro_single_sprites/spike.png", scale=0.25)
    spike.center_x = (WIDTH / 2 - 300) + spike.width / 2
    spike.center_y = HEIGHT / 2 + 100 - 35 - 50
    sprite_list.append(spike)
    return sprite_list


def draw_power_page_message() -> None:
    base_width = WIDTH / 2 - 300
    base_height = HEIGHT / 2 + 100
    draw_text(
        (
            "Power is required to pass each level. When power is 'collected' it will\n"
            "expire after a randomly generated amount of time, and will also\n"
            "respawn at the same spot at a random time. Collecting more power\n"
            "when you already have power will just add on to the current expiry\n"
            "time. You, sometimes, will have to weigh up the risk of gathering\n"
            "more power verses getting to the finish point faster."
        ),
        base_width,
        base_height,
        WHITE,
        font_size=18,
        anchor_y="center",
    )


def generate_power_sprites() -> SpriteList:
    sprite_list = SpriteList()
    power = Sprite("./assets/intro_single_sprites/power.png", scale=2)
    power.center_x = WIDTH / 2
    power.center_y = HEIGHT / 2 - 40
    sprite_list.append(power)
    return sprite_list


pages = [
    PageTuple(
        "Background",
        (
            "You are stuck on a remote island, off Antarctica, with limited\n"
            "resources and having lost your communication device.\n"
            "To escape this situation you must find your communication\n"
            "device to get in contact with the rest of your team, facing\n"
            "obstacles along the way."
        ),
        None,
    ),
    PageTuple("Items", draw_gameplay_page_message, generate_gameplay_sprites),
    PageTuple("Power", draw_power_page_message, generate_power_sprites),
    PageTuple("Good luck!", "", None),
]


class InstructionView(View):
    window: "GameWindow"

    def __init__(self) -> None:
        super().__init__()
        # Stores the index of pages that the screen is currently on
        self.set_page(0)
        self.current_page_index: int
        self.current_page: PageTuple
        self.sprite_list: Optional[SpriteList] = None

    def on_show(self) -> None:
        """This is run once when we switch to this view"""
        set_background_color(DARK_SLATE_BLUE)
        # Make the mouse visible
        self.window.set_mouse_visible(True)

    def setup(self) -> None:
        # Reset the viewport, necessary if we have a scrolling game and we need
        # to reset the viewport back to the start so we can see what we draw.
        set_viewport(0, WIDTH - 1, 0, HEIGHT - 1)
        self.sprite_list = None
        self.set_page(0)

    def set_page(self, index: int) -> None:
        self.current_page_index = index
        self.current_page = pages[index]
        if self.current_page.sprite_generator:
            self.sprite_list = self.current_page.sprite_generator()
        else:
            self.sprite_list = None

    def on_draw(self) -> None:
        """Draw this view"""
        start_render()
        if self.sprite_list:
            self.sprite_list.draw()
        draw_text(
            f"Instructions #{self.current_page_index + 1}",
            WIDTH / 2,
            HEIGHT - 60,
            WHITE,
            font_size=35,
            anchor_x="center",
        )
        draw_text(
            self.current_page.title,
            WIDTH / 2,
            HEIGHT - 100,
            WHITE,
            font_size=25,
            anchor_x="center",
        )
        if isinstance(self.current_page.message, str):
            draw_text(
                self.current_page.message,
                WIDTH / 2,
                HEIGHT / 2,
                WHITE,
                font_size=18,
                anchor_x="center",
            )
        else:
            self.current_page.message()
        draw_text(
            "Click to advance",
            WIDTH / 2,
            75,
            WHITE,
            font_size=20,
            anchor_x="center",
        )

    def start_game(self) -> None:
        game_view = self.window.game_view
        game_view.setup()
        self.window.show_view(game_view)

    def on_mouse_press(
        self, _x: float, _y: float, _button: int, _modifiers: int
    ) -> None:
        """If the user presses the mouse button, start the game."""
        if self.current_page_index < len(pages) - 1:
            self.set_page(self.current_page_index + 1)
        else:
            self.start_game()
