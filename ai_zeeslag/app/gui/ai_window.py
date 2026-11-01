"""Separate debug window that visualises what the AI is thinking.

The window runs in its own process (pygame can only drive one window per
process reliably). The game sends it :class:`DebugSnapshot` objects through a
multiprocessing queue, so the player window never blocks on debugging.

Keys: LEFT/RIGHT browse earlier AI moves, END jumps back to the latest move,
N toggles the numbers in the heat map.
"""
from __future__ import annotations

import multiprocessing
import os
import queue as std_queue
from multiprocessing.queues import Queue as MPQueue

import pygame

from app.ai.ai_logic import DebugMessage, DebugSnapshot
from app.game_logic.open_functions import CellState, Coordinate, ShotResult, coordinate_label
from app.gui.ui_helpers import (
    COLOR_ACCENT,
    COLOR_HIT,
    COLOR_MISS,
    COLOR_SUNK,
    COLOR_TEXT,
    COLOR_TEXT_DIM,
    DEBUG_WINDOW_SIZE,
    PLAYER_WINDOW_SIZE,
    WINDOW_MARGIN,
    BoardLayout,
    Color,
    body_font,
    draw_board_labels,
    draw_cross,
    draw_panel,
    draw_text,
    mono_font,
    title_font,
    wrap_text,
)

FPS: int = 30
HEATMAP_LAYOUT = BoardLayout(origin=(60, 130), cell_size=42, gap=2)
PANEL_X: int = 530
PANEL_WIDTH: int = 270

# Colour stops of the heat map: (value, colour).
HEAT_STOPS: list[tuple[float, Color]] = [
    (0.0, (22, 32, 66)),
    (0.35, (36, 104, 150)),
    (0.7, (236, 196, 64)),
    (1.0, (250, 84, 44)),
]


def heat_color(value: float) -> Color:
    """Map a 0..1 confidence to a colour."""
    value = max(0.0, min(1.0, value))
    for (low, low_color), (high, high_color) in zip(HEAT_STOPS, HEAT_STOPS[1:]):
        if value <= high:
            t = (value - low) / (high - low)
            return (
                int(low_color[0] + (high_color[0] - low_color[0]) * t),
                int(low_color[1] + (high_color[1] - low_color[1]) * t),
                int(low_color[2] + (high_color[2] - low_color[2]) * t),
            )
    return HEAT_STOPS[-1][1]


