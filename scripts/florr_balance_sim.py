"""Progression check: a bot plays the florr world offline (no server, no database) and grows.

    .venv\\Scripts\\python.exe scripts\\florr_balance_sim.py [minutes] [seed]
The bot keeps its best petals equipped, crafts whenever it has spare copies, hunts mobs of a zone it can
handle (roughly: zone tier <= average rarity of its loadout) and flees at low hp. It is only a yardstick for
'does progression happen at a sane pace?', not a model of a human.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from game.consumers.florr import world as w  # noqa: E402

minutes = float(sys.argv[1]) if len(sys.argv) > 1 else 40
seed = int(sys.argv[2]) if len(sys.argv) > 2 else 3
DT = 1.0 / w.TICK_RATE
REPORT_EVERY = (5 if minutes <= 60 else 20) * 60 * w.TICK_RATE
milestones = {}

world = w.World(rng=random.Random(seed))
bot = world.add_player("bot")
deaths = 0
deaths_by_tier = {}
last_manage = 0.0


def power(item):
    stats = w.petal_stats(item)
    return stats["rarity"] * 1000 + stats["dps"] + stats["hp"]


def manage_inventory():
    """Equip the strongest items, craft spare copies."""
    for item in sorted(bot.inventory, key=lambda i: -power(i)):
        kind, rarity = w.parse_item(item)
        if rarity < w.MAX_RARITY and bot.free_count(item) >= w.CRAFT_COST:
            world.craft(bot.id, item)
            break
    wanted = []
    for item in sorted(bot.inventory, key=lambda i: -power(i)):
        wanted += [item] * bot.inventory[item]
    wanted = wanted[:w.PETAL_COUNT]
    for slot in range(w.PETAL_COUNT):
        target = wanted[slot] if slot < len(wanted) else ""
        if bot.loadout[slot] != target and bot.swap_cd <= 0:
            # equip() checks ownership against the other slots, so free the slot first if needed
            if world.equip(bot.id, slot, target):
                return


def avg_rarity():
    rs = [w.parse_item(i)[1] for i in bot.loadout if i]
    return sum(rs) / len(rs) if rs else 0.0


def nearest(items, x, y):
    return min(items, key=lambda o: math.hypot(o.x - x, o.y - y), default=None)


def control():
    allowed_tier = min(w.ZONE_COUNT - 1, int(avg_rarity()))
    drop = nearest(world.drops.values(), bot.x, bot.y)
    mobs = [m for m in world.mobs.values() if m.tier <= allowed_tier]
    mob = nearest(mobs, bot.x, bot.y)
    close = [m for m in world.mobs.values() if math.hypot(m.x - bot.x, m.y - bot.y) < 160]
    if bot.hp < 40:
        if close:
            t = nearest(close, bot.x, bot.y)
            d = math.hypot(t.x - bot.x, t.y - bot.y) or 1.0
            world.set_input(bot.id, (bot.x - t.x) / d, (bot.y - t.y) / d, -1)
        else:
            world.set_input(bot.id, 0, 0, -1)
        return
    if drop is not None and math.hypot(drop.x - bot.x, drop.y - bot.y) < 400:
        tx, ty, mode, stand = drop.x, drop.y, 0, 0.0
    elif mob is not None and math.hypot(mob.x - bot.x, mob.y - bot.y) < 900:
        tx, ty, stand = mob.x, mob.y, 60.0
        mode = 1 if 100 <= math.hypot(mob.x - bot.x, mob.y - bot.y) < 220 else 0
    else:
        # nothing suitable around: walk to the middle of the ring we want to hunt in
        ring = 1200.0 if allowed_tier == 0 else (w.ZONE_EDGES[allowed_tier - 1] + (w.ZONE_EDGES[allowed_tier] if allowed_tier < w.ZONE_COUNT - 1 else 0)) / 2
        ang = math.atan2(bot.y - w.CENTER[1], bot.x - w.CENTER[0])
        tx, ty, mode, stand = w.CENTER[0] + ring * math.cos(ang), w.CENTER[1] + ring * math.sin(ang), 0, 30.0
    d = math.hypot(tx - bot.x, ty - bot.y) or 1.0
    world.set_input(bot.id, (tx - bot.x) / d if d > stand else 0, (ty - bot.y) / d if d > stand else 0, mode)


print(f"seed {seed}: minute | avg loadout rarity | hunting tier | kills | deaths | inventory (rarity: count)")
was_alive = True
for tick in range(1, int(minutes * 60 * w.TICK_RATE) + 1):
    if not bot.alive:
        world.respawn(bot.id)
    else:
        if tick % 40 == 0:
            manage_inventory()
        control()
    before = bot.alive
    world.step(DT)
    if before and not bot.alive:
        deaths += 1
        zone = w.zone_of(bot.x, bot.y)
        deaths_by_tier[zone] = deaths_by_tier.get(zone, 0) + 1
    for k in range(1, w.MAX_RARITY + 1):
        if k not in milestones and avg_rarity() >= k - 0.001:
            milestones[k] = round(tick / w.TICK_RATE / 60)
    if tick % REPORT_EVERY == 0:
        by_rarity = {}
        for item, n in bot.inventory.items():
            by_rarity[w.parse_item(item)[1]] = by_rarity.get(w.parse_item(item)[1], 0) + n
        print(f"  {tick // (60 * w.TICK_RATE):5d} | {avg_rarity():4.1f} | {min(w.ZONE_COUNT - 1, int(avg_rarity()))} | "
              f"{bot.kills:5d} | {deaths:3d} | {dict(sorted(by_rarity.items()))}")

print("minutes until the whole loadout averaged rarity k:", milestones)
print("deaths by zone tier:", dict(sorted(deaths_by_tier.items())))
print("final loadout:", bot.loadout)
