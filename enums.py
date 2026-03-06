from enum import Enum

class BotDifficulty(Enum):
    EASY = "Легкий"
    MEDIUM = "Средний"
    HARD = "Сложный"

class GameState(Enum):
    MENU = 1
    SETTINGS = 9
    SERVER_LIST = 2
    DIRECT_CONNECT = 7 
    WAITING_CONNECTION = 8
    PREPARATION = 3
    BATTLE = 4
    GAME_OVER = 5
    WAITING_PLAYER = 6

class CellState(Enum):
    EMPTY = 0
    SHIP = 1
    HIT = 2
    MISS = 3
    DESTROYED = 4
    
    def to_symbol(self):
        symbols = {
            CellState.EMPTY: ".",
            CellState.SHIP: "#",
            CellState.HIT: "X",
            CellState.MISS: "O",
            CellState.DESTROYED: "D"
        }
        return symbols.get(self, "?")