"""Authoritative simulation for the florr-style mode.

Pure Python (no Django / asyncio) so it can be unit tested and reasoned about on its own.
All units are world units; time is in seconds. Clients only send their input (move vector, petal
mode, equip / craft requests); the server decides everything else. Persistence is done by the
caller (see store.py / hub.py): this module only keeps `save_dirty` / `inv_dirty` flags on players.

An *item* is a petal of one kind and rarity tier, written "kind:rarity" (e.g. "rose:2").
"""
import math
import random

WORLD_W = 3000.0
WORLD_H = 3000.0
TICK_RATE = 20                    # simulation and snapshot rate (Hz)
VIEW_RADIUS = 1100.0              # entities farther than this from a player are not sent to them

PLAYER_RADIUS = 28.0
PLAYER_SPEED = 260.0
PLAYER_MAX_HP = 100.0
PLAYER_REGEN = 3.0                # hp per second, once out of combat
PLAYER_REGEN_DELAY = 4.0          # seconds without taking damage before regen starts
RESPAWN_DELAY = 1.0               # minimum time dead before a respawn request is accepted

PETAL_COUNT = 5                   # loadout slots
PETAL_RESPAWN = 2.0               # seconds for a broken petal to come back
ORBIT_OMEGA = 2.6                 # rad/s
# defend / neutral / attack. A chaser stops at mob radius + 0.9 * PLAYER_RADIUS from the player (about 45 for
# the smallest mob), and every ring must still reach it, otherwise holding the attack button would make a
# fight unwinnable. Attack instead deals more damage; defend makes petals wear down slower.
ORBIT_RADIUS = {-1: 46.0, 0: 64.0, 1: 76.0}
ORBIT_SHIFT_SPEED = 300.0         # how fast the orbit radius changes (units/s)
PETAL_HIT_MARGIN = 6.0            # petals hit a bit beyond their drawn size
ATTACK_DAMAGE_MULT = 1.5          # petal damage while the player holds "attack"
DEFEND_WEAR_MULT = 0.5            # damage petals take while the player holds "defend"
EQUIP_COOLDOWN = 0.4              # seconds between loadout changes

# ---- petals ------------------------------------------------------------------------------------
# dps: damage per second dealt to a mob it overlaps; hp: damage a petal absorbs before breaking;
# heal: hp per second given to the owner while the petal is intact. These are the rarity-0 values.
PETAL_TYPES = {
    "basic":   {"name": "花瓣", "color": "#ffffff", "radius": 11.0, "hp": 12.0, "dps": 44.0, "heal": 0.0},
    "stinger": {"name": "尖刺", "color": "#2b2b2b", "radius": 9.0,  "hp": 6.0,  "dps": 96.0, "heal": 0.0},
    "heavy":   {"name": "沉石", "color": "#9a9a9a", "radius": 15.0, "hp": 40.0, "dps": 28.0, "heal": 0.0},
    "rose":    {"name": "玫瑰", "color": "#ff7fb0", "radius": 10.0, "hp": 9.0,  "dps": 8.0,  "heal": 2.5},
}
PETAL_ORDER = list(PETAL_TYPES)   # index in this list is the compact id used in snapshots

RARITIES = [
    {"name": "普通", "color": "#7eef6d"},
    {"name": "罕见", "color": "#ffe65d"},
    {"name": "稀有", "color": "#4d52e3"},
    {"name": "史诗", "color": "#861fde"},
    {"name": "传说", "color": "#de1f1f"},
]
MAX_RARITY = len(RARITIES) - 1
PETAL_RARITY_POWER = 2.2          # hp / dps / heal multiplier per rarity tier
PETAL_RARITY_SIZE = 0.08          # radius growth per tier
CRAFT_COST = 5                    # petals of one item that are turned into one of the next tier
ITEM_CODE_BASE = 8                # snapshots encode an item as kind_index * 8 + rarity

STARTER_INVENTORY = {"basic:0": 5}
STARTER_LOADOUT = ["basic:0"] * PETAL_COUNT
INVENTORY_CAP = 9999


def make_item(kind, rarity=0):
    return f"{kind}:{rarity}"


