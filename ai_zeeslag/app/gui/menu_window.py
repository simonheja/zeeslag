import pygame
import os
import time

from app.gui.ui_helpers import (
    COLOR_ACCENT,
    COLOR_HIT,
    COLOR_INVALID,
    COLOR_TEXT,
    COLOR_TEXT_DIM,
    COLOR_TEXT_BLACK,
    COLOR_TEXT_ORANGE,
    COLOR_VALID,
    COLOR_WATER,
    COLOR_WATER_HOVER,
    COLOR_BACKGROUND,
    MENU_WINDOW_SIZE,
    WINDOW_MARGIN,
    BoardLayout,
    Button_Event_Handler,
    Button,
    Spinbox,
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
    """Initial screen for selecting the desired game state"""

    def __init__(self) -> None:
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
                "count_up": Button(pygame.Rect(30, 30, 30, 30), "^", 2),
                "count_down": Button(pygame.Rect(30, 60, 30, 30), "v"),
                "back": Button(pygame.Rect(100-BUTTON_WIDTH/2, 390, BUTTON_WIDTH, BUTTON_HEIGHT), "<< Difficulty"),
                "continue": Button(pygame.Rect(720-BUTTON_WIDTH/2, 390, BUTTON_WIDTH, BUTTON_HEIGHT), "Start Game")
            }
        }

        self.button_event_handler = Button_Event_Handler()
        
        self.spinbox = Spinbox(pygame.Rect(400,300,50,20), self.button_event_handler, "", (255,255,255), (200,200,200))
        self.spinbox.init_button_events()

        self.initialize_buttons()

        

    def initialize_buttons(self):
        """
        Add buttons to the event listner

        TODO:
        - buttons are currently detected globaly, make a selector that can disable buttons when they are not drawn to the screen
        """
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
                self._state.selected_difficulty,
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
            # call button event loop
            self.button_event_handler.handle_button_events(event.pos)

    def _update_difficulty(self, difficulty:str|None) -> None:
        if difficulty is None:
            # Reset difficulty
            self._state.selected_difficulty = None
            return
        
        match difficulty:
            case Difficulty.EASY:
                self._state.selected_difficulty = Difficulty.EASY
            case Difficulty.NORMAL:
                self._state.selected_difficulty = Difficulty.NORMAL
            case Difficulty.HARD:
                self._state.selected_difficulty = Difficulty.HARD
            case Difficulty.EXPERT:
                self._state.selected_difficulty = Difficulty.EXPERT
            case _:
                raise InvalidDifficulty(f"The selected difficulty '{difficulty}' could not be handeld")


    def update(self) -> None:
        pass

    # ------------------------------------------------------------------ #
    # Drawing
    # ------------------------------------------------------------------ #

    def draw_fps(self) -> None:
        if getattr(self, "_delta_time", None):
            draw_text(self._screen, f"FPS: {1/self._delta_time:.0f}", title_font(10), COLOR_VALID, (20, 5))

    def draw_difficulty_bar(self) -> None:
        match self._state.selected_difficulty:
            case Difficulty.EASY:
                draw_text(self._screen, f"Difficulty: {self._state.selected_difficulty}", title_font(40), COLOR_VALID, (400, 25))
            case Difficulty.NORMAL:
                draw_text(self._screen, f"Difficulty: {self._state.selected_difficulty}", title_font(40), COLOR_TEXT_BLACK, (400, 25))
            case Difficulty.HARD:
                draw_text(self._screen, f"Difficulty: {self._state.selected_difficulty}", title_font(40), COLOR_TEXT_ORANGE, (400, 25))
            case Difficulty.EXPERT:
                draw_text(self._screen, f"Difficulty: {self._state.selected_difficulty}", title_font(40), COLOR_HIT, (400, 25))
            case _:
                draw_text(self._screen, f"Difficulty: Not Selected", title_font(40), COLOR_TEXT_DIM, (400, 25))

    def draw(self) -> None:
        """
        Draw updates
        """
        # Draw background from image or color
        if self._background is not None:
            self._screen.blit(self._background, (0, 0))
        else:
            self._screen.fill(COLOR_BACKGROUND)

        # Get mouse position
        mouse = pygame.mouse.get_pos()

        # Draw/Update buttons
        self._refresh_buttons(mouse)

        self.draw_fps()

        self.draw_difficulty_bar()

        draw_text(self._screen, f"x: {mouse[0]} y: {mouse[1]}", title_font(12), COLOR_TEXT_BLACK, (775, 450))

        if self._state.selected_difficulty:
            draw_text(self._screen, f"Amount of ships: {self._state.ship_count}", title_font(16), COLOR_VALID, (200, 60))

    def _refresh_buttons(self, mouse:tuple[int,int]) -> None:
        if self._state.selected_difficulty is None:
            for button in self._buttons["difficulty-select"].values():
                button.draw(self._screen, mouse)
        elif self._state.selected_difficulty and True: # Tempory, no further checks yet
            for button in self._buttons["ships"].values():
                button.draw(self._screen, mouse)
                self.spinbox.draw(self._screen, mouse)
                


if __name__ == "__main__":
    menu = MenuWindow().start()

    # if the menu was exited using the close button, imidatly kill the programm
    if not menu.killed:
        print(menu.state)