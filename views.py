from typing import List, Optional, Tuple

from arcade import (
    PymunkPhysicsEngine,
    Sprite,
    SpriteList,
    View,
    draw_text,
    set_background_color,
    set_viewport,
    start_render,
)
from arcade.color import WHITE
from arcade.csscolor import DARK_SLATE_BLUE
from arcade.key import LEFT, RIGHT, UP, A, D, W
from arcade.tilemap import process_layer, read_tmx

from static_values import (
    BOOSTED_PLAYER_JUMP_IMPULSE,
    DEFAULT_DAMPING,
    GRAVITY,
    HEIGHT,
    PLAYER_FRICTION,
    PLAYER_JUMP_IMPULSE,
    PLAYER_MASS,
    PLAYER_MAX_HORIZONTAL_SPEED,
    PLAYER_MAX_VERTICAL_SPEED,
    PLAYER_MOVE_FORCE_IN_AIR,
    PLAYER_MOVE_FORCE_ON_GROUND,
    TILE_HEIGHT,
    TILE_WIDTH,
    VIEWPORT_MARGIN,
    WALL_FRICTION,
    WIDTH,
)


class GameView(View):
    def __init__(self) -> None:
        super().__init__()
        self.level = 1
        self.view_bottom: int
        self.view_left: int
        self.wall_list: SpriteList
        self.player: Sprite
        self.spring_board_positions: List[Tuple[int, int]] = []
        self.physics_engine: PymunkPhysicsEngine

        self.left_pressed = False
        self.right_pressed = False

        self.window.set_mouse_visible(False)

    def setup(self) -> None:
        self.player = Sprite(
            "./assets/characters/placeholder_character.png",
            hit_box_algorithm="Detailed",
        )
        self.player.center_x = 64
        self.player.center_y = 400
        self.load_map(f"./assets/maps/level_{self.level}.tmx")
        self.view_bottom = 0
        self.view_left = 0
        gravity = (0, -GRAVITY)

        damping = DEFAULT_DAMPING

        self.physics_engine = PymunkPhysicsEngine(damping=damping, gravity=gravity)

        self.physics_engine.add_sprite(
            self.player,
            friction=PLAYER_FRICTION,
            mass=PLAYER_MASS,
            moment=PymunkPhysicsEngine.MOMENT_INF,
            collision_type="player",
            max_horizontal_velocity=PLAYER_MAX_HORIZONTAL_SPEED,
            max_vertical_velocity=PLAYER_MAX_VERTICAL_SPEED,
        )

        self.physics_engine.add_sprite_list(
            self.wall_list,
            friction=WALL_FRICTION,
            collision_type="wall",
            body_type=PymunkPhysicsEngine.STATIC,
        )

    def load_map(self, resource: str) -> None:
        tile_name = "ground"
        spring_layer = "spring_boards"
        my_map = read_tmx(resource)

        self.wall_list = process_layer(
            map_object=my_map, layer_name=tile_name, use_spatial_hash=True, scaling=0.5
        )
        spring_boards = process_layer(
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
            set_background_color(my_map.background_color)

    def on_draw(self) -> None:
        start_render()
        self.wall_list.draw()
        self.player.draw()

    def calculate_jump_impulse(self) -> int:
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
                return BOOSTED_PLAYER_JUMP_IMPULSE

        return PLAYER_JUMP_IMPULSE

    def on_key_press(self, key: int, modifiers: int) -> None:
        if key == LEFT or key == A:
            self.left_pressed = True
        elif key == RIGHT or key == D:
            self.right_pressed = True
        elif key == UP or W:
            if self.physics_engine.is_on_ground(self.player):
                impulse = (0, self.calculate_jump_impulse())
                self.physics_engine.apply_impulse(self.player, impulse)

    def on_key_release(self, key: int, modifiers: int) -> None:
        if key == LEFT or key == A:
            self.left_pressed = False
        elif key == RIGHT or key == D:
            self.right_pressed = False

    def death(self) -> None:
        view = GameOverView()
        self.window.show_view(view)

    def on_update(self, delta_time: float) -> None:
        on_ground = self.physics_engine.is_on_ground(self.player)
        if self.left_pressed and not self.right_pressed:
            if on_ground:
                force = (-PLAYER_MOVE_FORCE_ON_GROUND, 0)
            else:
                force = (-PLAYER_MOVE_FORCE_IN_AIR, 0)
            self.physics_engine.apply_force(self.player, force)
        elif self.right_pressed and not self.left_pressed:
            if on_ground:
                force = (PLAYER_MOVE_FORCE_ON_GROUND, 0)
            else:
                force = (PLAYER_MOVE_FORCE_IN_AIR, 0)
            self.physics_engine.apply_force(self.player, force)
            self.physics_engine.set_friction(self.player, 0)
        else:
            self.physics_engine.set_friction(self.player, 1.0)

        self.physics_engine.step()

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
            set_viewport(
                self.view_left,
                WIDTH + self.view_left,
                self.view_bottom,
                HEIGHT + self.view_bottom,
            )


class GameOverView(View):
    """View to show when game is over"""

    def __init__(self) -> None:
        """This is run once when we switch to this view"""
        super().__init__()

        self.window.set_mouse_visible(True)
        # Make the mouse visible

        # Reset the viewport, necessary if we have a scrolling game and we need
        # to reset the viewport back to the start so we can see what we draw.
        set_viewport(0, WIDTH - 1, 0, HEIGHT - 1)

    def on_draw(self) -> None:
        """Draw this view"""
        start_render()
        draw_text(
            "Game Over", WIDTH / 2, HEIGHT / 2, WHITE, font_size=50, anchor_x="center"
        )
        draw_text(
            "Click to restart",
            WIDTH / 2,
            HEIGHT / 2 - 75,
            WHITE,
            font_size=20,
            anchor_x="center",
        )

    def on_mouse_press(self, _x: float, _y: float, _button: int, _modifiers: int) -> None:
        """If the user presses the mouse button, re-start the game."""
        game_view = GameView()
        game_view.setup()
        self.window.show_view(game_view)


class InstructionView(View):
    def on_show(self) -> None:
        """This is run once when we switch to this view"""
        set_background_color(DARK_SLATE_BLUE)

        self.window.set_mouse_visible(True)
        # Make the mouse visible

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
            "Click to advance",
            WIDTH / 2,
            HEIGHT / 2 - 75,
            WHITE,
            font_size=20,
            anchor_x="center",
        )

    def on_mouse_press(self, _x: float, _y: float, _button: int, _modifiers: int) -> None:
        """If the user presses the mouse button, start the game."""
        game_view = GameView()
        game_view.setup()
        self.window.show_view(game_view)