def parse_item(item):
    """'rose:2' -> ('rose', 2); a bare 'rose' (older saves) means rarity 0; anything invalid -> None."""
    if not isinstance(item, str):
        return None
    kind, sep, rarity = item.partition(":")
    if kind not in PETAL_TYPES:
        return None
    if not sep:
        return kind, 0
    if not rarity.isdigit() or not 0 <= int(rarity) <= MAX_RARITY:
        return None
    return kind, int(rarity)


def normalize_item(item):
    parsed = parse_item(item)
    return make_item(*parsed) if parsed else None


_STATS_CACHE = {}


def petal_stats(item):
    """Effective stats of an item: the base kind scaled by its rarity tier."""
    stats = _STATS_CACHE.get(item)
    if stats is None:
        kind, rarity = parse_item(item)
        base = PETAL_TYPES[kind]
        power = PETAL_RARITY_POWER ** rarity
        stats = {
            "kind": kind, "rarity": rarity, "name": base["name"], "color": base["color"],
            "radius": base["radius"] * (1.0 + PETAL_RARITY_SIZE * rarity),
            "hp": base["hp"] * power, "dps": base["dps"] * power, "heal": base["heal"] * power,
        }
        _STATS_CACHE[item] = stats
    return stats


def encode_item(item):
    kind, rarity = parse_item(item)
    return PETAL_ORDER.index(kind) * ITEM_CODE_BASE + rarity


# ---- zones and mobs --------------------------------------------------------------------------------
# Distance from the centre of the map decides the zone; deeper zones have stronger mobs (and better drops).
ZONE_EDGES = (1000.0, 650.0, 330.0)             # tier 0 beyond the first edge, tier 3 inside the last
ZONES = [
    {"name": "草地", "color": "#1ea761"},
    {"name": "森林", "color": "#188b4f"},
    {"name": "沼泽", "color": "#3e7a5a"},
    {"name": "深渊", "color": "#44406a"},
]
ZONE_COUNT = len(ZONES)
ZONE_OUTER = (None,) + ZONE_EDGES               # outer edge of tier t is ZONE_EDGES[t-1]; tier 0 has none
CENTER = (WORLD_W / 2, WORLD_H / 2)


def zone_of(x, y):
    d = math.hypot(x - CENTER[0], y - CENTER[1])
    for tier, edge in enumerate(ZONE_EDGES):
        if d >= edge:
            return tier
    return ZONE_COUNT - 1


MOB_HP_MULT = 2.6                 # per mob tier
MOB_DPS_MULT = 1.45
MOB_SIZE_GROWTH = 0.12
MOB_TARGETS = (16, 10, 6, 3)      # how many mobs of each tier the world keeps alive
# Drops are one rarity tier below the mob's tier (so going deeper alone does not skip crafting) and are
# one tier better than that DROP_BUMP_CHANCE of the time.
DROP_RARITY_OFFSET = -1
DROP_BUMP_CHANCE = 0.08
# Every drop chance in MOB_TYPES is multiplied by DROP_CHANCE_SCALE, and by DROP_TIER_FALLOFF per mob tier
# (a deeper drop is worth several shallow ones, so it should come less often). Tuned with scripts/florr_balance_sim.py.
DROP_CHANCE_SCALE = 0.45
DROP_TIER_FALLOFF = 0.7

