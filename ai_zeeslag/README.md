# Base game edits
## AI interactebility
In order to make the AI comunicate with the game, we need a function that is called something like `fire(x:int,y:int)`, the function would need to return a bool for being a hit or not.

This function will be used by both the player and the AI behind the scenes.

## Gamemodes
The singleplayer methode will be changed to show 2 grids, `the grid of the player` and `the grid of shots made on the AI's grid`

The multiplayer mode will most likely be stripped from the game.

# Basic AI behavior
## AI imparements
The AI will have the same limitation as the player, all the AI will be able to see is, `it's own ships` and `the shots it took on the player`

## AI player learning
A way for the AI to gradualy learn where the player's ships will be placed is through a matrix, where every time the ai strikes a ship it will do `+1` in the square where it hit.

Eventualy building a map of **hotspots** of more common places where the player will put their ships.

## AI increased difficutlty
When it comes to the ai placing ships, the ai could also keep a matrix of where it most commonly placed it's own ships, and choose a place with the least times being used.
Making it dificult to predict where the ai will place it's ships.

for example:
- Player matrix:
```
[[0,0,1,2,1,0,0,1,1,1],
[0,0,0,1,0,0,0,0,0,0],
[0,0,0,2,1,1,1,0,0,0],
[0,0,0,1,0,0,1,0,0,0],
[0,0,1,1,1,0,2,1,0,0],
[0,0,0,0,1,0,1,0,0,0],
[0,0,0,0,1,0,1,0,0,0],
[0,0,0,0,1,0,0,0,0,0],
[0,0,1,1,2,1,0,0,0,0],
[0,0,0,0,1,0,0,0,1,1]]
```

Every round the AI gets a chance to discover more of the players behaviors.