"""Entry point.

Run from the folder that contains ``app/``::

    python -m app.main
    python -m app.main --ai my_package.my_module:MyAI
    python -m app.main --no-debug --seed 42

``python app/main.py`` works as well.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

if __package__ in (None, ""):  # started as ``python app/main.py``
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ai.ai_logic import load_ai
from app.game_logic.game import Game
from app.gui.ai_window import DebugChannel
from app.gui.player_window import PlayerWindow


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Battleship: you against an AI.")
    parser.add_argument(
        "--ai",
        metavar="MODULE:CLASS",
        help="external algorithm, e.g. my_package.my_module:MyAI (default: built-in probability AI)",
    )
    parser.add_argument("--no-debug", action="store_true", help="do not open the AI debug window")
    parser.add_argument("--seed", type=int, default=None, help="seed for reproducible games")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    ai = load_ai(args.ai, seed=args.seed)
    game = Game(ai, seed=args.seed)

    channel = None if args.no_debug else DebugChannel(ai.name)
    if channel is not None:
        channel.start()
    try:
        PlayerWindow(game, channel.send if channel else None).run()
    finally:
        if channel is not None:
            channel.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
