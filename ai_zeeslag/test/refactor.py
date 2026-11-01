"""
Battleship: Human vs AI
=======================

Assets expected beside this file:
    bg.jpg
    secret.ttf

Install:
    pip install pygame

Run:
    python battleship_ai.py

The game uses two Pygame windows:
- Main window: the human player's fleet and incoming AI attacks.
- AI window: the AI's fleet, incoming human attacks, AI statistics, and the
  clickable target grid used by the human player.

AI integration
--------------
Pass an object implementing:

    class MyAI:
        def choose_move(self, observation: AIObservation) -> tuple[int, int]:
            ...

The AI receives only its own attack history and the coordinates it has not
yet attacked. It never receives the human player's hidden fleet layout.

The game controller also exposes get_observation(), get_legal_moves(),
fire_at(), player_fire_at(), and get_game_state() for external AI code.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Protocol

import pygame
from pygame._sdl2.video import Renderer, Texture, Window


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
AI_WINDOW_WIDTH = 1400
AI_WINDOW_HEIGHT = 800

BOARD_SIZE = 10
CELL_SIZE = 60
CELL_GAP = 4
BOARD_LEFT = 50
BOARD_TOP = 50
FPS = 30

BACKGROUND_FILE = "bg.jpg"
FONT_FILE = "secret.ttf"

WATER = "O"
HORIZONTAL = 1
VERTICAL = 2

COLOR_BACKGROUND = (235, 240, 245)
COLOR_GRID = (30, 50, 65)
COLOR_SHIP = (75, 90, 105)
COLOR_HIT = (210, 55, 55)
COLOR_MISS = (55, 135, 190)
COLOR_TEXT = (15, 25, 35)
COLOR_PANEL = (220, 228, 235)
COLOR_PREVIEW = (25, 25, 25)


# ---------------------------------------------------------------------------
# Data models and AI interface
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Ship:
    """A ship definition."""

    name: str
    length: int
    direction: int = HORIZONTAL


@dataclass(frozen=True)
class ShotRecord:
    """A shot made by the AI against the human player's board."""

    row: int
    column: int
    hit: bool


@dataclass(frozen=True)
class AIObservation:
    """
    Information the AI is allowed to know.

    `available_moves` contains untried (row, column) coordinates.
    `shots` contains the AI's previous attacks and whether they hit.
    No hidden human ship positions are included.
    """

    board_size: int
    available_moves: tuple[tuple[int, int], ...]
    shots: tuple[ShotRecord, ...]
    hits: tuple[tuple[int, int], ...]
    misses: tuple[tuple[int, int], ...]
    shots_taken: int
    hits_scored: int


@dataclass(frozen=True)
class ShotResult:
    """Result of a valid or invalid shot."""

    valid: bool
    hit: bool = False
    row: Optional[int] = None
    column: Optional[int] = None


@dataclass(frozen=True)
class GameState:
    """Public high-level game status."""

    game_over: bool
    winner: Optional[str]
    current_turn: str
    human_shots: int
    ai_shots: int
    human_hits: int
    ai_hits: int


class AIPlayer(Protocol):
    """Interface that an external AI algorithm must implement."""

    def choose_move(self, observation: AIObservation) -> tuple[int, int]:
        """Return the next target as (row, column)."""
        ...


class RandomAI:
    """Simple example AI. Replace this with your own algorithm."""

    def choose_move(self, observation: AIObservation) -> tuple[int, int]:
        if not observation.available_moves:
            raise RuntimeError("The AI has no legal moves remaining.")
        return random.choice(observation.available_moves)


# ---------------------------------------------------------------------------
# Board and game rules
# ---------------------------------------------------------------------------

