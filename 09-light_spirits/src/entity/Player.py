"""
Light Spirits

Author: Liber Jesus Puccini
liberjesusone@gmail.com

This file contains the class Player.

Movement, idling and the charged attack each live in their own state, in
src/states/entity/player, hung off state_machine below. 
Player itself only holds the data every one of those states
reads or writes (position, direction, how the current weapon is
charging, which sprite is currently showing) and the always-on behaviour
none of them need to differ on: rendering, reading the mouse, and
switching weapons.

Player carries two weapons, bow and sword (src/definitions/weapons.py),
and which one is equipped decides everything about what a charge and an
attack actually do, a ranged shot versus a melee cone, without the
states themselves ever branching on it. self.pose ("idle", "step",
"charge1", "charge2" or "attack") is the other half of that: it names
which of the equipped weapon's own texture keys is currently showing,
and is all the states ever have to set to change what is on screen.
"""

from typing import Any, Dict, Optional

import pygame

from gale.state import StateMachine

import settings
from actions import ATTACK, HEAL, MOVE_DOWN, MOVE_LEFT, MOVE_RIGHT, MOVE_UP, ROLL, SWITCH_WEAPON
from src import audio
from src.combat.visuals import flashed
from src.definitions.combat import HIT_FLASH_TIME
from src.definitions.weapons import WEAPON_DEFS, WEAPON_ORDER
from src.states.entity import player as player_states

""" How much of the player blocks. Not the whole body: in a top-down view
 only the feet are really on the ground, so a narrow box down there is
 what bumps into things. It is also what lets the head overlap a prop
 standing behind them without being stopped by it. """
FEET_WIDTH = 20
FEET_DEPTH = 12

SHADOW_COLOR = (0, 0, 0, 90)

# Energy to spend on actions
MAX_STAMINA = 4
MIN_STAMINA = 0.6  # To do an action see on_input()

""" The recovery bar at the bottom of the HUD: fixed size and position on
the virtual surface, centered horizontally, a fixed margin above the
bottom edge. Medium-dark pastel green, as asked -- a darker track
underneath it so an empty bar still reads as "there" rather than
invisible. """
HUD_BAR_WIDTH = 120
HUD_BAR_HEIGHT = 6
HUD_BAR_BOTTOM_MARGIN = 14

HUD_BAR_TRACK_COLOR = (32, 36, 32)
HUD_BAR_BORDER_COLOR = (70, 92, 74)
HUD_BAR_FILL_COLOR = (94, 148, 104)

MAX_HEALTH = 50

# The health bar sits right under the stamina bar, same size and track.
HUD_BAR_GAP = 3
HUD_HEALTH_BORDER_COLOR = (98, 50, 48)
HUD_HEALTH_FILL_COLOR = (168, 62, 58)

# Estus flasks: how many a run starts with, and how much of the maximum health each one restores.
ESTUS_CHARGES = 4
ESTUS_HEAL_FRACTION = 0.4

""" The quick items, a cross of four slots in the bottom left corner the
way Dark Souls lays them out: the bow above, the sword to the left, the
quiver to the right and the estus below. The weapon not in hand is drawn
faded, so the cross also shows which one is equipped. Each entry is the
slot's offset from the centre of the cross, in slots. """
QUICK_ITEM_SLOTS = {
    "bow": (0, -1),
    "sword": (-1, 0),
    "quiver": (1, 0),
    "estus": (0, 1),
}
QUICK_ITEM_MARGIN = 8
QUICK_ITEM_GAP = 2
QUICK_ITEM_FADED_ALPHA = 90

""" The roll's own texture keys, read directly instead of through
weapon_def like every other pose: a roll is not part of either weapon's
own set (see settings.CHARACTER_POSE_SETS), so there is nothing to look
up an equipped weapon for. """
ROLL_TEXTURES = {
    "roll1": "player-roll1-{direction}",
    "roll2": "player-roll2-{direction}",
    "roll3": "player-roll3-{direction}",
}


