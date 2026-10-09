"""Authoritative simulation for the florr-style mode.

Pure Python (no Django / asyncio) so it can be unit tested and reasoned about on its own.
All units are world units; time is in seconds. Clients only send their input (move vector and
petal mode), the server decides everything else.
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

PETAL_COUNT = 5
PETAL_RADIUS = 11.0
PETAL_HP = 12.0
PETAL_DPS = 22.0                  # damage per second dealt to a mob while overlapping
PETAL_RESPAWN = 2.0               # seconds for a broken petal to come back
ORBIT_OMEGA = 2.6                 # rad/s
ORBIT_RADIUS = {-1: 52.0, 0: 82.0, 1: 122.0}   # defend / neutral / attack
ORBIT_SHIFT_SPEED = 300.0         # how fast the orbit radius changes (units/s)

MOB_TYPES = {
    # dps: damage per second dealt to a player body or a petal it overlaps
    "beetle": {"hp": 70.0, "radius": 30.0, "speed": 120.0, "dps": 16.0, "aggro": 380.0},
}
MOB_TARGET_COUNT = 25
MOB_SPAWN_INTERVAL = 0.5          # at most one spawn per interval
MOB_SPAWN_MIN_DIST = 700.0        # never spawn closer than this to a player
MOB_WANDER_SPEED_FACTOR = 0.4
MOB_WANDER_INTERVAL = 3.0


def _clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


class Player:
    __slots__ = ("id", "name", "x", "y", "hp", "alive", "dx", "dy", "mode", "angle", "orbit_r",
                 "petal_hp", "petal_timer", "kills", "since_hit", "dead_for")

    def __init__(self, pid, name, x, y):
        self.id = pid
        self.name = name
        self.x, self.y = x, y
        self.hp = PLAYER_MAX_HP
        self.alive = True
        self.dx = self.dy = 0.0
        self.mode = 0
        self.angle = 0.0
        self.orbit_r = ORBIT_RADIUS[0]
        self.petal_hp = [PETAL_HP] * PETAL_COUNT
        self.petal_timer = [0.0] * PETAL_COUNT     # >0 while the petal is broken
        self.kills = 0
        self.since_hit = 999.0
        self.dead_for = 0.0

    def petal_pos(self, i):
        a = self.angle + i * (2 * math.pi / PETAL_COUNT)
        return self.x + self.orbit_r * math.cos(a), self.y + self.orbit_r * math.sin(a)

    def petal_alive(self, i):
        return self.petal_timer[i] <= 0.0


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


class World:
    def __init__(self, rng=None):
        self.rng = rng or random.Random()
        self.players = {}
        self.mobs = {}
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

    def add_player(self, name):
        x, y = self._random_spawn_point()
        p = Player(self._new_id(), name, x, y)
        self.players[p.id] = p
        return p

    def remove_player(self, pid):
        self.players.pop(pid, None)

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

    def respawn(self, pid):
        p = self.players.get(pid)
        if p is None or p.alive or p.dead_for < RESPAWN_DELAY:
            return False
        p.x, p.y = self._random_spawn_point()
        p.hp = PLAYER_MAX_HP
        p.alive = True
        p.dx = p.dy = 0.0
        p.petal_hp = [PETAL_HP] * PETAL_COUNT
        p.petal_timer = [0.0] * PETAL_COUNT
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

    def _step_player(self, p, dt):
        if not p.alive:
            p.dead_for += dt
            return
        p.x = _clamp(p.x + p.dx * PLAYER_SPEED * dt, PLAYER_RADIUS, WORLD_W - PLAYER_RADIUS)
        p.y = _clamp(p.y + p.dy * PLAYER_SPEED * dt, PLAYER_RADIUS, WORLD_H - PLAYER_RADIUS)
        p.angle = (p.angle + ORBIT_OMEGA * dt) % (2 * math.pi)

        target = ORBIT_RADIUS[p.mode]
        step = ORBIT_SHIFT_SPEED * dt
        p.orbit_r += _clamp(target - p.orbit_r, -step, step)

        for i in range(PETAL_COUNT):
            if p.petal_timer[i] > 0.0:
                p.petal_timer[i] -= dt
                if p.petal_timer[i] <= 0.0:
                    p.petal_timer[i] = 0.0
                    p.petal_hp[i] = PETAL_HP

        p.since_hit += dt
        if p.since_hit >= PLAYER_REGEN_DELAY and p.hp < PLAYER_MAX_HP:
            p.hp = min(PLAYER_MAX_HP, p.hp + PLAYER_REGEN * dt)

    def _spawn_mobs(self, dt):
        self._spawn_cd -= dt
        if self._spawn_cd > 0.0 or len(self.mobs) >= MOB_TARGET_COUNT or not self.players:
            return
        self._spawn_cd = MOB_SPAWN_INTERVAL
        for _ in range(8):  # a few attempts to find a spot away from every player
            x, y = self._random_spawn_point()
            if all(math.hypot(x - p.x, y - p.y) >= MOB_SPAWN_MIN_DIST for p in self.players.values() if p.alive):
                mob = Mob(self._new_id(), "beetle", x, y)
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
        target = self._nearest_alive_player(m.x, m.y, spec["aggro"])
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
        if d > 1e-6:
            move = min(d, speed * dt)
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
                    px, py = p.petal_pos(i)
                    if math.hypot(m.x - px, m.y - py) < spec["radius"] + PETAL_RADIUS:
                        m.hp -= PETAL_DPS * dt
                        m.last_hit_by = p.id
                        p.petal_hp[i] -= dmg
                        if p.petal_hp[i] <= 0.0:
                            p.petal_timer[i] = PETAL_RESPAWN
            if p.hp <= 0.0:
                p.hp = 0.0
                p.alive = False
                p.dead_for = 0.0
                p.dx = p.dy = 0.0

        for mid in [mid for mid, m in self.mobs.items() if m.hp <= 0.0]:
            killer = self.players.get(self.mobs[mid].last_hit_by)
            if killer is not None:
                killer.kills += 1
            del self.mobs[mid]

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
                "p": mask, "k": p.kills, "d": 0 if p.alive else 1,
            })
        mobs = []
        for m in self.mobs.values():
            if (m.x - me.x) ** 2 + (m.y - me.y) ** 2 > r2:
                continue
            mobs.append({"i": m.id, "t": m.kind, "x": round(m.x, 1), "y": round(m.y, 1),
                         "h": round(m.hp, 1), "H": m.max_hp})
        return {"t": "s", "tick": self.tick, "me": pid, "ps": players, "ms": mobs}