class Board:
    """Stores ship locations and the results of incoming shots."""

    def __init__(
        self,
        size: int = BOARD_SIZE,
        cell_size: int = CELL_SIZE,
        left: int = BOARD_LEFT,
        top: int = BOARD_TOP,
        gap: int = CELL_GAP,
    ) -> None:
        self.size = size
        self.cell_size = cell_size
        self.left = left
        self.top = top
        self.gap = gap
        self.pitch = cell_size + gap

        self.ships: list[list[str]] = []
        self.shots: list[list[Optional[str]]] = []
        self.hit_count = 0
        self.shot_count = 0
        self.reset()

    def reset(self) -> None:
        self.ships = [[WATER for _ in range(self.size)] for _ in range(self.size)]
        self.shots = [[None for _ in range(self.size)] for _ in range(self.size)]
        self.hit_count = 0
        self.shot_count = 0

    def place_ship(
        self,
        name: str,
        length: int,
        direction: int,
        row: int,
        column: int,
    ) -> bool:
        """Place a ship without overlap or orthogonal contact."""
        if direction == HORIZONTAL:
            row_step, column_step = 0, 1
        elif direction == VERTICAL:
            row_step, column_step = 1, 0
        else:
            return False

        cells = [
            (row + row_step * offset, column + column_step * offset)
            for offset in range(length)
        ]

        for ship_row, ship_column in cells:
            if not (0 <= ship_row < self.size and 0 <= ship_column < self.size):
                return False
            if self.ships[ship_row][ship_column] != WATER:
                return False

        proposed_cells = set(cells)
        for ship_row, ship_column in cells:
            neighbours = (
                (ship_row - 1, ship_column),
                (ship_row + 1, ship_column),
                (ship_row, ship_column - 1),
                (ship_row, ship_column + 1),
            )
            for neighbour_row, neighbour_column in neighbours:
                if not (
                    0 <= neighbour_row < self.size
                    and 0 <= neighbour_column < self.size
                ):
                    continue
                if (neighbour_row, neighbour_column) in proposed_cells:
                    continue
                if self.ships[neighbour_row][neighbour_column] != WATER:
                    return False

        for ship_row, ship_column in cells:
            self.ships[ship_row][ship_column] = name
        return True

    def place_random_fleet(self, fleet: list[Ship]) -> None:
        """Place every ship at a randomly selected legal position."""
        self.reset()

        for ship in fleet:
            candidates = [
                (row, column, direction)
                for direction in (HORIZONTAL, VERTICAL)
                for row in range(self.size)
                for column in range(self.size)
            ]
            random.shuffle(candidates)

            for row, column, direction in candidates:
                if self.place_ship(
                    ship.name, ship.length, direction, row, column
                ):
                    break
            else:
                raise RuntimeError(f"Unable to place ship {ship.name!r}.")

    def fire_at(self, row: int, column: int) -> ShotResult:
        """Fire at a board cell. Repeated or out-of-range shots are invalid."""
        if not (0 <= row < self.size and 0 <= column < self.size):
            return ShotResult(valid=False)

        if self.shots[row][column] is not None:
            return ShotResult(valid=False, row=row, column=column)

        hit = self.ships[row][column] != WATER
        self.shots[row][column] = "hit" if hit else "miss"
        self.shot_count += 1

        if hit:
            self.hit_count += 1

        return ShotResult(valid=True, hit=hit, row=row, column=column)

    def pixel_to_cell(self, x: int, y: int) -> Optional[tuple[int, int]]:
        """Convert a mouse position on this board to a grid coordinate."""
        offset_x = x - self.left
        offset_y = y - self.top

        if offset_x < 0 or offset_y < 0:
            return None

        row = offset_y // self.pitch
        column = offset_x // self.pitch

        if not (0 <= row < self.size and 0 <= column < self.size):
            return None

        if offset_x >= self.size * self.pitch or offset_y >= self.size * self.pitch:
            return None

        return int(row), int(column)

    def legal_moves(self) -> tuple[tuple[int, int], ...]:
        """Return every cell that has not been attacked yet."""
        return tuple(
            (row, column)
            for row in range(self.size)
            for column in range(self.size)
            if self.shots[row][column] is None
        )

    def draw(self, surface: pygame.Surface, reveal_ships: bool = True) -> None:
        """Draw the fleet and incoming shots."""
        for row in range(self.size):
            for column in range(self.size):
                x = self.left + column * self.pitch
                y = self.top + row * self.pitch
                ship_present = self.ships[row][column] != WATER
                shot = self.shots[row][column]

                if shot == "hit":
                    color = COLOR_HIT
                elif shot == "miss":
                    color = COLOR_MISS
                elif reveal_ships and ship_present:
                    color = COLOR_SHIP
                else:
                    color = COLOR_BACKGROUND

                pygame.draw.rect(
                    surface,
                    color,
                    (x, y, self.cell_size, self.cell_size),
                )
                pygame.draw.rect(
                    surface,
                    COLOR_GRID,
                    (x, y, self.cell_size, self.cell_size),
                    width=1,
                )


