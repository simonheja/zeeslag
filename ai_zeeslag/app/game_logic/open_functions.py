"""Shared constants, types and small helper functions for the game logic.

This module deliberately has no dependency on pygame, so the rules of the game
can be unit tested and reused by other front-ends (or by AI training scripts).

Conventions
-----------
* A ``Coordinate`` is always ``(row, column)``, both zero based.
* Rows are shown to the user as numbers (1-10), columns as letters (A-J).
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterator

BOARD_SIZE: int = 10

Coordinate = tuple[int, int]


class Orientation(Enum):
    """Direction in which a ship extends from its origin cell."""

    HORIZONTAL = "horizontal"  # extends to the right (increasing column)
    VERTICAL = "vertical"  # extends downwards (increasing row)

    def toggled(self) -> "Orientation":
        """Return the other orientation."""
        if self is Orientation.HORIZONTAL:
            return Orientation.VERTICAL
        return Orientation.HORIZONTAL


class CellState(Enum):
    """What the shooter knows about a cell of the opponent's board."""

    UNKNOWN = "unknown"  # not shot at yet
    MISS = "miss"  # shot at, water
    HIT = "hit"  # shot at, part of a ship that is still afloat
    SUNK = "sunk"  # part of a ship that has been sunk completely


class ShotResult(Enum):
    """Result of a single shot."""

    MISS = "miss"
    HIT = "hit"
    SUNK = "sunk"


@dataclass(frozen=True)
class ShipSpec:
    """Type of ship: name and length in cells."""

    name: str
    size: int


# Standard fleet (17 ship cells in total).
FLEET: tuple[ShipSpec, ...] = (
    ShipSpec("Battleship", 5),
    ShipSpec("Cruiser", 4),
    ShipSpec("Frigate", 3),
    ShipSpec("Frigate", 3),
    ShipSpec("Minesweeper", 2),
)


@dataclass(frozen=True)
class ShotOutcome:
    """Everything that is revealed to both sides by one shot."""

    coordinate: Coordinate
    result: ShotResult
    sunk_ship: ShipSpec | None = None  # only set when ``result`` is SUNK


def in_bounds(coordinate: Coordinate, board_size: int = BOARD_SIZE) -> bool:
    """Return True if ``coordinate`` lies on a board of ``board_size`` cells."""
    row, column = coordinate
    return 0 <= row < board_size and 0 <= column < board_size


def ship_cells(origin: Coordinate, length: int, orientation: Orientation) -> list[Coordinate]:
    """Return the cells a ship of ``length`` would occupy (may be out of bounds)."""
    row, column = origin
    if orientation is Orientation.HORIZONTAL:
        return [(row, column + offset) for offset in range(length)]
    return [(row + offset, column) for offset in range(length)]


def neighbours(
    coordinate: Coordinate,
    board_size: int = BOARD_SIZE,
    include_diagonals: bool = True,
) -> Iterator[Coordinate]:
    """Yield the in-bounds cells touching ``coordinate``."""
    row, column = coordinate
    for row_offset in (-1, 0, 1):
        for column_offset in (-1, 0, 1):
            if row_offset == 0 and column_offset == 0:
                continue
            if not include_diagonals and row_offset != 0 and column_offset != 0:
                continue
            candidate = (row + row_offset, column + column_offset)
            if in_bounds(candidate, board_size):
                yield candidate


def coordinate_label(coordinate: Coordinate) -> str:
    """Human readable label such as ``'B4'`` for ``(3, 1)``."""
    row, column = coordinate
    return f"{chr(ord('A') + column)}{row + 1}"
