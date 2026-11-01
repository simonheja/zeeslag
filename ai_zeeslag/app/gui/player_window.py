"""The window in which the human plays against the AI."""
from __future__ import annotations

import os
from typing import Callable

import pygame

from app.ai.ai_logic import DebugMessage
from app.game_logic.board import Board
from app.game_logic.game import Game, Phase, Side
from app.game_logic.open_functions import (
    CellState,
    Coordinate,
    Orientation,
    ShotOutcome,
    ShotResult,
    coordinate_label,
    in_bounds,
    ship_cells,
)
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
    PLAYER_WINDOW_SIZE,
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

FPS: int = 60
AI_MOVE_DELAY_MS: int = 700

BIG_LAYOUT = BoardLayout(origin=(50, 130), cell_size=48, gap=2)  # 500 px: main board
SMALL_LAYOUT = BoardLayout(origin=(620, 170), cell_size=28, gap=2)  # 300 px: own fleet
PANEL_RECT = pygame.Rect(580, 100, 420, 560)

DebugSender = Callable[[DebugMessage], None]


def describe_outcome(outcome: ShotOutcome, shooter: Side) -> str:
    """Short sentence about a shot, from the human's point of view."""
    if outcome.result is ShotResult.MISS:
        return "miss"
    if outcome.result is ShotResult.HIT:
        return "hit!"
    name = outcome.sunk_ship.name if outcome.sunk_ship else "ship"
    return f"you sunk the enemy {name}!" if shooter is Side.HUMAN else f"the AI sunk your {name}!"


