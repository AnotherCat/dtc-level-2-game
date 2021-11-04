import os

from arcade import Window, run

from static_values import HEIGHT, TITLE, WIDTH
from views import GameOverView, GameView, GameWonView, InstructionView

# Change the file path to the directory `main.py` is in. This ensures that asset path's will work
file_path = os.path.dirname(os.path.abspath(__file__))
os.chdir(file_path)


class GameWindow(Window):
    def __init__(self, width: int, height: int, title: str) -> None:
        super().__init__(width=width, height=height, title=title)
        self.instruction_view = InstructionView()
        self.game_view = GameView()
        self.game_over_view = GameOverView()
        self.winning_view = GameWonView()


if __name__ == "__main__":
    window = GameWindow(WIDTH, HEIGHT, TITLE)
    window.show_view(window.instruction_view)
    run()
