# Examples for AI integration

This folder contains a small, self-contained example showing how to connect the game logic in `start_base/Zeeslag-NickRaw/pygame_battleship.py` to the ideas discussed in `ai_zeeslag/README.md`.

The key idea is:

- keep a board state for the opponent
- expose a simple `fire(x, y)` function
- track a confidence matrix (hotspots)
- choose the next shot by preferring cells with the highest confidence among cells that have not yet been fired at

See `ai_integration_example.py` for a compact demo.