class PlayerWindow:
    """Placement screen, battle screen and result screen in one pygame window.

    Args:
        game: The game to play.
        send_debug: Optional callback that receives every AI move (for the
            separate AI debug window).
    """

    def __init__(self, game: Game, send_debug: DebugSender | None = None) -> None:
        self._game = game
        self._send_debug = send_debug or (lambda message: None)
        self._screen: pygame.Surface
        self._background: pygame.Surface | None = None
        self._running = False

        self._orientation = Orientation.HORIZONTAL
        self._dragging = False
        self._ai_move_at = 0
        self._human_message = ""
        self._ai_message = ""

        self._buttons: dict[str, Button] = {
            "rotate": Button(pygame.Rect(600, 470, 190, 44), "Rotate (R)"),
            "random": Button(pygame.Rect(810, 470, 190, 44), "Random"),
            "reset": Button(pygame.Rect(600, 522, 190, 44), "Reset"),
            "start": Button(pygame.Rect(600, 584, 400, 56), "Start battle"),
            "new_game": Button(pygame.Rect(600, 600, 190, 44), "New game"),
        }

    # ------------------------------------------------------------------ #
    # Main loop
    # ------------------------------------------------------------------ #
    def run(self) -> None:
        self.setup()
        clock = pygame.time.Clock()
        self._running = True
        while self._running:
            for event in pygame.event.get():
                self.handle_event(event)
            self.update()
            self.draw()
            pygame.display.flip()
            clock.tick(FPS)
        pygame.quit()

    def setup(self) -> None:
        """Create the pygame window."""
        os.environ.setdefault("SDL_VIDEO_WINDOW_POS", f"{WINDOW_MARGIN},40")
        pygame.init()
        self._screen = pygame.display.set_mode(PLAYER_WINDOW_SIZE)
        pygame.display.set_caption("Battleship - you vs the AI")
        self._background = load_background(PLAYER_WINDOW_SIZE)

    # ------------------------------------------------------------------ #
    # Events
    # ------------------------------------------------------------------ #
    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self._running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._running = False
        elif self._game.phase is Phase.PLACEMENT:
            self._handle_placement_event(event)
        else:
            self._handle_battle_event(event)

    def _handle_placement_event(self, event: pygame.event.Event) -> None:
        game = self._game
        if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            self._orientation = self._orientation.toggled()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            self._orientation = self._orientation.toggled()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._refresh_buttons()
            if self._buttons["rotate"].contains(event.pos):
                self._orientation = self._orientation.toggled()
            elif self._buttons["random"].contains(event.pos):
                game.randomize_human_fleet()
            elif self._buttons["reset"].contains(event.pos):
                game.clear_human_fleet()
            elif self._buttons["start"].contains(event.pos):
                self._begin_battle()
            elif game.next_ship_to_place is not None:
                self._dragging = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self._dragging:
            self._dragging = False
            target = BIG_LAYOUT.coordinate_at(event.pos)
            if target is not None:
                game.place_human_ship(target, self._orientation)

    def _handle_battle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return
        if self._buttons["new_game"].contains(event.pos):
            self._start_new_game()
            return
        game = self._game
        if game.phase is Phase.PLAYING and game.current_turn is Side.HUMAN:
            target = BIG_LAYOUT.coordinate_at(event.pos)
            if target is not None and game.ai_board.is_valid_target(target):
                self._fire_at(target)

    # ------------------------------------------------------------------ #
    # Game actions
    # ------------------------------------------------------------------ #
    def _begin_battle(self) -> None:
        self._game.start_battle()
        self._human_message = "Battle started - fire at the enemy waters!"
        self._ai_message = ""
        self._send_debug("reset")

    def _start_new_game(self) -> None:
        self._game.new_game()
        self._dragging = False
        self._human_message = self._ai_message = ""
        self._send_debug("reset")

    def _fire_at(self, target: Coordinate) -> None:
        outcome = self._game.human_fire(target)
        self._human_message = f"You fired at {coordinate_label(target)}: {describe_outcome(outcome, Side.HUMAN)}"
        self._ai_message = ""
        if self._game.phase is Phase.PLAYING:
            self._ai_move_at = pygame.time.get_ticks() + AI_MOVE_DELAY_MS

    def update(self) -> None:
        """Let the AI move once its (cosmetic) thinking delay has passed."""
        game = self._game
        if game.phase is Phase.PLAYING and game.current_turn is Side.AI:
            if pygame.time.get_ticks() >= self._ai_move_at:
                outcome, snapshot = game.ai_fire()
                label = coordinate_label(outcome.coordinate)
                self._ai_message = f"AI fired at {label}: {describe_outcome(outcome, Side.AI)}"
                self._send_debug(snapshot)

    # ------------------------------------------------------------------ #
    # Drawing
    # ------------------------------------------------------------------ #
    def draw(self) -> None:
        if self._background is not None:
            self._screen.blit(self._background, (0, 0))
        else:
            self._screen.fill((12, 24, 40))
        self._refresh_buttons()
        mouse = pygame.mouse.get_pos()

        if self._game.phase is Phase.PLACEMENT:
            self._draw_placement(mouse)
        else:
            self._draw_battle(mouse)

    def _refresh_buttons(self) -> None:
        game = self._game
        placing = game.phase is Phase.PLACEMENT
        self._buttons["reset"].enabled = bool(game.human_board.ships)
        self._buttons["start"].enabled = placing and game.next_ship_to_place is None
        self._buttons["new_game"].label = "Play again" if game.phase is Phase.GAME_OVER else "New game"

    # ---- placement ---------------------------------------------------- #
    def _draw_placement(self, mouse: tuple[int, int]) -> None:
        screen = self._screen
        game = self._game
        draw_text(screen, "Place your fleet", title_font(40), COLOR_ACCENT, (300, 50))
        draw_text(screen, "Your waters", title_font(24), COLOR_TEXT, (300, 100))

        draw_board_labels(screen, BIG_LAYOUT, body_font(16))
        self._draw_board(BIG_LAYOUT, game.human_board, show_ships=True)
        if self._dragging:
            self._draw_drag_preview(mouse)

        draw_panel(screen, PANEL_RECT)
        draw_text(screen, "Your fleet", title_font(26), COLOR_TEXT, (PANEL_RECT.centerx, 125))
        placed = len(game.human_board.ships)
        for index, spec in enumerate(game.fleet):
            y = 175 + index * 36
            for step in range(spec.size):
                square = pygame.Rect(600 + step * 24, y - 10, 20, 20)
                color = COLOR_SHIP if index < placed else COLOR_WATER_HOVER
                pygame.draw.rect(screen, color, square, border_radius=3)
            label_color = COLOR_TEXT_DIM if index < placed else COLOR_TEXT
            suffix = "  placed" if index < placed else ("  <- next" if index == placed else "")
            draw_text(screen, spec.name + suffix, body_font(20), label_color, (735, y), "midleft")

        instructions = [
            "Press on the board and drag to position the next ship,",
            "release to drop it. Right-click or press R to rotate.",
            "Ships may not touch each other (not even diagonally).",
        ]
        for index, line in enumerate(instructions):
            draw_text(screen, line, body_font(17), COLOR_TEXT_DIM, (600, 372 + index * 22), "midleft")
        orientation_text = f"Orientation: {self._orientation.value}"
        draw_text(screen, orientation_text, body_font(18), COLOR_ACCENT, (600, 446), "midleft")

        for name in ("rotate", "random", "reset", "start"):
            self._buttons[name].draw(screen, mouse)

    def _draw_drag_preview(self, mouse: tuple[int, int]) -> None:
        spec = self._game.next_ship_to_place
        if spec is None:
            return
        target = BIG_LAYOUT.coordinate_at(mouse)
        if target is not None:
            valid = self._game.can_place_human_ship(target, self._orientation)
            color = COLOR_VALID if valid else COLOR_INVALID
            for cell in ship_cells(target, spec.size, self._orientation):
                if in_bounds(cell):
                    pygame.draw.rect(self._screen, color, BIG_LAYOUT.cell_rect(cell), border_radius=4)
        else:  # free floating ship that follows the cursor
            rect = pygame.Rect(0, 0, BIG_LAYOUT.cell_size, BIG_LAYOUT.cell_size)
            for step in range(spec.size):
                if self._orientation is Orientation.HORIZONTAL:
                    rect.topleft = (mouse[0] - 20 + step * BIG_LAYOUT.pitch, mouse[1] - 20)
                else:
                    rect.topleft = (mouse[0] - 20, mouse[1] - 20 + step * BIG_LAYOUT.pitch)
                pygame.draw.rect(self._screen, COLOR_SHIP, rect, border_radius=4)

    # ---- battle ------------------------------------------------------- #
    def _draw_battle(self, mouse: tuple[int, int]) -> None:
        screen = self._screen
        game = self._game
        playing = game.phase is Phase.PLAYING

        if game.phase is Phase.GAME_OVER:
            won = game.winner is Side.HUMAN
            header = "You won!" if won else "The AI won"
            header_color = COLOR_ACCENT if won else COLOR_HIT
        elif game.current_turn is Side.HUMAN:
            header, header_color = "Your turn - fire at the enemy waters", COLOR_TEXT
        else:
            header, header_color = "The AI is thinking...", COLOR_TEXT_DIM
        draw_text(screen, header, title_font(34), header_color, (300, 40))
        draw_text(screen, "Enemy waters", title_font(22), COLOR_TEXT, (300, 90))

        hover: Coordinate | None = None
        if playing and game.current_turn is Side.HUMAN:
            candidate = BIG_LAYOUT.coordinate_at(mouse)
            if candidate is not None and game.ai_board.is_valid_target(candidate):
                hover = candidate
        draw_board_labels(screen, BIG_LAYOUT, body_font(16))
        # Enemy ships are only revealed once the game is over.
        self._draw_board(BIG_LAYOUT, game.ai_board, show_ships=not playing, hover=hover)

        draw_text(screen, self._human_message, body_font(20), COLOR_TEXT, (50, 655), "midleft")
        draw_text(screen, self._ai_message, body_font(20), COLOR_TEXT_DIM, (50, 682), "midleft")

        draw_panel(screen, PANEL_RECT)
        draw_text(screen, "Your fleet", title_font(22), COLOR_TEXT, (PANEL_RECT.centerx, 130))
        draw_board_labels(screen, SMALL_LAYOUT, body_font(12))
        self._draw_board(SMALL_LAYOUT, game.human_board, show_ships=True)

        enemy_left = [spec.size for spec in game.ai_board.remaining_ships()]
        own_left = [spec.size for spec in game.human_board.remaining_ships()]
        stats = [
            f"Your shots: {game.shots_fired(Side.HUMAN)}  (hits: {game.hits_landed(Side.HUMAN)})",
            f"AI shots: {game.shots_fired(Side.AI)}  (hits: {game.hits_landed(Side.AI)})",
            f"Enemy ships afloat: {len(enemy_left)}  {enemy_left}",
            f"Your ships afloat: {len(own_left)}  {own_left}",
        ]
        for index, line in enumerate(stats):
            draw_text(screen, line, body_font(19), COLOR_TEXT, (600, 505 + index * 24), "midleft")
        self._buttons["new_game"].draw(screen, mouse)

    # ---- board -------------------------------------------------------- #
    def _draw_board(
        self,
        layout: BoardLayout,
        board: Board,
        show_ships: bool,
        hover: Coordinate | None = None,
    ) -> None:
        for row in range(layout.size):
            for column in range(layout.size):
                coordinate = (row, column)
                rect = layout.cell_rect(coordinate)
                state = board.shot_state(coordinate)

                color = COLOR_WATER
                if show_ships and board.ship_at(coordinate) is not None:
                    color = COLOR_SHIP
                if hover == coordinate:
                    color = COLOR_WATER_HOVER
                if state is CellState.HIT:
                    color = COLOR_HIT
                elif state is CellState.SUNK:
                    color = COLOR_SUNK
                pygame.draw.rect(self._screen, color, rect, border_radius=4)

                if state is CellState.MISS:
                    pygame.draw.circle(self._screen, COLOR_MISS, rect.center, max(3, layout.cell_size // 8))
                elif state in (CellState.HIT, CellState.SUNK):
                    draw_cross(self._screen, rect, COLOR_TEXT, 3 if layout.cell_size > 30 else 2)
