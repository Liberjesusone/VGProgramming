# Light Spirits

A top-down action RPG built with Pygame and the Gale engine. Inpired in Albion gameplay and Dark Souls-styled ruins and difficulty, an archer working through them, with the capability to use a sword and slide, building up to a two-phase boss.

Final project for ISPPV1 (Video Game Programming I), Universidad de Los Andes.

## Status

Milestone 3. An archer with a bow and a sword, each with its own charged attack aimed at the mouse, a dodge roll with invulnerability frames, and a shared stamina bar gating both. Three enemy kinds (zombie, witch, golem) guard the ruins, each with a single unpredictable charged attack and a stun that can chain if the player isn't careful. Runs borderless fullscreen with the mouse confined to the window. The final boss's art exists but is not wired into gameplay yet. See `CHANGELOG.md` for progress by milestone.

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

All art is AI-generated, then packed by `tools/build_assets.py` into one tileset per category in `assets/tilesets/` (a PNG plus a JSON index naming every region), which both the game and Tiled load. The full-resolution originals live in `assets/source/`, kept out of the repository for their size, so the script only runs on the machine that has them. See that file's docstring for the conversion pipeline and why it works the way it does.

## Map (Tiled)

The current map is still generated in code (`src/world/Level.py`), on a fixed seed. Milestone 4 replaces it with a map authored in Tiled, painted with the same tilesets `tools/build_assets.py` already produces. Layer names, object properties and export settings are all fixed there so a map built there loads the same way.

## Screenshots

### Milestone 3

![Golem attacking the player](milestones_png/milestone3/golem_attack.png)
![Zombie attacking the player](milestones_png/milestone3/zombie_attack.png)
![Witch attacking the player, while the others enemies chases him](milestones_png/milestone3/witch_archer_attack.png)

### Milestone 2

![Archer exploring the ruins](milestones_png/milestone2/archer_ingame.png)
![Sword swing, with the attack's cone and every collision box visible in the debug overlay](milestones_png/milestone2/weapons_debug.png)

### Milestone 1

![Depth-sorted props and floor, early build](milestones_png/milestone1.png)
