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
    _ship_config: list[ShipSpec]|None = None
    ship_count:int = 0

    @property
    def ship_config(self) -> tuple[ShipSpec, ...] | None:
        if self._ship_config is None:
            return 
        else:
            return tuple(self._ship_config)

    def add_ship(self, ship:ShipSpec) -> None:
        if self._ship_config is None or self.ship_count <= 0:
            self._ship_config = []
            self.ship_count = 0
        
        self._ship_config.append(ship)
        self.ship_count += 1

    def remove_ship(self, ship_index:int = -1) -> None:
        if not (self._ship_config is None):
            if self.ship_count > 0:
                self._ship_config.pop(ship_index)
                self.ship_count -= 1
        else:
            pass # Add error handeling here

    def complete(self):
        return not (self.selected_dificutly is None) and not (self.ship_config is None) and self.ship_count > 0

@dataclass
class GameSettings:
    dificulty: Difficulty
    ai_model: Available_AI
    ship_config: tuple[ShipSpec, ...]