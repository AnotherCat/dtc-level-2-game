from enum import IntEnum
from typing import Any, List, NamedTuple

import arcade

from arcade import PhysicsEnginePlatformer, Sprite, Texture


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
    "distance_before_change_texture" the distance moved to update the animation after
    """

    def __init__(
        self,
        frames: int,
        image_path: str,
        distance_before_change_texture: int,
    ) -> None:
        """Setup the player"""
        super().__init__(hit_box_algorithm="Detailed")

        # Set passed through vars
        self.frames = frames
        self.distance_before_change_texture = distance_before_change_texture

        # Stores what direction the character is facing. This is used to access the texture list
        # the first in the list will be right facing, and the second left facing
        self.facing = FacingDirection.RIGHT

        # Which texture is currently loaded / to be loaded. It is 0 to (frames - 1)
        self.current_texture = 0

        # If the player is standing still
        self.idle = True

        # Load the idle texture pair
        self.idle_texture_pair = load_texture_pair(f"{image_path}_idle.png")

        # Used to measure the distance the player has travelled, then used to move the animation frames
        self.last_x_position = self.center_x

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

    def update_animation_with_physics(
        self, physics_engine: PhysicsEnginePlatformer, delta_time: float = 1 / 60
    ) -> None:
        """Handle being moved by the pymunk engine"""
        # Figure out if we need to face left or right
        if self.change_x < 0 and self.facing == FacingDirection.RIGHT:
            self.facing = FacingDirection.LEFT
        elif self.change_x > 0 and self.facing == FacingDirection.LEFT:
            self.facing = FacingDirection.RIGHT

        # Animation while jumping, this is set to the 'idle' texture
        # Check if the player is touching the ground

        if not physics_engine.can_jump():
            self.texture = self.get_texture_from_pair(self.idle_texture_pair)

            # Also reset the moving textures, and set the last position to the current position
            # so that the animation doesn't 'jump' when it lands
            self.last_x_position = self.center_x
            self.current_texture = 0
            return

        # Animation while idle
        if self.change_x == 0:
            self.texture = self.get_texture_from_pair(self.idle_texture_pair)

            # Also reset the moving textures, and set the last position to the current position
            # so that the animation doesn't 'jump' when it starts moving again
            self.last_x_position = self.center_x
            self.current_texture = 0
            return

        x_moved = abs(self.last_x_position - self.center_x)

        # Check if the player has moved enough to change the texture
        if x_moved >= self.distance_before_change_texture:
            self.last_x_position = self.center_x

            # Move the current texture to the next texture
            self.current_texture += 1
            if self.current_texture > (self.frames - 1):

                self.current_texture = 0
            self.texture = self.get_texture_from_pair(
                self.moving_textures[self.current_texture]
            )
