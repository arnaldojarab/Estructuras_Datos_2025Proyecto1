from enum import Enum, auto

class GameState(Enum):
    MENU = auto()
    PLAYING = auto()
    INVENTORY = auto()
    GAME_OVER = auto()
    PAUSED = auto()
