import asyncio
import functools
import json
import math
import random
import unittest

from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import AnonymousUser, User
from django.test import TransactionTestCase, override_settings

from game.consumers.florr import world as w
from game.consumers.florr.hub import hub
from game.consumers.florr.index import FlorrPlayer
from game.consumers.florr.world import Drop, Mob, World
from game.models.florr.florr import FlorrPetal, FlorrProfile
from game.models.player.player import Player


class FixedRandom(random.Random):
    """Random whose random() always returns `value`, so drop rolls are deterministic."""
    def __init__(self, value, seed=1):
        super().__init__(seed)
        self.value = value

    def random(self):
        return self.value


def make_world(rng=None):
    w_ = World(rng=rng or random.Random(1234))
    w_._spawn_cd = 10 ** 9      # tests place their own mobs
    return w_


def place(player, x, y):
    player.x, player.y = x, y


def add_mob(world, kind, x, y, hp=None):
    mob = Mob(world._new_id(), kind, x, y)
    if hp is not None:
        mob.hp = mob.max_hp = hp
    world.mobs[mob.id] = mob
    return mob


class FlorrWorldTests(unittest.TestCase):
    # ---- movement / input -------------------------------------------------------
    def test_movement_is_clamped_to_the_world(self):
        world = make_world()
        p = world.add_player("a")
        place(p, w.WORLD_W - 5, 100)
        world.set_input(p.id, 1, 0, 0)
        for _ in range(40):
            world.step(0.05)
        self.assertLessEqual(p.x, w.WORLD_W - w.PLAYER_RADIUS)

    def test_input_is_sanitised(self):
        world = make_world()
        p = world.add_player("a")
        world.set_input(p.id, 50, 50, 99)           # oversized vector, invalid mode
        self.assertAlmostEqual(math.hypot(p.dx, p.dy), 1.0)
        self.assertEqual(p.mode, 0)
        world.set_input(p.id, float("nan"), 0, 1)   # ignored
        world.set_input(p.id, "x", 0, 1)            # ignored
        self.assertAlmostEqual(math.hypot(p.dx, p.dy), 1.0)

    def test_speed_is_limited_regardless_of_input(self):
        world = make_world()
        p = world.add_player("a")
        place(p, 1000, 1000)
        world.set_input(p.id, 1e9, 0, 0)
        world.step(1.0)
        self.assertAlmostEqual(p.x, 1000 + w.PLAYER_SPEED, places=3)

    def test_petals_extend_and_retract(self):
        world = make_world()
        p = world.add_player("a")
        world.set_input(p.id, 0, 0, 1)
        for _ in range(40):
            world.step(0.05)
        self.assertAlmostEqual(p.orbit_r, w.ORBIT_RADIUS[1])
        world.set_input(p.id, 0, 0, -1)
        for _ in range(40):
            world.step(0.05)
        self.assertAlmostEqual(p.orbit_r, w.ORBIT_RADIUS[-1])

    # ---- mobs ---------------------------------------------------------------------
    def test_mobs_spawn_up_to_the_target_and_never_near_a_player(self):
        for seed in range(20):
            world = World(rng=random.Random(seed))
            p = world.add_player("a")
            place(p, 1500, 1500)
            world.step(w.MOB_SPAWN_INTERVAL + 0.01)       # exactly one spawn
            self.assertEqual(len(world.mobs), 1)
            for m in world.mobs.values():
                self.assertGreaterEqual(math.hypot(m.x - p.x, m.y - p.y), w.MOB_SPAWN_MIN_DIST)
        world = World(rng=random.Random(1234))
        place(world.add_player("a"), 1500, 1500)
        for _ in range(int(w.MOB_TARGET_COUNT * 2 * w.MOB_SPAWN_INTERVAL / 0.1) + 50):
            world.step(0.1)
        self.assertLessEqual(len(world.mobs), w.MOB_TARGET_COUNT)
        self.assertGreater(len(world.mobs), 10)

    def test_every_mob_kind_can_spawn(self):
        world = World(rng=random.Random(99))
        place(world.add_player("a"), 1500, 1500)
        seen = set()
        for _ in range(3000):
            world.step(0.5)
            seen |= {m.kind for m in world.mobs.values()}
            world.mobs.clear()
        self.assertEqual(seen, set(w.MOB_TYPES))

    def test_no_mobs_spawn_without_players(self):
        world = World(rng=random.Random(1))
        for _ in range(100):
            world.step(0.1)
        self.assertEqual(len(world.mobs), 0)

    def test_rocks_never_move_and_ladybugs_never_chase(self):
        world = make_world()
        p = world.add_player("a")
        place(p, 1500, 1500)
        rock = add_mob(world, "rock", 1700, 1500)
        ladybug = add_mob(world, "ladybug", 1500, 1700)
        rock_pos = (rock.x, rock.y)
        ladybug_start = math.hypot(ladybug.x - p.x, ladybug.y - p.y)
        for _ in range(20):          # 1 second: a chaser at wasp/beetle speed would have closed in
            world.step(0.05)
        self.assertEqual((rock.x, rock.y), rock_pos)
        # wander speed is at most 36 u/s, so in 1s a ladybug cannot have come much closer
        self.assertGreater(math.hypot(ladybug.x - p.x, ladybug.y - p.y), ladybug_start - 40)

    def test_wasps_and_beetles_chase_within_aggro_range(self):
        for kind in ("wasp", "beetle"):
            world = make_world()
            p = world.add_player("a")
            place(p, 1500, 1500)
            mob = add_mob(world, kind, 1500 + w.MOB_TYPES[kind]["aggro"] - 20, 1500)
            before = math.hypot(mob.x - p.x, mob.y - p.y)
            for _ in range(10):
                world.step(0.05)
            self.assertLess(math.hypot(mob.x - p.x, mob.y - p.y), before - 20, kind)

    def test_chasers_stop_at_the_body_instead_of_walking_into_it(self):
        for kind in ("beetle", "wasp"):
            world = make_world()
            p = world.add_player("a", inventory={}, loadout=[])        # no petals: nothing kills the mob
            place(p, 1500, 1500)
            mob = add_mob(world, kind, 1500 + 200, 1500, hp=10_000)
            p.hp = 10 ** 6                                              # survive the biting
            for _ in range(100):
                world.step(0.05)
                p.hp = 10 ** 6
            contact = w.MOB_TYPES[kind]["radius"] + w.PLAYER_RADIUS * w.MOB_CONTACT_FACTOR
            self.assertAlmostEqual(math.hypot(mob.x - p.x, mob.y - p.y), contact, delta=1.0, msg=kind)

    def test_every_ring_reaches_a_mob_hugging_the_body(self):
        """If a mode could not touch the smallest chaser, holding that button would lose fights outright."""
        wasp = w.MOB_TYPES["wasp"]
        contact = wasp["radius"] + w.PLAYER_RADIUS * w.MOB_CONTACT_FACTOR
        for mode in (-1, 0, 1):
            for kind in w.PETAL_TYPES:
                world = make_world()
                p = world.add_player("a", inventory={kind: 5}, loadout=[kind] * 5)
                place(p, 1500, 1500)
                p.orbit_r = w.ORBIT_RADIUS[mode]
                world.set_input(p.id, 0, 0, mode)
                mob = add_mob(world, "wasp", 1500 + contact, 1500, hp=10_000)
                for _ in range(int(2 * math.pi / w.ORBIT_OMEGA / 0.02) + 5):   # one full petal revolution
                    mob.x, mob.y = p.x + contact, p.y
                    world.step(0.02)
                self.assertLess(mob.hp, 10_000, f"mode {mode} with {kind} never touched a hugging wasp")

    def test_attack_hits_harder_and_defend_wears_petals_slower(self):
        def run(mode):
            world, p, mob = self._petal_mob_overlap("basic")
            world.set_input(p.id, 0, 0, mode)
            p.orbit_r = w.ORBIT_RADIUS[mode]
            mob.x, mob.y = p.petal_pos(0)
            world.step(0.05)
            return 10_000 - mob.hp, w.PETAL_TYPES["basic"]["hp"] - p.petal_hp[0]
        neutral_dmg, neutral_wear = run(0)
        attack_dmg, _ = run(1)
        _, defend_wear = run(-1)
        self.assertAlmostEqual(attack_dmg, neutral_dmg * w.ATTACK_DAMAGE_MULT, places=3)
        self.assertAlmostEqual(defend_wear, neutral_wear * w.DEFEND_WEAR_MULT, places=3)

    # ---- combat ----------------------------------------------------------------------
    def _petal_mob_overlap(self, loadout_kind, mob_kind="rock", mob_hp=10_000):
        world = make_world()
        p = world.add_player("a", inventory={loadout_kind: 5}, loadout=[loadout_kind] * 5)
        place(p, 1500, 1500)
        px, py = p.petal_pos(0)
        mob = add_mob(world, mob_kind, px, py, hp=mob_hp)
        return world, p, mob

    def test_petal_types_differ_in_damage(self):
        dealt = {}
        for kind in ("basic", "stinger", "heavy", "rose"):
            world, p, mob = self._petal_mob_overlap(kind)
            mob.x, mob.y = p.petal_pos(0)
            world.step(0.05)
            dealt[kind] = 10_000 - mob.hp
        self.assertGreater(dealt["stinger"], dealt["basic"])
        self.assertGreater(dealt["basic"], dealt["heavy"])
        self.assertGreater(dealt["heavy"], dealt["rose"])

    def test_heavy_petals_outlast_stingers(self):
        broken_after = {}
        for kind in ("stinger", "heavy"):
            world, p, mob = self._petal_mob_overlap(kind)
            for step in range(1, 400):
                mob.x, mob.y = p.petal_pos(0)
                world.step(0.05)
                if not p.petal_alive(0):
                    broken_after[kind] = step
                    break
        self.assertGreater(broken_after["heavy"], broken_after["stinger"])

    def test_broken_petals_come_back(self):
        world, p, mob = self._petal_mob_overlap("basic")
        for _ in range(100):
            mob.x, mob.y = p.petal_pos(0)
            world.step(0.05)
            if not p.petal_alive(0):
                break
        self.assertFalse(p.petal_alive(0))
        del world.mobs[mob.id]
        for _ in range(int(w.PETAL_RESPAWN / 0.05) + 2):
            world.step(0.05)
        self.assertTrue(p.petal_alive(0))
        self.assertEqual(p.petal_hp[0], w.PETAL_TYPES["basic"]["hp"])

    def test_roses_heal_their_owner(self):
        world = make_world()
        p = world.add_player("a", inventory={"rose": 5}, loadout=["rose"] * 5)
        p.hp, p.since_hit = 50.0, 0.0           # in combat: no natural regen, only roses
        world.step(1.0)
        self.assertAlmostEqual(p.hp, 50.0 + 5 * w.PETAL_TYPES["rose"]["heal"], places=3)
        q = world.add_player("b")
        q.hp, q.since_hit = 50.0, 0.0
        world.step(1.0)
        self.assertEqual(q.hp, 50.0)

    def test_player_dies_then_can_respawn_after_delay(self):
        world = make_world()
        p = world.add_player("a")
        place(p, 1500, 1500)
        mob = add_mob(world, "beetle", p.x, p.y, hp=10_000)
        for _ in range(400):
            mob.x, mob.y = p.x, p.y
            world.step(0.05)
            if not p.alive:
                break
        self.assertFalse(p.alive)
        self.assertEqual(p.hp, 0.0)
        self.assertFalse(world.respawn(p.id))            # too early
        for _ in range(int(w.RESPAWN_DELAY / 0.05) + 2):
            world.step(0.05)
        self.assertTrue(world.respawn(p.id))
        self.assertTrue(p.alive)
        self.assertEqual(p.hp, w.PLAYER_MAX_HP)
        self.assertEqual(sorted(p.loadout), ["basic"] * 5)   # nothing is lost on death
        self.assertFalse(world.respawn(p.id))            # already alive

    def test_regen_only_after_out_of_combat(self):
        world = make_world()
        p = world.add_player("a")
        p.hp = 50.0
        p.since_hit = 0.0
        world.step(1.0)
        self.assertEqual(p.hp, 50.0)
        for _ in range(int(w.PLAYER_REGEN_DELAY) + 1):
            world.step(1.0)
        self.assertGreater(p.hp, 50.0)

    # ---- kills and drops ------------------------------------------------------------
    def test_kill_is_credited_and_flags_progress_for_saving(self):
        world, p, mob = self._petal_mob_overlap("basic", mob_kind="ladybug", mob_hp=1.0)
        mob.x, mob.y = p.petal_pos(0)
        world.step(0.05)
        self.assertNotIn(mob.id, world.mobs)
        self.assertEqual((p.kills, p.kills_total), (1, 1))
        self.assertTrue(p.save_dirty)

    def test_a_dead_mob_drops_what_its_table_says(self):
        for roll, expect_drops in ((0.0, True), (0.999, False)):
            world = make_world(FixedRandom(roll))
            mob = add_mob(world, "rock", 100, 100)     # nobody around, so nothing gets picked up
            del world.mobs[mob.id]
            world._kill_mob(mob)
            kinds = sorted(d.kind for d in world.drops.values())
            if expect_drops:
                self.assertEqual(kinds, sorted(k for k, _ in w.MOB_TYPES["rock"]["drops"]))
            else:
                self.assertEqual(kinds, [])

    def test_walking_over_a_drop_picks_it_up(self):
        world = make_world()
        p = world.add_player("a")
        place(p, 1500, 1500)
        world.drops[500] = Drop(500, "stinger", 1500 + 30, 1500)
        far = Drop(501, "rose", 1500 + 400, 1500)
        world.drops[501] = far
        p.inv_dirty = False
        world.step(0.05)
        self.assertEqual(p.inventory.get("stinger"), 1)
        self.assertNotIn(500, world.drops)
        self.assertIn(501, world.drops)
        self.assertEqual(p.pickups, ["stinger"])
        self.assertTrue(p.inv_dirty and p.save_dirty)
        msg = world.inventory_message(p.id)
        self.assertEqual(msg["got"], ["stinger"])
        self.assertEqual(msg["inv"]["stinger"], 1)
        self.assertFalse(p.inv_dirty)
        self.assertEqual(world.inventory_message(p.id)["got"], [])

    def test_dead_players_cannot_pick_up(self):
        world = make_world()
        p = world.add_player("a")
        place(p, 1500, 1500)
        p.alive = False
        world.drops[500] = Drop(500, "stinger", 1500, 1500)
        world.step(0.05)
        self.assertIn(500, world.drops)

    def test_only_one_player_gets_a_drop(self):
        world = make_world()
        a, b = world.add_player("a"), world.add_player("b")
        place(a, 1500, 1500)
        place(b, 1505, 1500)
        world.drops[500] = Drop(500, "heavy", 1500, 1500)
        world.step(0.05)
        self.assertEqual(a.inventory.get("heavy", 0) + b.inventory.get("heavy", 0), 1)

    def test_drops_expire_and_are_capped(self):
        world = make_world()
        world.drops[1] = Drop(1, "basic", 10, 10)
        for _ in range(int(w.DROP_TTL / 0.5) + 2):
            world.step(0.5)
        self.assertEqual(world.drops, {})
        world.rng = FixedRandom(0.0)
        for i in range(w.DROP_CAP):
            world.drops[10_000 + i] = Drop(10_000 + i, "basic", 10, 10)
        world._kill_mob(Mob(1, "rock", 100, 100))
        self.assertEqual(len(world.drops), w.DROP_CAP)

    def test_inventory_cap(self):
        world = make_world()
        p = world.add_player("a", inventory={"basic": w.INVENTORY_CAP}, loadout=["basic"] * 5)
        place(p, 1500, 1500)
        world.drops[1] = Drop(1, "basic", 1500, 1500)
        world.step(0.05)
        self.assertEqual(p.inventory["basic"], w.INVENTORY_CAP)
        self.assertIn(1, world.drops)

    # ---- loadout ---------------------------------------------------------------------
    def _owner(self, inventory):
        world = make_world()
        p = world.add_player("a", inventory=inventory, loadout=[])
        return world, p

    def test_new_players_get_the_starter_kit(self):
        p = make_world().add_player("a")
        self.assertEqual(p.inventory, {"basic": 5})
        self.assertEqual(p.loadout, ["basic"] * 5)

    def test_equip_rules(self):
        world, p = self._owner({"basic": 2, "rose": 1})
        self.assertEqual(p.loadout, [""] * 5)
        self.assertTrue(world.equip(p.id, 0, "basic"))
        self.assertEqual(p.loadout[0], "basic")
        self.assertTrue(p.save_dirty)
        world.step(1.0)                                        # let the swap cooldown pass
        self.assertTrue(world.equip(p.id, 1, "basic"))
        world.step(1.0)
        self.assertFalse(world.equip(p.id, 2, "basic"), "only two copies owned")
        self.assertFalse(world.equip(p.id, 2, "stinger"), "not owned")
        self.assertFalse(world.equip(p.id, 2, "nonsense"), "unknown kind")
        self.assertFalse(world.equip(p.id, 5, "rose"), "slot out of range")
        self.assertFalse(world.equip(p.id, -1, "rose"))
        self.assertFalse(world.equip(p.id, True, "rose"), "bool is not a slot")
        self.assertFalse(world.equip(p.id, "0", "rose"))
        self.assertFalse(world.equip(p.id, 2, None))
        self.assertTrue(world.equip(p.id, 2, "rose"))
        world.step(1.0)
        self.assertTrue(world.equip(p.id, 0, ""), "unequip")
        self.assertEqual(p.loadout, ["", "basic", "rose", "", ""])
        self.assertFalse(p.petal_alive(0))

    def test_equip_swaps_use_the_same_copy(self):
        world, p = self._owner({"basic": 1})
        world.equip(p.id, 0, "basic")
        world.step(1.0)
        self.assertFalse(world.equip(p.id, 1, "basic"), "the single copy is already in slot 0")
        self.assertTrue(world.equip(p.id, 0, "basic"), "re-equipping the same kind is a no-op")

    def test_equip_has_a_cooldown_and_resets_the_petal(self):
        world, p = self._owner({"basic": 5, "rose": 5})
        world.equip(p.id, 0, "basic")
        self.assertFalse(world.equip(p.id, 1, "basic"), "cooldown")
        world.step(w.EQUIP_COOLDOWN + 0.01)
        p.loadout[3] = "basic"
        p.petal_hp[3] = 1.0
        self.assertTrue(world.equip(p.id, 3, "rose"))
        self.assertEqual(p.petal_hp[3], w.PETAL_TYPES["rose"]["hp"])

    def test_failed_equip_still_asks_the_client_to_resync(self):
        world, p = self._owner({"basic": 1})
        p.inv_dirty = False
        self.assertFalse(world.equip(p.id, 0, "stinger"))
        self.assertTrue(p.inv_dirty)

    def test_stored_data_is_sanitised_on_load(self):
        world = make_world()
        p = world.add_player("a", inventory={"basic": 2, "ghost": 5, "rose": -3, "heavy": "x", "stinger": "4"},
                             loadout=["basic", "basic", "basic", "ghost", "stinger", "rose", "rose"])
        self.assertEqual(p.inventory, {"basic": 2, "stinger": 4})
        self.assertEqual(p.loadout, ["basic", "basic", "", "", "stinger"])
        self.assertEqual(len(p.loadout), w.PETAL_COUNT)
        self.assertEqual(w.sanitize_loadout(None, {}), [""] * w.PETAL_COUNT)

    def test_a_player_with_an_empty_loadout_deals_no_damage(self):
        world = make_world()
        p = world.add_player("a", inventory={"basic": 5}, loadout=[])
        place(p, 1500, 1500)
        mob = add_mob(world, "rock", 1500 + p.orbit_r, 1500, hp=100)
        for _ in range(20):
            world.step(0.05)
        self.assertEqual(mob.hp, 100)

    # ---- snapshots -----------------------------------------------------------------
    def test_snapshot_only_contains_what_is_in_view(self):
        world = make_world()
        me = world.add_player("me")
        near = world.add_player("near")
        far = world.add_player("far")
        place(me, 1000, 1000)
        place(near, 1500, 1000)
        place(far, 1000 + w.VIEW_RADIUS + 50, 1000)
        add_mob(world, "beetle", 1000, 1200).id
        far_mob = add_mob(world, "beetle", 1000, 1000 + w.VIEW_RADIUS + 50)
        world.drops[900] = Drop(900, "rose", 1000, 1100)
        world.drops[901] = Drop(901, "rose", 1000, 1000 + w.VIEW_RADIUS + 50)
        snap = world.snapshot_for(me.id)
        self.assertEqual({p["i"] for p in snap["ps"]}, {me.id, near.id})
        self.assertNotIn(far_mob.id, {m["i"] for m in snap["ms"]})
        self.assertEqual(len(snap["ms"]), 1)
        self.assertEqual([d["i"] for d in snap["ds"]], [900])
        self.assertEqual(snap["ds"][0]["k"], w.PETAL_ORDER.index("rose"))
        mine = next(p for p in snap["ps"] if p["i"] == me.id)
        self.assertEqual(mine["l"], [w.PETAL_ORDER.index("basic")] * 5)
        json.dumps(snap)       # must be serialisable
        self.assertIsNone(world.snapshot_for(99999))

    def test_snapshot_marks_empty_and_broken_slots(self):
        world = make_world()
        p = world.add_player("a", inventory={"basic": 2}, loadout=["basic", "", "basic"])
        p.petal_timer[2] = 1.0
        snap = world.snapshot_for(p.id)
        mine = snap["ps"][0]
        self.assertEqual(mine["l"][1], -1)
        self.assertEqual(mine["p"], 0b00001)