# ---------------------------------------------------------------------------
# Main display
# ---------------------------------------------------------------------------

class MainDisplay:
    """Manages the human player's main game window."""

    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Battleship - Player")
        self.clock = pygame.time.Clock()

        asset_dir = Path(__file__).resolve().parent
        self.font_path = str(asset_dir / FONT_FILE)
        background_path = asset_dir / BACKGROUND_FILE

        if background_path.exists():
            background = pygame.image.load(str(background_path)).convert()
            self.background = pygame.transform.scale(
                background, (SCREEN_WIDTH, SCREEN_HEIGHT)
            )
        else:
            self.background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            self.background.fill(COLOR_BACKGROUND)

        self.fonts: dict[int, pygame.font.Font] = {}

    def font(self, size: int) -> pygame.font.Font:
        if size not in self.fonts:
            try:
                self.fonts[size] = pygame.font.Font(self.font_path, size)
            except FileNotFoundError:
                self.fonts[size] = pygame.font.Font(None, size)
        return self.fonts[size]

    def draw_text(
        self,
        text: str,
        size: int,
        center: tuple[int, int],
        surface: Optional[pygame.Surface] = None,
    ) -> None:
        target = surface if surface is not None else self.screen
        rendered = self.font(size).render(text, True, COLOR_TEXT)
        target.blit(rendered, rendered.get_rect(center=center))

    def tick(self) -> None:
        self.clock.tick(FPS)


# ---------------------------------------------------------------------------
# Separate AI information and target window
# ---------------------------------------------------------------------------

class AIWindow:
    """
    A second SDL2 window showing the AI fleet and AI diagnostics.

    The grid in this window is clickable: the human player selects a target
    by clicking a cell on the AI board.
    """

    def __init__(self, font_provider: MainDisplay) -> None:
        self.width = AI_WINDOW_WIDTH
        self.height = AI_WINDOW_HEIGHT
        self.window = Window(
            "Battleship - AI board and information",
            size=(self.width, self.height),
            position=(SCREEN_WIDTH + 30, 40),
        )
        self.renderer = Renderer(self.window)
        self.surface = pygame.Surface((self.width, self.height))
        self.font_provider = font_provider
        self.window_id = self.window.id
        self.is_open = True

    def draw_text(
        self,
        text: str,
        size: int,
        center: tuple[int, int],
        color: tuple[int, int, int] = COLOR_TEXT,
    ) -> None:
        rendered = self.font_provider.font(size).render(text, True, color)
        self.surface.blit(rendered, rendered.get_rect(center=center))

    def render(
        self,
        ai_board: Board,
        state: GameState,
        last_human_shot: Optional[ShotResult],
        last_ai_shot: Optional[ShotResult],
        status_message: str,
    ) -> None:
        if not self.is_open:
            return

        self.surface.fill(COLOR_BACKGROUND)
        ai_board.draw(self.surface, reveal_ships=True)

        panel = pygame.Rect(750, 40, 600, 700)
        pygame.draw.rect(self.surface, COLOR_PANEL, panel, border_radius=12)

        self.draw_text("AI BOARD", 36, (1000, 85))
        self.draw_text("Click a cell to attack the AI", 22, (1000, 130))

        self.draw_text("GAME INFORMATION", 27, (1000, 220))
        self.draw_text(f"Turn: {state.current_turn}", 23, (870, 275))
        self.draw_text(f"Status: {status_message}", 19, (1000, 320))

        self.draw_text("Human attacks", 22, (905, 390))
        self.draw_text(f"Shots: {state.human_shots}", 20, (905, 425))
        self.draw_text(f"Hits: {state.human_hits}", 20, (905, 455))

        self.draw_text("AI attacks", 22, (905, 520))
        self.draw_text(f"Shots: {state.ai_shots}", 20, (905, 555))
        self.draw_text(f"Hits: {state.ai_hits}", 20, (905, 585))

        if last_human_shot is not None and last_human_shot.valid:
            result = "hit" if last_human_shot.hit else "miss"
            self.draw_text(f"Last human shot: {result}", 18, (955, 650))

        if last_ai_shot is not None and last_ai_shot.valid:
            result = "hit" if last_ai_shot.hit else "miss"
            self.draw_text(f"Last AI shot: {result}", 18, (955, 680))

        self.draw_text(
            "Ships: S=5  K=4  F=3  M=2",
            18,
            (950, 720),
        )

        texture = Texture.from_surface(self.renderer, self.surface)
        self.renderer.clear()
        self.renderer.blit(texture)
        self.renderer.present()
        #  texture.destroy()

    def close(self) -> None:
        if self.is_open:
            self.is_open = False
            self.window.destroy()


