import pygame
import os

from app.gui.ui_helpers import (
    COLOR_ACCENT,
    COLOR_HIT,
    COLOR_INVALID,
    COLOR_MISS,
    COLOR_SHIP,
    COLOR_SUNK,
    COLOR_TEXT,
    COLOR_TEXT_DIM,
    COLOR_VALID,
    COLOR_WATER,
    COLOR_WATER_HOVER,
    MENU_WINDOW_SIZE,
    WINDOW_MARGIN,
    BoardLayout,
    Button,
    body_font,
    draw_board_labels,
    draw_cross,
    draw_panel,
    draw_text,
    load_background,
    title_font,
)
from app.data.game_init_data import (
    Dificulty,
    MenuState
)

class ManuWindow:
    """Initial screen for selecting the desired game state

    Args:
        pass:pass
    """

    def __init__(self, *args) -> None:
        self._screen: pygame.Surface
        self._background: pygame.Surface | None = None
        self._running = False
        self._state = MenuState()

    def start(self):
        self.setup()
        clock = pygame.time.Clock()
        self._running = True
        while self._running:
            for event in pygame.event.get():
                self.handle_event(event)
            self.update()

    def setup(self):
        os.environ.setdefault("SDL_VIDEO_WINDOW_POS", f"{WINDOW_MARGIN},40")
        pygame.init()
        self._screen = pygame.display.set_mode(MENU_WINDOW_SIZE)
        pygame.display.set_caption("Battleship - Menu")
        self._background = load_background(MENU_WINDOW_SIZE)

    def handle_event(self, event):
        pass

    def update(self):
        state = self._state
        if state.selected_dificutly != None:
            pass