from dataclasses import dataclass
from enum import IntEnum
from app.game_logic.open_functions import (
    ShipSpec
)


class Dificulty(IntEnum):
    EASY = 1
    NORMAL = 2
    EXPERT = 3
    LUNY = 4

class MenuState:
    selected_dificutly: Dificulty|None = None
    boat_config: tuple[ShipSpec]|None = None