# ---------------------------------------------------------------------------
# Game controller and public AI API
# ---------------------------------------------------------------------------

class BattleshipGame:
    """
    Human-versus-AI game controller.

    Public AI methods:
        get_observation()
        get_legal_moves()
        fire_at(row, column)
        get_game_state()

    To plug in an algorithm, pass an AIPlayer implementation to the
    constructor. Its choose_move() method receives an AIObservation.
    """

    FLEET = (
        Ship("S", 5),
        Ship("K", 4),
        Ship("F", 3),
        Ship("F", 3),
        Ship("M", 2),
    )
    WINNING_HITS = sum(ship.length for ship in FLEET)

    def __init__(self, ai_agent: Optional[AIPlayer] = None) -> None:
        self.display = MainDisplay()
        self.ai_window: Optional[AIWindow] = None
        self.ai_agent: AIPlayer = ai_agent if ai_agent is not None else RandomAI()

        self.player_board = Board()
        self.ai_board = Board()

        self.game_over = False
        self.winner: Optional[str] = None
        self.current_turn = "human"
        self.last_human_shot: Optional[ShotResult] = None
        self.last_ai_shot: Optional[ShotResult] = None
        self.status_message = "Place your fleet to begin."

    def make_fleet(self) -> list[Ship]:
        return [Ship(ship.name, ship.length, ship.direction) for ship in self.FLEET]

    # ----- Public API for AI algorithms ---------------------------------

    def get_legal_moves(self) -> tuple[tuple[int, int], ...]:
        """
        Return untried cells on the human board.

        This method does not expose the locations of the human's ships.
        """
        return self.player_board.legal_moves()

    def get_observation(self) -> AIObservation:
        """Return the information available to the AI algorithm."""
        shots: list[ShotRecord] = []

        for row in range(self.player_board.size):
            for column in range(self.player_board.size):
                result = self.player_board.shots[row][column]
                if result is not None:
                    shots.append(
                        ShotRecord(
                            row=row,
                            column=column,
                            hit=(result == "hit"),
                        )
                    )

        hits = tuple((shot.row, shot.column) for shot in shots if shot.hit)
        misses = tuple((shot.row, shot.column) for shot in shots if not shot.hit)

        return AIObservation(
            board_size=self.player_board.size,
            available_moves=self.get_legal_moves(),
            shots=tuple(shots),
            hits=hits,
            misses=misses,
            shots_taken=len(shots),
            hits_scored=len(hits),
        )

    def fire_at(self, row: int, column: int) -> ShotResult:
        """
        Execute an AI attack against the human board.

        Intended to be called by the AI algorithm. Returns a ShotResult.
        """
        if self.game_over or self.current_turn != "ai":
            return ShotResult(valid=False)

        result = self.player_board.fire_at(row, column)
        if result.valid:
            self.last_ai_shot = result
            if self.player_board.hit_count >= self.WINNING_HITS:
                self.game_over = True
                self.winner = "AI"
                self.status_message = "The AI has won."
            else:
                self.current_turn = "human"
                self.status_message = (
                    f"AI fired at ({row}, {column}): "
                    f"{'hit' if result.hit else 'miss'}"
                )
        return result

    def player_fire_at(self, row: int, column: int) -> ShotResult:
        """Execute a human attack against the AI board."""
        if self.game_over or self.current_turn != "human":
            return ShotResult(valid=False)

        result = self.ai_board.fire_at(row, column)
        if result.valid:
            self.last_human_shot = result
            if self.ai_board.hit_count >= self.WINNING_HITS:
                self.game_over = True
                self.winner = "Human"
                self.status_message = "You have won!"
            else:
                self.current_turn = "ai"
                self.status_message = (
                    f"Human fired at ({row}, {column}): "
                    f"{'hit' if result.hit else 'miss'}"
                )
        return result

    def get_game_state(self) -> GameState:
        """Return public game status and statistics."""
        return GameState(
            game_over=self.game_over,
            winner=self.winner,
            current_turn=self.current_turn,
            human_shots=self.ai_board.shot_count,
            ai_shots=self.player_board.shot_count,
            human_hits=self.ai_board.hit_count,
            ai_hits=self.player_board.hit_count,
        )

    def play_ai_turn(self) -> ShotResult:
        """
        Ask the configured AI to choose and execute one move.

        An external AI can instead call get_observation() and fire_at()
        itself, provided it is currently the AI's turn.
        """
        if self.game_over or self.current_turn != "ai":
            return ShotResult(valid=False)

        observation = self.get_observation()
        if not observation.available_moves:
            self.game_over = True
            self.winner = "Human"
            self.status_message = "The AI has no legal moves remaining."
            return ShotResult(valid=False)

        row, column = self.ai_agent.choose_move(observation)

        if (row, column) not in observation.available_moves:
            raise ValueError(
                f"AI returned illegal move {(row, column)}. "
                "Choose a coordinate from observation.available_moves."
            )

        return self.fire_at(row, column)

    # ----- Menu and setup ------------------------------------------------

    def run(self) -> None:
        running = True

        while running:
            self.display.tick()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    x, y = event.pos
                    if 350 < x < 650 and 430 < y < 510:
                        if self.start_game():
                            self.game_loop()

            self.draw_menu()

        if self.ai_window is not None:
            self.ai_window.close()
        pygame.quit()

    def draw_menu(self) -> None:
        self.display.screen.blit(self.display.background, (0, 0))
        self.display.draw_text(
            "Battleship", 100, (SCREEN_WIDTH // 2, 230)
        )
        self.display.draw_text("PLAY AGAINST AI", 34, (500, 470))
        pygame.display.flip()

    def start_game(self) -> bool:
        """Set up the human fleet and generate the AI fleet."""
        self.player_board = Board()
        self.ai_board = Board()

        if not self.place_human_fleet():
            return False

        self.ai_board.place_random_fleet(self.make_fleet())

        self.game_over = False
        self.winner = None
        self.current_turn = "human"
        self.last_human_shot = None
        self.last_ai_shot = None
        self.status_message = "Your turn. Click the AI board to attack."

        self.ai_window = AIWindow(self.display)
        return True

    # ----- Human fleet placement ----------------------------------------

    def place_human_fleet(self) -> bool:
        """Let the human drag and drop their five ships."""
        self.display.screen = pygame.display.set_mode(
            (SCREEN_WIDTH + 200, SCREEN_HEIGHT)
        )
        self.display.background = pygame.transform.scale(
            self.display.background, (SCREEN_WIDTH + 200, SCREEN_HEIGHT)
        )

        ships = self.make_fleet()
        ship_index = 0
        dragging = False
        mouse_x, mouse_y = 800, 400
        running = True
        self.player_board.reset()

        while running and ship_index < len(ships):
            self.display.tick()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break

                if ship_index >= len(ships):
                    break

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_x, mouse_y = event.pos
                    dragging = True
                    if 870 < mouse_x < 988 and 685 < mouse_y < 718:
                        ships[ship_index] = Ship(
                            ships[ship_index].name,
                            ships[ship_index].length,
                            VERTICAL
                            if ships[ship_index].direction == HORIZONTAL
                            else HORIZONTAL,
                        )

                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    dragging = False
                    mouse_x, mouse_y = event.pos
                    cell = self.player_board.pixel_to_cell(mouse_x, mouse_y)

                    if cell is not None:
                        row, column = cell
                        ship = ships[ship_index]
                        if self.player_board.place_ship(
                            ship.name, ship.length, ship.direction, row, column
                        ):
                            ship_index += 1

                    mouse_x, mouse_y = 800, 400

                elif event.type == pygame.MOUSEMOTION and dragging:
                    mouse_x, mouse_y = event.pos

            if ship_index < len(ships):
                self.draw_placement_screen(
                    ships[ship_index], mouse_x, mouse_y
                )

        self.display.screen = pygame.display.set_mode(
            (SCREEN_WIDTH, SCREEN_HEIGHT)
        )
        self.display.background = pygame.transform.scale(
            self.display.background, (SCREEN_WIDTH, SCREEN_HEIGHT)
        )
        return running and ship_index == len(ships)

    def draw_placement_screen(
        self,
        ship: Ship,
        mouse_x: int,
        mouse_y: int,
    ) -> None:
        screen = self.display.screen
        screen.blit(self.display.background, (0, 0))
        self.player_board.draw(screen, reveal_ships=True)

        preview_x = mouse_x - 20
        preview_y = mouse_y - 20
        for _ in range(ship.length):
            pygame.draw.rect(
                screen,
                COLOR_PREVIEW,
                (preview_x, preview_y, CELL_SIZE, CELL_SIZE),
            )
            if ship.direction == HORIZONTAL:
                preview_x += CELL_SIZE + CELL_GAP
            else:
                preview_y += CELL_SIZE + CELL_GAP

        self.display.draw_text("SWITCH", 30, (1000, 700))
        self.display.draw_text("PLACE YOUR FLEET", 28, (1000, 100))
        self.display.draw_text("RULES", 30, (985, 150))
        self.display.draw_text(
            "1. Place each ship on the board.", 20, (1000, 200)
        )
        self.display.draw_text(
            "2. Ships cannot touch sideways.", 20, (1000, 245)
        )
        pygame.display.flip()

    # ----- Main game loop -----------------------------------------------

    def game_loop(self) -> None:
        running = True

        while running and not self.game_over:
            self.display.tick()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break

                if event.type == pygame.WINDOWCLOSE:
                    if getattr(event, "window", None) == (
                        self.ai_window.window_id if self.ai_window else None
                    ):
                        running = False
                        break

                if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
                    continue

                event_window = getattr(
                    event, "window", getattr(event, "windowID", None)
                )

                # The AI board is the human's target grid.
                if (
                    self.ai_window is not None
                    and event_window == self.ai_window.window_id
                    and self.current_turn == "human"
                ):
                    cell = self.ai_board.pixel_to_cell(*event.pos)
                    if cell is not None:
                        row, column = cell
                        result = self.player_fire_at(row, column)

                        if result.valid and not self.game_over:
                            self.play_ai_turn()

            self.draw_main_screen()
            self.draw_ai_window()

        if self.game_over:
            self.show_winner()

        if self.ai_window is not None:
            self.ai_window.close()
            self.ai_window = None

    # ----- Drawing -------------------------------------------------------

    def draw_main_screen(self) -> None:
        """The main window displays only the human player's own board."""
        self.display.screen.blit(self.display.background, (0, 0))
        self.player_board.draw(self.display.screen, reveal_ships=True)

        state = self.get_game_state()
        self.display.draw_text("YOUR FLEET", 38, (950, 100))
        self.display.draw_text(f"Turn: {state.current_turn}", 27, (950, 180))
        self.display.draw_text(
            f"AI shots received: {state.ai_shots}", 22, (950, 250)
        )
        self.display.draw_text(
            f"Ships hit: {state.ai_hits}/{self.WINNING_HITS}",
            22,
            (950, 295),
        )
        self.display.draw_text(
            "Attack the AI board", 23, (950, 400)
        )
        self.display.draw_text(
            "in the second window.", 23, (950, 435)
        )
        self.display.draw_text(self.status_message, 17, (950, 530))
        pygame.display.flip()

    def draw_ai_window(self) -> None:
        if self.ai_window is None or not self.ai_window.is_open:
            return
        self.ai_window.render(
            ai_board=self.ai_board,
            state=self.get_game_state(),
            last_human_shot=self.last_human_shot,
            last_ai_shot=self.last_ai_shot,
            status_message=self.status_message,
        )

    def show_winner(self) -> None:
        running = True

        while running:
            self.display.tick()
            for event in pygame.event.get():
                if event.type in (pygame.QUIT, pygame.MOUSEBUTTONDOWN):
                    running = False

            self.display.screen.blit(self.display.background, (0, 0))
            message = "You won!" if self.winner == "Human" else "The AI won!"
            self.display.draw_text(message, 60, (SCREEN_WIDTH // 2, 300))
            self.display.draw_text(
                f"Human shots: {self.ai_board.shot_count}",
                28,
                (SCREEN_WIDTH // 2, 410),
            )
            self.display.draw_text(
                f"AI shots: {self.player_board.shot_count}",
                28,
                (SCREEN_WIDTH // 2, 460),
            )
            self.display.draw_text(
                "Click to return to the menu", 22, (SCREEN_WIDTH // 2, 700)
            )
            pygame.display.flip()


# ---------------------------------------------------------------------------
# Example entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Replace RandomAI() with your own class implementing choose_move().
    game = BattleshipGame(ai_agent=RandomAI())
    game.run()