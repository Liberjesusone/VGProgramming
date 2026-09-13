# Changelog

All notable changes to this project are documented here, newest first.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Milestone 2]

### Added

- Archer character art (hooded, faceless design), replacing the placeholder box the player used to be drawn as.
- A full weapon system: bow (ranged) and sword (melee cone), each with its own idle/walk/charge1/charge2/attack poses, an internal player state machine (idle/walk/attack/roll), and instant weapon switching (`Q`).
- Charged attacks: holding the attack button builds a charge that scales the bow's speed, damage and range, or the sword's cone width, reach and damage, aimed at the mouse rather than at the movement direction.
- Dodge roll (`Space`): a fixed-distance dash a the held movement direction, or toward the mouse if none is held, with its own 3-pose animation and a window of invulnerability. Cancels any charge already building.
- Stamina: a shared resource spent by attacks and rolls, regenerating over time, shown as a bar at the bottom of the HUD.
- The attack's range/cone is now drawn live while charging, not only in the debug overlay, so the hitbox is always visible while aiming.
- Borderless fullscreen window sized to the real desktop resolution, with the mouse confined to it so aiming can no longer slip past the window's edge.
- Title screen background art, with a vignette and a warm, weathered tint over it.
- `actions.py`: every input action id centralized in one place instead of repeated as string literals across the project.

### Fixed

- The charge1/charge2 pose threshold compared a duration in seconds against the 0..1 charge fraction directly, so it fired at a slightly different moment than the matching stamina cost tier. Both now convert the same way.
- A circular import between `Player` and its own states, resolved with a type-checking-only import.

### Changed

- Window size is read from the real desktop at startup instead of a constant hand-tuned for one machine, so the game fits whatever screen it runs on with no per-machine adjustment.

## [Milestone 1]

### Added

- Game skeleton: title screen, play state, game over screen on a `gale.state.StateStack`.
- Procedural floor: 5 stone/wood/earth materials blended across a 60x40 tile map.
- Depth-sorted props (pillar, dead tree, boulder, brazier, sarcophagus) the player can walk behind.
- Player movement (WASD), with wall sliding and a small feet-only collision box.
- `tools/build_assets.py`: converts raw AI-generated art into game-ready tilesets and sprites.
- Debug overlay (`F1`): collision boxes and depth-sort lines.

### Fixed

- Prop background removal left thin magenta fringes, and on the brazier whole patches of magenta enclosed by the sprite itself. Now removed with a two-threshold flood fill instead of a single color test.

### Changed

- `Prop.solid_rect` is now computed once at creation instead of rebuilt on every collision check.