# dps: damage per second dealt to a player body or a petal it overlaps; aggro 0 = never chases;
# speed 0 = never moves; drops: (petal kind, chance) rolled independently on death.
MOB_TYPES = {
    "ladybug": {"name": "瓢虫", "color": "#e0443e", "hp": 35.0,  "radius": 22.0, "speed": 90.0,  "dps": 5.0,
                "aggro": 0.0,   "weight": 35, "drops": (("basic", 0.45), ("rose", 0.12))},
    "beetle":  {"name": "甲虫", "color": "#8e5fb3", "hp": 70.0,  "radius": 30.0, "speed": 120.0, "dps": 15.0,
                "aggro": 380.0, "weight": 30, "drops": (("basic", 0.35), ("stinger", 0.10))},
    "wasp":    {"name": "黄蜂", "color": "#f2c230", "hp": 45.0,  "radius": 20.0, "speed": 190.0, "dps": 22.0,
                "aggro": 450.0, "weight": 15, "drops": (("stinger", 0.22), ("basic", 0.20))},
    "rock":    {"name": "岩石", "color": "#7b7f86", "hp": 160.0, "radius": 36.0, "speed": 0.0,   "dps": 10.0,
                "aggro": 0.0,   "weight": 20, "drops": (("heavy", 0.30), ("basic", 0.20))},
}
MOB_KINDS = list(MOB_TYPES)
MOB_WEIGHTS = [MOB_TYPES[k]["weight"] for k in MOB_KINDS]
MOB_SPAWN_INTERVAL = 0.5          # at most one spawn per interval
MOB_SPAWN_MIN_DIST = 700.0        # never spawn closer than this to a player
MOB_WANDER_SPEED_FACTOR = 0.4
MOB_WANDER_INTERVAL = 3.0
MOB_CONTACT_FACTOR = 0.9          # chasers stop at mob radius + this * player radius from the player centre

DROP_RADIUS = 12.0
DROP_PICKUP_REACH = 12.0          # extra reach on top of both radii, so pickups feel forgiving
DROP_TTL = 45.0
DROP_CAP = 150


def _clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


def drop_chance(base_chance, tier):
    return base_chance * DROP_CHANCE_SCALE * DROP_TIER_FALLOFF ** tier


def sanitize_inventory(raw):
    """Canonical item ids with sane counts (used for data coming from the database)."""
    inv = {}
    for item, count in (raw or {}).items():
        item = normalize_item(item)
        if item is None:
            continue
        try:
            count = int(count)
        except (TypeError, ValueError):
            continue
        if count > 0:
            inv[item] = min(inv.get(item, 0) + count, INVENTORY_CAP)
    return inv


def sanitize_loadout(raw, inventory):
    """A loadout is PETAL_COUNT slots; each filled slot needs its own owned copy of that item."""
    loadout = []
    used = {}
    for item in list(raw or [])[:PETAL_COUNT]:
        item = normalize_item(item) if item else None
        if item and used.get(item, 0) < inventory.get(item, 0):
            used[item] = used.get(item, 0) + 1
            loadout.append(item)
        else:
            loadout.append("")
    loadout += [""] * (PETAL_COUNT - len(loadout))
    return loadout


def welcome_info():
    """Static catalogue the client needs to draw things (sent once per connection)."""
    return {
        "w": WORLD_W, "h": WORLD_H, "player_r": PLAYER_RADIUS, "petal_n": PETAL_COUNT,
        "player_hp": PLAYER_MAX_HP, "omega": ORBIT_OMEGA, "tick_rate": TICK_RATE, "drop_r": DROP_RADIUS,
        "petals": [dict(id=k, name=v["name"], color=v["color"], radius=v["radius"]) for k, v in PETAL_TYPES.items()],
        "rarities": RARITIES, "max_rarity": MAX_RARITY, "item_base": ITEM_CODE_BASE,
        "size_growth": PETAL_RARITY_SIZE, "craft_cost": CRAFT_COST,
        "mobs": {k: {"name": v["name"], "color": v["color"], "radius": v["radius"]} for k, v in MOB_TYPES.items()},
        "zones": [dict(name=z["name"], color=z["color"], outer=ZONE_OUTER[i]) for i, z in enumerate(ZONES)],
        "center": CENTER,
    }


