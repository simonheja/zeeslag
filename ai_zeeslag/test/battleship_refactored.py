"""
Battleship (Pygame)
-------------------
A refactored, single-file version of the supplied game.

Assets expected beside this file:
    bg.jpg
    secret.ttf

Run with:
    python battleship.py

The game keeps the original rules and presentation:
- 10x10 boards and ships of lengths 5, 4, 3, 3 and 2.
- Ships may be horizontal or vertical.
- Ships may not touch orthogonally (diagonal contact is allowed).
- Single-player means shooting at a randomly generated fleet.
- Two-player mode alternates turns after each valid, previously unused shot.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pygame


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 800
PLACEMENT_EXTRA_WIDTH = 200

BOARD_SIZE = 10
CELL_SIZE = 60
CELL_GAP = 4
BOARD_LEFT = 50
BOARD_TOP = 50
FPS = 27

BACKGROUND_FILE = "bg.jpg"
FONT_FILE = "secret.ttf"

WATER = "O"
HORIZONTAL = 1
VERTICAL = 2

COLOR_HIT = (255, 0, 0)
COLOR_HIDDEN_WATER = (0, 0, 255)
COLOR_MISS = (0, 0, 0)
COLOR_SHIP = (0, 0, 0)
COLOR_TEXT = (0, 0, 0)


@dataclass
class Ship:
    """A ship definition used during fleet placement."""

    name: str
    length: int
    direction: int = HORIZONTAL

    def switch_direction(self) -> None:
        self.direction = VERTICAL if self.direction == HORIZONTAL else HORIZONTAL


# ---------------------------------------------------------------------------
# Board and game rules
# ---------------------------------------------------------------------------

class Board:
    """Stores a fleet and the shots fired at that fleet."""

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
        self.shots: list[list[str]] = []
        self.hit_count = 0
        self.shot_count = 0

        self.reset()

    def reset(self) -> None:
        """Create empty fleet and shot grids."""
        self.ships = [[WATER for _ in range(self.size)] for _ in range(self.size)]
        self.shots = [[WATER for _ in range(self.size)] for _ in range(self.size)]
        self.hit_count = 0
        self.shot_count = 0

    def cell_from_pixel(self, pixel_x: int, pixel_y: int) -> Optional[tuple[int, int]]:
        """
        Convert a screen position to (row, column).

        As in the original game, the four-pixel spacing after each cell is
        included in that cell's clickable area.
        """
        offset_x = pixel_x - self.left
        offset_y = pixel_y - self.top

        if offset_x <= 0 or offset_y <= 0:
            return None

        column = offset_x // self.pitch
        row = offset_y // self.pitch

        if not (0 <= row < self.size and 0 <= column < self.size):
            return None

        if offset_x >= self.size * self.pitch or offset_y >= self.size * self.pitch:
            return None

        return int(row), int(column)

    def place_ship(
        self,
        name: str,
        length: int,
        direction: int,
        row: int,
        column: int,
    ) -> bool:
        """
        Place a ship if it fits and does not touch another ship orthogonally.

        Diagonal contact is allowed, matching the adjacency checks in the
        original implementation. The board is only changed after every
        validation has passed, so a failed placement cannot leave partial data.
        """
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

        # Every ship segment must be inside the board and currently empty.
        for ship_row, ship_column in cells:
            if not (0 <= ship_row < self.size and 0 <= ship_column < self.size):
                return False
            if self.ships[ship_row][ship_column] != WATER:
                return False

        ship_cells = set(cells)

        # Check the four orthogonal neighbours of every proposed segment.
        for ship_row, ship_column in cells:
            for neighbour_row, neighbour_column in (
                (ship_row - 1, ship_column),
                (ship_row + 1, ship_column),
                (ship_row, ship_column - 1),
                (ship_row, ship_column + 1),
            ):
                if not (0 <= neighbour_row < self.size):
                    continue
                if not (0 <= neighbour_column < self.size):
                    continue
                if (neighbour_row, neighbour_column) in ship_cells:
                    continue
                if self.ships[neighbour_row][neighbour_column] != WATER:
                    return False

        for ship_row, ship_column in cells:
            self.ships[ship_row][ship_column] = name

        return True

    def place_random_fleet(self, fleet: list[Ship]) -> None:
        """Place a complete fleet by shuffling valid starting candidates."""
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
                if self.place_ship(ship.name, ship.length, direction, row, column):
                    break
            else:
                # This should not occur for the standard 10x10 fleet.
                raise RuntimeError(f"Could not place ship {ship.name!r}")

    def fire_at(self, pixel_x: int, pixel_y: int) -> Optional[bool]:
        """
        Fire at a screen coordinate.

        Returns:
            True  - a new shot was fired (hit or miss)
            False - this cell was already fired at
            None  - the click was outside the board
        """
        cell = self.cell_from_pixel(pixel_x, pixel_y)
        if cell is None:
            return None

        row, column = cell
        if self.shots[row][column] != WATER:
            return False

        self.shots[row][column] = "X"
        self.shot_count += 1

        if self.ships[row][column] != WATER:
            self.hit_count += 1

        return True

    def draw(self, surface: pygame.Surface, placing: bool = False) -> None:
        """Draw the board in placement mode or in normal play."""
        for row in range(self.size):
            y = self.top + row * self.pitch

            for column in range(self.size):
                x = self.left + column * self.pitch

                if placing:
                    color = COLOR_HIT if self.ships[row][column] != WATER else COLOR_HIDDEN_WATER
                elif self.shots[row][column] == WATER:
                    color = COLOR_HIDDEN_WATER
                elif self.ships[row][column] != WATER:
                    color = COLOR_HIT
                else:
                    color = COLOR_MISS

                pygame.draw.rect(
                    surface,
                    color,
                    (x, y, self.cell_size, self.cell_size),
                )


# ---------------------------------------------------------------------------
# Pygame presentation helpers
# ---------------------------------------------------------------------------

class GameDisplay:
    """Owns the window, background, clock and cached fonts."""

    def __init__(self) -> None:
        pygame.init()

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Battleship")
        self.clock = pygame.time.Clock()

        asset_dir = Path(__file__).resolve().parent
        self.font_path = str(asset_dir / FONT_FILE)

        background = pygame.image.load(str(asset_dir / BACKGROUND_FILE)).convert()
        self.background = pygame.transform.scale(
            background, (SCREEN_WIDTH, SCREEN_HEIGHT)
        )
        self.fonts: dict[int, pygame.font.Font] = {}

    def font(self, size: int) -> pygame.font.Font:
        if size not in self.fonts:
            self.fonts[size] = pygame.font.Font(self.font_path, size)
        return self.fonts[size]

    def draw_text(
        self,
        text: str,
        size: int,
        center: tuple[int, int],
        surface: Optional[pygame.Surface] = None,
    ) -> None:
        target = surface or self.screen
        rendered = self.font(size).render(text, True, COLOR_TEXT)
        rect = rendered.get_rect(center=center)
        target.blit(rendered, rect)

    def draw_background(self) -> None:
        self.screen.blit(self.background, (0, 0))

    def tick(self) -> None:
        self.clock.tick(FPS)

    def set_placement_mode(self, enabled: bool) -> None:
        if enabled:
            size = (SCREEN_WIDTH + PLACEMENT_EXTRA_WIDTH, SCREEN_HEIGHT)
        else:
            size = (SCREEN_WIDTH, SCREEN_HEIGHT)

        self.screen = pygame.display.set_mode(size)
        self.background = pygame.transform.scale(self.background, size)


# ---------------------------------------------------------------------------
# Game controller
# ---------------------------------------------------------------------------

class BattleshipGame:
    """Coordinates menus, ship placement, turns and win screens."""

    FLEET = (
        Ship("S", 5),
        Ship("K", 4),
        Ship("F", 3),
        Ship("F", 3),
        Ship("M", 2),
    )
    WINNING_HITS = sum(ship.length for ship in FLEET)

    def __init__(self) -> None:
        self.display = GameDisplay()
        self.player_turn: Optional[int] = None
        self.player_one_board: Optional[Board] = None
        self.player_two_board: Optional[Board] = None
        self.single_player_board: Optional[Board] = None

    def make_fleet(self) -> list[Ship]:
        return [Ship(ship.name, ship.length, ship.direction) for ship in self.FLEET]

    # ----- Main menu -----------------------------------------------------

    def run(self) -> None:
        menu_running = True

        while menu_running:
            self.display.tick()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    menu_running = False

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    x, y = event.pos

                    if 350 < x < 650:
                        if 400 < y < 450:
                            self.player_turn = None
                            self.start_game()
                        elif 500 < y < 550:
                            self.player_turn = 1
                            self.start_game()

            self.draw_menu()

        pygame.quit()

    def draw_menu(self) -> None:
        self.display.draw_background()
        self.display.draw_text("Battleship", 115, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4))
        self.display.draw_text("singleplayer", 30, (500, 420))
        self.display.draw_text("multiplayer", 30, (500, 520))
        pygame.display.flip()

    # ----- Ship placement -----------------------------------------------

    def place_fleet(self, board: Board, player_number: int) -> bool:
        """Run the drag-and-drop placement screen for one player."""
        self.display.set_placement_mode(True)
        ships = self.make_fleet()
        ship_index = 0
        dragging = False
        mouse_x, mouse_y = 800, 400
        running = True

        board.reset()

        while running and ship_index < len(ships):
            self.display.tick()

            for event in pygame.event.get():
                # The final successful placement can complete the fleet while
                # there are still events waiting in this event batch.
                if ship_index >= len(ships):
                    break

                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_x, mouse_y = event.pos
                    dragging = True

                    if 870 < mouse_x < 988 and 685 < mouse_y < 718:
                        ships[ship_index].switch_direction()

                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    dragging = False
                    mouse_x, mouse_y = event.pos

                    if 50 < mouse_x < 680 and 50 < mouse_y < 690:
                        cell = board.cell_from_pixel(mouse_x, mouse_y)
                        if cell is not None:
                            row, column = cell
                            ship = ships[ship_index]

                            if board.place_ship(
                                ship.name,
                                ship.length,
                                ship.direction,
                                row,
                                column,
                            ):
                                ship_index += 1

                    # Keep the original preview reset after every drop.
                    mouse_x, mouse_y = 800, 400

                    # Do not process another placement event or draw a preview
                    # after the last ship has been placed.
                    if ship_index >= len(ships):
                        break

                elif event.type == pygame.MOUSEMOTION and dragging:
                    mouse_x, mouse_y = event.pos

            if ship_index < len(ships):
                self.draw_placement_screen(
                    board,
                    ships[ship_index],
                    mouse_x,
                    mouse_y,
                    player_number,
                )

        self.display.set_placement_mode(False)
        return running

    def draw_placement_screen(
        self,
        board: Board,
        ship: Ship,
        mouse_x: int,
        mouse_y: int,
        player_number: int,
    ) -> None:
        screen = self.display.screen
        self.display.draw_background()

        board.draw(screen, placing=True)

        preview_x = mouse_x - 20
        preview_y = mouse_y - 20
        for segment in range(ship.length):
            pygame.draw.rect(
                screen,
                COLOR_SHIP,
                (preview_x, preview_y, CELL_SIZE, CELL_SIZE),
            )
            if ship.direction == HORIZONTAL:
                preview_x += CELL_SIZE + CELL_GAP
            else:
                preview_y += CELL_SIZE + CELL_GAP

        self.display.draw_text("SWITCH", 30, (930, 700))
        self.display.draw_text(
            f"Player {player_number}, it's your turn", 30, (930, 100)
        )
        self.display.draw_text("RULES", 30, (915, 150))
        self.display.draw_text(
            "1. Place the ship on the board.", 21, (895, 200)
        )
        self.display.draw_text(
            "2. Don't put it next to another ship", 21, (935, 250)
        )

        pygame.display.flip()

    # ----- Starting a game ----------------------------------------------

    def start_game(self) -> None:
        if self.player_turn is None:
            self.single_player_board = Board()
            self.single_player_board.place_random_fleet(self.make_fleet())
        else:
            self.player_one_board = Board()
            if not self.place_fleet(self.player_one_board, 1):
                return

            self.player_two_board = Board()
            if not self.place_fleet(self.player_two_board, 2):
                return

            self.player_turn = 1

        self.game_loop()

    # ----- Game loop and drawing ---------------------------------------

    def game_loop(self) -> None:
        running = True

        while running:
            self.display.tick()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break

                if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
                    continue

                x, y = event.pos

                # Stop button.
                if 855 < x < 940 and 80 < y < 120:
                    running = False
                    break

                if self.player_turn == 1:
                    assert self.player_two_board is not None
                    result = self.player_two_board.fire_at(x, y)

                    if result is not None:
                        if result:
                            self.player_turn = 2

                        if self.player_two_board.hit_count == self.WINNING_HITS:
                            assert self.player_one_board is not None
                            self.show_winner(
                                winner=1,
                                bombs=self.player_one_board.shot_count,
                                loser=2,
                                loser_hits=self.player_two_board.hit_count,
                            )
                            running = False

                        self.draw_game_screen()

                elif self.player_turn == 2:
                    assert self.player_one_board is not None
                    result = self.player_one_board.fire_at(x, y)

                    if result is not None:
                        if result:
                            self.player_turn = 1

                        if self.player_one_board.hit_count == self.WINNING_HITS:
                            assert self.player_two_board is not None
                            self.show_winner(
                                winner=2,
                                bombs=self.player_two_board.shot_count,
                                loser=1,
                                loser_hits=self.player_one_board.hit_count,
                            )
                            running = False

                        self.draw_game_screen()

                else:
                    assert self.single_player_board is not None
                    self.single_player_board.fire_at(x, y)

                    if self.single_player_board.hit_count == self.WINNING_HITS:
                        self.show_winner(winner=0, bombs=self.single_player_board.shot_count)
                        running = False

            self.draw_game_screen()

    def draw_game_screen(self) -> None:
        self.display.draw_background()

        if self.player_turn == 1:
            assert self.player_two_board is not None
            self.player_two_board.draw(self.display.screen)
            self.display.draw_text("Player 1, it is your turn", 30, (700, 750))

        elif self.player_turn == 2:
            assert self.player_one_board is not None
            self.player_one_board.draw(self.display.screen)
            self.display.draw_text("Player 2, it is your turn", 30, (700, 750))

        else:
            assert self.single_player_board is not None
            self.single_player_board.draw(self.display.screen)

        self.display.draw_text("Stop", 30, (900, 100))
        pygame.display.flip()

    # ----- Winner screen ------------------------------------------------

    def show_winner(
        self,
        winner: int,
        bombs: int,
        loser: Optional[int] = None,
        loser_hits: Optional[int] = None,
    ) -> None:
        running = True

        while running:
            self.display.tick()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    running = False

            self.display.draw_background()

            if winner != 0:
                self.display.draw_text(
                    f"Player {winner} has won!", 50, (500, 100)
                )
                self.display.draw_text(
                    f"Player {loser} has hit {loser_hits} ships",
                    25,
                    (500, 570),
                )
            else:
                self.display.draw_text("You won!", 50, (500, 100))

            self.display.draw_text(
                f"{bombs} bombs were thrown", 25, (500, 620)
            )
            self.display.draw_text(
                "Click anywhere on the screen to go back...", 20, (500, 770)
            )
            pygame.display.flip()


if __name__ == "__main__":
    BattleshipGame().run()