class DebugWindow:
    """Shows the AI's confidence matrix and reasoning for each of its moves."""

    def __init__(self, messages: "MPQueue[DebugMessage]", ai_name: str) -> None:
        self._messages = messages
        self._ai_name = ai_name
        self._snapshots: list[DebugSnapshot] = []
        self._selected: int | None = None  # None = follow the latest move
        self._show_numbers = True
        self._running = False
        self._screen: pygame.Surface
        self._cursor_y = 0

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
            self.poll_messages()
            self.draw()
            pygame.display.flip()
            clock.tick(FPS)
        pygame.quit()

    def setup(self) -> None:
        pygame.display.init()
        self._place_next_to_player_window()
        pygame.init()
        self._screen = pygame.display.set_mode(DEBUG_WINDOW_SIZE)
        pygame.display.set_caption(f"AI debug - {self._ai_name}")

    @staticmethod
    def _place_next_to_player_window() -> None:
        """Put this window right of the player window if the screen is wide enough."""
        x = WINDOW_MARGIN + PLAYER_WINDOW_SIZE[0] + WINDOW_MARGIN
        try:
            desktop_width = pygame.display.get_desktop_sizes()[0][0]
        except (pygame.error, IndexError, AttributeError):
            return
        if desktop_width >= x + DEBUG_WINDOW_SIZE[0] + WINDOW_MARGIN:
            os.environ["SDL_VIDEO_WINDOW_POS"] = f"{x},40"

    # ------------------------------------------------------------------ #
    # Input
    # ------------------------------------------------------------------ #
    def poll_messages(self) -> None:
        while True:
            try:
                message = self._messages.get_nowait()
            except std_queue.Empty:
                return
            except (EOFError, OSError):
                self._running = False
                return
            if isinstance(message, DebugSnapshot):
                self._snapshots.append(message)
            elif message == "reset":
                self._snapshots.clear()
                self._selected = None
            elif message == "quit":
                self._running = False

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self._running = False
        elif event.type == pygame.KEYDOWN:
            last = len(self._snapshots) - 1
            current = last if self._selected is None else self._selected
            if event.key == pygame.K_LEFT and last >= 0:
                self._selected = max(0, current - 1)
            elif event.key == pygame.K_RIGHT and last >= 0:
                self._selected = None if current + 1 >= last else current + 1
            elif event.key == pygame.K_END:
                self._selected = None
            elif event.key == pygame.K_n:
                self._show_numbers = not self._show_numbers
            elif event.key == pygame.K_ESCAPE:
                self._running = False

    @property
    def _current(self) -> DebugSnapshot | None:
        if not self._snapshots:
            return None
        return self._snapshots[-1] if self._selected is None else self._snapshots[self._selected]

    # ------------------------------------------------------------------ #
    # Drawing
    # ------------------------------------------------------------------ #
    def draw(self) -> None:
        screen = self._screen
        screen.fill((14, 20, 32))
        snapshot = self._current

        draw_text(screen, "AI debug", title_font(36), COLOR_ACCENT, (60, 40), "midleft")
        draw_text(screen, self._ai_name, body_font(20), COLOR_TEXT_DIM, (60, 76), "midleft")
        draw_text(screen, "Confidence matrix", title_font(20), COLOR_TEXT, (60, 96), "midleft")

        draw_board_labels(screen, HEATMAP_LAYOUT, body_font(15))
        self._draw_heatmap(snapshot)
        self._draw_legend()
        draw_text(
            screen,
            "LEFT/RIGHT: browse moves   END: latest   N: numbers on/off",
            body_font(15),
            COLOR_TEXT_DIM,
            (60, 735),
            "midleft",
        )
        self._draw_side_panel(snapshot)

    def _draw_heatmap(self, snapshot: DebugSnapshot | None) -> None:
        screen = self._screen
        layout = HEATMAP_LAYOUT
        confidence = snapshot.info.confidence if snapshot and snapshot.info else None
        peak = max((max(row) for row in confidence), default=0.0) if confidence else 0.0
        number_font = mono_font(13)

        for row in range(layout.size):
            for column in range(layout.size):
                rect = layout.cell_rect((row, column))
                state = snapshot.shots[row][column] if snapshot else CellState.UNKNOWN
                if state is CellState.UNKNOWN:
                    value = confidence[row][column] / peak if confidence and peak > 0 else 0.0
                    pygame.draw.rect(screen, heat_color(value), rect, border_radius=4)
                    if self._show_numbers and confidence and value > 0:
                        text_color = (10, 14, 24) if value > 0.55 else COLOR_TEXT
                        draw_text(screen, str(round(value * 100)), number_font, text_color, rect.center)
                elif state is CellState.MISS:
                    pygame.draw.rect(screen, (46, 54, 70), rect, border_radius=4)
                    pygame.draw.circle(screen, COLOR_MISS, rect.center, 4)
                else:
                    pygame.draw.rect(screen, COLOR_SUNK if state is CellState.SUNK else COLOR_HIT, rect, border_radius=4)
                    draw_cross(screen, rect, COLOR_TEXT, 2)

        if snapshot is not None:  # outline the cell the AI fired at
            pygame.draw.rect(screen, (255, 255, 255), layout.cell_rect(snapshot.outcome.coordinate).inflate(4, 4), 3, border_radius=5)

    def _draw_legend(self) -> None:
        screen = self._screen
        layout = HEATMAP_LAYOUT
        bar = pygame.Rect(layout.origin[0], layout.origin[1] + layout.pixel_size + 24, layout.pixel_size, 14)
        for x in range(bar.width):
            pygame.draw.line(screen, heat_color(x / (bar.width - 1)), (bar.left + x, bar.top), (bar.left + x, bar.bottom))
        draw_text(screen, "0", body_font(14), COLOR_TEXT_DIM, (bar.left, bar.bottom + 12), "midleft")
        draw_text(screen, "relative confidence (100 = best cell)", body_font(14), COLOR_TEXT_DIM, (bar.centerx, bar.bottom + 12))
        draw_text(screen, "100", body_font(14), COLOR_TEXT_DIM, (bar.right, bar.bottom + 12), "midright")

        keys = [("hit", COLOR_HIT), ("sunk", COLOR_SUNK), ("miss", (46, 54, 70))]
        x = bar.left
        for label, color in keys:
            pygame.draw.rect(screen, color, pygame.Rect(x, bar.bottom + 36, 14, 14), border_radius=3)
            draw_text(screen, label, body_font(14), COLOR_TEXT_DIM, (x + 20, bar.bottom + 43), "midleft")
            x += 80
        pygame.draw.rect(screen, (255, 255, 255), pygame.Rect(x, bar.bottom + 36, 14, 14), 2, border_radius=3)
        draw_text(screen, "last shot", body_font(14), COLOR_TEXT_DIM, (x + 20, bar.bottom + 43), "midleft")

    # ---- side panel --------------------------------------------------- #
    def _write(self, text: str, color: Color = COLOR_TEXT, size: int = 17, indent: int = 0) -> None:
        """Write one line (wrapped) in the side panel and advance the cursor."""
        font = body_font(size)
        for line in wrap_text(text, font, PANEL_WIDTH - 20 - indent):
            if self._cursor_y > DEBUG_WINDOW_SIZE[1] - 30:
                return
            draw_text(self._screen, line, font, color, (PANEL_X + 14 + indent, self._cursor_y), "midleft")
            self._cursor_y += size + 5

    def _heading(self, text: str) -> None:
        self._cursor_y += 8
        self._write(text, COLOR_ACCENT, 18)

    def _draw_side_panel(self, snapshot: DebugSnapshot | None) -> None:
        panel = pygame.Rect(PANEL_X, 100, PANEL_WIDTH, DEBUG_WINDOW_SIZE[1] - 120)
        draw_panel(self._screen, panel, 230)
        self._cursor_y = panel.top + 20

        if snapshot is None:
            self._write("Waiting for the AI's first move...", COLOR_TEXT_DIM)
            return

        position = self._snapshots.index(snapshot) + 1
        browsing = "" if self._selected is None else "  (browsing)"
        self._write(f"Move {snapshot.turn_number}  -  {position}/{len(self._snapshots)}{browsing}", COLOR_TEXT, 18)

        outcome = snapshot.outcome
        result_color = COLOR_MISS if outcome.result is ShotResult.MISS else COLOR_HIT
        self._write(f"Shot: {coordinate_label(outcome.coordinate)} -> {outcome.result.value.upper()}", result_color, 18)
        if outcome.sunk_ship is not None:
            self._write(f"Sunk the {outcome.sunk_ship.name} ({outcome.sunk_ship.size})", COLOR_HIT)
        if snapshot.illegal_move:
            self._write("AI returned an ILLEGAL cell; a random cell was used.", COLOR_HIT)
        self._write(f"Think time: {snapshot.think_time_ms:.2f} ms", COLOR_TEXT_DIM)
        self._write(f"Ships left to find: {list(snapshot.remaining_ship_sizes)}", COLOR_TEXT_DIM)

        info = snapshot.info
        if info is None:
            self._heading("No debug info")
            self._write("This AI does not implement get_debug_info().", COLOR_TEXT_DIM)
            return

        self._heading("Mode")
        self._write(info.mode or "-", COLOR_TEXT)
        if info.stats:
            self._heading("Stats")
            for key, value in info.stats.items():
                self._write(f"{key}: {value}", COLOR_TEXT_DIM)
        if info.notes:
            self._heading("Notes")
            for note in info.notes:
                self._write(note, COLOR_TEXT_DIM)

        self._heading("Top candidates (before the shot)")
        for rank, (coordinate, share) in enumerate(self._top_candidates(snapshot), start=1):
            self._write(f"{rank}. {coordinate_label(coordinate)}   {share:.0%}", COLOR_TEXT_DIM)

        self._heading("Recent moves")
        upto = self._snapshots.index(snapshot) + 1
        for past in reversed(self._snapshots[max(0, upto - 6):upto]):
            self._write(
                f"#{past.turn_number}  {coordinate_label(past.outcome.coordinate)}  {past.outcome.result.value}",
                COLOR_TEXT_DIM,
            )

    @staticmethod
    def _top_candidates(snapshot: DebugSnapshot, count: int = 4) -> list[tuple[Coordinate, float]]:
        """Best cells according to the confidence matrix, as a share of its maximum."""
        info = snapshot.info
        if info is None:
            return []
        peak = max((max(row) for row in info.confidence), default=0.0)
        if peak <= 0:
            return []
        cells = [
            ((row, column), value / peak)
            for row, values in enumerate(info.confidence)
            for column, value in enumerate(values)
            if value > 0
        ]
        cells.sort(key=lambda item: item[1], reverse=True)
        return cells[:count]


def run_ai_window(messages: "MPQueue[DebugMessage]", ai_name: str = "AI") -> None:
    """Entry point of the debug process."""
    DebugWindow(messages, ai_name).run()


class DebugChannel:
    """Starts the debug window in a separate process and feeds it messages."""

    def __init__(self, ai_name: str) -> None:
        context = multiprocessing.get_context("spawn")
        self._queue: MPQueue[DebugMessage] = context.Queue()
        self._process = context.Process(target=run_ai_window, args=(self._queue, ai_name), daemon=True)

    def start(self) -> None:
        self._process.start()

    def send(self, message: DebugMessage) -> None:
        """Forward a message; silently ignored once the window has been closed."""
        if self._process.is_alive():
            self._queue.put(message)

    def close(self) -> None:
        """Ask the window to quit and make sure the process is gone."""
        if self._process.is_alive():
            self._queue.put("quit")
            self._process.join(timeout=1.5)
            if self._process.is_alive():
                self._process.terminate()
        self._queue.close()
        self._queue.cancel_join_thread()
