from typing import Optional, Union

from arcade import draw_text
from arcade.color import BLIZZARD_BLUE


class Label:
    def __init__(
        self,
        format_string: str,
        initial_value: Union[str, int, float],
        x_offset: int,
        y_offset: int,
    ) -> None:
        """Create Label

        Args:
            format_string (str): The string to format values against. Must have one of "{value}" where the value will be.
            initial_value (Union[str, int, float]): The initial value to use
            x_offset (int): The y offset from the y supplied on draw
            y_offset (int): The x offset from the x supplied on draw
        """
        self.format_string = format_string
        self.value = self.format_value(initial_value)
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.flash_duration_left: float = 0
        self.font_size: float = 16
        self.original_font_size = 16

    def format_value(self, new_value: Union[str, int, float]) -> str:
        """Formats the formate string with the string provided and returns that.

        Args:
            new_value (Union[str, int, float]): The new value to format the formate string with

        Returns:
            str: Formatted value
        """
        return self.format_string.format(value=new_value)

    def draw(
        self, x: int, y: int, new_value: Optional[Union[str, int, float]] = None
    ) -> None:
        """Draws the text label in the specificed position.

        Args:
            x (int): The x values to draw the label off. This is suggested to be the left of the viewport
            y (int): The y values to draw the label off. This is suggested to be the bottom of the viewport
            new_value (Optional[Union[str, int, float]], optional): The new value to pass into the format string. Defaults to None and will not be updated if None.
        """
        if new_value is not None:
            self.value = self.format_value(new_value)
        draw_text(
            text=self.value,
            start_x=x + self.x_offset,
            start_y=y + self.y_offset,
            color=BLIZZARD_BLUE,
            font_size=self.font_size,
            anchor_x="right",
        )

    def flash(self, duration: float) -> None:
        """Increases the labels size for duration seconds

        Args:
            duration (float): The duration until the label should be at it's original size
        """
        self.flash_duration_left = duration
        self.font_size = 20

    def update(self, delta_time: float) -> None:
        """Handle updating the label. This relates to the flash feature, and reducing the size back to normal.

        Args:
            delta_time (float): The time since the last update
        """
        if self.flash_duration_left == 0:
            return
        ratio_left = delta_time / self.flash_duration_left
        font_size_difference = self.font_size - self.original_font_size
        font_size_to_change = abs(font_size_difference * ratio_left)
        if self.font_size - font_size_to_change <= self.original_font_size:
            self.font_size = self.original_font_size
            self.flash_duration_left = 0
            return
        self.font_size -= font_size_to_change
