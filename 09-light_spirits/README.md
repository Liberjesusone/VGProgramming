# Light Spirits

A top-down action RPG built with Pygame and the Gale engine. Inpired in Albion gameplay and Dark Souls-styled ruins and difficulty, an archer working through them, with the capability to use a sword and slide, building up to a two-phase boss.

Final project for ISPPV1 (Video Game Programming I), Universidad de Los Andes.

## Status

Early development. Current build has the state machine (start / play / game over), a generated map with collidable scenery and depth sorting, and a placeholder player that walks around it. See `CHANGELOG.md` for progress by milestone.

## Running it

From this folder:

```
python main.py
```

Requires `gale-engine` (see the repo root's `requirements.txt`). `numpy` is also needed, but only to run `tools/build_assets.py`, not to play the game.

## Controls

- `WASD` — move
- `Enter` — confirm (title screen, game over)
- `F1` — toggle debug view (collision boxes, depth-sort lines)

## Assets

Floor and prop art is AI-generated, then converted into game-ready tiles and sprites by `tools/build_assets.py` (raw sources in `assets/source/`, output in `assets/graphics/`). See that file's docstring for the conversion pipeline and why it works the way it does.
