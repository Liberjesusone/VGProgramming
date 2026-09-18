# Changelog

All notable changes to this project are documented here, newest first.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Milestone 6]

### Added

- Music, Dark Souls style: the title screen has its own soundtrack, exploring the ruins is silent, and the boss fight's soundtrack starts the moment the samurai wakes. It cuts out when he falls, the Light Spirit rises to its own track, and the fight music comes back the instant that track ends, with no gap. The ending plays its own track in full, and the title music returns once it is over.
- Sound effects for every hit and action: sword swings (player, zombie, both boss forms), the golem's slam, the samurai's thrust warning, the spirit's arrow volley (one sound for the whole rain, not one per arrow), the witch's arrow landing, arrows striking a body, the player being hit, rolling, drinking an estus flask, and "you died" on the game over screen.
- Any number of effects play at once: two zombies and the player swinging together are three swings. The mixer now has 32 channels instead of pygame's default 8, where a new effect is silently dropped once every channel is busy.
- `src/audio.py` grows from a single `play` into the whole audio interface: `play` for effects, and `play_music`, `queue_music` and `stop_music` for the single music stream. A missing file, or a machine with no audio device, plays nothing instead of raising.
- Estus flasks: 4 per run, `R` drinks one and restores 40% of the maximum health. Only while standing or walking, the same as a roll, and never at full health, where it would only waste the flask.
- A Dark Souls quick item cross in the bottom left corner of the HUD: the bow above, the sword to the left, the quiver to the right and the estus below. The weapon not in hand is drawn faded, and the estus shows how many flasks are left, switching to an empty flask with no number once they run out.

### Changed

- Audio is split into two folders: `assets/sounds` holds short effects, loaded into memory up front so they play instantly; `assets/music` holds long tracks, streamed from disk one at a time so a five minute soundtrack never sits decoded in memory.
- The two `.m4a` tracks, a format pygame cannot read, and the 58 MB title soundtrack were converted to `.ogg` (the title track is now 5.8 MB). The originals are archived in `assets/source/sounds`, kept out of the repository like every other source asset.
- Each enemy attack and boss strike names its own sound in `ENEMY_DEFS`/`bosses.py` (`sound`, and `land_sound` for the witch's lobbed shot), the same data-driven way every other part of an attack is tuned.

### Removed

- `samurai_thrust_cue.wav`, a placeholder borrowed from an earlier project; the thrust now warns with its own `samurai_thrust` sound.

## [Milestone 5]

### Added

- The ruins are now a hand-built Tiled map (`assets/maps/ruins_v2.tmj`) instead of the procedural generator, loaded by `Level.try_load_tilemap`. Every tile layer is drawn as painted; only the `walls` layer blocks, and only on tiles marked `collision = solid` in Tiled's own tileset editor.
- `src/world/tiled.py`: reads a Tiled JSON export directly, without gale's own `load_tiled_map`, for two reasons that loader doesn't handle: it opens tileset images through the path Tiled wrote into the map, which only exists on the machine that saved it, and it drops a tile object's `gid`, the one field that says what a placed object actually is. Here a tileset is matched to one of ours by its image's file name, and a tile object keeps the sprite it was placed with.
- Every placed object becomes what its own tileset says it is, regardless of which object layer it was dropped on: a `prop` sprite becomes a solid `Prop`, `decor`/`bonfire` become non-blocking `Decor`, `enemies` spawns the right kind of `Enemy`, `bosses` sets where the samurai waits, and `player` sets where the run starts. A tile's exact region is resolved from our own tileset JSON index, not from any name typed into Tiled, so nothing needs to be labelled by hand to be recognised.
- Only the tilesets actually painted into a tile layer have their image loaded and registered; a tileset only ever referenced by objects (`props`, `enemies`, `bosses`, `decor`, `bonfire`) never gets pulled into the renderer at all.
- `src/world/Decor.py`: scenery drawn and depth-sorted exactly like a `Prop`, anchored on its feet, but never solid.
- 7 more props (torii gate, stone lantern, dead black pine, katana grave, tattered war banner, fallen shrine bell, armor remains) now have collision footprints, alongside the original five.
- A prop's solid footprint can now be more than one box (`solid_parts` in `PROP_DEFS`), so the torii gate blocks only its two pillars and stays walkable through the middle, and the war banner blocks only its pole.
- The procedural generator (`Level._generate`) is kept as a fallback: if `ruins_v2.tmj` is missing, the level builds exactly as it did before, seed and all.

### Fixed

- `F2` (teleport to the boss arena) now lands on the nearest free spot instead of wherever the fixed offset happened to be, which could be inside a wall on the hand-built map.
- We had to adapt our own logic of load_tilemap to get the behaviour that we are expecting when we put a tile that represents a memory object in a Object-Layer, because then we no longer need to fill a Tiled project with empty boxes that has some specific gid, that could lead into typing mistakes.

## [Milestone 4]

### Added

- The final boss: Samurai Gurenmaru, and the Light Spirit that rises from his body once he falls. Two `Boss` subclasses (`SamuraiBoss`, `SpiritBoss`) sharing one base class and a family of states in `src/states/entity/boss/`, the same data-driven shape as `Enemy`/`ENEMY_DEFS`, now in `src/definitions/bosses.py`.
- Samurai Gurenmaru: always closes the distance. A normal slash with a chance to immediately chain a second, faster one; a surprise dash that closes in fast and ends in a slash; and a thrust, a thin, long, near-straight cone telegraphed by a sound cue and a camera shake the instant it locks in, which heavily stuns on a hit and, landed or not, is always followed by a dash back in and three fast combo hits.
- Every melee swing, on either form, is one shared "strike" definition (wind-up poses, charge/lock timing, cone, damage, stun, a forward lunge, an optional warning cue and impact shake) resolved by a single `BossStrikeState`.
- The Light Spirit: rises out of the samurai's corpse with a tween (fades in while lifting clear of the body) once he falls. Fights as an archer that tries to hold a fixed distance band, strafing unpredictably from side to side; fires single fast, heavy arrows; periodically casts a rain of arrows that lands staggered around the player; and, if the player closes in, swings its bow for a weak hit that launches them back, then either backdashes away if there is room behind it, or flees along whatever direction is actually clear if it is cornered.
- A fading afterimage trail while either form dashes, and a translucent, flickering look for the spirit (the art itself is fully opaque; the ghostly look is entirely a render-time effect, since generated art has no real transparency to rely on).
- A named boss health bar, replacing the player's own HUD bar while a boss fight is on screen, with a pale "damage lag" segment that holds briefly after a hit before draining down to the new value, and an "ENEMY FELLED" banner when the samurai falls.
- The ending: once the spirit falls, both forms dissolve together, the player loses control and becomes invulnerable, the screen fades to black over several seconds, and a small flame kindles and burns out in the middle of the screen before the game returns to the title.
- `src/audio.py` and `assets/sounds/`: a minimal sound system (`audio.play(name)`) backing the thrust's warning cue. A missing sound plays nothing instead of erroring.
- `F2`: teleports the player to the boss arena, for testing the fight without crossing the map every time.

### Changed

- `Level.entities` can now hold a `Boss` alongside regular `Enemy` instances. Anything that iterates it (the player's melee swing, arrows) now checks a shared `hittable` property instead of assuming everything in the list can always be hit, since a fallen boss's body stays on screen as a corpse long after it stops being one.

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