class Player:
    __slots__ = ("id", "name", "x", "y", "hp", "alive", "dx", "dy", "mode", "angle", "orbit_r",
                 "loadout", "inventory", "petal_hp", "petal_timer", "kills", "kills_total", "since_hit",
                 "dead_for", "swap_cd", "inv_dirty", "save_dirty", "pickups")

    def __init__(self, pid, name, x, y, inventory, loadout, kills_total):
        self.id = pid
        self.name = name
        self.x, self.y = x, y
        self.hp = PLAYER_MAX_HP
        self.alive = True
        self.dx = self.dy = 0.0
        self.mode = 0
        self.angle = 0.0
        self.orbit_r = ORBIT_RADIUS[0]
        self.inventory = inventory
        self.loadout = loadout
        self.petal_hp = [0.0] * PETAL_COUNT
        self.petal_timer = [0.0] * PETAL_COUNT     # >0 while the petal is broken
        self.reset_petals()
        self.kills = 0                 # this session
        self.kills_total = kills_total
        self.since_hit = 999.0
        self.dead_for = 0.0
        self.swap_cd = 0.0
        self.inv_dirty = True          # tell the client its inventory (first message after welcome)
        self.save_dirty = False        # needs to be written to the database
        self.pickups = []              # items received since the client was last told

    def reset_petals(self):
        for i in range(PETAL_COUNT):
            self.reset_petal(i)

    def reset_petal(self, i):
        item = self.loadout[i]
        self.petal_hp[i] = petal_stats(item)["hp"] if item else 0.0
        self.petal_timer[i] = 0.0

    def petal_alive(self, i):
        return bool(self.loadout[i]) and self.petal_timer[i] <= 0.0

    def petal_pos(self, i):
        a = self.angle + i * (2 * math.pi / PETAL_COUNT)
        return self.x + self.orbit_r * math.cos(a), self.y + self.orbit_r * math.sin(a)

    def free_count(self, item):
        """Owned copies of `item` that are not sitting in a loadout slot."""
        return self.inventory.get(item, 0) - sum(1 for i in self.loadout if i == item)


class Mob:
    __slots__ = ("id", "kind", "tier", "x", "y", "hp", "max_hp", "radius", "dps",
                 "wander_x", "wander_y", "wander_t", "last_hit_by")

    def __init__(self, mid, kind, x, y, tier=0):
        spec = MOB_TYPES[kind]
        self.id = mid
        self.kind = kind
        self.tier = tier
        self.x, self.y = x, y
        self.hp = self.max_hp = spec["hp"] * MOB_HP_MULT ** tier
        self.radius = spec["radius"] * (1.0 + MOB_SIZE_GROWTH * tier)
        self.dps = spec["dps"] * MOB_DPS_MULT ** tier
        self.wander_x, self.wander_y, self.wander_t = x, y, 0.0
        self.last_hit_by = None


class Drop:
    __slots__ = ("id", "item", "x", "y", "ttl")

    def __init__(self, did, item, x, y):
        self.id, self.item, self.x, self.y, self.ttl = did, item, x, y, DROP_TTL


