import pygame
import os
import time

from app.gui.ui_helpers import (
    COLOR_ACCENT,
    COLOR_HIT,
    COLOR_INVALID,
    COLOR_TEXT,
    COLOR_TEXT_DIM,
    COLOR_VALID,
    COLOR_WATER,
    COLOR_WATER_HOVER,
    COLOR_BACKGROUND,
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
    Difficulty,
    Available_AI,
    MenuState,
    GameSettings
)

from app.exceptions.MenuExceptions import (
    InvalidDifficulty
)

FPS = 60

BUTTON_WIDTH = 190
BUTTON_HEIGHT = 44

class MenuWindow:
    """Initial screen for selecting the desired game state

    Args:
        pass:pass
    """

    def __init__(self, *args) -> None:
        self._screen: pygame.Surface
        self._background: pygame.Surface | None = None
        self._running = False
        self._state = MenuState()

        self.killed = False
        self._buttons:dict[str, dict[str,Button]] = {
            "difficulty-select": {
                Difficulty.EASY : Button(pygame.Rect(400-BUTTON_WIDTH/2, 60, BUTTON_WIDTH, BUTTON_HEIGHT), "Easy"),
                Difficulty.NORMAL: Button(pygame.Rect(400-BUTTON_WIDTH/2, 110, BUTTON_WIDTH, BUTTON_HEIGHT), "Normal"),
                Difficulty.HARD: Button(pygame.Rect(400-BUTTON_WIDTH/2, 160, BUTTON_WIDTH, BUTTON_HEIGHT), "Hard"),
                Difficulty.EXPERT: Button(pygame.Rect(400-BUTTON_WIDTH/2, 210, BUTTON_WIDTH, BUTTON_HEIGHT), "Expert")
            },
            "back": {
                "difficulty": Button(pygame.Rect(100-BUTTON_WIDTH/2, 400, BUTTON_WIDTH, BUTTON_HEIGHT), "<< Difficulty")
            },
            "continue": {
                "start": Button(pygame.Rect(720-BUTTON_WIDTH/2, 400, BUTTON_WIDTH, BUTTON_HEIGHT), "Start Game")
            }
        }

    @property
    def state(self) -> GameSettings|None:
        if self._state.complete():
            return GameSettings(
                self._state.selected_dificutly,
                Available_AI.DEFAULT,
                self._state.boat_config
            )

    def start(self):
        self.setup()
        clock = pygame.time.Clock()
        self._running = True
        while self._running:
            start = time.perf_counter()
            for event in pygame.event.get():
                self.handle_event(event)
            self.update()
            self.draw()
            pygame.display.flip()
            clock.tick(FPS)
            stop = time.perf_counter()
            self._delta_time = stop-start

        pygame.quit()
        return self

    def setup(self) -> None:
        os.environ.setdefault("SDL_VIDEO_WINDOW_POS", f"{WINDOW_MARGIN},40")
        pygame.init()
        self._screen = pygame.display.set_mode(MENU_WINDOW_SIZE)
        pygame.display.set_caption("Battleship - Menu")
        self._background = load_background(MENU_WINDOW_SIZE)

    def handle_event(self, event) -> None:
        if event.type == pygame.QUIT:
            self._running = False
            self.killed = True

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Check buttons
            for mode, button in self._buttons["difficulty-select"].items():
                if button.contains(event.pos):
                    self._update_difficulty(mode)

            for button in self._buttons["back"].values():
                if button.contains(event.pos):
                    self._update_difficulty(None)

            if self._buttons["continue"]["start"].contains(event.pos):
                self._running = False

    def _update_difficulty(self, difficulty:str|None) -> None:
        if difficulty is None:
            self._state.selected_dificutly = None
            return
        
        match difficulty:
            case Difficulty.EASY:
                self._state.selected_dificutly = Difficulty.EASY
            case Difficulty.NORMAL:
                self._state.selected_dificutly = Difficulty.NORMAL
            case Difficulty.HARD:
                self._state.selected_dificutly = Difficulty.HARD
            case Difficulty.EXPERT:
                self._state.selected_dificutly = Difficulty.EXPERT
            case _:
                raise InvalidDifficulty(f"The selected difficulty '{difficulty}' could not be handeld")


    def update(self) -> None:
        state = self._state
        if state.selected_dificutly != None:
            pass

    # ------------------------------------------------------------------ #
    # Drawing
    # ------------------------------------------------------------------ #
    def draw(self) -> None:
        if self._background is not None:
            self._screen.blit(self._background, (0, 0))
        else:
            self._screen.fill(COLOR_BACKGROUND)

        mouse = pygame.mouse.get_pos()
        self._refresh_buttons(mouse)

        if getattr(self, "_delta_time", None):
            draw_text(self._screen, f"FPS: {1/self._delta_time:.0f}", title_font(10), COLOR_VALID, (20, 5))

        draw_text(self._screen, f"Selected difficulty: {self._state.selected_dificutly}", title_font(40), COLOR_TEXT_DIM, (400, 25))
        draw_text(self._screen, f"x: {mouse[0]} y: {mouse[1]}", title_font(16), COLOR_HIT, (760, 440))

    def _refresh_buttons(self, mouse:tuple[int,int]) -> None:
        state = self._state
        if state.selected_dificutly is None:
            for button in self._buttons["difficulty-select"].values():
                button.draw(self._screen, mouse)
        elif True: # Tempory, no further checks yet
            self._buttons["back"]["difficulty"].draw(self._screen, mouse)
            self._buttons["continue"]["start"].draw(self._screen, mouse)

if __name__ == "__main__":
    menu = MenuWindow().start()

    # if the menu was exited using the close button, imidatly kill the programm
    if not menu.killed:
        print(menu.state)