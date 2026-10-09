import asyncio
import json
import math
import random
import unittest

from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import User
from django.test import override_settings

from game.consumers.florr import world as w
from game.consumers.florr.hub import hub
from game.consumers.florr.index import FlorrPlayer
from game.consumers.florr.world import World


def make_world():
    return World(rng=random.Random(1234))


def place(player, x, y):
    player.x, player.y = x, y


class FlorrWorldTests(unittest.TestCase):
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

    def test_mobs_spawn_up_to_the_target_and_never_near_a_player(self):
        for seed in range(20):
            world = World(rng=random.Random(seed))
            p = world.add_player("a")
            place(p, 1500, 1500)
            world.step(w.MOB_SPAWN_INTERVAL + 0.01)       # exactly one spawn
            self.assertEqual(len(world.mobs), 1)
            for m in world.mobs.values():
                self.assertGreaterEqual(math.hypot(m.x - p.x, m.y - p.y), w.MOB_SPAWN_MIN_DIST)
        world = make_world()
        place(world.add_player("a"), 1500, 1500)
        for _ in range(int(w.MOB_TARGET_COUNT * 2 * w.MOB_SPAWN_INTERVAL / 0.1) + 50):
            world.step(0.1)
        self.assertLessEqual(len(world.mobs), w.MOB_TARGET_COUNT)
        self.assertGreater(len(world.mobs), 10)

    def test_no_mobs_spawn_without_players(self):
        world = make_world()
        for _ in range(100):
            world.step(0.1)
        self.assertEqual(len(world.mobs), 0)

    def _world_with_mob_on_petal(self):
        world = make_world()
        p = world.add_player("a")
        place(p, 1500, 1500)
        p.orbit_r = w.ORBIT_RADIUS[0]
        px, py = p.petal_pos(0)
        mob = w.Mob(world._new_id(), "beetle", px, py)
        world.mobs[mob.id] = mob
        return world, p, mob

    def test_petals_damage_mobs_and_credit_the_kill(self):
        world, p, mob = self._world_with_mob_on_petal()
        mob.hp = 1.0
        mob.x, mob.y = p.petal_pos(0)
        world._spawn_cd = 999      # keep the world free of extra mobs
        world.step(0.05)
        self.assertNotIn(mob.id, world.mobs)
        self.assertEqual(p.kills, 1)

    def test_mob_breaks_petals_and_they_come_back(self):
        world, p, mob = self._world_with_mob_on_petal()
        world._spawn_cd = 999
        mob.hp = mob.max_hp = 10_000   # tank, so the mob survives
        for _ in range(60):
            mob.x, mob.y = p.petal_pos(0)
            world.step(0.05)
            if not p.petal_alive(0):
                break
        self.assertFalse(p.petal_alive(0))
        del world.mobs[mob.id]
        for _ in range(int(w.PETAL_RESPAWN / 0.05) + 2):
            world.step(0.05)
        self.assertTrue(p.petal_alive(0))
        self.assertEqual(p.petal_hp[0], w.PETAL_HP)

    def test_player_dies_then_can_respawn_after_delay(self):
        world = make_world()
        p = world.add_player("a")
        place(p, 1500, 1500)
        world._spawn_cd = 999
        mob = w.Mob(world._new_id(), "beetle", p.x, p.y)
        mob.hp = mob.max_hp = 10_000
        world.mobs[mob.id] = mob
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
        self.assertFalse(world.respawn(p.id))            # already alive

    def test_regen_only_after_out_of_combat(self):
        world = make_world()
        p = world.add_player("a")
        world._spawn_cd = 999
        p.hp = 50.0
        p.since_hit = 0.0
        world.step(1.0)
        self.assertEqual(p.hp, 50.0)
        for _ in range(int(w.PLAYER_REGEN_DELAY) + 1):
            world.step(1.0)
        self.assertGreater(p.hp, 50.0)

    def test_snapshot_only_contains_what_is_in_view(self):
        world = make_world()
        me = world.add_player("me")
        near = world.add_player("near")
        far = world.add_player("far")
        place(me, 1000, 1000)
        place(near, 1500, 1000)
        place(far, 1000 + w.VIEW_RADIUS + 50, 1000)
        world.mobs[1000] = w.Mob(1000, "beetle", 1000, 1200)
        world.mobs[1001] = w.Mob(1001, "beetle", 1000, 1000 + w.VIEW_RADIUS + 50)
        snap = world.snapshot_for(me.id)
        self.assertEqual({p["i"] for p in snap["ps"]}, {me.id, near.id})
        self.assertEqual({m["i"] for m in snap["ms"]}, {1000})
        json.dumps(snap)       # must be serialisable
        self.assertIsNone(world.snapshot_for(99999))


class FlorrConsumerTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # in-memory channel layer: these tests must not depend on a running Redis
        self._settings = override_settings(CHANNEL_LAYERS={"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
        self._settings.enable()
        self._reset_hub()

    async def asyncTearDown(self):
        for communicator in getattr(self, "_open", []):
            await communicator.disconnect()
        if hub._task is not None:
            hub._task.cancel()
        self._reset_hub()
        self._settings.disable()

    def _reset_hub(self):
        hub.world = World(rng=random.Random(5))
        hub.clients.clear()
        hub.by_name.clear()
        hub._task = None
        self._open = []

    async def _connect(self, username):
        communicator = WebsocketCommunicator(FlorrPlayer.as_asgi(), "/wss/florr/")
        communicator.scope["user"] = User(username=username)
        connected, _ = await communicator.connect()
        self._open.append(communicator)
        return communicator, connected

    async def test_anonymous_users_are_rejected(self):
        communicator = WebsocketCommunicator(FlorrPlayer.as_asgi(), "/wss/florr/")
        from django.contrib.auth.models import AnonymousUser
        communicator.scope["user"] = AnonymousUser()
        connected, code = await communicator.connect()
        self.assertFalse(connected)
        self.assertEqual(code, 4401)

    async def test_welcome_comes_first_then_state(self):
        communicator, connected = await self._connect("alice")
        self.assertTrue(connected)
        welcome = json.loads(await communicator.receive_from(timeout=2))
        self.assertEqual(welcome["t"], "welcome")
        self.assertEqual(welcome["w"], w.WORLD_W)
        state = json.loads(await communicator.receive_from(timeout=2))
        self.assertEqual(state["t"], "s")
        self.assertEqual(state["me"], welcome["id"])
        me = next(p for p in state["ps"] if p["i"] == welcome["id"])
        self.assertEqual(me["n"], "alice")

    async def test_input_moves_the_player_and_garbage_is_ignored(self):
        communicator, _ = await self._connect("bob")
        welcome = json.loads(await communicator.receive_from(timeout=2))
        pid = welcome["id"]
        player = hub.world.players[pid]
        player.x, player.y = 1000.0, 1000.0
        await communicator.send_to(text_data="not json")
        await communicator.send_to(text_data=json.dumps([1, 2, 3]))
        await communicator.send_to(text_data="x" * 5000)
        await communicator.send_to(text_data=json.dumps({"t": "in", "dx": 1, "dy": 0, "m": 1}))
        await asyncio.sleep(0.5)
        self.assertGreater(player.x, 1000.0)
        self.assertEqual(player.mode, 1)

    async def test_second_session_replaces_the_first(self):
        first, _ = await self._connect("carol")
        await first.receive_from(timeout=2)            # welcome
        second, _ = await self._connect("carol")
        await second.receive_from(timeout=2)
        names = [p.name for p in hub.world.players.values()]
        self.assertEqual(names.count("carol"), 1)
        self.assertEqual(len(hub.clients), 1)
        # the first socket gets closed with 4409; drain its queue until the close shows up
        closed = False
        for _ in range(20):
            msg = await first.receive_output(timeout=2)
            if msg["type"] == "websocket.close":
                self.assertEqual(msg["code"], 4409)
                closed = True
                break
        self.assertTrue(closed)

    async def test_disconnect_removes_the_player(self):
        communicator, _ = await self._connect("dave")
        await communicator.receive_from(timeout=2)
        self.assertEqual(len(hub.world.players), 1)
        await communicator.disconnect()
        self.assertEqual(len(hub.world.players), 0)
        self.assertEqual(hub.clients, {})
