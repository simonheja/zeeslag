"""AI interface, debug data structures and the default AI.

Plugging in your own algorithm
------------------------------
Subclass :class:`BattleshipAI`, implement :meth:`BattleshipAI.choose_shot`
and start the game with::

    python -m app.main --ai my_package.my_module:MyAI

The AI never sees the player's ships, only an :class:`AIView` of the shots it
has fired so far. Optionally implement :meth:`BattleshipAI.get_debug_info` to
feed the debug window (confidence matrix, mode, notes, ...).
"""
from __future__ import annotations

import importlib
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Sequence, Union

from app.game_logic.open_functions import (
    CellState,
    Coordinate,
    Orientation,
    ShipSpec,
    ShotOutcome,
    in_bounds,
    ship_cells,
)

ShotGrid = tuple[tuple[CellState, ...], ...]


# ---------------------------------------------------------------------- #
# Data passed between the game, the AI and the debug window
# ---------------------------------------------------------------------- #
@dataclass(frozen=True)
class AIView:
    """Everything the AI is allowed to know when it has to choose a shot."""

    board_size: int
    shots: ShotGrid  # shots[row][column] -> CellState of the opponent's board
    remaining_ship_sizes: tuple[int, ...]  # sizes of the opponent's ships still afloat

    def state_at(self, coordinate: Coordinate) -> CellState:
        row, column = coordinate
        return self.shots[row][column]

    def cells_in_state(self, state: CellState) -> list[Coordinate]:
        return [
            (row, column)
            for row in range(self.board_size)
            for column in range(self.board_size)
            if self.shots[row][column] is state
        ]

    def unknown_cells(self) -> list[Coordinate]:
        return self.cells_in_state(CellState.UNKNOWN)


@dataclass
class AIDebugInfo:
    """Optional information an AI can expose for the debug window.

    Attributes:
        confidence: ``board_size x board_size`` matrix (``confidence[row][column]``).
            Any scale works, the window normalises it. Cells that were already
            shot at should be 0.
        mode: Short label of what the AI is doing, e.g. ``"HUNT"``.
        notes: Free text lines.
        stats: Free key/value pairs that are listed in the window.
    """

    confidence: list[list[float]]
    mode: str = ""
    notes: list[str] = field(default_factory=list)
    stats: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class DebugSnapshot:
    """One AI move, as sent to the debug window."""

    turn_number: int
    ai_name: str
    outcome: ShotOutcome  # the shot the AI fired and its result
    shots: ShotGrid  # knowledge of the AI *after* the shot
    remaining_ship_sizes: tuple[int, ...]  # after the shot
    think_time_ms: float
    info: AIDebugInfo | None  # the AI's reasoning *before* the shot
    illegal_move: bool = False  # True if the AI returned an invalid cell


# Messages understood by the debug window: a snapshot, ``"reset"`` or ``"quit"``.
DebugMessage = Union[DebugSnapshot, str]


# ---------------------------------------------------------------------- #
# Interface
# ---------------------------------------------------------------------- #
class BattleshipAI(ABC):
    """Interface every Battleship algorithm has to implement."""

    name: str = "Custom AI"

    def reset(self, board_size: int, fleet: Sequence[ShipSpec]) -> None:
        """Called once at the start of every game."""

    @abstractmethod
    def choose_shot(self, view: AIView) -> Coordinate:
        """Return the ``(row, column)`` to fire at. Must be an unknown cell."""

    def on_shot_result(self, outcome: ShotOutcome) -> None:
        """Called after each of the AI's shots with the result."""

    def get_debug_info(self) -> AIDebugInfo | None:
        """Called right after :meth:`choose_shot`; return None if not supported."""
        return None


# ---------------------------------------------------------------------- #
# Default AI: probability density
# ---------------------------------------------------------------------- #
class ProbabilityAI(BattleshipAI):
    """Counts how many ways the remaining ships could still fit through each cell.

    * HUNT mode (no unresolved hits): fire at the cell covered by the most
      possible ship placements.
    * TARGET mode (unresolved hits): only placements that cover at least one
      known hit are considered, so the AI finishes off a ship it found.
    """

    name = "Probability density AI"

    def __init__(self, seed: int | None = None) -> None:
        self._rng = random.Random(seed)
        self._last_debug: AIDebugInfo | None = None

    def reset(self, board_size: int, fleet: Sequence[ShipSpec]) -> None:
        self._last_debug = None

    def choose_shot(self, view: AIView) -> Coordinate:
        unresolved_hits = view.cells_in_state(CellState.HIT)
        require_hit = bool(unresolved_hits)
        mode = "TARGET" if require_hit else "HUNT"

        counts, placements = self._count_placements(view, require_hit)
        if require_hit and placements == 0:
            # The hits cannot be explained by the remaining ships; fall back.
            counts, placements = self._count_placements(view, require_hit=False)
            mode = "HUNT (fallback)"

        candidates = view.unknown_cells()
        best_score = max(counts[row][column] for row, column in candidates)
        best_cells = [cell for cell in candidates if counts[cell[0]][cell[1]] == best_score]
        choice = self._rng.choice(best_cells)

        confidence = [
            [value / best_score if best_score > 0 else 0.0 for value in row] for row in counts
        ]
        self._last_debug = AIDebugInfo(
            confidence=confidence,
            mode=mode,
            notes=[
                f"{len(best_cells)} cell(s) tie for the best score; picked {choice} at random."
                if len(best_cells) > 1
                else "A single best cell was found.",
            ],
            stats={
                "placements considered": str(placements),
                "unresolved hits": str(len(unresolved_hits)),
                "best raw score": f"{best_score:g}",
            },
        )
        return choice

    def get_debug_info(self) -> AIDebugInfo | None:
        return self._last_debug

    @staticmethod
    def _count_placements(view: AIView, require_hit: bool) -> tuple[list[list[float]], int]:
        """Return (score per cell, number of placements that were counted)."""
        size = view.board_size
        counts = [[0.0] * size for _ in range(size)]
        placements = 0
        for ship_size in view.remaining_ship_sizes:
            for orientation in Orientation:
                for row in range(size):
                    for column in range(size):
                        cells = ship_cells((row, column), ship_size, orientation)
                        if not all(in_bounds(cell, size) for cell in cells):
                            continue
                        states = [view.state_at(cell) for cell in cells]
                        if CellState.MISS in states or CellState.SUNK in states:
                            continue
                        covered_hits = states.count(CellState.HIT)
                        if require_hit and covered_hits == 0:
                            continue
                        weight = float(covered_hits) if require_hit else 1.0
                        placements += 1
                        for cell, state in zip(cells, states):
                            if state is CellState.UNKNOWN:
                                counts[cell[0]][cell[1]] += weight
        return counts, placements


# ---------------------------------------------------------------------- #
# Loading
# ---------------------------------------------------------------------- #
def load_ai(spec: str | None = None, seed: int | None = None) -> BattleshipAI:
    """Create an AI.

    Args:
        spec: ``None`` for the default AI, or ``"package.module:ClassName"``
            for an external algorithm (its constructor must take no arguments).
        seed: Seed for the default AI (reproducible games).
    """
    if spec is None:
        return ProbabilityAI(seed=seed)
    module_name, _, class_name = spec.partition(":")
    if not module_name or not class_name:
        raise ValueError("AI spec must look like 'package.module:ClassName'")
    module = importlib.import_module(module_name)
    ai = getattr(module, class_name)()
    if not isinstance(ai, BattleshipAI):
        raise TypeError(f"{spec} is not a BattleshipAI subclass")
    return ai
