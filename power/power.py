from math import floor
from typing import List, NamedTuple

from arcade import Sprite, SpriteList
from arcade.sprite_list import check_for_collision, check_for_collision_with_list

from label import Label
from power.custom_random import RandomManager
from static_values import HEIGHT, WIDTH


class DormantTuple(NamedTuple):
    live_time: float
    sprite: Sprite


class PowerManager:
    def __init__(self, sprite_list: SpriteList, player: Sprite) -> None:
        self.player = player
        # Time passed
        self.clock: float = 0

        # List of sprites to draw, initaly this is all sprites provided
        self.sprite_list = sprite_list

        # List of sprites that have been "collected" and are waiting to regenerate
        self.dormant_sprites: List[DormantTuple] = []

        # How much time is left until the player has no power
        self.power_time_remaining: float = 0

        # "evened out" random generators
        self.random_power_generator = RandomManager(36, 8)
        self.random_dormant_generator = RandomManager(40, 15)

        # Power label to display the power
        self.power_label = Label(
            format_string="Power Expiry: {value}",
            initial_value=self.power_left,
            x_offset=WIDTH - 50,
            y_offset=HEIGHT - 35,
        )

    @property
    def has_power(self) -> bool:
        """
        If the player has power

        Returns:
            bool
        """
        return self.power_time_remaining > 0

    @property
    def power_left(self) -> str:
        """
        Returns a string with how much power is left, or "No Power"

        Returns:
            str
        """
        if self.power_time_remaining < 0:
            return "No Power"
        whole = floor(self.power_time_remaining)
        decimal = self.power_time_remaining - whole
        if decimal >= 0.5:
            return f"{whole}.5"
        else:
            if whole == 0:
                return "No Power"
            return f"{whole}.0"

    def hit(self, sprite: Sprite) -> None:
        """
        Process a 'hit', this is when the player comes into contact with a power sprite
        Removes the sprite from the draw list, and appends it to the dormant sprite list, and increments the power value

        Args:
            sprite (Sprite): [description]
        """
        self.sprite_list.remove(sprite)
        self.dormant_sprites.append(
            DormantTuple(
                self.clock + self.random_dormant_generator.generate_value(), sprite
            )
        )
        self.power_time_remaining += self.random_power_generator.generate_value()

    def revive(self, sprite: Sprite) -> None:
        self.sprite_list.append(sprite)

    def draw(self, x: int, y: int) -> None:
        """
        Draw related sprites

        Args:
            x (int): X offset (screen offset)
            y (int): Y offset (screen offset)
        """
        self.sprite_list.draw()
        self.power_label.draw(x, y)

    def check_collision(self) -> None:
        """
        Check for collisions with the player and the too draw list
        """
        collisions = check_for_collision_with_list(self.player, self.sprite_list)
        for power in collisions:
            self.hit(power)

    def update(self, delta_time: float) -> None:
        self.power_label.update(
            delta_time
        )  # Before we 'correct' the delta_time because it's corrected by label
        delta_time = delta_time / 2  # It seems like delta_time isn't exactly seconds

        # Updating the 'time'
        self.clock += delta_time

        # Check if there are any dormant sprites that need to be revived
        for sprite in self.dormant_sprites:
            if sprite.live_time <= self.clock and not check_for_collision(
                self.player, sprite.sprite
            ):
                self.revive(sprite.sprite)
                self.dormant_sprites.remove(sprite)

        # If there is power decrease it by the time
        if self.has_power:
            self.power_time_remaining -= delta_time

        # Update the label's value
        self.power_label.set_value(self.power_left)
