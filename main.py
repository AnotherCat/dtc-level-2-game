import logging
import os

from typing import List, Tuple

import arcade

TILE_WIDTH = 124
TILE_HEIGHT = TILE_WIDTH
WIDTH = 10 * TILE_WIDTH
HEIGHT = 6 * TILE_HEIGHT
VIEWPORT_MARGIN = 140
PLAYER_MOVEMENT_SPEED = 10
PLAYER_JUMP_SPEED = 8
BOOSTED_JUMP_SPEED = 12
TITLE = "Ice Game"
GRAVITY = 0.5

file_path = os.path.dirname(os.path.abspath(__file__))
os.chdir(file_path)
logging.basicConfig(level=logging.DEBUG)


class Game(arcade.Window):
    def __init__(self) -> None:
        super().__init__(WIDTH, HEIGHT, TITLE)
        self.level = 1
        self.view_bottom: int
        self.view_left: int
        self.wall_list: arcade.SpriteList
        self.player: arcade.Sprite
        self.physics_engine: arcade.PhysicsEnginePlatformer
        self.spring_board_positions: List[Tuple[int, int]] = []

    def setup(self) -> None:
        self.player = arcade.Sprite("./assets/characters/placeholder_character.png")
        self.player.center_x = 64
        self.player.center_y = 124
        self.load_map(f"./assets/maps/level_{self.level}.tmx")
        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player, self.wall_list, GRAVITY
        )
        self.view_bottom = 0
        self.view_left = 0

    def load_map(self, resource: str) -> None:
        tile_name = "ground"
        spring_layer = "spring_boards"
        my_map = arcade.tilemap.read_tmx(resource)

        self.wall_list = arcade.tilemap.process_layer(
            map_object=my_map, layer_name=tile_name, use_spatial_hash=True, scaling=0.5
        )
        spring_boards = arcade.tilemap.process_layer(
            map_object=my_map,
            layer_name=spring_layer,
            use_spatial_hash=True,
            scaling=0.5,
        )
        for spring_board in spring_boards:
            self.wall_list.append(spring_board)
            self.spring_board_positions.append(
                (
                    spring_board.center_x - (spring_board.width / 2),
                    spring_board.center_y + (spring_board.height / 2),
                )
            )

        if my_map.background_color:
            arcade.set_background_color(my_map.background_color)

    def on_draw(self) -> None:
        arcade.start_render()
        self.wall_list.draw()
        self.player.draw()

    def calculate_jump_speed(self) -> int:
        for pos in self.spring_board_positions:
            colliding_x = (
                pos[0] < self.player.center_x
                and pos[0] + TILE_WIDTH > self.player.center_x
            )
            colliding_y = (
                pos[1] < self.player.center_y
                and pos[1] + TILE_HEIGHT > self.player.center_y
            )
            if colliding_x and colliding_y:
                return BOOSTED_JUMP_SPEED

        return PLAYER_JUMP_SPEED

    def on_key_press(self, key: int, modifiers: int) -> None:
        if key == arcade.key.UP or key == arcade.key.W:
            if self.physics_engine.can_jump():
                x = self.calculate_jump_speed()
                logging.debug(x)
                self.player.change_y = x
        elif key == arcade.key.LEFT or key == arcade.key.A:
            self.player.change_x = -PLAYER_MOVEMENT_SPEED
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.player.change_x = PLAYER_MOVEMENT_SPEED

    def on_key_release(self, key: int, modifiers: int) -> None:
        if (
            key == arcade.key.LEFT
            or key == arcade.key.A
            or key == arcade.key.RIGHT
            or key == arcade.key.D
        ):
            self.player.change_x = 0

    def death(self) -> None:
        self.setup()

    def on_update(self, delta_time: float) -> None:
        self.physics_engine.update()
        if self.player.center_y < self.player.height - 300:
            self.death()
        changed = False

        if self.player.center_x <= self.player.width / 2:
            self.player.center_x = self.player.width / 2
            self.player.change_x = 0

        max_left_distance = self.view_left + VIEWPORT_MARGIN
        if self.player.left < max_left_distance:
            self.view_left -= max_left_distance - self.player.left
            changed = True

        max_left_distance = self.view_left + WIDTH - VIEWPORT_MARGIN
        if self.player.right > max_left_distance:
            self.view_left += self.player.right - max_left_distance
            changed = True

        max_bottom_distance = self.view_bottom + VIEWPORT_MARGIN
        if self.player.bottom < max_bottom_distance:
            self.view_bottom -= max_bottom_distance - self.player.bottom
            changed = True

        max_top_distance = self.view_bottom + HEIGHT - VIEWPORT_MARGIN
        if self.player.top > max_top_distance:
            self.view_bottom += self.player.top - max_top_distance
            changed = True

        if self.view_left <= 0:
            self.view_left = 0
        if self.view_bottom <= 0:
            self.view_bottom = 0

        # Ensure that the viewport will map exactly onto pixels on the sprites

        self.view_left = int(self.view_left)
        self.view_bottom = int(self.view_bottom)

        # If we changed the boundary values, update the view port to match
        if changed:
            arcade.set_viewport(
                self.view_left,
                WIDTH + self.view_left,
                self.view_bottom,
                HEIGHT + self.view_bottom,
            )


if __name__ == "__main__":
    game = Game()
    game.setup()
    arcade.run()
