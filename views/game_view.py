from label import Label
from typing import TYPE_CHECKING, List, NamedTuple, Optional

from arcade import (
    PymunkPhysicsEngine,
    SpriteList,
    Sprite,
    View,
    check_for_collision_with_list,
    set_background_color,
    set_viewport,
    start_render,
)
from arcade.key import LEFT, RIGHT, UP, A, D, W
from arcade.tilemap import process_layer, read_tmx
from copy import deepcopy

from errors import IncorrectNumberOfMarkers
from sprites.player import Player
from static_values import (
    BOOSTED_PLAYER_JUMP_IMPULSE,
    DEFAULT_DAMPING,
    GRAVITY,
    HEIGHT,
    MAX_LEVEL,
    PLAYER_FRICTION,
    PLAYER_JUMP_IMPULSE,
    PLAYER_MASS,
    PLAYER_MAX_HORIZONTAL_SPEED,
    PLAYER_MAX_VERTICAL_SPEED,
    PLAYER_MOVE_FORCE_IN_AIR,
    PLAYER_MOVE_FORCE_ON_GROUND,
    TILE_HEIGHT,
    TILE_WIDTH,
    TIME_PER_POWER_DECREASE,
    VIEWPORT_MARGIN,
    WALL_FRICTION,
    WIDTH,
    INITIAL_POWER,
    START_LEVEL
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
        self.time_until_next_generation = 0
        self.time_per_generation = time_per_generation

    def update(self, delta_time: float) -> Optional[Sprite]:
        self.time_until_next_generation -= delta_time
        if self.time_until_next_generation <= 0:
            self.time_until_next_generation = self.time_per_generation
            
            return deepcopy(self.sprite)

class GameView(View):
    def __init__(self) -> None:
        super().__init__()
        self.level = START_LEVEL
        self.power: float = INITIAL_POWER
        self.view_bottom: int
        self.view_left: int
        self.wall_list: SpriteList
        self.battery_list: SpriteList
        self.death_list: SpriteList
        self.win_list: SpriteList

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
        self.physics_engine: PymunkPhysicsEngine

        self.left_pressed = False
        self.right_pressed = False

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
            dead_zone=0.5,
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

        gravity = (0, -GRAVITY)
        self.power = INITIAL_POWER
        self.power_label = Label(format_string="Power Level: {value}",
        initial_value=self.power, x_offset = WIDTH - 50, y_offset= HEIGHT - 35)

        self.time_since_last_power_decrease = 0

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
        self.physics_engine.add_sprite_list(self.moving_up_list, body_type=PymunkPhysicsEngine.KINEMATIC,
 )
        self.left_pressed = False
        self.right_pressed = False

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
            layer_name = win_layer_name,
            use_spatial_hash= True,
            scaling= 0.5,
        )

        moving_up_list = process_layer(
            map_object=map,
            layer_name =moving_up_layer_name,
            use_spatial_hash= False,
            scaling = 0.5
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
            #if moving_up.seconds_per_tile:
             #   seconds_per_tile = moving_up.seconds_per_tile
            moving_tile_generator = MovingUpTileGenerator(
                    time_per_generation=seconds_per_tile,
                    sprite = moving_up
                )
            self.static_moving_up_list.append(
                moving_tile_generator
            )

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
        self.power_label.draw(self.view_left, self.view_bottom, round(self.power,1 ))

    def calculate_jump_impulse(self) -> int:
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

    def check_for_collision_with_battery(self):
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
        to_decrease = 1 /  TIME_PER_POWER_DECREASE * delta_time
        self.power -= to_decrease
        """
        self.time_since_last_power_decrease += delta_time
        if self.time_since_last_power_decrease >= TIME_PER_POWER_DECREASE:
            self.time_since_last_power_decrease -=TIME_PER_POWER_DECREASE
            self.power -= 1
        """

    def check_power(self) -> None:
        """Check to see if the power is too low
        """
        if self.power <= 0:
            self.death()
            return

    def update_moving_sprites(self, delta_time: float) -> None:
        for moving_up in self.static_moving_up_list:
            moving_sprite = moving_up.update(delta_time)
            if moving_sprite is not None:
                moving_sprite.change_y = 50
                self.moving_up_list.append(moving_sprite)
                self.physics_engine.add_sprite(
                    moving_sprite,
                    body_type=PymunkPhysicsEngine.KINEMATIC
                )

        for moving_sprite in self.moving_up_list:
            if moving_sprite.boundary_top and \
                    moving_sprite.top > moving_sprite.boundary_top:
                moving_sprite.remove_from_sprite_lists()
                return
            if moving_sprite.right > (WIDTH + self.view_left) or \
                    moving_sprite.left < (self.view_left) or \
                    moving_sprite.top > (HEIGHT + self.view_bottom):
                # The bottom is not included in the check because it starts below the view port
                moving_sprite.remove_from_sprite_lists()
                return

            # Figure out and set our moving platform velocity.
            # Pymunk uses velocity is in pixels per second. If we instead have
            # pixels per frame, we need to convert.
            velocity = (moving_sprite.change_x * 1 / delta_time, moving_sprite.change_y * 1 / delta_time)
            self.physics_engine.set_velocity(moving_sprite, velocity)
    def on_update(self, delta_time: float) -> None:
        self.update_moving_sprites(delta_time)


        if self.check_for_collision_with_death() or self.player.center_y < self.player.height - 300 or self.player.center_x <= self.player.width / 2:
            self.death()
            return
        if self.check_for_collision_with_win():
            self.win()
            return

        self.check_for_collision_with_battery()


        self.reduce_power(delta_time=delta_time)
        self.check_power()
        self.power_label.update(delta_time=delta_time)

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
