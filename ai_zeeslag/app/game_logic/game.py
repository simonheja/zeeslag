"""Game flow: placement, turns, win detection and the link to the AI."""
from __future__ import annotations

import random
import time
from dataclasses import dataclass
from enum import Enum
from typing import Sequence

from app.ai.ai_logic import AIView, BattleshipAI, DebugSnapshot
from app.game_logic.board import Board, InvalidShotError
from app.game_logic.open_functions import (
    BOARD_SIZE,
    FLEET,
    Coordinate,
    Orientation,
    ShipSpec,
    ShotOutcome,
    ShotResult,
)


class Phase(Enum):
    PLACEMENT = "placement"
    PLAYING = "playing"
    GAME_OVER = "game_over"


class Side(Enum):
    HUMAN = "human"
    AI = "ai"


@dataclass(frozen=True)
class TurnRecord:
    """One shot in the game history."""

    turn_number: int  # counted per shooter, starting at 1
    shooter: Side
    outcome: ShotOutcome


class Game:
    """A game of Battleship between a human and a :class:`BattleshipAI`."""

    def __init__(
        self,
        ai: BattleshipAI,
        board_size: int = BOARD_SIZE,
        fleet: Sequence[ShipSpec] = FLEET,
        allow_touching: bool = False,
        seed: int | None = None,
    ) -> None:
        self._ai = ai
        self._board_size = board_size
        self._fleet: tuple[ShipSpec, ...] = tuple(fleet)
        self._allow_touching = allow_touching
        self._rng = random.Random(seed)

        self.human_board: Board
        self.ai_board: Board
        self.phase: Phase
        self.current_turn: Side
        self.winner: Side | None
        self.history: list[TurnRecord]
        self.new_game()

    # ------------------------------------------------------------------ #
    # Setup
    # ------------------------------------------------------------------ #
    @property
    def ai_name(self) -> str:
        return self._ai.name

    @property
    def fleet(self) -> tuple[ShipSpec, ...]:
        return self._fleet

    def new_game(self) -> None:
        """Reset everything and go back to the placement phase."""
        self.human_board = Board(self._board_size, self._allow_touching)
        self.ai_board = Board(self._board_size, self._allow_touching)
        self.phase = Phase.PLACEMENT
        self.current_turn = Side.HUMAN
        self.winner = None
        self.history = []

    @property
    def next_ship_to_place(self) -> ShipSpec | None:
        """The next ship the human still has to place, or None when done."""
        placed = len(self.human_board.ships)
        return self._fleet[placed] if placed < len(self._fleet) else None

    def can_place_human_ship(self, origin: Coordinate, orientation: Orientation) -> bool:
        ship = self.next_ship_to_place
        return ship is not None and self.human_board.can_place(ship, origin, orientation)

    def place_human_ship(self, origin: Coordinate, orientation: Orientation) -> bool:
        """Place the next ship of the fleet. Returns False if the position is invalid."""
        if self.phase is not Phase.PLACEMENT or not self.can_place_human_ship(origin, orientation):
            return False
        ship = self.next_ship_to_place
        assert ship is not None
        self.human_board.place_ship(ship, origin, orientation)
        return True

    def clear_human_fleet(self) -> None:
        self.human_board.clear()

    def randomize_human_fleet(self) -> None:
        self.human_board.place_fleet_randomly(self._fleet, self._rng)

    def start_battle(self) -> None:
        """Place the AI's fleet at random and begin the game (human shoots first)."""
        if self.phase is not Phase.PLACEMENT or self.next_ship_to_place is not None:
            raise RuntimeError("Place the whole fleet before starting the battle")
        self.ai_board.place_fleet_randomly(self._fleet, self._rng)
        self._ai.reset(self._board_size, self._fleet)
        self.phase = Phase.PLAYING
        self.current_turn = Side.HUMAN

    # ------------------------------------------------------------------ #
    # Shooting
    # ------------------------------------------------------------------ #
    def human_fire(self, coordinate: Coordinate) -> ShotOutcome:
        """The human fires at the AI's board."""
        self._require(Side.HUMAN)
        if not self.ai_board.is_valid_target(coordinate):
            raise InvalidShotError(f"Invalid target {coordinate}")
        outcome = self.ai_board.receive_shot(coordinate)
        self._register_shot(Side.HUMAN, outcome, self.ai_board)
        return outcome

    def ai_fire(self) -> tuple[ShotOutcome, DebugSnapshot]:
        """Ask the AI for a shot, fire it at the human's board and report it."""
        self._require(Side.AI)
        view = self._build_ai_view()

        started = time.perf_counter()
        raw_choice = self._ai.choose_shot(view)
        think_time_ms = (time.perf_counter() - started) * 1000.0
        info = self._ai.get_debug_info()

        coordinate = self._sanitise(raw_choice)
        illegal = coordinate is None or not self.human_board.is_valid_target(coordinate)
        if illegal:  # a faulty external AI must not crash the game
            coordinate = self._rng.choice(self._unshot_cells(self.human_board))
        assert coordinate is not None

        outcome = self.human_board.receive_shot(coordinate)
        self._ai.on_shot_result(outcome)
        self._register_shot(Side.AI, outcome, self.human_board)

        snapshot = DebugSnapshot(
            turn_number=self.shots_fired(Side.AI),
            ai_name=self._ai.name,
            outcome=outcome,
            shots=self.human_board.shot_grid(),
            remaining_ship_sizes=tuple(s.size for s in self.human_board.remaining_ships()),
            think_time_ms=think_time_ms,
            info=info,
            illegal_move=illegal,
        )
        return outcome, snapshot

    # ------------------------------------------------------------------ #
    # Statistics
    # ------------------------------------------------------------------ #
    def shots_fired(self, side: Side) -> int:
        return sum(1 for record in self.history if record.shooter is side)

    def hits_landed(self, side: Side) -> int:
        return sum(
            1
            for record in self.history
            if record.shooter is side and record.outcome.result is not ShotResult.MISS
        )

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #
    def _require(self, side: Side) -> None:
        if self.phase is not Phase.PLAYING:
            raise RuntimeError("The game is not in the playing phase")
        if self.current_turn is not side:
            raise RuntimeError(f"It is not the turn of {side.value}")

    def _register_shot(self, shooter: Side, outcome: ShotOutcome, target: Board) -> None:
        self.history.append(TurnRecord(self.shots_fired(shooter) + 1, shooter, outcome))
        if target.all_sunk:
            self.phase = Phase.GAME_OVER
            self.winner = shooter
        else:
            self.current_turn = Side.AI if shooter is Side.HUMAN else Side.HUMAN

    def _build_ai_view(self) -> AIView:
        return AIView(
            board_size=self._board_size,
            shots=self.human_board.shot_grid(),
            remaining_ship_sizes=tuple(s.size for s in self.human_board.remaining_ships()),
        )

    @staticmethod
    def _sanitise(choice: object) -> Coordinate | None:
        try:
            row, column = choice  # type: ignore[misc]
            return int(row), int(column)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _unshot_cells(board: Board) -> list[Coordinate]:
        return [
            (row, column)
            for row in range(board.size)
            for column in range(board.size)
            if board.is_valid_target((row, column))
        ]