def run_async_db(fn, *args, **kwargs):
    return database_sync_to_async(fn)(*args, **kwargs)


def with_cleanup(test):
    """Async tests must close their sockets and stop the hub loop inside their own event loop."""
    @functools.wraps(test)
    async def wrapper(self):
        try:
            await test(self)
        finally:
            for communicator in self._open:
                await communicator.disconnect()
            if hub._task is not None:
                hub._task.cancel()
    return wrapper


# TransactionTestCase (not unittest's IsolatedAsyncioTestCase): the Django test runner only creates
# the throw-away test database for Django test cases, otherwise these tests would hit db.sqlite3.
@override_settings(CHANNEL_LAYERS={"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
class FlorrConsumerTests(TransactionTestCase):
    """WebSocket + database against the test database."""

    def setUp(self):
        self._reset_hub()

    def tearDown(self):
        self._reset_hub()

    def _reset_hub(self):
        hub.world = World(rng=random.Random(5))
        hub.world._spawn_cd = 10 ** 9
        hub.clients.clear()
        hub.by_name.clear()
        hub._task = None
        hub._flush_task = None
        self._open = []

    async def _make_user(self, username):
        return await run_async_db(User.objects.create_user, username=username, password="x")

    async def _connect(self, user):
        communicator = WebsocketCommunicator(FlorrPlayer.as_asgi(), "/wss/florr/")
        communicator.scope["user"] = user
        connected, code = await communicator.connect()
        if connected:
            self._open.append(communicator)
        return communicator, connected, code

    async def _next(self, communicator, kind, tries=40):
        for _ in range(tries):
            msg = json.loads(await communicator.receive_from(timeout=2))
            if msg["t"] == kind:
                return msg
        self.fail(f"no {kind!r} message received")

    async def _db_inventory(self, username):
        def read():
            player = Player.objects.get(user__username=username)
            return (dict(FlorrPetal.objects.filter(player=player).values_list("kind", "count")),
                    FlorrProfile.objects.get(player=player))
        return await run_async_db(read)

    @with_cleanup
    async def test_anonymous_users_are_rejected(self):
        communicator, connected, code = await self._connect(AnonymousUser())
        self.assertFalse(connected)
        self.assertEqual(code, 4401)

    @with_cleanup
    async def test_welcome_first_then_starter_inventory_and_state(self):
        user = await self._make_user("fl_alice")
        communicator, connected, _ = await self._connect(user)
        self.assertTrue(connected)
        welcome = json.loads(await communicator.receive_from(timeout=2))
        self.assertEqual(welcome["t"], "welcome")
        self.assertEqual([p["id"] for p in welcome["petals"]], w.PETAL_ORDER)
        self.assertEqual(set(welcome["mobs"]), set(w.MOB_TYPES))
        inv = await self._next(communicator, "inv")
        self.assertEqual(inv["inv"], {"basic": 5})
        self.assertEqual(inv["lo"], ["basic"] * 5)
        state = await self._next(communicator, "s")
        me = next(p for p in state["ps"] if p["i"] == welcome["id"])
        self.assertEqual(me["n"], "fl_alice")
        inventory, profile = await self._db_inventory("fl_alice")
        self.assertEqual(inventory, {"basic": 5})
        self.assertEqual(profile.loadout, ",".join(["basic"] * 5))

    @with_cleanup
    async def test_input_moves_the_player_and_garbage_is_ignored(self):
        user = await self._make_user("fl_bob")
        communicator, _, _ = await self._connect(user)
        welcome = json.loads(await communicator.receive_from(timeout=2))
        player = hub.world.players[welcome["id"]]
        player.x, player.y = 1000.0, 1000.0
        for junk in ("not json", json.dumps([1, 2, 3]), "x" * 5000, json.dumps({"t": "equip", "slot": "a", "kind": 3}),
                     json.dumps({"t": "equip"}), json.dumps({"t": 5})):
            await communicator.send_to(text_data=junk)
        await communicator.send_to(text_data=json.dumps({"t": "in", "dx": 1, "dy": 0, "m": 1}))
        await asyncio.sleep(0.5)
        self.assertGreater(player.x, 1000.0)
        self.assertEqual(player.mode, 1)

    @with_cleanup
    async def test_pickups_are_saved_on_disconnect_and_restored_next_time(self):
        user = await self._make_user("fl_carol")
        first, _, _ = await self._connect(user)
        welcome = await self._next(first, "welcome")
        player = hub.world.players[welcome["id"]]
        player.x, player.y = 1500.0, 1500.0
        hub.world.drops[777] = Drop(777, "stinger", 1500.0, 1500.0)
        got = await self._next(first, "inv")      # first inv is the initial one
        while "stinger" not in got["got"]:
            got = await self._next(first, "inv")
        self.assertEqual(got["inv"]["stinger"], 1)
        player.kills_total = 3
        player.save_dirty = True
        await first.disconnect()
        self._open.remove(first)
        inventory, profile = await self._db_inventory("fl_carol")
        self.assertEqual(inventory, {"basic": 5, "stinger": 1})
        self.assertEqual(profile.kills_total, 3)

        second, _, _ = await self._connect(user)
        inv = await self._next(second, "inv")
        self.assertEqual(inv["inv"], {"basic": 5, "stinger": 1})
        self.assertEqual(inv["kt"], 3)

    @with_cleanup
    async def test_equip_over_the_socket_is_validated_and_persisted(self):
        user = await self._make_user("fl_dave")
        communicator, _, _ = await self._connect(user)
        welcome = await self._next(communicator, "welcome")
        player = hub.world.players[welcome["id"]]
        player.inventory["rose"] = 2
        await self._next(communicator, "inv")

        await communicator.send_to(text_data=json.dumps({"t": "equip", "slot": 1, "kind": "stinger"}))   # not owned
        inv = await self._next(communicator, "inv")
        self.assertEqual(inv["lo"], ["basic"] * 5)
        await asyncio.sleep(w.EQUIP_COOLDOWN + 0.1)
        await communicator.send_to(text_data=json.dumps({"t": "equip", "slot": 1, "kind": "rose"}))
        inv = await self._next(communicator, "inv")
        self.assertEqual(inv["lo"], ["basic", "rose", "basic", "basic", "basic"])
        await communicator.disconnect()
        self._open.remove(communicator)
        _, profile = await self._db_inventory("fl_dave")
        self.assertEqual(profile.loadout, "basic,rose,basic,basic,basic")

    @with_cleanup
    async def test_periodic_flush_saves_dirty_players_without_a_disconnect(self):
        user = await self._make_user("fl_erin")
        communicator, _, _ = await self._connect(user)
        welcome = await self._next(communicator, "welcome")
        player = hub.world.players[welcome["id"]]
        player.inventory["heavy"] = 4
        player.save_dirty = True
        await hub._flush()
        inventory, _ = await self._db_inventory("fl_erin")
        self.assertEqual(inventory.get("heavy"), 4)
        self.assertFalse(player.save_dirty)

    @with_cleanup
    async def test_second_session_replaces_the_first_and_inherits_unsaved_progress(self):
        user = await self._make_user("fl_frank")
        first, _, _ = await self._connect(user)
        welcome = await self._next(first, "welcome")
        player = hub.world.players[welcome["id"]]
        player.inventory["rose"] = 3                # progress that was never flushed
        player.save_dirty = True

        second, _, _ = await self._connect(user)
        await self._next(second, "welcome")
        inv = await self._next(second, "inv")
        self.assertEqual(inv["inv"].get("rose"), 3)
        names = [p.name for p in hub.world.players.values()]
        self.assertEqual(names.count("fl_frank"), 1)
        self.assertEqual(len(hub.clients), 1)
        closed = False
        for _ in range(60):                         # the first socket gets closed with 4409
            msg = await first.receive_output(timeout=2)
            if msg["type"] == "websocket.close":
                self.assertEqual(msg["code"], 4409)
                closed = True
                break
        self.assertTrue(closed)

    @with_cleanup
    async def test_disconnect_removes_the_player(self):
        user = await self._make_user("fl_gina")
        communicator, _, _ = await self._connect(user)
        await self._next(communicator, "welcome")
        self.assertEqual(len(hub.world.players), 1)
        await communicator.disconnect()
        self._open.remove(communicator)
        self.assertEqual(len(hub.world.players), 0)
        self.assertEqual(hub.clients, {})
