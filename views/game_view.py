from copy import deepcopy
from typing import TYPE_CHECKING, List, NamedTuple, Optional

from arcade import (
    Sprite,
    SpriteList,
    View,
    check_for_collision_with_list,
    set_background_color,
    set_viewport,
    start_render,
)
from arcade.key import LEFT, RIGHT, UP, A, D, W
from arcade.physics_engines import PhysicsEnginePlatformer
from arcade.tilemap import process_layer, read_tmx

from errors import IncorrectNumberOfMarkers
from label import Label
from sprites.player import Player
from static_values import (
    BOOSTED_PLAYER_JUMP_SPEED,
    GRAVITY,
    HEIGHT,
    INITIAL_POWER,
    MAX_LEVEL,
    PLAYER_JUMP_SPEED,
    PLAYER_MOVEMENT_SPEED,
    START_LEVEL,
    TILE_HEIGHT,
    TILE_WIDTH,
    TIME_PER_POWER_DECREASE,
    VIEWPORT_MARGIN,
    WIDTH,
)

if TYPE_CHECKING:
    from main import GameWindow


class CoordinateTuple(NamedTuple):
    """
    A representation of a coordinate that makes references to coordinates easier to understand.
    For example `position.x` instead of `position[0]`
    """

    x: int
    y: int


class MovingUpTileGenerator:
    """
    A class for 'deciding' when to 'generate' a new moving up sprite
    """

    def __init__(self, time_per_generation: float, sprite: Sprite) -> None:
        self.sprite = sprite
        self.time_until_next_generation: float = 0
        self.time_per_generation = time_per_generation

    def update(self, delta_time: float) -> Optional[Sprite]:
        self.time_until_next_generation -= delta_time
        if self.time_until_next_generation <= 0:
            self.time_until_next_generation = self.time_per_generation

            return deepcopy(self.sprite)
        return None  # Appease mypy


