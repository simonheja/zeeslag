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
    Buttons,
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
from app.game_logic.open_functions import (
    ShipSpec
)

# Set FPS cap to 60
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
            "ships": {
                "count_up": Button(pygame.Rect(30, 30, 30, 30), "^"),
                "count_down": Button(pygame.Rect(30, 60, 30, 30), "v"),
                "back": Button(pygame.Rect(100-BUTTON_WIDTH/2, 400, BUTTON_WIDTH, BUTTON_HEIGHT), "<< Difficulty"),
                "continue": Button(pygame.Rect(720-BUTTON_WIDTH/2, 400, BUTTON_WIDTH, BUTTON_HEIGHT), "Start Game")
            }
        }

        self.button_event_handler = Buttons()
        self.initialize_buttons()

    def initialize_buttons(self):
        @self.button_event_handler.button_event(self._buttons["difficulty-select"][Difficulty.EASY])
        def set_dificulty_easy():
            self._update_difficulty(Difficulty.EASY)

        @self.button_event_handler.button_event(self._buttons["difficulty-select"][Difficulty.NORMAL])
        def set_dificulty_normal():
            self._update_difficulty(Difficulty.NORMAL)

        @self.button_event_handler.button_event(self._buttons["difficulty-select"][Difficulty.HARD])
        def set_dificulty_hard():
            self._update_difficulty(Difficulty.HARD)

        @self.button_event_handler.button_event(self._buttons["difficulty-select"][Difficulty.EXPERT])
        def set_dificulty_expert():
            self._update_difficulty(Difficulty.EXPERT)

        @self.button_event_handler.button_event(self._buttons["ships"]["back"])
        def reset_difficulty():
            self._update_difficulty(None)

        @self.button_event_handler.button_event(self._buttons["ships"]["continue"])
        def start_game():
            self._running = False

        @self.button_event_handler.button_event(self._buttons["ships"]["count_up"])
        def add_ship():
            self._state.add_ship(ShipSpec("Destroyer", 5))

        @self.button_event_handler.button_event(self._buttons["ships"]["count_down"])
        def remove_ship():
            self._state.remove_ship()

    @property
    def state(self) -> GameSettings|None:
        if self._state.complete():
            return GameSettings(
                self._state.selected_dificutly,
                Available_AI.DEFAULT,
                self._state.ship_config
            )

    def start(self):
        self.setup()
        clock = pygame.time.Clock()
        self._running = True
        while self._running:
            start = time.perf_counter()
            for event in pygame.event.get():
                self.handle_event(event)

            # Call update event
            self.update()

            # Update changes in the buffer
            self.draw()

            # Display all applied changes to the screen
            pygame.display.flip()

            # Limit FPS to set FPS cap
            clock.tick(FPS)

            # Do a calculation on the amount of time it took to render the current frame
            # AKA. 'DeltaTime'
            stop = time.perf_counter()
            self._delta_time = stop-start

        # UnInitialize pygame for clean shutdown
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
            self.button_event_handler.handle_button_events(event.pos)

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
        """
        Draw updates
        """
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

        if self._state.selected_dificutly:
            draw_text(self._screen, f"Amount of ships: {self._state.ship_count}", title_font(16), COLOR_VALID, (200, 60))

    def _refresh_buttons(self, mouse:tuple[int,int]) -> None:
        state = self._state
        if state.selected_dificutly is None:
            for button in self._buttons["difficulty-select"].values():
                button.draw(self._screen, mouse)
        elif state.selected_dificutly and True: # Tempory, no further checks yet
            for button in self._buttons["ships"].values():
                button.draw(self._screen, mouse)


if __name__ == "__main__":
    menu = MenuWindow().start()

    # if the menu was exited using the close button, imidatly kill the programm
    if not menu.killed:
        print(menu.state)