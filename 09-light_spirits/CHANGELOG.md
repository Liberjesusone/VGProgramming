# Changelog

All notable changes to this project are documented here, newest first.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Milestone 3]

### Added

- Three enemy kinds (zombie, witch, golem), one data-driven `Enemy` class reading everything about a kind from `ENEMY_DEFS`, the same way `Player` reads `WEAPON_DEFS`.
- Enemy AI: stands guard until the player enters its aggro radius, then chases in a straight line, closes to its attack's engage range, charges, attacks, recovers, and chases again. No patrol, and aggro is never lost once triggered.
- Unpredictable enemy attacks: each charge picks a random release point from the attack's own range (the zombie can swing almost immediately or hold a full charge), and the aim locks in and the telegraph thickens shortly before release, the player's one cue that the attack is committed.
- Enemy attacks resolve as either a melee cone (zombie, golem) or a lobbed area attack that telegraphs a filling red circle on the ground before it lands (the witch's `AreaShot`).
- Player stun: a hit that carries one knocks the player back, shakes the sprite, and takes away control for a duration. Light and heavy tiers; a second hit landing while already stunned extends the stagger instead of cutting it short.
- Rolling through a hit (`Player.invulnerable`, added in Milestone 2 but unused until now) actually avoids it.
- A health bar under the stamina bar in the HUD.
- Charging, for the player or an enemy, now slows movement, more so at the heavier charge tier, so committing to a strong attack costs something.
- A brief red tint flashes on anything that takes damage.
- A landed or missed melee swing now also draws a solid version of its cone for the length of the swing, not just the translucent charge preview, so it stays readable for an instant after the fact. Used by the player's sword and every melee enemy.
- `tools/build_assets.py` rewritten around **tilesets**: every art category (floors, walls, fences, forest, rocks, cliffs, player, enemies, bosses, props, decor, bonfire, hud) is now one packed PNG in `assets/tilesets/` plus a JSON index of every region's exact rect, instead of one loose file per sprite. The same PNGs are what Tiled will paint the map with (see `TILED_GUIDE.md`).
- New art, packed and ready to place: royal/black/cracked marble and calm-grass floors; stone and marble walls; wood and iron fences; dense forest and rock-field edges; cliff edges and an abyss backdrop; a full animated bonfire (unlit/lit base, two flame loops, a kindling burst, drifting embers); decoration sheets (grass, marble ruins, rocks, bonfire seating); and Dark-Souls-style HUD pieces (flask, bow, sword, quiver, item slot, message banner).
- The final boss's art: a samurai (movement + slash) and, for a second phase, his spectral archer form (movement + bow + a short melee slash). Packed into the `bosses` tileset, not wired into gameplay yet.

### Fixed

- Sheet-splitting in `build_assets.py` glued rows together when smoke or other loose particles drifted between them; row/column detection now needs a minimum share of the sheet's busiest row, not just any stray pixel.
- Thin dark details (iron bars, a cliff's dark edge) were being erased along with the magenta background; they're recoloured to the grey they were drawn as instead of being cut away.
- The flame animation's source came back on black rather than magenta; its brightness is now read directly as alpha, keeping the glow's true colour instead of fading it toward black.
- The agro of the enemies was being taken only by the player aproximation, now it also takes it when the player hit them with bow from distance.

### Changed

- `assets/graphics/` is gone. Every texture now lives in `assets/tilesets/`, sliced once at startup into the same texture keys the rest of the game already used, so nothing outside `settings.py` had to change.
- `assets/source/` (the full-resolution originals) is excluded from the repository via `.gitignore`; only the packed tilesets are small enough, and are all the game or Tiled ever need, to ship.

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
