import arcade, os
import logging

WIDTH = 1200
HEIGHT = 700
LEFT_VIEWPORT_MARGIN = 1
PLAYER_MOVEMENT_SPEED = 10
PLAYER_JUMP_SPEED = 5
TITLE = "Ice Game"
GRAVITY = 1

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

    def setup(self) -> None:
        self.player = arcade.Sprite(
            "./assets/characters/placeholder_character.png"
        )
        self.player.center_x = 64
        self.player.center_y = 124
        self.load_map(f"./assets/maps/level_{self.level}.tmx")
        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player, self.wall_list, GRAVITY
        )
        self.view_bottom = 0
        self.view_left = 0


    def load_map(self, resource: str) -> None:
        layer_name = "ground"
        my_map = arcade.tilemap.read_tmx(resource)


        self.wall_list = arcade.tilemap.process_layer(
            map_object=my_map, layer_name=layer_name, use_spatial_hash=True, scaling=0.5
        )
        if my_map.background_color:
            arcade.set_background_color(my_map.background_color)

    def on_draw(self) -> None:
        arcade.start_render()
        self.wall_list.draw()
        self.player.draw()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.UP or key == arcade.key.W:
            if self.physics_engine.can_jump():
                self.player.change_y = PLAYER_JUMP_SPEED
        elif key == arcade.key.LEFT or key == arcade.key.A:
            self.player.change_x = -PLAYER_MOVEMENT_SPEED
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.player.change_x = PLAYER_MOVEMENT_SPEED
        
    def on_key_release(self, key, modifiers):
        if key == arcade.key.LEFT or key == arcade.key.A or key == arcade.key.RIGHT or key == arcade.key.D:
            self.player.change_x = 0

    def on_update(self, delta_time):
        self.physics_engine.update()
        changed = False
        left_boundary = self.view_left + LEFT_VIEWPORT_MARGIN
        if self.player.left < left_boundary:
            self.view_left


if __name__ == "__main__":
    game = Game()
    game.setup()
    arcade.run()