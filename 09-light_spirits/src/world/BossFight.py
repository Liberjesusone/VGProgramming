"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains the class BossFight: the whole final encounter, from
the samurai waiting in his arena to the flame that ends the game. Each
form of the boss fights on its own (see SamuraiBoss, SpiritBoss); this is
only what happens around and between them, one phase after another:

dormant: the samurai waits, nothing on screen yet.
samurai: his name and health bar show while he fights.
felled: he falls, holds his pose kneeling in smoke under an ENEMY FELLED
    banner, the moment the fight looks won, and stays down as a corpse.
emerging: his spirit rises out of the body, its own name and a bar that
    fills as it rises.
spirit: the second fight, the samurai's corpse still lying there.
ending: the spirit breaks apart and the body fades with it. From here on
    the world stops: the player loses control and can no longer be hurt.
darkening: the screen fades to black over DARKEN_TIME seconds.
flame: a small flame kindles in the middle of the black screen.
finished: PlayState returns to the title screen.
"""

from typing import Any, Optional

import pygame

import settings
from src.entity.SamuraiBoss import SamuraiBoss
from src.entity.SpiritBoss import SpiritBoss

FELLED_TIME = 4.0
ENDING_TIME = 4.0
DARKEN_TIME = 10.0
FLAME_TIME = 4.5

# Phases in which the world is paused and the player has no control.
FROZEN_PHASES = ("ending", "darkening", "flame", "finished")

BANNER_TEXT = "ENEMY FELLED"
BANNER_WIDTH = 360
BANNER_FADE_IN = 0.6
BANNER_FADE_OUT = 0.8

""" The boss bar sits at the bottom of the screen above the player's own
two bars, the name just over its left end. The pale lag segment is the
health just lost: it waits LAG_DELAY seconds after the last hit, then
drains at LAG_SPEED health per second, so a heavy blow reads at a glance. """
BAR_WIDTH = 380
BAR_HEIGHT = 6
BAR_BOTTOM_OFFSET = 46
LAG_DELAY = 0.6
LAG_SPEED = 30.0
BAR_TRACK_COLOR = (24, 20, 20)
BAR_FILL_COLOR = (150, 34, 30)
BAR_LAG_COLOR = (214, 176, 96)
BAR_BORDER_COLOR = (110, 88, 58)

# The final flame: its kindling burst, then its steady loop, scaled up with no smoothing.
KINDLE_FRAMES = 8
FLAME_FRAMES = 8
KINDLE_TIME = 1.2
FLAME_FPS = 10
FLAME_SCALE = 0.8
FLAME_FADE = 0.8


class BossFight:
    def __init__(self, level: Any) -> None:
        self.level = level
        x, y = level.boss_spawn

        self.samurai = SamuraiBoss(x, y, level)
        level.entities.append(self.samurai)
        self.spirit: Optional[SpiritBoss] = None

        self.phase = "dormant"
        self.timer = 0.0

        self.lag_health = 0.0
        self.lag_hold = 0.0
        self._last_health: Optional[int] = None

    def _enter(self, phase: str) -> None:
        self.phase = phase
        self.timer = 0.0

    @property
    def world_frozen(self) -> bool:
        return self.phase in FROZEN_PHASES

    @property
    def finished(self) -> bool:
        return self.phase == "finished"

    @property
    def bar_boss(self) -> Optional[Any]:
        if self.phase == "samurai":
            return self.samurai
        if self.phase in ("emerging", "spirit"):
            return self.spirit
        return None

    # ------------------------------------------------------------
    # Update
    # ------------------------------------------------------------
    def update(self, dt: float, player: Any) -> None:
        """ Called while the world runs normally, after Level.update has
        already moved both forms of the boss for this frame. """
        self.timer += dt

        if self.phase == "dormant" and self.samurai.awake:
            self._enter("samurai")
        elif self.phase == "samurai" and self.samurai.health <= 0:
            self.samurai.change_state("felled")
            self.level.hazards.clear()
            self._enter("felled")
        elif self.phase == "felled" and self.timer >= FELLED_TIME:
            self.spirit = SpiritBoss(self.samurai.x, self.samurai.y, self.level)
            self.level.entities.append(self.spirit)
            self._enter("emerging")
        elif self.phase == "emerging" and self.spirit.emerged:
            self._enter("spirit")
        elif self.phase == "spirit" and self.spirit.health <= 0:
            self._begin_ending(player)

        self._update_lag(dt)

    def _begin_ending(self, player: Any) -> None:
        self.spirit.change_state("dissolve", "defeated", 1.0, "dissolve", 2.4)
        self.samurai.change_state("dissolve", "defeated", 0.4, "defeated", 3.0)
        self.level.hazards.clear()
        self.level.projectiles.clear()

        # Whatever the player was doing is dropped; the roll's own exit would
        # otherwise switch invulnerability back off after it is set below.
        player.change_state("idle")
        player.charge = 0.0
        player.attack_held = False
        player.attack_requested = False
        player.roll_requested = False

        for action in player.held:
            player.held[action] = False

        player.invulnerable = True
        self._enter("ending")

    def update_frozen(self, dt: float, player: Any) -> None:
        """ Called instead of the whole world's update once it stops: only
        the dissolving bosses keep moving, and the ending plays on. """
        self.timer += dt

        for boss in (self.samurai, self.spirit):
            if boss is not None and not boss.removed:
                boss.update(dt, player)

        if self.phase == "ending" and self.timer >= ENDING_TIME:
            self._enter("darkening")
        elif self.phase == "darkening" and self.timer >= DARKEN_TIME:
            self._enter("flame")
        elif self.phase == "flame" and self.timer >= FLAME_TIME:
            self._enter("finished")

    def _update_lag(self, dt: float) -> None:
        """ If the lag health bar is larger than the boss health and it has passed more
        than LAG_DELAY seconds, then the lag health starts decreasing at LAG_SPEED"""
        boss = self.bar_boss

        if boss is None:
            self._last_health = None
            return

        if self._last_health is not None and boss.health < self._last_health:
            self.lag_hold = LAG_DELAY

        if self._last_health is None or self.lag_health < boss.health:
            self.lag_health = boss.health
        else:
            self.lag_hold -= dt

            if self.lag_hold <= 0:
                self.lag_health = max(boss.health, self.lag_health - LAG_SPEED * dt)

        self._last_health = boss.health

    # ------------------------------------------------------------
    # Render
    # ------------------------------------------------------------
    def render_hud(self, surface: pygame.Surface) -> None:
        """ Renders the Boss Fight HUD, the increasing health if it's emerging,
        the real health and lag_health during a fight, or a felled banner if defeated"""
        boss = self.bar_boss

        if boss is not None:
            if self.phase == "emerging":
                fraction = min(1.0, self.timer / boss.definition["emerge_time"])
                lag = fraction
            else:
                fraction = boss.health / boss.max_health
                lag = self.lag_health / boss.max_health

            self._render_bar(surface, boss.name, fraction, lag)

        if self.phase == "felled":
            self._render_banner(surface)

    def _render_bar(self, surface: pygame.Surface, name: str, fraction: float, lag: float) -> None:
        """ Renders the Boss's name, health (param: fraction) and lag_health (param: lag) 
        :param lag: the percent [0; 1] of lag health that should print, could be the same
            as the real health or just the same as fraction if its emerging 
        :param fraction: the percent [0; 1] of real health   
        """
        left = (settings.VIRTUAL_WIDTH - BAR_WIDTH) // 2
        top = settings.VIRTUAL_HEIGHT - BAR_BOTTOM_OFFSET

        label = settings.FONTS["small"].render(name, True, settings.COLOR_TEXT)
        surface.blit(label, (left, top - label.get_height() - 2))

        track = pygame.Rect(left, top, BAR_WIDTH, BAR_HEIGHT)
        pygame.draw.rect(surface, BAR_TRACK_COLOR, track)

        lag_rect = pygame.Rect(left, top, round(BAR_WIDTH * max(0.0, min(1.0, lag))), BAR_HEIGHT)
        pygame.draw.rect(surface, BAR_LAG_COLOR, lag_rect)

        fill = pygame.Rect(left, top, round(BAR_WIDTH * max(0.0, min(1.0, fraction))), BAR_HEIGHT)
        pygame.draw.rect(surface, BAR_FILL_COLOR, fill)

        pygame.draw.rect(surface, BAR_BORDER_COLOR, track, 1)

    def _render_banner(self, surface: pygame.Surface) -> None:
        """ Renders the Felled banner when defeating a Boss
        it calcs. the alpha value using the fade_in/put times
        and scale hte banner tile horizontaly and vertically with BANNER_WIDTH"""
        fade_in = self.timer / BANNER_FADE_IN
        fade_out = (FELLED_TIME - self.timer) / BANNER_FADE_OUT
        alpha = int(255 * max(0.0, min(1.0, fade_in, fade_out)))

        if alpha <= 0:
            return

        art = settings.TILESETS["hud"]["bonfire_banner"]
        height = round(art.get_height() * BANNER_WIDTH / art.get_width())
        banner = pygame.transform.smoothscale(art, (BANNER_WIDTH, height))
        banner.set_alpha(alpha)

        centre = (settings.VIRTUAL_WIDTH // 2, round(settings.VIRTUAL_HEIGHT * 0.4))
        surface.blit(banner, banner.get_rect(center=centre))

        text = settings.FONTS["medium"].render(BANNER_TEXT, True, settings.COLOR_ACCENT)
        text.set_alpha(alpha)
        surface.blit(text, text.get_rect(center=centre))

    def render_overlay(self, surface: pygame.Surface) -> None:
        """ Drawn over everything else, the HUD included, so the whole
        screen goes dark at the end and not just the world. """
        if self.phase == "darkening":
            veil = pygame.Surface(surface.get_size())
            veil.fill((0, 0, 0))
            veil.set_alpha(int(255 * min(1.0, self.timer / DARKEN_TIME)))
            surface.blit(veil, (0, 0))
        elif self.phase in ("flame", "finished"):
            surface.fill((0, 0, 0))
            self._render_flame(surface)

    def _render_flame(self, surface: pygame.Surface) -> None:
        regions = settings.TILESETS["bonfire"]

        if self.timer < KINDLE_TIME:    # * 2 justo to iterate through more frames 
            index = min(KINDLE_FRAMES, int(self.timer * 2 / KINDLE_TIME * KINDLE_FRAMES) + 1)
            frame = regions[f"bonfire_kindle_{index}"]
        else:
            index = int((self.timer - KINDLE_TIME) * FLAME_FPS) % FLAME_FRAMES + 1
            frame = regions[f"bonfire_flame_a_{index}"]

        size = (frame.get_width() * FLAME_SCALE, frame.get_height() * FLAME_SCALE)
        flame = pygame.transform.scale(frame, size)
        flame.set_alpha(int(255 * max(0.0, min(1.0, (FLAME_TIME - self.timer) / FLAME_FADE))))

        # Bottom centred just under the middle of the screen, so a tall frame grows upward.
        bottom = (settings.VIRTUAL_WIDTH // 2, settings.VIRTUAL_HEIGHT // 2 + 24)
        surface.blit(flame, flame.get_rect(midbottom=bottom))