class Player:
    def __init__(self, x: float, y: float, level: Any) -> None:
        # The feet, same anchor every prop uses, so both can be sorted
        # against each other with no conversion.
        self.x: float = x
        self.y: float = y

        # Held on to so states can test movement/attacks against it without
        # every one of them needing it threaded through their own constructor.
        self.level = level

        self.health: int = MAX_HEALTH

        self.equipped_weapon: str = "bow"

        """ Which of the 4 sprites is showing. Assigned by movement while
        walking (see PlayerWalkState) and by aim while charging or
        attacking (see _aim_bucket), there is no diagonal art, so
        this is always the nearest of the 4 compass directions to
        whichever of those is currently in charge of it. """
        self.direction: str = "down"

        """ Which of the equipped weapon's own texture keys is showing,
        see the module docstring. Every state that changes what the
        player looks like does it by setting this, never by touching
        settings.TEXTURES directly. """
        self.pose: str = "idle"

        """ Where an attack actually points: a continuous world-space unit
        vector toward the mouse, updated every frame in update() below,
        independent of the coarse, 4-way sprite direction above. """
        self.aim_direction: pygame.Vector2 = pygame.Vector2(0, 1)

        self.held: Dict[str, bool] = {
            MOVE_LEFT: False,
            MOVE_RIGHT: False,
            MOVE_UP: False,
            MOVE_DOWN: False,
        }

        """ Edge-triggered intent, the same shape as sword_requested in
        Princess: set once by on_input, consumed (and cleared) by
        whichever state's update() is running when it happens. """
        self.attack_held: bool = False
        self.attack_requested: bool = False

        # This energy is wasted in AttackState/RollState depending on the action
        self.current_stamina: float = MAX_STAMINA

        """ Same edge-triggered shape as attack_requested, consumed by
        PlayerBaseState._update_roll, only Idle and Walk call that,
        so a roll is never available mid-swing or mid-roll. """
        self.roll_requested: bool = False

        # True for a duration of PlayerRollState, read by damage() below, the one place 
        # anything that hits the player (an Enemy, for now) actually goes through.
        self.invulnerable: bool = False

        """ 0..1, how much of the equipped weapon's own charge_time has
        been held so far. Meaningful for either weapon, a bow draws
        further back, a sword winds up higher, which is exactly why
        it lives here rather than being named after one of them. """
        self.charge: float = 0.0

        # Pure render offset, see PlayerWalkState, never touched by
        # anything that cares about the player's actual position.
        self.bob_offset: float = 0.0

        # Same kind of render only offset, horizontal, see PlayerStunState.
        self.stagger_offset: float = 0.0

        # Seconds left of the tint shown right after taking damage.
        self.hit_flash: float = 0.0

        self.estus: int = ESTUS_CHARGES

        # The weapon icons as drawn when that weapon is not in hand, faded once here.
        self._faded_weapon_icons: Dict[str, pygame.Surface] = {}

        for weapon in WEAPON_ORDER:
            icon = settings.TILESETS["hud"][f"hud_{weapon}"].copy()
            icon.set_alpha(QUICK_ITEM_FADED_ALPHA)
            self._faded_weapon_icons[weapon] = icon

        """ Sized off the feet's own footprint, not off the sprite's
        silhouette: a weapon held out to one side makes the *picture*
        wider in some directions than others, but the character is not
        actually standing any wider, so the shadow would wobble between
        directions (and between weapons) if it followed the sprite instead. """
        shadow_width = FEET_WIDTH + 10
        self._shadow = pygame.Surface((shadow_width, FEET_DEPTH), pygame.SRCALPHA)
        pygame.draw.ellipse(self._shadow, SHADOW_COLOR, self._shadow.get_rect())

        self.state_machine = StateMachine(
            {
                "idle": lambda sm, p=self: player_states.PlayerIdleState(p, sm),
                "walk": lambda sm, p=self: player_states.PlayerWalkState(p, sm),
                "attack": lambda sm, p=self: player_states.PlayerAttackState(p, sm),
                "roll": lambda sm, p=self: player_states.PlayerRollState(p, sm),
                "stun": lambda sm, p=self: player_states.PlayerStunState(p, sm),
            }
        )
        self.change_state("idle")

    def change_state(self, name: str, *args: Any, **kwargs: Any) -> None:
        self.state_machine.change(name, *args, **kwargs)

    # ------------------------------------------------------------
    # Properties and Geometry
    # ------------------------------------------------------------
    @property
    def dead(self) -> bool:
        return self.health <= 0

    def damage(self, amount: int, stun: Optional[str] = None, source: Any = None) -> None:
        """ The one way anything hurts the player. Ignored entirely while
        rolling, so no attacker ever has to check invulnerable itself.

        stun is "light", "heavy" or None, see combat.STUNS, and source is
        the world point the hit came from, which the stagger pushes the
        player away from. """
        if self.invulnerable:
            return

        audio.play("player_receive_dmg")
        self.health = max(0, self.health - amount)
        self.hit_flash = HIT_FLASH_TIME

        if stun is not None and not self.dead:
            current = self.state_machine.current
            carried = current.remaining if isinstance(current, player_states.PlayerStunState) else 0.0
            self.change_state("stun", stun, source if source is not None else self.center, carried)

    @property
    def sort_y(self) -> float:
        """ Where this player sits in the front-to-back order. The feet, so a
        player standing lower on the screen is drawn in front of props above it."""
        return self.y

    @property
    def weapon_def(self) -> Dict[str, Any]:
        return WEAPON_DEFS[self.equipped_weapon]

    @property
    def sprite(self) -> pygame.Surface:
        if self.pose in ROLL_TEXTURES:
            key = ROLL_TEXTURES[self.pose].format(direction=self.direction)
        else:
            key = self.weapon_def[f"{self.pose}_texture"].format(direction=self.direction)

        return settings.TEXTURES[key]

    @property
    def width(self) -> int:
        """ The current sprite's own width, not a fixed constant: 'down'
        (a weapon held out to the side) reads wider than 'up' (mostly
        hidden behind the body), and forcing one width for both would
        either crop one or pad the other with empty space. """
        return self.sprite.get_width()

    @property
    def height(self) -> int:
        """ Every pose was scaled to the same settings.PLAYER_HEIGHT at
        build time (see tools/build_assets.py), so this one never
        actually varies the way width does. """
        return settings.PLAYER_HEIGHT

    @property
    def center(self) -> pygame.Vector2:
        """ The middle of the body: what the camera follows, and the
        point every attack/aim distance is measured from. Using the feet
        for either would sit the view, and a weapon's reach, half a body
        too low. """
        return pygame.Vector2(self.x, self.y - self.height / 2)

    def feet_rect_at(self, x: float, y: float) -> pygame.Rect:
        return pygame.Rect(
            round(x - FEET_WIDTH / 2), round(y - FEET_DEPTH), FEET_WIDTH, FEET_DEPTH
        )

    @property
    def feet_rect(self) -> pygame.Rect:
        return self.feet_rect_at(self.x, self.y)

    @property
    def image_rect(self) -> pygame.Rect:
        return pygame.Rect(
            round(self.x - self.width / 2),
            round(self.y - self.height),
            self.width,
            self.height,
        )

    def _move_axis(self, dx: float, dy: float) -> None:
        """ Move the collision rect and checks if the level allows it.
        Called once per axis, so a diagonal move that clips a wall on
        only one of the two axes still slides along it. """
        target_x = self.x + dx
        target_y = self.y + dy

        if self.level.blocked(self.feet_rect_at(target_x, target_y)):
            return

        self.x, self.y = target_x, target_y

    def _bucket_direction(self, vector: pygame.Vector2) -> str:
        """ Any vector's nearest compass direction, for picking which of
        the 4 discrete sprites to show, movement/aim/roll are all
        continuous, the art is not. """
        if abs(vector.x) > abs(vector.y):
            return "right" if vector.x > 0 else "left"

        return "down" if vector.y > 0 else "up"

    def _aim_bucket(self) -> str:
        return self._bucket_direction(self.aim_direction)

    def drink_estus(self) -> None:
        """ Spends one flask to restore ESTUS_HEAL_FRACTION of the maximum
        health. Only from idle or walk, the same as a roll, never mid-swing
        or while staggered, and never at full health, where it would only
        waste the flask. """
        if self.estus == 0 or self.health >= MAX_HEALTH:
            return

        if not isinstance(self.state_machine.current, (player_states.PlayerIdleState, player_states.PlayerWalkState)):
            return

        self.estus -= 1
        self.health = min(MAX_HEALTH, self.health + round(MAX_HEALTH * ESTUS_HEAL_FRACTION))
        audio.play("stus_flask")

    def can_switch_weapon(self) -> bool:
        """ Not mid-charge and not mid-attack, switching weapons while
        either is in progress would either strand a charge built up for
        a weapon no longer in hand, or interrupt a swing/shot already
        under way. """
        return (
            self.charge == 0.0
            and not self.attack_held
            and not isinstance(
                self.state_machine.current,
                (player_states.PlayerAttackState, player_states.PlayerStunState),
            )
        )

    def switch_weapon(self) -> None:
        if not self.can_switch_weapon():
            return

        index = WEAPON_ORDER.index(self.equipped_weapon)
        self.equipped_weapon = WEAPON_ORDER[(index + 1) % len(WEAPON_ORDER)]
        self.pose = "idle"

    # ------------------------------------------------------------
    # Input 
    # ------------------------------------------------------------
    def on_input(self, input_id: str, input_data: Any) -> None:
        if input_id == ATTACK:
            if input_data.pressed and self.current_stamina >= MIN_STAMINA:
                self.attack_held = True
            elif input_data.released and self.attack_held:
                self.attack_held = False
                self.attack_requested = True
            return

        if input_id == SWITCH_WEAPON and input_data.pressed:
            self.switch_weapon()
            return

        if input_id == ROLL and input_data.pressed and self.current_stamina >= MIN_STAMINA:
            # Only queued from Idle/Walk: requesting it mid-swing or mid-roll
            if isinstance(self.state_machine.current,
                         (player_states.PlayerIdleState, player_states.PlayerWalkState)):
                self.roll_requested = True
            return

        if input_id == HEAL and input_data.pressed:
            self.drink_estus()
            return

        if input_id in self.held:
            if input_data.pressed:
                self.held[input_id] = True
            elif input_data.released:
                self.held[input_id] = False

    # ------------------------------------------------------------
    # Update
    # ------------------------------------------------------------
    def update(self, dt: float, camera: Any) -> None:
        self.current_stamina = min(self.current_stamina + dt, MAX_STAMINA)
        self.hit_flash = max(0.0, self.hit_flash - dt)
        self._update_aim(camera)
        self.state_machine.update(dt)

    def _update_aim(self, camera: Any) -> None:
        mouse_virtual = settings.to_virtual(pygame.mouse.get_pos())
        mouse_world = pygame.Vector2(camera.screen_to_world(mouse_virtual))
        to_mouse = mouse_world - self.center

        """ Guards the normalize(): if the mouse sits exactly on the
        player's own centre there is no direction to face, so the last
        one found is kept rather than raising or snapping to (0, 0). """
        if to_mouse.length_squared() > 1:
            self.aim_direction = to_mouse.normalize()

    # ------------------------------------------------------------
    # Render 
    # ------------------------------------------------------------
    def render(self, surface: pygame.Surface, camera: Any) -> None:
        """ No per-frame scaling, matching Prop.render: this project never
        changes camera.zoom, so the extra transform would only cost
        time without changing a single pixel of the result. The day
        zoom does change, both of these need the same fix at once. """

        # The attack hitbox
        if self.attack_held:
            self._render_charge_preview(surface, camera)
        elif isinstance(self.state_machine.current, player_states.PlayerAttackState):
            self.state_machine.current.render_hit(surface, camera)
        
        shadow_rect = pygame.Rect(
            round(self.x - self._shadow.get_width() / 2),
            round(self.y - 8),
            self._shadow.get_width(),
            FEET_DEPTH,
        )
        surface.blit(self._shadow, camera.apply(shadow_rect))

        # We render the bob_offset of walking and stagger_offset of stun, and aslo the flasehd
        sprite_rect = self.image_rect.move(round(self.stagger_offset), round(self.bob_offset))
        sprite = flashed(self.sprite) if self.hit_flash > 0 else self.sprite
        surface.blit(sprite, camera.apply(sprite_rect))
        

    def render_hud(self, surface: pygame.Surface) -> None:
        """ The stamina bar, with the health bar right under it. Drawn
        directly in virtual-surface coordinates, so neither ever scrolls
        or pans with the camera. """
        stamina_top = settings.VIRTUAL_HEIGHT - HUD_BAR_BOTTOM_MARGIN - HUD_BAR_HEIGHT

        self._render_bar(
            surface, stamina_top, self.current_stamina / MAX_STAMINA,
            HUD_BAR_FILL_COLOR, HUD_BAR_BORDER_COLOR,
        )
        self._render_bar(
            surface, stamina_top + HUD_BAR_HEIGHT + HUD_BAR_GAP, self.health / MAX_HEALTH,
            HUD_HEALTH_FILL_COLOR, HUD_HEALTH_BORDER_COLOR,
        )
        self._render_quick_items(surface)

    def _render_quick_items(self, surface: pygame.Surface) -> None:
        hud = settings.TILESETS["hud"]
        slot = hud["hud_slot"]
        step_x = slot.get_width() + QUICK_ITEM_GAP
        step_y = slot.get_height() + QUICK_ITEM_GAP

        # The centre of the cross, placed so its left and bottom slots sit QUICK_ITEM_MARGIN from the edges.
        centre_x = QUICK_ITEM_MARGIN + slot.get_width() / 2 + step_x
        centre_y = settings.VIRTUAL_HEIGHT - QUICK_ITEM_MARGIN - slot.get_height() / 2 - step_y

        icons = {
            "quiver": hud["hud_quiver"],
            "estus": hud["hud_flask_full"] if self.estus > 0 else hud["hud_flask_empty"],
        }

        for weapon in WEAPON_ORDER:
            in_hand = weapon == self.equipped_weapon
            icons[weapon] = hud[f"hud_{weapon}"] if in_hand else self._faded_weapon_icons[weapon]

        for item, (offset_x, offset_y) in QUICK_ITEM_SLOTS.items():
            centre = (round(centre_x + offset_x * step_x), round(centre_y + offset_y * step_y))
            surface.blit(slot, slot.get_rect(center=centre))
            surface.blit(icons[item], icons[item].get_rect(center=centre))

        # How many flasks are left, in the estus slot's lower right corner; an empty flask shows no number.
        if self.estus > 0:
            estus_slot = slot.get_rect(center=(round(centre_x), round(centre_y + step_y)))
            count = settings.FONTS["small"].render(str(self.estus), True, settings.COLOR_TEXT)
            surface.blit(count, count.get_rect(bottomright=(estus_slot.right - 3, estus_slot.bottom - 2)))

    def _render_bar(
        self, surface: pygame.Surface, top: int, fraction: float,
        fill_color: tuple, border_color: tuple,
    ) -> None:
        # Clamped both ways: stamina can dip below zero after an action
        # that costs more than what was left.
        fraction = max(0.0, min(1.0, fraction))

        track = pygame.Rect(
            (settings.VIRTUAL_WIDTH - HUD_BAR_WIDTH) // 2, top, HUD_BAR_WIDTH, HUD_BAR_HEIGHT
        )
        pygame.draw.rect(surface, HUD_BAR_TRACK_COLOR, track)

        fill = track.copy()
        fill.width = round(HUD_BAR_WIDTH * fraction)
        pygame.draw.rect(surface, fill_color, fill)
        pygame.draw.rect(surface, border_color, track, 1)

    def render_debug(self, surface: pygame.Surface, camera: Any) -> None:
        pygame.draw.rect(surface, (90, 220, 140), camera.apply(self.image_rect), 1)
        pygame.draw.rect(surface, (220, 80, 80), camera.apply(self.feet_rect), 1)

        # A short line pointing where an attack would go, always visible in debug 
        # so the mouse-aim wiring itself is easy to confirm even outside a swing/shot.
        tip = self.center + self.aim_direction * 26
        pygame.draw.line(
            surface,
            (120, 190, 230),
            camera.world_to_screen((self.center.x, self.center.y)),
            camera.world_to_screen((tip.x, tip.y)),
            1,
        )

        """ The attack's own hitbox (while it is actually happening) is drawn 
        by PlayerAttackState itself, it is the one place that already knows 
        exactly what that attack locked in, and nothing outside it needs to. """
        current = self.state_machine.current
        render_debug = getattr(current, "render_debug", None)

        if render_debug is not None:
            render_debug(surface, camera)

    def _render_charge_preview(self, surface: pygame.Surface, camera: Any) -> None:
        weapon = self.weapon_def

        if weapon["kind"] == "melee":
            from src.combat.cone import polygon_points
            from src.definitions.combat import lerp

            half_angle = lerp(weapon["min_half_angle"], weapon["max_half_angle"], self.charge)
            reach = lerp(weapon["min_reach"], weapon["max_reach"], self.charge)
            points = [
                camera.world_to_screen((point.x, point.y))
                for point in polygon_points(self.center, self.aim_direction, half_angle, reach)
            ]
            pygame.draw.polygon(surface, settings.ATTACK_HITBOX_COLOR, points, 1)
        else:
            tip = self.center + self.aim_direction * weapon["max_range"] / 3
            pygame.draw.line(
                surface,
                settings.ATTACK_HITBOX_COLOR,
                camera.world_to_screen((self.center.x, self.center.y)),
                camera.world_to_screen((tip.x, tip.y)),
                1,
            )
        