class World:
    def __init__(self, rng=None):
        self.rng = rng or random.Random()
        self.players = {}
        self.mobs = {}
        self.drops = {}
        self._next_id = 1
        self._spawn_cd = 0.0
        self.tick = 0

    # ---- player lifecycle -------------------------------------------------
    def _new_id(self):
        i = self._next_id
        self._next_id += 1
        return i

    def _point_in_zone(self, tier):
        """A random point whose zone is `tier`, inside the map."""
        margin = 100.0
        if tier == 0:       # the outer zone is the map minus a disc: rejection sampling is fine
            for _ in range(100):
                x, y = self.rng.uniform(margin, WORLD_W - margin), self.rng.uniform(margin, WORLD_H - margin)
                if zone_of(x, y) == 0:
                    return x, y
            return margin, margin
        outer = ZONE_EDGES[tier - 1]
        inner = ZONE_EDGES[tier] if tier < ZONE_COUNT - 1 else 0.0
        r = math.sqrt(self.rng.uniform(inner * inner, outer * outer))      # uniform over the ring's area
        a = self.rng.uniform(0.0, 2 * math.pi)
        return CENTER[0] + r * math.cos(a), CENTER[1] + r * math.sin(a)

    def _player_spawn_point(self):
        return self._point_in_zone(0)

    def add_player(self, name, inventory=None, loadout=None, kills_total=0):
        """`inventory`/`loadout` come from the database; None means a brand new player."""
        if inventory is None:
            inventory = dict(STARTER_INVENTORY)
            loadout = list(STARTER_LOADOUT)
        inventory = sanitize_inventory(inventory)
        loadout = sanitize_loadout(loadout, inventory)
        x, y = self._player_spawn_point()
        p = Player(self._new_id(), name, x, y, inventory, loadout, kills_total)
        self.players[p.id] = p
        return p

    def remove_player(self, pid):
        self.players.pop(pid, None)

    def player_state(self, pid):
        """What has to be persisted for a player."""
        p = self.players.get(pid)
        if p is None:
            return None
        return {"inventory": dict(p.inventory), "loadout": list(p.loadout), "kills_total": p.kills_total}

    def set_input(self, pid, dx, dy, mode):
        p = self.players.get(pid)
        if p is None:
            return
        # never trust the client: finite numbers, magnitude <= 1, mode in {-1, 0, 1}
        try:
            dx, dy = float(dx), float(dy)
        except (TypeError, ValueError):
            return
        if not (math.isfinite(dx) and math.isfinite(dy)):
            return
        mag = math.hypot(dx, dy)
        if mag > 1.0:
            dx, dy = dx / mag, dy / mag
        p.dx, p.dy = dx, dy
        p.mode = mode if mode in (-1, 0, 1) else 0

    def equip(self, pid, slot, item):
        """Put `item` ("" = empty) into a loadout slot. Always flags the inventory for resync."""
        p = self.players.get(pid)
        if p is None:
            return False
        p.inv_dirty = True
        if isinstance(slot, bool) or not isinstance(slot, int) or not 0 <= slot < PETAL_COUNT:
            return False
        if item != "":
            item = normalize_item(item)
            if item is None:
                return False
        if p.loadout[slot] == item:
            return True
        if p.swap_cd > 0.0:
            return False
        if item:
            used_elsewhere = sum(1 for i, k in enumerate(p.loadout) if k == item and i != slot)
            if p.inventory.get(item, 0) <= used_elsewhere:
                return False
        p.loadout[slot] = item
        p.reset_petal(slot)
        p.swap_cd = EQUIP_COOLDOWN
        p.save_dirty = True
        return True

    def craft(self, pid, item):
        """CRAFT_COST unequipped copies of `item` become one copy of the next rarity tier."""
        p = self.players.get(pid)
        if p is None:
            return False
        p.inv_dirty = True
        item = normalize_item(item)
        if item is None:
            return False
        kind, rarity = parse_item(item)
        if rarity >= MAX_RARITY or p.free_count(item) < CRAFT_COST:
            return False
        upgraded = make_item(kind, rarity + 1)
        if p.inventory.get(upgraded, 0) >= INVENTORY_CAP:
            return False
        p.inventory[item] -= CRAFT_COST
        if p.inventory[item] <= 0:
            del p.inventory[item]
        p.inventory[upgraded] = p.inventory.get(upgraded, 0) + 1
        p.pickups.append(upgraded)
        p.save_dirty = True
        return True

    def respawn(self, pid):
        p = self.players.get(pid)
        if p is None or p.alive or p.dead_for < RESPAWN_DELAY:
            return False
        p.x, p.y = self._player_spawn_point()
        p.hp = PLAYER_MAX_HP
        p.alive = True
        p.dx = p.dy = 0.0
        p.reset_petals()
        p.since_hit = 999.0
        p.orbit_r = ORBIT_RADIUS[0]
        return True

    # ---- simulation ---------------------------------------------------------
    def step(self, dt):
        self.tick += 1
        for p in self.players.values():
            self._step_player(p, dt)
        self._spawn_mobs(dt)
        for m in list(self.mobs.values()):
            self._step_mob(m, dt)
        self._resolve_combat(dt)
        self._step_drops(dt)

    def _step_player(self, p, dt):
        p.swap_cd = max(0.0, p.swap_cd - dt)
        if not p.alive:
            p.dead_for += dt
            return
        p.x = _clamp(p.x + p.dx * PLAYER_SPEED * dt, PLAYER_RADIUS, WORLD_W - PLAYER_RADIUS)
        p.y = _clamp(p.y + p.dy * PLAYER_SPEED * dt, PLAYER_RADIUS, WORLD_H - PLAYER_RADIUS)
        p.angle = (p.angle + ORBIT_OMEGA * dt) % (2 * math.pi)

        target = ORBIT_RADIUS[p.mode]
        step = ORBIT_SHIFT_SPEED * dt
        p.orbit_r += _clamp(target - p.orbit_r, -step, step)

        heal = 0.0
        for i in range(PETAL_COUNT):
            item = p.loadout[i]
            if not item:
                continue
            if p.petal_timer[i] > 0.0:
                p.petal_timer[i] -= dt
                if p.petal_timer[i] <= 0.0:
                    p.reset_petal(i)
            else:
                heal += petal_stats(item)["heal"]

        p.since_hit += dt
        if p.hp < PLAYER_MAX_HP:
            if p.since_hit >= PLAYER_REGEN_DELAY:
                heal += PLAYER_REGEN
            p.hp = min(PLAYER_MAX_HP, p.hp + heal * dt)

    def _spawn_mobs(self, dt):
        self._spawn_cd -= dt
        if self._spawn_cd > 0.0 or not self.players:
            return
        counts = [0] * ZONE_COUNT
        for m in self.mobs.values():
            counts[m.tier] += 1
        open_tiers = [t for t in range(ZONE_COUNT) if counts[t] < MOB_TARGETS[t]]
        if not open_tiers:
            return
        self._spawn_cd = MOB_SPAWN_INTERVAL
        tier = min(open_tiers, key=lambda t: counts[t] / MOB_TARGETS[t])      # fill the emptiest zone first
        for _ in range(8):  # a few attempts to find a spot away from every player
            x, y = self._point_in_zone(tier)
            if all(math.hypot(x - p.x, y - p.y) >= MOB_SPAWN_MIN_DIST for p in self.players.values() if p.alive):
                kind = self.rng.choices(MOB_KINDS, MOB_WEIGHTS)[0]
                mob = Mob(self._new_id(), kind, x, y, tier)
                self.mobs[mob.id] = mob
                return

    def _nearest_alive_player(self, x, y, max_dist):
        best, best_d = None, max_dist
        for p in self.players.values():
            if not p.alive:
                continue
            d = math.hypot(p.x - x, p.y - y)
            if d <= best_d:
                best, best_d = p, d
        return best

    def _step_mob(self, m, dt):
        spec = MOB_TYPES[m.kind]
        if spec["speed"] <= 0.0:
            return
        target = self._nearest_alive_player(m.x, m.y, spec["aggro"]) if spec["aggro"] > 0.0 else None
        if target is not None:
            tx, ty, speed = target.x, target.y, spec["speed"]
        else:
            m.wander_t -= dt
            if m.wander_t <= 0.0 or math.hypot(m.wander_x - m.x, m.wander_y - m.y) < 10.0:
                m.wander_t = MOB_WANDER_INTERVAL
                m.wander_x = _clamp(m.x + self.rng.uniform(-400, 400), 50, WORLD_W - 50)
                m.wander_y = _clamp(m.y + self.rng.uniform(-400, 400), 50, WORLD_H - 50)
            tx, ty, speed = m.wander_x, m.wander_y, spec["speed"] * MOB_WANDER_SPEED_FACTOR
        d = math.hypot(tx - m.x, ty - m.y)
        # a chaser stops when it touches the body instead of walking into its centre: from there no
        # petal ring could ever reach it, while it keeps biting
        reach = d - (m.radius + PLAYER_RADIUS * MOB_CONTACT_FACTOR) if target is not None else d
        if d > 1e-6 and reach > 0.0:
            move = min(reach, speed * dt)
            m.x += (tx - m.x) / d * move
            m.y += (ty - m.y) / d * move

    def _resolve_combat(self, dt):
        for p in self.players.values():
            if not p.alive:
                continue
            for m in self.mobs.values():
                dmg = m.dps * dt
                # mob body vs player body
                if math.hypot(m.x - p.x, m.y - p.y) < m.radius + PLAYER_RADIUS:
                    p.hp -= dmg
                    p.since_hit = 0.0
                # petals vs mob body
                for i in range(PETAL_COUNT):
                    if not p.petal_alive(i):
                        continue
                    stats = petal_stats(p.loadout[i])
                    px, py = p.petal_pos(i)
                    if math.hypot(m.x - px, m.y - py) < m.radius + stats["radius"] + PETAL_HIT_MARGIN:
                        m.hp -= stats["dps"] * dt * (ATTACK_DAMAGE_MULT if p.mode == 1 else 1.0)
                        m.last_hit_by = p.id
                        p.petal_hp[i] -= dmg * (DEFEND_WEAR_MULT if p.mode == -1 else 1.0)
                        if p.petal_hp[i] <= 0.0:
                            p.petal_timer[i] = PETAL_RESPAWN
            if p.hp <= 0.0:
                p.hp = 0.0
                p.alive = False
                p.dead_for = 0.0
                p.dx = p.dy = 0.0

        for mid in [mid for mid, m in self.mobs.items() if m.hp <= 0.0]:
            self._kill_mob(self.mobs.pop(mid))

    def _kill_mob(self, m):
        killer = self.players.get(m.last_hit_by)
        if killer is not None:
            killer.kills += 1
            killer.kills_total += 1
            killer.save_dirty = True
        for kind, chance in MOB_TYPES[m.kind]["drops"]:
            if len(self.drops) < DROP_CAP and self.rng.random() < drop_chance(chance, m.tier):
                rarity = max(0, m.tier + DROP_RARITY_OFFSET)
                if rarity < MAX_RARITY and self.rng.random() < DROP_BUMP_CHANCE:
                    rarity += 1
                d = Drop(self._new_id(), make_item(kind, rarity),
                         _clamp(m.x + self.rng.uniform(-25, 25), 0, WORLD_W),
                         _clamp(m.y + self.rng.uniform(-25, 25), 0, WORLD_H))
                self.drops[d.id] = d

    def _step_drops(self, dt):
        for p in self.players.values():
            if not p.alive:
                continue
            reach = PLAYER_RADIUS + DROP_RADIUS + DROP_PICKUP_REACH
            for did, d in list(self.drops.items()):
                if math.hypot(d.x - p.x, d.y - p.y) > reach:
                    continue
                if p.inventory.get(d.item, 0) >= INVENTORY_CAP:
                    continue
                p.inventory[d.item] = p.inventory.get(d.item, 0) + 1
                p.pickups.append(d.item)
                p.inv_dirty = p.save_dirty = True
                del self.drops[did]
        for did in [did for did, d in self.drops.items() if d.ttl - dt <= 0.0]:
            del self.drops[did]
        for d in self.drops.values():
            d.ttl -= dt

    # ---- snapshots -----------------------------------------------------------
    def snapshot_for(self, pid):
        me = self.players.get(pid)
        if me is None:
            return None
        r2 = VIEW_RADIUS * VIEW_RADIUS
        players = []
        for p in self.players.values():
            if p is not me and (p.x - me.x) ** 2 + (p.y - me.y) ** 2 > r2:
                continue
            mask = 0
            for i in range(PETAL_COUNT):
                if p.alive and p.petal_alive(i):
                    mask |= 1 << i
            players.append({
                "i": p.id, "n": p.name, "x": round(p.x, 1), "y": round(p.y, 1),
                "h": round(p.hp, 1), "a": round(p.angle, 3), "r": round(p.orbit_r, 1),
                "p": mask, "l": [encode_item(it) if it else -1 for it in p.loadout],
                "k": p.kills, "d": 0 if p.alive else 1,
            })
        mobs = []
        for m in self.mobs.values():
            if (m.x - me.x) ** 2 + (m.y - me.y) ** 2 > r2:
                continue
            mobs.append({"i": m.id, "t": m.kind, "u": m.tier, "R": round(m.radius, 1),
                         "x": round(m.x, 1), "y": round(m.y, 1), "h": round(m.hp, 1), "H": round(m.max_hp, 1)})
        drops = [{"i": d.id, "k": encode_item(d.item), "x": round(d.x, 1), "y": round(d.y, 1)}
                 for d in self.drops.values() if (d.x - me.x) ** 2 + (d.y - me.y) ** 2 <= r2]
        return {"t": "s", "tick": self.tick, "me": pid, "ps": players, "ms": mobs, "ds": drops}

    def inventory_message(self, pid):
        """Private message for one player: what they own, what is equipped, what they just received."""
        p = self.players.get(pid)
        if p is None:
            return None
        msg = {"t": "inv", "inv": dict(p.inventory), "lo": list(p.loadout), "kt": p.kills_total, "got": p.pickups}
        p.pickups = []
        p.inv_dirty = False
        return msg
