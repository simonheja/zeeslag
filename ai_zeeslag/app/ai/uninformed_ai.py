"""Uninformed search AIs: BFS, DFS and iterative-deepening DFS.

All three start at a random cell and shoot cells in the order a graph
search would discover them (4-neighbour grid). They never use probabilities.
With ``hit_aware=True`` the unknown neighbours of an unresolved hit are
shot first (hunt/target behaviour, still without any probability estimate).
"""
from __future__ import annotations

import random
from collections import deque
from typing import Sequence

from app.ai.ai_logic import AIDebugInfo, AIView, BattleshipAI
from app.game_logic.open_functions import (
    CellState,
    Coordinate,
    ShipSpec,
    coordinate_label,
    neighbours,
)


def _adjacent(cell: Coordinate, size: int) -> list[Coordinate]:
    return list(neighbours(cell, size, include_diagonals=False))


def bfs_order(root: Coordinate, size: int) -> list[Coordinate]:
    """Cells in breadth-first order (rings around the root)."""
    order: list[Coordinate] = []
    seen = {root}
    queue = deque([root])
    while queue:
        cell = queue.popleft()
        order.append(cell)
        for nxt in _adjacent(cell, size):
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return order


def dfs_order(root: Coordinate, size: int) -> list[Coordinate]:
    """Cells in depth-first order (long snake-like runs)."""
    order: list[Coordinate] = []
    visited: set[Coordinate] = set()
    stack = [root]
    while stack:
        cell = stack.pop()
        if cell in visited:
            continue
        visited.add(cell)
        order.append(cell)
        stack.extend(n for n in _adjacent(cell, size) if n not in visited)
    return order


def iddfs_order(root: Coordinate, size: int) -> list[Coordinate]:
    """Cells in the order iterative-deepening DFS first discovers them.

    Every iteration re-walks the tree from the root with a larger depth
    limit; only cells not seen in earlier iterations are new shots.
    """
    order: list[Coordinate] = []
    discovered: set[Coordinate] = set()
    total = size * size

    for limit in range(2 * size):
        best_depth: dict[Coordinate, int] = {}

        def visit(cell: Coordinate, depth: int) -> None:
            if best_depth.get(cell, depth + 1) <= depth:
                return  # already reached this cell at least as shallowly
            best_depth[cell] = depth
            if cell not in discovered:
                discovered.add(cell)
                order.append(cell)
            if depth < limit:
                for nxt in _adjacent(cell, size):
                    visit(nxt, depth + 1)

        visit(root, 0)
        if len(order) == total:
            break
    return order


_STRATEGIES = {"bfs": bfs_order, "dfs": dfs_order, "iddfs": iddfs_order}


class UninformedAI(BattleshipAI):
    """Random start cell + an uninformed search order over the grid."""

    name = "Uninformed search AI"

    def __init__(self, strategy: str = "bfs", hit_aware: bool = False, seed: int | None = None) -> None:
        if strategy not in _STRATEGIES:
            raise ValueError(f"strategy must be one of {sorted(_STRATEGIES)}")
        self._strategy = strategy
        self._hit_aware = hit_aware
        self._rng = random.Random(seed)
        self._root: Coordinate = (0, 0)
        self._order: list[Coordinate] = []
        self._rank: dict[Coordinate, int] = {}
        self._last_debug: AIDebugInfo | None = None
        self.name = f"{strategy.upper()} search AI" + (" (hit-aware)" if hit_aware else "")

    def reset(self, board_size: int, fleet: Sequence[ShipSpec]) -> None:
        self._root = (self._rng.randrange(board_size), self._rng.randrange(board_size))
        self._order = _STRATEGIES[self._strategy](self._root, board_size)
        self._rank = {cell: index for index, cell in enumerate(self._order)}
        self._last_debug = None

    def choose_shot(self, view: AIView) -> Coordinate:
        if not self._order:  # reset() was not called; be defensive
            self.reset(view.board_size, ())

        choice: Coordinate | None = None
        mode = self._strategy.upper()

        if self._hit_aware:
            for hit in view.cells_in_state(CellState.HIT):
                for nxt in _adjacent(hit, view.board_size):
                    if view.state_at(nxt) is CellState.UNKNOWN:
                        choice, mode = nxt, f"{mode} + TARGET"
                        break
                if choice is not None:
                    break

        if choice is None:
            choice = next(
                (cell for cell in self._order if view.state_at(cell) is CellState.UNKNOWN),
                None,
            )
        if choice is None:  # cannot happen on a connected grid, but never crash
            choice = self._rng.choice(view.unknown_cells())

        self._last_debug = self._build_debug(view, choice, mode)
        return choice

    def get_debug_info(self) -> AIDebugInfo | None:
        return self._last_debug

    def _build_debug(self, view: AIView, choice: Coordinate, mode: str) -> AIDebugInfo:
        total = len(self._order)
        confidence = [[0.0] * view.board_size for _ in range(view.board_size)]
        for cell, rank in self._rank.items():
            if view.state_at(cell) is CellState.UNKNOWN:
                confidence[cell[0]][cell[1]] = (total - rank) / total  # earlier = hotter
        return AIDebugInfo(
            confidence=confidence,
            mode=mode,
            notes=[
                f"Search starts at {coordinate_label(self._root)}.",
                f"Next shot: {coordinate_label(choice)} (search rank {self._rank.get(choice, -1) + 1}/{total}).",
            ],
            stats={"strategy": self._strategy, "hit aware": str(self._hit_aware)},
        )


# `load_ai` calls the constructor without arguments, so each strategy gets a
# thin subclass that can be selected with --ai app.ai.uninformed_ai:BFSAI
class BFSAI(UninformedAI):
    def __init__(self) -> None:
        super().__init__("bfs")


class DFSAI(UninformedAI):
    def __init__(self) -> None:
        super().__init__("dfs")


class IDDFSAI(UninformedAI):
    def __init__(self) -> None:
        super().__init__("iddfs")


class HitAwareBFSAI(UninformedAI):
    def __init__(self) -> None:
        super().__init__("bfs", hit_aware=True)

class HitAwareDFSAI(UninformedAI):
    def __init__(self) -> None:
        super().__init__("dfs", hit_aware=True)

class HitAwareIDDFSAI(UninformedAI):
    def __init__(self) -> None:
        super().__init__("iddfs", hit_aware=True)