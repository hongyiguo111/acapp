"""Rough balance check: a simple bot plays the florr world offline (no server, no database).

    .venv\\Scripts\\python.exe scripts\\florr_balance_sim.py [minutes] [seed]
The bot walks to the nearest drop or mob, keeps mobs on its petal ring and runs away at low hp.
It is only a yardstick for 'is the loop alive?' (kills/min, deaths, loot), not a model of a human.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from game.consumers.florr import world as w  # noqa: E402

minutes = float(sys.argv[1]) if len(sys.argv) > 1 else 10
seed = int(sys.argv[2]) if len(sys.argv) > 2 else 3
DT = 1.0 / w.TICK_RATE

world = w.World(rng=random.Random(seed))
bot = world.add_player("bot")
deaths = 0
kills_by_kind = {}
seen_mobs = {}


def nearest(items, x, y):
    return min(items, key=lambda o: math.hypot(o.x - x, o.y - y), default=None)


for tick in range(int(minutes * 60 * w.TICK_RATE)):
    if not bot.alive:
        deaths += 1 if bot.dead_for == 0.0 else 0
        world.respawn(bot.id)
    else:
        drop = nearest(world.drops.values(), bot.x, bot.y)
        mob = nearest(world.mobs.values(), bot.x, bot.y)
        target, mode = None, 0
        close = [m for m in world.mobs.values() if math.hypot(m.x - bot.x, m.y - bot.y) < 150]
        if bot.hp < 40 and close:
            # run away from the nearest threat with petals pulled in
            threat = nearest(close, bot.x, bot.y)
            d = math.hypot(threat.x - bot.x, threat.y - bot.y) or 1.0
            world.set_input(bot.id, (bot.x - threat.x) / d, (bot.y - threat.y) / d, -1)
            target = False
        elif bot.hp < 40:
            world.set_input(bot.id, 0, 0, -1)                  # nothing near: rest and regenerate
            target = False
        elif drop is not None and math.hypot(drop.x - bot.x, drop.y - bot.y) < 400:
            target = drop
        elif mob is not None:
            target = mob
            dist = math.hypot(mob.x - bot.x, mob.y - bot.y)
            # extended petals only help at range; a mob touching the body sits inside the neutral ring
            mode = 1 if 100 <= dist < 220 else 0
        if target:
            d = math.hypot(target.x - bot.x, target.y - bot.y) or 1.0
            stand_off = 60.0 if isinstance(target, w.Mob) else 0.0
            if d > stand_off:
                world.set_input(bot.id, (target.x - bot.x) / d, (target.y - bot.y) / d, mode)
            else:
                world.set_input(bot.id, 0, 0, mode)
        elif target is None:
            world.set_input(bot.id, 0, 0, mode)
    before = set(world.mobs)
    for mid in before:
        seen_mobs[mid] = world.mobs[mid].kind
    world.step(DT)
    for mid in before - set(world.mobs):
        if world.mobs.get(mid) is None and seen_mobs.get(mid):
            kills_by_kind[seen_mobs[mid]] = kills_by_kind.get(seen_mobs[mid], 0) + 1

print(f"simulated {minutes:g} min, seed {seed}")
print(f"kills: {bot.kills} ({bot.kills / minutes:.1f}/min)  deaths: {deaths}")
print("mobs gone by kind (incl. none killed by the bot):", kills_by_kind)
print("inventory:", bot.inventory)
print("mobs alive:", len(world.mobs), " drops lying around:", len(world.drops))