class GameView(View):
    def __init__(self) -> None:
        super().__init__()
        self.level = START_LEVEL
        self.power: float = INITIAL_POWER
        self.view_bottom: int
        self.view_left: int
        self.battery_list: SpriteList
        self.death_list: SpriteList
        self.win_list: SpriteList

        # All sprites that the player should be able to have "contact" with.
        self.contact_list: SpriteList

        # Wall sprites
        self.wall_list: SpriteList

        # List of sprites that are moving up currently
        self.moving_up_list: SpriteList

        # The list of sprites that sprites will "rise" from
        self.static_moving_up_list: List[MovingUpTileGenerator]
        self.player: Player
        self.power_label: Label
        self.time_since_last_power_decrease = 0
        self.spring_board_positions: List[CoordinateTuple] = []

        # The bottom x and y position that the player should start at
        self.player_start_position: CoordinateTuple
        self.physics_engine: PhysicsEnginePlatformer

        self.window.set_mouse_visible(False)
        self.window: "GameWindow"

        # If the view should update the viewport
        # This is false when other views are focused
        self.inactive = True

    def setup(self) -> None:

        """Sets up the view. This is separate from __init__ so that the view can be 'reset' without recreating the view."""
        self.static_moving_up_list = []
        self.moving_up_list = SpriteList()
        self.inactive = False
        self.load_map(f"./assets/maps/level_{self.level}.tmx")
        self.player = Player(
            frames=3,
            image_path="./assets/characters/main_character/main_character",
            distance_before_change_texture=20,
        )

        # Add set the x,y positions of the player so that the bottom position of the player is inline with the stored position
        self.player.center_x = self.player_start_position.x + (self.player.height / 2)
        self.player.center_y = self.player_start_position.y + (self.player.width / 2)

        # Set the viewport to the player's position, if it is further away than the viewport margin
        self.view_bottom = (
            self.player.bottom + VIEWPORT_MARGIN
            if self.player.bottom > VIEWPORT_MARGIN
            else 0
        )
        self.view_left = (
            self.player.left + VIEWPORT_MARGIN
            if self.player.left > VIEWPORT_MARGIN
            else 0
        )
        self.power = INITIAL_POWER
        self.power_label = Label(
            format_string="Power Level: {value}",
            initial_value=self.power,
            x_offset=WIDTH - 50,
            y_offset=HEIGHT - 35,
        )

        self.time_since_last_power_decrease = 0

        # Perform an effectlivy "shallow copy" of the wall_list
        # so that when appending to contact_list that doesn't also append to the wall_list
        # normal shallow copy functions like copy.copy() or List[:] (https://docs.python.org/3/library/copy.html) don't seem to work with arcade SpriteLists
        self.contact_list = SpriteList(use_spatial_hash=True)
        for wall in self.wall_list:
            self.contact_list.append(wall)

        self.physics_engine = PhysicsEnginePlatformer(
            self.player, self.contact_list, GRAVITY
        )

    def load_map(self, resource: str) -> None:
        """
        Load the maps from tmx files. Different layers are used for different types of objects.
        """

        # This layer holds the 'walls', the tiles that are used to 'walk' on, that the player can't pass through
        tile_layer_name = "wall_contact"

        # This layer holds the springboards. The tiles are processed and then appended to the wall list
        spring_layer_name = "springboards"

        # This layer holds the batteries, which are a collectable
        battery_layer_name = "batteries"

        # This layer holds a single tile, which is a wall tile. This tile marks where the character should 'start'
        # The single tile is processed and then appended to the wall list
        start_marker_layer_name = "start_level_marker"

        # This layer contains tiles that if touched kill the player
        death_layer_name = "death"

        # This layer contains tiles that if touched the player will 'win' the level
        win_layer_name = "end_flag"

        # This layer contain the 'start' point of the moving upwards tiles
        moving_up_layer_name = "rising_only"

        # Read the tmx file
        map = read_tmx(resource)

        # Process layers, returning a sprite list
        spring_boards = process_layer(
            map_object=map,
            layer_name=spring_layer_name,
            use_spatial_hash=True,
            scaling=0.5,
        )
        start_marker_list = process_layer(
            map_object=map,
            layer_name=start_marker_layer_name,
            use_spatial_hash=True,
            scaling=0.5,
        )

        self.wall_list = process_layer(
            map_object=map,
            layer_name=tile_layer_name,
            use_spatial_hash=True,
            scaling=0.5,
        )

        self.battery_list = process_layer(
            map_object=map,
            layer_name=battery_layer_name,
            use_spatial_hash=True,
            scaling=0.5,
        )

        self.death_list = process_layer(
            map_object=map,
            layer_name=death_layer_name,
            use_spatial_hash=True,
            scaling=0.5,
        )

        self.win_list = process_layer(
            map_object=map,
            layer_name=win_layer_name,
            use_spatial_hash=True,
            scaling=0.5,
        )

        moving_up_list = process_layer(
            map_object=map,
            layer_name=moving_up_layer_name,
            use_spatial_hash=False,
            scaling=0.5,
        )

        # Process the marker and store it's coordinate
        marker_list_len = len(start_marker_list)
        if marker_list_len > 1 or marker_list_len < 1:
            raise IncorrectNumberOfMarkers(
                "There are too many markers in this level!"
                f"Expected markers: 1, Markers: {len(start_marker_list)}"
            )
        # Since the length was checked above, there should be only one item.
        marker_sprite = start_marker_list[0]
        # The player should start on the top of the tile, this stores the bottom x and bottom y of the start position.
        self.player_start_position = CoordinateTuple(
            x=marker_sprite.center_x + TILE_HEIGHT / 2,
            # 100 is added to the y value because the pymunk physics engine takes a while to kick in
            y=100 + marker_sprite.center_y - TILE_WIDTH / 2,
        )
        # Add the sprite to the wall list
        self.wall_list.append(marker_sprite)

        for spring_board in spring_boards:
            self.wall_list.append(spring_board)
            self.spring_board_positions.append(
                CoordinateTuple(
                    x=spring_board.center_x - (spring_board.width / 2),
                    y=spring_board.center_y + (spring_board.height / 2),
                )
            )

        for moving_up in moving_up_list:
            seconds_per_tile = 3
            # if moving_up.seconds_per_tile:
            #   seconds_per_tile = moving_up.seconds_per_tile
            moving_tile_generator = MovingUpTileGenerator(
                time_per_generation=seconds_per_tile, sprite=moving_up
            )
            self.static_moving_up_list.append(moving_tile_generator)

        if map.background_color:
            set_background_color(map.background_color)

    def on_draw(self) -> None:
        start_render()
        self.wall_list.draw()
        self.battery_list.draw()
        self.death_list.draw()
        self.win_list.draw()
        self.player.draw()
        self.moving_up_list.draw()
        self.power_label.draw(self.view_left, self.view_bottom, round(self.power, 1))

    def calculate_jump_speed(self) -> int:
        for pos in self.spring_board_positions:
            colliding_x = (
                pos.x < self.player.center_x
                and pos.x + TILE_WIDTH > self.player.center_x
            )
            colliding_y = (
                pos.y < self.player.center_y
                and pos.y + TILE_HEIGHT > self.player.center_y
            )
            if colliding_x and colliding_y:
                return BOOSTED_PLAYER_JUMP_SPEED

        return PLAYER_JUMP_SPEED

    def on_key_press(self, key: int, modifiers: int) -> None:
        if key == LEFT or key == A:
            self.player.change_x = -PLAYER_MOVEMENT_SPEED
        elif key == RIGHT or key == D:
            self.player.change_x = PLAYER_MOVEMENT_SPEED
        elif key == UP or W:
            if self.physics_engine.can_jump():

                self.player.change_y = self.calculate_jump_speed()

    def on_key_release(self, key: int, modifiers: int) -> None:
        if key == LEFT or key == A or key == RIGHT or key == D:
            self.player.change_x = 0

    def death(self) -> None:
        self.inactive = True
        self.window.game_over_view.setup()
        self.window.show_view(self.window.game_over_view)

    def win(self) -> None:
        self.level += 1
        if self.level > MAX_LEVEL:
            self.inactive = True
            self.window.winning_view.setup()
            self.window.show_view(self.window.winning_view)
            self.level = START_LEVEL
        else:
            self.setup()

    def check_for_collision_with_death(self) -> bool:
        return len(check_for_collision_with_list(self.player, self.death_list)) > 0

    def check_for_collision_with_win(self) -> bool:
        return len(check_for_collision_with_list(self.player, self.win_list)) > 0

    def check_for_collision_with_battery(self) -> None:
        list = check_for_collision_with_list(self.player, self.battery_list)
        for battery in list:
            battery.remove_from_sprite_lists()
            self.power_label.flash(10)
            self.power += 1

    def reduce_power(self, delta_time: float) -> None:
        """Reduces the power based on how much time has passed

        Args:
            delta_time (float): The time since last update
        """
        to_decrease = 1 / TIME_PER_POWER_DECREASE * delta_time
        self.power -= to_decrease
        """
        self.time_since_last_power_decrease += delta_time
        if self.time_since_last_power_decrease >= TIME_PER_POWER_DECREASE:
            self.time_since_last_power_decrease -=TIME_PER_POWER_DECREASE
            self.power -= 1
        """

    def check_power(self) -> None:
        """Check to see if the power is too low"""
        if self.power <= 0:
            self.death()
            return

    def update_moving_sprites(self, delta_time: float) -> None:
        for moving_up in self.static_moving_up_list:
            moving_sprite = moving_up.update(
                delta_time
            )  # See if a new sprite should be generated

            if moving_sprite is not None:
                moving_sprite.change_y = 4
                self.moving_up_list.append(moving_sprite)
                self.contact_list.append(moving_sprite)
        for moving_sprite in self.moving_up_list:
            if (
                moving_sprite.boundary_top
                and moving_sprite.top > moving_sprite.boundary_top
            ):
                moving_sprite.remove_from_sprite_lists()
                return
            if (
                moving_sprite.right > (WIDTH + self.view_left)
                or moving_sprite.left < (self.view_left)
                or moving_sprite.top > (HEIGHT + self.view_bottom)
            ):
                # The bottom is not included in the check because it starts below the view port
                moving_sprite.remove_from_sprite_lists()
                return
            moving_sprite.update()

            # NOTE MAY NEED TO ADD SETTING THE SPRITE'S SPEED HERE

    def on_update(self, delta_time: float) -> None:
        self.update_moving_sprites(delta_time)
        self.player.update_animation_with_physics(
            physics_engine=self.physics_engine, delta_time=delta_time
        )

        if (
            self.check_for_collision_with_death()
            or self.player.center_y < self.player.height - 300
            or self.player.center_x <= self.player.width / 2
        ):
            self.death()
            return
        if self.check_for_collision_with_win():
            self.win()
            return

        self.check_for_collision_with_battery()

        self.reduce_power(delta_time=delta_time)
        self.check_power()
        self.power_label.update(delta_time=delta_time)

        self.physics_engine.update()

        changed = False

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
        if changed and not self.inactive:
            set_viewport(
                self.view_left,
                WIDTH + self.view_left,
                self.view_bottom,
                HEIGHT + self.view_bottom,
            )
