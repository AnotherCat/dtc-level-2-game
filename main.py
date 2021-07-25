import logging
import os

import arcade

from static_values import HEIGHT, TITLE, WIDTH
from views import InstructionView

file_path = os.path.dirname(os.path.abspath(__file__))
os.chdir(file_path)
logging.basicConfig(level=logging.INFO)


if __name__ == "__main__":
    window = arcade.Window(WIDTH, HEIGHT, TITLE)
    start_view = InstructionView()
    window.show_view(start_view)
    arcade.run()
