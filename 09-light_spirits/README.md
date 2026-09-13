# Light Spirits

A top-down action RPG built with Pygame and the Gale engine. Inpired in Albion gameplay and Dark Souls-styled ruins and difficulty, an archer working through them, with the capability to use a sword and slide, building up to a two-phase boss.

Final project for ISPPV1 (Video Game Programming I), Universidad de Los Andes.

## Status

Milestone 2. An archer with a bow and a sword, each with its own charged attack aimed at the mouse, a dodge roll with invulnerability frames, and a shared stamina bar gating both. Runs borderless fullscreen with the mouse confined to the window. See `CHANGELOG.md` for progress by milestone.

## Running it

From this folder:

```
python main.py
```

Requires `gale-engine` (see the repo root's `requirements.txt`). `numpy` is also needed, both to run `tools/build_assets.py` and to draw the title screen's vignette.

## Controls

- `WASD` — move
- Mouse — aim
- Left click (hold) — charge the equipped weapon's attack, release to fire/swing
- `Space` — dodge roll, toward whatever movement key is held, or toward the mouse if none is
- `Q` — switch weapon (bow / sword)
- `Enter` — confirm (title screen, game over)
- `F1` — toggle debug view (collision boxes, depth-sort lines)

## Assets

Floor, prop and character art is AI-generated, then converted into game-ready tiles and sprites by `tools/build_assets.py` (raw sources in `assets/source/`, output in `assets/graphics/`). See that file's docstring for the conversion pipeline and why it works the way it does.

## Screenshots

### Milestone 2

![Archer exploring the ruins](milestones_png/milestone2/archer_ingame.png)
![Sword swing, with the attack's cone and every collision box visible in the debug overlay](milestones_png/milestone2/weapons_debug.png)

### Milestone 1

![Depth-sorted props and floor, early build](milestones_png/milestone1.png)
