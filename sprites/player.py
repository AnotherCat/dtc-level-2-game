from enum import IntEnum
from typing import Any, List, NamedTuple

import arcade

from arcade import PymunkPhysicsEngine, Sprite, Texture


class FacingDirection(IntEnum):
    RIGHT = 0
    LEFT = 1


class TexturePair(NamedTuple):
    right: Texture
    left: Texture


def load_texture_pair(image_path: str) -> TexturePair:
    """Returns an instance of TexturePair with the textures set"""
    right_facing = arcade.load_texture(image_path)
    left_facing = arcade.load_texture(image_path, flipped_horizontally=True)
    return TexturePair(right=right_facing, left=left_facing)


class Player(Sprite):
    """
    Class for managing the player's animations
    "frames" How many frames the character has
    "image_path" The path to the characters images, "_frame_{frame_num}.png" will be appended. (frame_num is 0 to (frames - 1))
    The idle frame must be "{image_path}_idle.png"
    All images must be facing right
    "dead_zone" the amount of distance to ignore movement, so that animations are not updating constantly
    "distance_before_change_texture" the distance moved to update the animation after
    """

    def __init__(
        self,
        frames: int,
        image_path: str,
        dead_zone: float,
        distance_before_change_texture: int,
    ) -> None:
        """Setup the player"""
        super().__init__(hit_box_algorithm="Detailed")

        # Set passed through vars
        self.frames = frames
        self.dead_zone = dead_zone
        self.distance_before_change_texture = distance_before_change_texture

        # Stores what direction the character is facing. This is used to access the texture list
        # the first in the list will be right facing, and the second left facing
        self.facing = FacingDirection.RIGHT

        # Which texture is currently loaded / to be loaded. It is 0 to (frames - 1)
        self.current_texture = 0

        # The 'odometer' to track how much the sprite has moved
        self.x_odometer: float = 0

        # If the player is standing still
        self.idle = True

        # Load the idle texture pair
        self.idle_texture_pair = load_texture_pair(f"{image_path}_idle.png")

        # Load the textures for moving. This will have "frames" number of items
        self.moving_textures: List[TexturePair] = []
        for i in range(self.frames):
            texture_pair = load_texture_pair(f"{image_path}_frame_{i}.png")
            self.moving_textures.append(texture_pair)

        self.texture = self.idle_texture_pair.right

    def get_texture_from_pair(self, texture_pair: TexturePair) -> Texture:
        """Selects which texture to use from the texture pair depending on the facing direction"""
        if self.facing == FacingDirection.RIGHT:
            return texture_pair.right
        else:
            return texture_pair.left

    def pymunk_moved(
        self, physics_engine: PymunkPhysicsEngine, dx: float, dy: float, d_angle: Any
    ) -> None:
        """Handle being moved by the pymunk engine"""
        # Figure out if we need to face left or right
        if dx < -self.dead_zone and self.facing == FacingDirection.RIGHT:
            self.facing = FacingDirection.LEFT
        elif dx > self.dead_zone and self.facing == FacingDirection.LEFT:
            self.facing = FacingDirection.RIGHT

        # Add to the odometer how far we've moved
        self.x_odometer += dx
        """
        # Animation while jumping
        # Check if the player is touching the ground
        is_on_ground = physics_engine.is_on_ground(self)
        if not is_on_ground:
            if dy > self.dead_zone:
                self.texture = self.get_texture_from_pair(self.jump_texture_pair)
                return
            elif dy < -self.dead_zone:
                self.texture = self.get_texture_from_pair(self.fall_texture_pair)
                return
        """

        # Animation while idle
        if abs(dx) <= self.dead_zone:
            self.texture = self.get_texture_from_pair(self.idle_texture_pair)
            return

        # Check if the player has moved enough to change the texture
        if abs(self.x_odometer) > self.distance_before_change_texture:

            # Reset the odometer
            self.x_odometer = 0

            # Move the current texture to the next texture
            self.current_texture += 1
            if self.current_texture > (self.frames - 1):
                self.current_texture = 0
            self.texture = self.get_texture_from_pair(
                self.moving_textures[self.current_texture]
            )
