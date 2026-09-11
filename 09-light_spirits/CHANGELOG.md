# Changelog

All notable changes to this project are documented here, newest first.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

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
