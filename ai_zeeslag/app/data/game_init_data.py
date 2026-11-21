from dataclasses import dataclass
from enum import IntEnum, StrEnum
from app.game_logic.open_functions import (
    ShipSpec
)


class Difficulty(StrEnum):
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"
    EXPERT = "expert"

class Available_AI(StrEnum):
    DEFAULT = "probability density"
    MINMAX = "MiniMax algorithm"

@dataclass
class MenuState:
    selected_dificutly: Difficulty|None = None
    boat_config: tuple[ShipSpec, ...]|None = None

    def complete(self):
        return not (self.selected_dificutly is None) and not (self.boat_config is None)

@dataclass
class GameSettings:
    dificulty: Difficulty
    ai_model: Available_AI
    ship_config: tuple[ShipSpec, ...]