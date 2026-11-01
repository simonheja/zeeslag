"""A single player's board: ship placement and incoming shots."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Sequence

from app.game_logic.open_functions import (
    BOARD_SIZE,
    CellState,
    Coordinate,
    Orientation,
    ShipSpec,
    ShotOutcome,
    ShotResult,
    in_bounds,
    neighbours,
    ship_cells,
)


class PlacementError(ValueError):
    """Raised when a ship cannot be placed at the requested position."""


class InvalidShotError(ValueError):
    """Raised when a shot is out of bounds or was already fired."""


@dataclass
class PlacedShip:
    """A ship that has been put on a board."""

    spec: ShipSpec
    cells: tuple[Coordinate, ...]
    hits: set[Coordinate] = field(default_factory=set)

    @property
    def is_sunk(self) -> bool:
        return len(self.hits) == len(self.cells)


class Board:
    """Holds the ships of one player and records the shots fired at them.

    Args:
        size: Number of rows and columns.
        allow_touching: If False, ships may not touch each other, not even
            diagonally.
    """

    def __init__(self, size: int = BOARD_SIZE, allow_touching: bool = False) -> None:
        self.size: int = size
        self.allow_touching: bool = allow_touching
        self._ships: list[PlacedShip] = []
        self._ship_at: dict[Coordinate, PlacedShip] = {}
        self._shots: dict[Coordinate, CellState] = {}

    # ------------------------------------------------------------------ #
    # Placement
    # ------------------------------------------------------------------ #
    @property
    def ships(self) -> tuple[PlacedShip, ...]:
        return tuple(self._ships)

    def clear(self) -> None:
        """Remove all ships and shots."""
        self._ships.clear()
        self._ship_at.clear()
        self._shots.clear()

    def can_place(self, spec: ShipSpec, origin: Coordinate, orientation: Orientation) -> bool:
        """Return True if ``spec`` fits at ``origin`` without breaking the rules."""
        for cell in ship_cells(origin, spec.size, orientation):
            if not in_bounds(cell, self.size) or cell in self._ship_at:
                return False
            if not self.allow_touching:
                if any(other in self._ship_at for other in neighbours(cell, self.size)):
                    return False
        return True

    def place_ship(self, spec: ShipSpec, origin: Coordinate, orientation: Orientation) -> PlacedShip:
        """Place a ship, raising ``PlacementError`` if that is not allowed."""
        if not self.can_place(spec, origin, orientation):
            raise PlacementError(f"Cannot place {spec.name} at {origin} ({orientation.value})")
        ship = PlacedShip(spec, tuple(ship_cells(origin, spec.size, orientation)))
        self._ships.append(ship)
        for cell in ship.cells:
            self._ship_at[cell] = ship
        return ship

    def place_fleet_randomly(self, fleet: Sequence[ShipSpec], rng: random.Random | None = None) -> None:
        """Clear the board and place the whole ``fleet`` at random positions."""
        rng = rng or random.Random()
        for _ in range(200):
            self.clear()
            if all(self._place_randomly(spec, rng) for spec in fleet):
                return
        raise PlacementError("Could not place the fleet; is the board too small?")

    def _place_randomly(self, spec: ShipSpec, rng: random.Random) -> bool:
        options = [
            ((row, column), orientation)
            for orientation in Orientation
            for row in range(self.size)
            for column in range(self.size)
            if self.can_place(spec, (row, column), orientation)
        ]
        if not options:
            return False
        origin, orientation = rng.choice(options)
        self.place_ship(spec, origin, orientation)
        return True

    # ------------------------------------------------------------------ #
    # Shooting
    # ------------------------------------------------------------------ #
    def is_valid_target(self, coordinate: Coordinate) -> bool:
        """True if the cell is on the board and has not been shot at yet."""
        return in_bounds(coordinate, self.size) and coordinate not in self._shots

    def receive_shot(self, coordinate: Coordinate) -> ShotOutcome:
        """Fire at ``coordinate`` and return what happened."""
        if not self.is_valid_target(coordinate):
            raise InvalidShotError(f"Invalid target {coordinate}")
        ship = self._ship_at.get(coordinate)
        if ship is None:
            self._shots[coordinate] = CellState.MISS
            return ShotOutcome(coordinate, ShotResult.MISS)

        ship.hits.add(coordinate)
        if ship.is_sunk:
            for cell in ship.cells:
                self._shots[cell] = CellState.SUNK
            return ShotOutcome(coordinate, ShotResult.SUNK, ship.spec)
        self._shots[coordinate] = CellState.HIT
        return ShotOutcome(coordinate, ShotResult.HIT)

    # ------------------------------------------------------------------ #
    # Queries
    # ------------------------------------------------------------------ #
    def shot_state(self, coordinate: Coordinate) -> CellState:
        return self._shots.get(coordinate, CellState.UNKNOWN)

    def ship_at(self, coordinate: Coordinate) -> PlacedShip | None:
        return self._ship_at.get(coordinate)

    def shot_grid(self) -> tuple[tuple[CellState, ...], ...]:
        """Immutable ``rows x columns`` snapshot of everything known about this board."""
        return tuple(
            tuple(self.shot_state((row, column)) for column in range(self.size))
            for row in range(self.size)
        )

    def remaining_ships(self) -> list[ShipSpec]:
        """Specs of the ships that are still afloat."""
        return [ship.spec for ship in self._ships if not ship.is_sunk]

    @property
    def all_sunk(self) -> bool:
        return bool(self._ships) and all(ship.is_sunk for ship in self._ships)
