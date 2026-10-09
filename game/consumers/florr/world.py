"""Authoritative simulation for the florr-style mode.

Pure Python (no Django / asyncio) so it can be unit tested and reasoned about on its own.
All units are world units; time is in seconds. Clients only send their input (move vector, petal
mode, equip requests); the server decides everything else. Persistence is done by the caller
(see store.py / hub.py): this module only keeps `save_dirty` / `inv_dirty` flags on players.
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
PETAL_HIT_MARGIN = 6.0            # petals hit a bit beyond their drawn size
ATTACK_DAMAGE_MULT = 1.5          # petal damage while the player holds "attack"
DEFEND_WEAR_MULT = 0.5            # damage petals take while the player holds "defend"
ORBIT_SHIFT_SPEED = 300.0         # how fast the orbit radius changes (units/s)
EQUIP_COOLDOWN = 0.4              # seconds between loadout changes

# dps: damage per second dealt to a mob it overlaps; hp: damage a petal absorbs before breaking;
# heal: hp per second given to the owner while the petal is intact.
PETAL_TYPES = {
    "basic":   {"name": "花瓣", "color": "#ffffff", "radius": 11.0, "hp": 12.0, "dps": 44.0, "heal": 0.0},
    "stinger": {"name": "尖刺", "color": "#2b2b2b", "radius": 9.0,  "hp": 6.0,  "dps": 96.0, "heal": 0.0},
    "heavy":   {"name": "沉石", "color": "#9a9a9a", "radius": 15.0, "hp": 40.0, "dps": 28.0, "heal": 0.0},
    "rose":    {"name": "玫瑰", "color": "#ff7fb0", "radius": 10.0, "hp": 9.0,  "dps": 8.0,  "heal": 2.5},
}
PETAL_ORDER = list(PETAL_TYPES)   # index in this list is the compact id used in snapshots
STARTER_INVENTORY = {"basic": 5}
STARTER_LOADOUT = ["basic"] * PETAL_COUNT
INVENTORY_CAP = 9999

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
MOB_TARGET_COUNT = 30
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


def sanitize_inventory(raw):
    """Keep only known petal kinds with sane counts (used for data coming from the database)."""
    inv = {}
    for kind, count in (raw or {}).items():
        if kind in PETAL_TYPES:
            try:
                count = int(count)
            except (TypeError, ValueError):
                continue
            if count > 0:
                inv[kind] = min(count, INVENTORY_CAP)
    return inv


def sanitize_loadout(raw, inventory):
    """A loadout is PETAL_COUNT slots; each filled slot needs its own owned copy of that petal."""
    loadout = []
    used = {}
    for kind in list(raw or [])[:PETAL_COUNT]:
        if kind in PETAL_TYPES and used.get(kind, 0) < inventory.get(kind, 0):
            used[kind] = used.get(kind, 0) + 1
            loadout.append(kind)
        else:
            loadout.append("")
    loadout += [""] * (PETAL_COUNT - len(loadout))
    return loadout


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
        self.pickups = []              # kinds picked up since the client was last told

    def reset_petals(self):
        for i in range(PETAL_COUNT):
            self.reset_petal(i)

    def reset_petal(self, i):
        kind = self.loadout[i]
        self.petal_hp[i] = PETAL_TYPES[kind]["hp"] if kind else 0.0
        self.petal_timer[i] = 0.0

    def petal_alive(self, i):
        return bool(self.loadout[i]) and self.petal_timer[i] <= 0.0

    def petal_pos(self, i):
        a = self.angle + i * (2 * math.pi / PETAL_COUNT)
        return self.x + self.orbit_r * math.cos(a), self.y + self.orbit_r * math.sin(a)


class Mob:
    __slots__ = ("id", "kind", "x", "y", "hp", "max_hp", "wander_x", "wander_y", "wander_t", "last_hit_by")

    def __init__(self, mid, kind, x, y):
        spec = MOB_TYPES[kind]
        self.id = mid
        self.kind = kind
        self.x, self.y = x, y
        self.hp = self.max_hp = spec["hp"]
        self.wander_x, self.wander_y, self.wander_t = x, y, 0.0
        self.last_hit_by = None


class Drop:
    __slots__ = ("id", "kind", "x", "y", "ttl")

    def __init__(self, did, kind, x, y):
        self.id, self.kind, self.x, self.y, self.ttl = did, kind, x, y, DROP_TTL


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

    def _random_spawn_point(self):
        margin = 200.0
        return (self.rng.uniform(margin, WORLD_W - margin), self.rng.uniform(margin, WORLD_H - margin))

    def add_player(self, name, inventory=None, loadout=None, kills_total=0):
        """`inventory`/`loadout` come from the database; None means a brand new player."""
        if inventory is None:
            inventory = dict(STARTER_INVENTORY)
            loadout = list(STARTER_LOADOUT)
        inventory = sanitize_inventory(inventory)
        loadout = sanitize_loadout(loadout, inventory)
        x, y = self._random_spawn_point()
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

    def equip(self, pid, slot, kind):
        """Put `kind` ("" = empty) into a loadout slot. Always flags the inventory for resync."""
        p = self.players.get(pid)
        if p is None:
            return False
        p.inv_dirty = True
        if isinstance(slot, bool) or not isinstance(slot, int) or not 0 <= slot < PETAL_COUNT:
            return False
        if not isinstance(kind, str) or (kind and kind not in PETAL_TYPES):
            return False
        if p.loadout[slot] == kind:
            return True
        if p.swap_cd > 0.0:
            return False
        if kind:
            used_elsewhere = sum(1 for i, k in enumerate(p.loadout) if k == kind and i != slot)
            if p.inventory.get(kind, 0) <= used_elsewhere:
                return False
        p.loadout[slot] = kind
        p.reset_petal(slot)
        p.swap_cd = EQUIP_COOLDOWN
        p.save_dirty = True
        return True

    def respawn(self, pid):
        p = self.players.get(pid)
        if p is None or p.alive or p.dead_for < RESPAWN_DELAY:
            return False
        p.x, p.y = self._random_spawn_point()
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
            kind = p.loadout[i]
            if not kind:
                continue
            if p.petal_timer[i] > 0.0:
                p.petal_timer[i] -= dt
                if p.petal_timer[i] <= 0.0:
                    p.reset_petal(i)
            else:
                heal += PETAL_TYPES[kind]["heal"]

        p.since_hit += dt
        if p.hp < PLAYER_MAX_HP:
            if p.since_hit >= PLAYER_REGEN_DELAY:
                heal += PLAYER_REGEN
            p.hp = min(PLAYER_MAX_HP, p.hp + heal * dt)

    def _spawn_mobs(self, dt):
        self._spawn_cd -= dt
        if self._spawn_cd > 0.0 or len(self.mobs) >= MOB_TARGET_COUNT or not self.players:
            return
        self._spawn_cd = MOB_SPAWN_INTERVAL
        for _ in range(8):  # a few attempts to find a spot away from every player
            x, y = self._random_spawn_point()
            if all(math.hypot(x - p.x, y - p.y) >= MOB_SPAWN_MIN_DIST for p in self.players.values() if p.alive):
                kind = self.rng.choices(MOB_KINDS, MOB_WEIGHTS)[0]
                mob = Mob(self._new_id(), kind, x, y)
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
        reach = d - (spec["radius"] + PLAYER_RADIUS * MOB_CONTACT_FACTOR) if target is not None else d
        if d > 1e-6 and reach > 0.0:
            move = min(reach, speed * dt)
            m.x += (tx - m.x) / d * move
            m.y += (ty - m.y) / d * move

    def _resolve_combat(self, dt):
        for p in self.players.values():
            if not p.alive:
                continue
            for m in self.mobs.values():
                spec = MOB_TYPES[m.kind]
                dmg = spec["dps"] * dt
                # mob body vs player body
                if math.hypot(m.x - p.x, m.y - p.y) < spec["radius"] + PLAYER_RADIUS:
                    p.hp -= dmg
                    p.since_hit = 0.0
                # petals vs mob body
                for i in range(PETAL_COUNT):
                    if not p.petal_alive(i):
                        continue
                    pt = PETAL_TYPES[p.loadout[i]]
                    px, py = p.petal_pos(i)
                    if math.hypot(m.x - px, m.y - py) < spec["radius"] + pt["radius"] + PETAL_HIT_MARGIN:
                        m.hp -= pt["dps"] * dt * (ATTACK_DAMAGE_MULT if p.mode == 1 else 1.0)
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
            if len(self.drops) < DROP_CAP and self.rng.random() < chance:
                d = Drop(self._new_id(), kind,
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
                if p.inventory.get(d.kind, 0) >= INVENTORY_CAP:
                    continue
                p.inventory[d.kind] = p.inventory.get(d.kind, 0) + 1
                p.pickups.append(d.kind)
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
                "p": mask, "l": [PETAL_ORDER.index(k) if k else -1 for k in p.loadout],
                "k": p.kills, "d": 0 if p.alive else 1,
            })
        mobs = []
        for m in self.mobs.values():
            if (m.x - me.x) ** 2 + (m.y - me.y) ** 2 > r2:
                continue
            mobs.append({"i": m.id, "t": m.kind, "x": round(m.x, 1), "y": round(m.y, 1),
                         "h": round(m.hp, 1), "H": m.max_hp})
        drops = [{"i": d.id, "k": PETAL_ORDER.index(d.kind), "x": round(d.x, 1), "y": round(d.y, 1)}
                 for d in self.drops.values() if (d.x - me.x) ** 2 + (d.y - me.y) ** 2 <= r2]
        return {"t": "s", "tick": self.tick, "me": pid, "ps": players, "ms": mobs, "ds": drops}

    def inventory_message(self, pid):
        """Private message for one player: what they own, what is equipped, what they just picked up."""
        p = self.players.get(pid)
        if p is None:
            return None
        msg = {"t": "inv", "inv": dict(p.inventory), "lo": list(p.loadout), "kt": p.kills_total, "got": p.pickups}
        p.pickups = []
        p.inv_dirty = False
        return msg
