# Breakout — Power-Up Assignment

This document covers what was added on top of the base Breakout study case, the ball_catch power_up, the twin rocket cannons, and a third, custom power_up of my own design; **BreakBricks**.

The existing `PowerUp` base class and `AbstractFactory("src.powerups")` setup already provided everything needed to plug new power_ups in: subclass `PowerUp`, implement `take(play_state)`, and register the class in `src/powerups/__init__.py` so the factory can find it by name. All three power_ups below follow that same shape.

## Ball Catch - `StopBall`

Picking this up doesn't do anything by itself, it just arms a flag on the play state (`play_state.stuck_next = True`). The actual behavior lives in `PlayState.update`, the next time *any* ball touches the paddle while that flag is set, instead of rebounding it gets stuck to the paddle (`ball.is_stuck = True`) and stops moving. While a ball is stuck, `PlayState.update` skips its physics entirely, and `render` keeps redrawing it stucked to the paddle's position every frame.

Pressing the serve key while at least one ball is stuck (`any(ball.is_stuck for ball in self.balls)`) launches every stuck ball at once with a fresh random velocity, exactly like the initial serve at the start of a life.

## Cannons - `Rocket`

This one spawns two independent `Rocket` instances, one on each side of the paddle, both created and attached the moment the power_up is picked up. Each rocket tracks the paddle's position every frame while it's waiting to be fired (`was_taken and not was_fired`), so it visually rides along with the paddle instead of being left behind.

Pressing the fire key launches both rockets simultaneously, they can't be re-armed until they either hit a brick or fly off the top of the screen, since a new Rocket power-up only spawns while `l_rocket` and `r_rocket` are both `None`. On impact, a rocket calls `brick.destroy()` (full destruction in one hit, ignoring tier and color) and disappears, it only consumes one brick.

## Custom Power_Up - `BreakBricks`

This is the power_up I designed myself. The idea, instead of a single predictable effect, it detonates a **random number of bricks scattered anywhere on the board**, between 3 and 10, favoring smaller amounts most of the time but occasionally granting a much bigger clear, so picking it up always feels a little unpredictable.

### How the amount is decided

`take()` rolls a single `random.random()` and walks through a manually weighted ladder of thresholds:

```python
p = random.random()
if   p <= 0.09: amount = 10
elif p <= 0.11: amount = 9
elif p <= 0.13: amount = 8
elif p <= 0.16: amount = 7
elif p <= 0.19: amount = 6
elif p <= 0.22: amount = 5
elif p <= 0.5:  amount = 4
else:           amount = 3
```

This isn't a uniform 3–10 roll, it's deliberately front-loaded toward the low end. Roughly half the time (`p > 0.5`) you get the minimum, 3 brick, the big 10-brick selection only shows up about 9% of the time. The intent is that BreakBricks should feel useful on every pickup without being an auto-win button whenever it happens to spawn.

### How the bricks are chosen and destroyed

```python
candidates = [b for b in play_state.brickset.bricks.values() if not b.broken]
amount = min(amount, len(candidates))
for b in random.sample(candidates, amount):
    b.destroy()
```

Only bricks that are still standing (`not b.broken`) are eligible, there's no point "destroying" one that's already gone. `random.sample` picks that many *distinct* bricks with no repeats, anywhere on the board, not just near where the power-up was collected. Each chosen brick is destroyed outright with `Brick.destroy()` — the same one-hit full destruction the rockets use, regardless of its current tier or color.

The `amount = min(amount, len(candidates))` clamp matters more than it looks: late in a level, when very few bricks are left, asking `random.sample` for more bricks than actually exist raises a `ValueError`. This keeps the power-up safe to use right up to the last few bricks on the board, instead of crashing the game at the worst possible moment.

### A bug this power_up exposed in the win condition

Getting BreakBricks working correctly surfaced a real issue in `PlayState`'s victory check that had nothing to do with the power_up's own code. The original check was:

```python
if self.brickset.size == 1 and next((True for _, b in self.brickset.bricks.items() if b.broken), False):
```

It was written assuming bricks always disappear one at a time, the ball breaks one, the count drops from 2 to 1, and this catches that in-between moment right before the last brick is swept from the dictionary. BreakBricks can wipe out the *last several* bricks on the board in a single frame, so the count can jump straight from, say, 7 to 0, skipping right over the value 1 that the old check was waiting for. Victory would never trigger, and the game would sit there with an empty board and a bouncing ball forever.

The fix was to simplify the check to what it actually means: `self.brickset.size == 0`. It's simpler than the original *and* correct for both the normal one-brick-at-a-time case and for BreakBricks' bulk destruction, no more relying on a specific removal pattern.
