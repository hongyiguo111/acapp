import asyncio
import functools
import json
import math
import random

import unittest
from unittest import mock
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import AnonymousUser, User
from django.test import TransactionTestCase, override_settings

from game.consumers.florr import store
from game.consumers.florr import world as w
from game.consumers.florr.hub import hub
from game.consumers.florr.index import FlorrPlayer
from game.consumers.florr.world import Drop, Mob, World
from game.models.florr.florr import FlorrPetal, FlorrProfile
from game.models.player.player import Player


class FixedRandom(random.Random):
    """Random whose random() always returns `value`, so drop rolls are deterministic.

    0.0  -> every drop happens and is bumped one rarity tier
    0.09 -> every drop happens (all chances are >= 0.10) and none is bumped (bump chance is 0.08)
    0.999 -> nothing drops
    """
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


def add_mob(world, kind, x, y, hp=None, tier=0):
    mob = Mob(world._new_id(), kind, x, y, tier)
    if hp is not None:
        mob.hp = mob.max_hp = hp
    world.mobs[mob.id] = mob
    return mob


class FlorrItemTests(unittest.TestCase):
    def test_parse_and_normalize(self):
        self.assertEqual(w.parse_item("rose:2"), ("rose", 2))
        self.assertEqual(w.parse_item("rose"), ("rose", 0), "older saves have no rarity")
        self.assertEqual(w.normalize_item("rose"), "rose:0")
        self.assertEqual(w.normalize_item("rose:4"), "rose:4")
        for bad in ("rose:5", "rose:x", "rose:-1", "rose:", ":1", "nonsense", "nonsense:1", "", None, 5, ["rose"], "rose:1:2"):
            self.assertIsNone(w.parse_item(bad), repr(bad))

    def test_rarity_scales_the_stats(self):
        base, second, top = w.petal_stats("rose:0"), w.petal_stats("rose:1"), w.petal_stats(f"rose:{w.MAX_RARITY}")
        self.assertAlmostEqual(second["hp"], base["hp"] * w.PETAL_RARITY_POWER)
        self.assertAlmostEqual(second["dps"], base["dps"] * w.PETAL_RARITY_POWER)
        self.assertAlmostEqual(second["heal"], base["heal"] * w.PETAL_RARITY_POWER)
        self.assertAlmostEqual(second["radius"], base["radius"] * (1 + w.PETAL_RARITY_SIZE))
        self.assertAlmostEqual(top["hp"], base["hp"] * w.PETAL_RARITY_POWER ** w.MAX_RARITY)
        self.assertEqual((base["kind"], second["rarity"]), ("rose", 1))

    def test_snapshot_item_codes_round_trip(self):
        for kind in w.PETAL_TYPES:
            for rarity in range(w.MAX_RARITY + 1):
                code = w.encode_item(w.make_item(kind, rarity))
                self.assertEqual((w.PETAL_ORDER[code // w.ITEM_CODE_BASE], code % w.ITEM_CODE_BASE), (kind, rarity))
        self.assertGreater(w.ITEM_CODE_BASE, w.MAX_RARITY)

    def test_zones(self):
        self.assertEqual(w.zone_of(*w.CENTER), w.ZONE_COUNT - 1)
        self.assertEqual(w.zone_of(50, 50), 0)
        for tier, edge in enumerate(w.ZONE_EDGES):
            self.assertEqual(w.zone_of(w.CENTER[0] + edge + 1, w.CENTER[1]), tier)
            self.assertEqual(w.zone_of(w.CENTER[0] + edge - 1, w.CENTER[1]), tier + 1)
        self.assertEqual(len(w.MOB_TARGETS), w.ZONE_COUNT)

    def test_welcome_info_is_serialisable_and_complete(self):
        info = w.welcome_info()
        json.dumps(info)
        self.assertEqual([p["id"] for p in info["petals"]], w.PETAL_ORDER)
        self.assertEqual(len(info["rarities"]), w.MAX_RARITY + 1)
        self.assertEqual(len(info["zones"]), w.ZONE_COUNT)
        self.assertIsNone(info["zones"][0]["outer"])
        self.assertEqual(info["craft_cost"], w.CRAFT_COST)


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

    # ---- zones and mob spawning --------------------------------------------------------
    def test_points_come_from_the_requested_zone(self):
        world = make_world()
        for tier in range(w.ZONE_COUNT):
            for _ in range(300):
                x, y = world._point_in_zone(tier)
                self.assertEqual(w.zone_of(x, y), tier)
                self.assertTrue(0 <= x <= w.WORLD_W and 0 <= y <= w.WORLD_H)

    def test_players_start_and_respawn_in_the_outer_zone(self):
        world = make_world()
        for i in range(100):
            p = world.add_player(f"p{i}")
            self.assertEqual(w.zone_of(p.x, p.y), 0)
        p.alive, p.dead_for = False, 5.0
        place(p, *w.CENTER)
        self.assertTrue(world.respawn(p.id))
        self.assertEqual(w.zone_of(p.x, p.y), 0)

    def test_mobs_spawn_per_zone_up_to_the_targets_and_never_near_a_player(self):
        world = World(rng=random.Random(8))
        player = world.add_player("a")
        place(player, 60, 60)                               # far corner: far from every spawn ring
        seen = set()
        for _ in range(1500):
            world.step(0.5)
            for m in world.mobs.values():
                if m.id not in seen:
                    seen.add(m.id)
                    self.assertEqual(w.zone_of(m.x, m.y), m.tier, "a mob is born in the zone it belongs to")
                    self.assertGreaterEqual(math.hypot(m.x - player.x, m.y - player.y), w.MOB_SPAWN_MIN_DIST)
        counts = [sum(1 for m in world.mobs.values() if m.tier == t) for t in range(w.ZONE_COUNT)]
        self.assertEqual(counts, list(w.MOB_TARGETS))

    def test_every_mob_kind_can_spawn(self):
        world = World(rng=random.Random(99))
        place(world.add_player("a"), 60, 60)
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

    def test_mob_tiers_scale_hp_damage_and_size(self):
        spec = w.MOB_TYPES["beetle"]
        base, deep = Mob(1, "beetle", 0, 0, 0), Mob(2, "beetle", 0, 0, 3)
        self.assertEqual((base.max_hp, base.dps, base.radius), (spec["hp"], spec["dps"], spec["radius"]))
        self.assertAlmostEqual(deep.max_hp, spec["hp"] * w.MOB_HP_MULT ** 3)
        self.assertAlmostEqual(deep.dps, spec["dps"] * w.MOB_DPS_MULT ** 3)
        self.assertAlmostEqual(deep.radius, spec["radius"] * (1 + 3 * w.MOB_SIZE_GROWTH))

    # ---- mob behaviour ------------------------------------------------------------------
    def test_rocks_never_move_and_ladybugs_never_chase(self):
        world = make_world()
        p = world.add_player("a")
        place(p, 1500, 1500)
        rock = add_mob(world, "rock", 1700, 1500)
        ladybug = add_mob(world, "ladybug", 1500, 1700)
        rock_pos = (rock.x, rock.y)
        ladybug_start = math.hypot(ladybug.x - p.x, ladybug.y - p.y)
        for _ in range(20):
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
        for kind, tier in (("beetle", 0), ("wasp", 0), ("wasp", 3)):
            world = make_world()
            p = world.add_player("a", inventory={}, loadout=[])        # no petals: nothing kills the mob
            place(p, 1500, 1500)
            mob = add_mob(world, kind, 1500 + 250, 1500, hp=10 ** 9, tier=tier)
            for _ in range(120):
                world.step(0.05)
                p.hp = 10 ** 6                                          # survive the biting
            contact = mob.radius + w.PLAYER_RADIUS * w.MOB_CONTACT_FACTOR
            self.assertAlmostEqual(math.hypot(mob.x - p.x, mob.y - p.y), contact, delta=1.0, msg=f"{kind} tier {tier}")

    def test_every_ring_reaches_a_mob_hugging_the_body(self):
        """If a mode could not touch the smallest chaser, holding that button would lose fights outright."""
        for tier in (0, 3):
            for mode in (-1, 0, 1):
                for kind in w.PETAL_TYPES:
                    item = w.make_item(kind, tier)
                    world = make_world()
                    p = world.add_player("a", inventory={item: 5}, loadout=[item] * 5)
                    place(p, 1500, 1500)
                    p.orbit_r = w.ORBIT_RADIUS[mode]
                    world.set_input(p.id, 0, 0, mode)
                    mob = add_mob(world, "wasp", 1500, 1500, hp=10 ** 9, tier=tier)
                    contact = mob.radius + w.PLAYER_RADIUS * w.MOB_CONTACT_FACTOR
                    for _ in range(int(2 * math.pi / w.ORBIT_OMEGA / 0.02) + 5):    # one full petal revolution
                        mob.x, mob.y = p.x + contact, p.y
                        world.step(0.02)
                    self.assertLess(mob.hp, 10 ** 9, f"tier {tier} mode {mode} {kind} never touched a hugging wasp")

    # ---- combat ----------------------------------------------------------------------
    def _petal_mob_overlap(self, item, mob_kind="rock", mob_hp=10_000, mob_tier=0):
        world = make_world()
        p = world.add_player("a", inventory={item: 5}, loadout=[item] * 5)
        place(p, 1500, 1500)
        px, py = p.petal_pos(0)
        mob = add_mob(world, mob_kind, px, py, hp=mob_hp, tier=mob_tier)
        return world, p, mob

    def _damage_dealt(self, item, mode=0):
        world, p, mob = self._petal_mob_overlap(item)
        world.set_input(p.id, 0, 0, mode)
        p.orbit_r = w.ORBIT_RADIUS[mode]
        mob.x, mob.y = p.petal_pos(0)
        world.step(0.05)
        return 10_000 - mob.hp

    def test_petal_types_differ_in_damage(self):
        dealt = {k: self._damage_dealt(w.make_item(k)) for k in ("basic", "stinger", "heavy", "rose")}
        self.assertGreater(dealt["stinger"], dealt["basic"])
        self.assertGreater(dealt["basic"], dealt["heavy"])
        self.assertGreater(dealt["heavy"], dealt["rose"])

    def test_higher_rarity_petals_hit_harder(self):
        self.assertAlmostEqual(self._damage_dealt("basic:2"), self._damage_dealt("basic:0") * w.PETAL_RARITY_POWER ** 2, places=3)

    def test_heavy_petals_outlast_stingers_and_rarity_adds_durability(self):
        def broken_after(item):
            world, p, mob = self._petal_mob_overlap(item)
            for step in range(1, 2000):
                mob.x, mob.y = p.petal_pos(0)
                world.step(0.05)
                if not p.petal_alive(0):
                    return step
            return None
        self.assertGreater(broken_after("heavy:0"), broken_after("stinger:0"))
        self.assertGreater(broken_after("stinger:1"), broken_after("stinger:0"))

    def test_attack_hits_harder_and_defend_wears_petals_slower(self):
        def run(mode):
            world, p, mob = self._petal_mob_overlap("basic:0")
            world.set_input(p.id, 0, 0, mode)
            p.orbit_r = w.ORBIT_RADIUS[mode]
            mob.x, mob.y = p.petal_pos(0)
            world.step(0.05)
            return 10_000 - mob.hp, w.petal_stats("basic:0")["hp"] - p.petal_hp[0]
        neutral_dmg, neutral_wear = run(0)
        attack_dmg, _ = run(1)
        _, defend_wear = run(-1)
        self.assertAlmostEqual(attack_dmg, neutral_dmg * w.ATTACK_DAMAGE_MULT, places=3)
        self.assertAlmostEqual(defend_wear, neutral_wear * w.DEFEND_WEAR_MULT, places=3)

    def test_deep_mobs_hurt_more_and_take_longer_to_kill(self):
        def fight(tier):
            world, p, mob = self._petal_mob_overlap("basic:0", mob_kind="beetle", mob_hp=None, mob_tier=tier)
            mob.x, mob.y = p.petal_pos(0)
            world.step(0.05)
            return mob.max_hp - mob.hp, p.petal_hp[0]
        shallow_dmg, shallow_hp = fight(0)
        deep_dmg, deep_hp = fight(2)
        self.assertAlmostEqual(shallow_dmg, deep_dmg, places=6, msg="the petal deals the same damage, the mob just has more hp")
        self.assertLess(deep_hp, shallow_hp, "a deeper mob wears petals down faster")

    def test_broken_petals_come_back(self):
        world, p, mob = self._petal_mob_overlap("basic:0")
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
        self.assertEqual(p.petal_hp[0], w.petal_stats("basic:0")["hp"])

    def test_roses_heal_their_owner_and_rarity_scales_it(self):
        for rarity in (0, 2):
            item = w.make_item("rose", rarity)
            world = make_world()
            p = world.add_player("a", inventory={item: 5}, loadout=[item] * 5)
            p.hp, p.since_hit = 10.0, 0.0           # in combat: no natural regen, only roses (low start: no cap)
            world.step(1.0)
            self.assertAlmostEqual(p.hp, 10.0 + 5 * w.petal_stats(item)["heal"], places=3)
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
        self.assertEqual(p.loadout, ["basic:0"] * 5)     # nothing is lost on death
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
        world, p, mob = self._petal_mob_overlap("basic:0", mob_kind="ladybug", mob_hp=1.0)
        mob.x, mob.y = p.petal_pos(0)
        world.step(0.05)
        self.assertNotIn(mob.id, world.mobs)
        self.assertEqual((p.kills, p.kills_total), (1, 1))
        self.assertTrue(p.save_dirty)

    def _drops_of(self, roll, kind="rock", tier=0):
        world = make_world(FixedRandom(roll))
        mob = Mob(1, kind, 100, 100, tier)             # nobody around, so nothing gets picked up
        with mock.patch.object(w, "DROP_CHANCE_SCALE", 1.0), mock.patch.object(w, "DROP_TIER_FALLOFF", 1.0):
            world._kill_mob(mob)                        # raw table chances, so the fixed rolls are decisive
        return sorted(d.item for d in world.drops.values())

    def test_drop_chances_shrink_with_the_tier(self):
        for base in (0.1, 0.45):
            chances = [w.drop_chance(base, t) for t in range(w.ZONE_COUNT)]
            self.assertAlmostEqual(chances[0], base * w.DROP_CHANCE_SCALE)
            self.assertEqual(chances, sorted(chances, reverse=True))
            self.assertAlmostEqual(chances[2], chances[1] * w.DROP_TIER_FALLOFF)
        self.assertLess(max(c for spec in w.MOB_TYPES.values() for _, c in spec["drops"]), 1.0 / w.DROP_CHANCE_SCALE)

    def test_a_dead_mob_drops_what_its_table_says(self):
        kinds = sorted(k for k, _ in w.MOB_TYPES["rock"]["drops"])
        self.assertEqual(self._drops_of(0.09), [w.make_item(k, 0) for k in kinds])
        self.assertEqual(self._drops_of(0.999), [])

    def test_drop_rarity_follows_the_mob_tier_with_an_occasional_bump(self):
        kinds = sorted(k for k, _ in w.MOB_TYPES["beetle"]["drops"])
        for tier in range(w.ZONE_COUNT):
            base = max(0, tier + w.DROP_RARITY_OFFSET)
            self.assertEqual(self._drops_of(0.09, "beetle", tier), [w.make_item(k, base) for k in kinds])
            self.assertEqual(self._drops_of(0.0, "beetle", tier), [w.make_item(k, base + 1) for k in kinds], "bumped")
        top = Mob(1, "beetle", 100, 100, 3)
        top.tier = w.MAX_RARITY                         # a bump can never exceed the top tier
        world = make_world(FixedRandom(0.0))
        world._kill_mob(top)
        self.assertTrue(all(w.parse_item(d.item)[1] == w.MAX_RARITY for d in world.drops.values()))

    def test_walking_over_a_drop_picks_it_up(self):
        world = make_world()
        p = world.add_player("a")
        place(p, 1500, 1500)
        world.drops[500] = Drop(500, "stinger:2", 1500 + 30, 1500)
        world.drops[501] = Drop(501, "rose:0", 1500 + 400, 1500)
        p.inv_dirty = False
        world.step(0.05)
        self.assertEqual(p.inventory.get("stinger:2"), 1)
        self.assertNotIn(500, world.drops)
        self.assertIn(501, world.drops)
        self.assertEqual(p.pickups, ["stinger:2"])
        self.assertTrue(p.inv_dirty and p.save_dirty)
        msg = world.inventory_message(p.id)
        self.assertEqual(msg["got"], ["stinger:2"])
        self.assertEqual(msg["inv"]["stinger:2"], 1)
        self.assertFalse(p.inv_dirty)
        self.assertEqual(world.inventory_message(p.id)["got"], [])

    def test_dead_players_cannot_pick_up(self):
        world = make_world()
        p = world.add_player("a")
        place(p, 1500, 1500)
        p.alive = False
        world.drops[500] = Drop(500, "stinger:0", 1500, 1500)
        world.step(0.05)
        self.assertIn(500, world.drops)

    def test_only_one_player_gets_a_drop(self):
        world = make_world()
        a, b = world.add_player("a"), world.add_player("b")
        place(a, 1500, 1500)
        place(b, 1505, 1500)
        world.drops[500] = Drop(500, "heavy:0", 1500, 1500)
        world.step(0.05)
        self.assertEqual(a.inventory.get("heavy:0", 0) + b.inventory.get("heavy:0", 0), 1)

    def test_drops_expire_and_are_capped(self):
        world = make_world()
        world.drops[1] = Drop(1, "basic:0", 10, 10)
        for _ in range(int(w.DROP_TTL / 0.5) + 2):
            world.step(0.5)
        self.assertEqual(world.drops, {})
        world.rng = FixedRandom(0.0)
        for i in range(w.DROP_CAP):
            world.drops[10_000 + i] = Drop(10_000 + i, "basic:0", 10, 10)
        world._kill_mob(Mob(1, "rock", 100, 100))
        self.assertEqual(len(world.drops), w.DROP_CAP)

    def test_inventory_cap(self):
        world = make_world()
        p = world.add_player("a", inventory={"basic:0": w.INVENTORY_CAP}, loadout=["basic:0"] * 5)
        place(p, 1500, 1500)
        world.drops[1] = Drop(1, "basic:0", 1500, 1500)
        world.step(0.05)
        self.assertEqual(p.inventory["basic:0"], w.INVENTORY_CAP)
        self.assertIn(1, world.drops)

    # ---- loadout ---------------------------------------------------------------------
    def _owner(self, inventory):
        world = make_world()
        p = world.add_player("a", inventory=inventory, loadout=[])
        return world, p

    def test_new_players_get_the_starter_kit(self):
        p = make_world().add_player("a")
        self.assertEqual(p.inventory, {"basic:0": 5})
        self.assertEqual(p.loadout, ["basic:0"] * 5)

    def test_equip_rules(self):
        world, p = self._owner({"basic:0": 2, "rose:1": 1})
        self.assertEqual(p.loadout, [""] * 5)
        self.assertTrue(world.equip(p.id, 0, "basic:0"))
        self.assertEqual(p.loadout[0], "basic:0")
        self.assertTrue(p.save_dirty)
        world.step(1.0)                                        # let the swap cooldown pass
        self.assertTrue(world.equip(p.id, 1, "basic"), "a bare kind means rarity 0")
        world.step(1.0)
        self.assertFalse(world.equip(p.id, 2, "basic:0"), "only two copies owned")
        self.assertFalse(world.equip(p.id, 2, "basic:1"), "another rarity is a different item")
        self.assertFalse(world.equip(p.id, 2, "stinger:0"), "not owned")
        self.assertFalse(world.equip(p.id, 2, "nonsense"), "unknown kind")
        self.assertFalse(world.equip(p.id, 2, "rose:9"), "unknown rarity")
        self.assertFalse(world.equip(p.id, 5, "rose:1"), "slot out of range")
        self.assertFalse(world.equip(p.id, -1, "rose:1"))
        self.assertFalse(world.equip(p.id, True, "rose:1"), "bool is not a slot")
        self.assertFalse(world.equip(p.id, "0", "rose:1"))
        self.assertFalse(world.equip(p.id, 2, None))
        self.assertTrue(world.equip(p.id, 2, "rose:1"))
        world.step(1.0)
        self.assertTrue(world.equip(p.id, 0, ""), "unequip")
        self.assertEqual(p.loadout, ["", "basic:0", "rose:1", "", ""])
        self.assertFalse(p.petal_alive(0))

    def test_equip_swaps_use_the_same_copy(self):
        world, p = self._owner({"basic:0": 1})
        world.equip(p.id, 0, "basic:0")
        world.step(1.0)
        self.assertFalse(world.equip(p.id, 1, "basic:0"), "the single copy is already in slot 0")
        self.assertTrue(world.equip(p.id, 0, "basic:0"), "re-equipping the same item is a no-op")

    def test_equip_has_a_cooldown_and_resets_the_petal(self):
        world, p = self._owner({"basic:0": 5, "rose:0": 5})
        world.equip(p.id, 0, "basic:0")
        self.assertFalse(world.equip(p.id, 1, "basic:0"), "cooldown")
        world.step(w.EQUIP_COOLDOWN + 0.01)
        p.loadout[3] = "basic:0"
        p.petal_hp[3] = 1.0
        self.assertTrue(world.equip(p.id, 3, "rose:0"))
        self.assertEqual(p.petal_hp[3], w.petal_stats("rose:0")["hp"])

    def test_failed_equip_still_asks_the_client_to_resync(self):
        world, p = self._owner({"basic:0": 1})
        p.inv_dirty = False
        self.assertFalse(world.equip(p.id, 0, "stinger:0"))
        self.assertTrue(p.inv_dirty)

    def test_stored_data_is_sanitised_on_load(self):
        world = make_world()
        p = world.add_player("a", inventory={"basic": 2, "basic:0": 1, "ghost": 5, "rose:3": -3, "heavy:9": 4,
                                             "stinger:1": "4", "heavy:0": "x"},
                             loadout=["basic", "basic:0", "basic:0", "ghost", "stinger:1", "rose:3", "rose:0"])
        self.assertEqual(p.inventory, {"basic:0": 3, "stinger:1": 4})
        self.assertEqual(p.loadout, ["basic:0", "basic:0", "basic:0", "", "stinger:1"])
        self.assertEqual(len(p.loadout), w.PETAL_COUNT)
        self.assertEqual(w.sanitize_loadout(None, {}), [""] * w.PETAL_COUNT)

    def test_a_player_with_an_empty_loadout_deals_no_damage(self):
        world = make_world()
        p = world.add_player("a", inventory={"basic:0": 5}, loadout=[])
        place(p, 1500, 1500)
        mob = add_mob(world, "rock", 1500 + p.orbit_r, 1500, hp=100)
        for _ in range(20):
            world.step(0.05)
        self.assertEqual(mob.hp, 100)

    # ---- crafting --------------------------------------------------------------------
    def test_crafting_turns_five_into_one_of_the_next_tier(self):
        world, p = self._owner({"basic:0": 7, "basic:1": 1})
        p.inv_dirty = p.save_dirty = False
        self.assertTrue(world.craft(p.id, "basic:0"))
        self.assertEqual(p.inventory, {"basic:0": 7 - w.CRAFT_COST, "basic:1": 2})
        self.assertEqual(p.pickups, ["basic:1"])
        self.assertTrue(p.inv_dirty and p.save_dirty)
        self.assertFalse(world.craft(p.id, "basic:0"), "only 2 left")
        self.assertEqual(p.inventory, {"basic:0": 2, "basic:1": 2}, "a refused craft changes nothing")

    def test_crafting_cannot_use_equipped_copies(self):
        world = make_world()
        p = world.add_player("a", inventory={"basic:0": 7}, loadout=["basic:0"] * 5)
        self.assertEqual(p.free_count("basic:0"), 2)
        self.assertFalse(world.craft(p.id, "basic:0"), "5 owned but only 2 are free")
        p.inventory["basic:0"] = 10
        self.assertTrue(world.craft(p.id, "basic:0"))
        self.assertEqual(p.inventory["basic:0"], 5)
        self.assertEqual(p.loadout, ["basic:0"] * 5, "the loadout is untouched")

    def test_crafting_uses_up_the_stack_and_removes_the_key(self):
        world, p = self._owner({"rose:2": w.CRAFT_COST})
        self.assertTrue(world.craft(p.id, "rose:2"))
        self.assertEqual(p.inventory, {"rose:3": 1})

    def test_crafting_stops_at_the_top_tier_and_rejects_junk(self):
        top = w.make_item("basic", w.MAX_RARITY)
        world, p = self._owner({top: 20, "basic:0": 20})
        self.assertFalse(world.craft(p.id, top))
        for junk in ("nonsense", "basic:9", None, 7, ""):
            self.assertFalse(world.craft(p.id, junk), repr(junk))
        self.assertEqual(p.inventory, {top: 20, "basic:0": 20})
        self.assertTrue(world.craft(p.id, "basic"), "a bare kind means rarity 0")

    def test_crafted_petals_can_be_equipped_and_are_stronger(self):
        world, p = self._owner({"basic:0": w.CRAFT_COST})
        world.craft(p.id, "basic:0")
        self.assertTrue(world.equip(p.id, 0, "basic:1"))
        self.assertEqual(p.petal_hp[0], w.petal_stats("basic:1")["hp"])

    # ---- snapshots -----------------------------------------------------------------
    def test_snapshot_only_contains_what_is_in_view(self):
        world = make_world()
        me = world.add_player("me")
        near = world.add_player("near")
        far = world.add_player("far")
        place(me, 1000, 1000)
        place(near, 1500, 1000)
        place(far, 1000 + w.VIEW_RADIUS + 50, 1000)
        add_mob(world, "beetle", 1000, 1200, tier=2)
        far_mob = add_mob(world, "beetle", 1000, 1000 + w.VIEW_RADIUS + 50)
        world.drops[900] = Drop(900, "rose:3", 1000, 1100)
        world.drops[901] = Drop(901, "rose:0", 1000, 1000 + w.VIEW_RADIUS + 50)
        snap = world.snapshot_for(me.id)
        self.assertEqual({p["i"] for p in snap["ps"]}, {me.id, near.id})
        self.assertNotIn(far_mob.id, {m["i"] for m in snap["ms"]})
        self.assertEqual(len(snap["ms"]), 1)
        mob = snap["ms"][0]
        self.assertEqual((mob["t"], mob["u"]), ("beetle", 2))
        self.assertAlmostEqual(mob["R"], w.MOB_TYPES["beetle"]["radius"] * (1 + 2 * w.MOB_SIZE_GROWTH), places=1)
        self.assertEqual([d["i"] for d in snap["ds"]], [900])
        self.assertEqual(snap["ds"][0]["k"], w.encode_item("rose:3"))
        mine = next(p for p in snap["ps"] if p["i"] == me.id)
        self.assertEqual(mine["l"], [w.encode_item("basic:0")] * 5)
        json.dumps(snap)       # must be serialisable
        self.assertIsNone(world.snapshot_for(99999))

    def test_snapshot_marks_empty_and_broken_slots(self):
        world = make_world()
        p = world.add_player("a", inventory={"basic:0": 2}, loadout=["basic:0", "", "basic:0"])
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

    async def _db_state(self, username):
        def read():
            player = Player.objects.get(user__username=username)
            rows = FlorrPetal.objects.filter(player=player).values_list("kind", "rarity", "count")
            return ({w.make_item(k, r): c for k, r, c in rows}, FlorrProfile.objects.get(player=player))
        return await run_async_db(read)

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
        self.assertEqual(len(welcome["rarities"]), w.MAX_RARITY + 1)
        self.assertEqual(len(welcome["zones"]), w.ZONE_COUNT)
        inv = await self._next(communicator, "inv")
        self.assertEqual(inv["inv"], {"basic:0": 5})
        self.assertEqual(inv["lo"], ["basic:0"] * 5)
        state = await self._next(communicator, "s")
        me = next(p for p in state["ps"] if p["i"] == welcome["id"])
        self.assertEqual(me["n"], "fl_alice")
        inventory, profile = await self._db_state("fl_alice")
        self.assertEqual(inventory, {"basic:0": 5})
        self.assertEqual(profile.loadout, ",".join(["basic:0"] * 5))

    @with_cleanup
    async def test_older_saves_without_rarity_still_load(self):
        user = await self._make_user("fl_legacy")

        def seed():
            player, _ = Player.objects.get_or_create(user=user)
            FlorrProfile.objects.create(player=player, loadout="basic,basic,,rose,basic", kills_total=4)
            FlorrPetal.objects.create(player=player, kind="basic", count=5)      # rarity defaults to 0
            FlorrPetal.objects.create(player=player, kind="rose", count=1)
        await run_async_db(seed)
        communicator, _, _ = await self._connect(user)
        inv = await self._next(communicator, "inv")
        self.assertEqual(inv["inv"], {"basic:0": 5, "rose:0": 1})
        self.assertEqual(inv["lo"], ["basic:0", "basic:0", "", "rose:0", "basic:0"])
        self.assertEqual(inv["kt"], 4)

    @with_cleanup
    async def test_input_moves_the_player_and_garbage_is_ignored(self):
        user = await self._make_user("fl_bob")
        communicator, _, _ = await self._connect(user)
        welcome = json.loads(await communicator.receive_from(timeout=2))
        player = hub.world.players[welcome["id"]]
        player.x, player.y = 1000.0, 1000.0
        for junk in ("not json", json.dumps([1, 2, 3]), "x" * 5000, json.dumps({"t": "equip", "slot": "a", "item": 3}),
                     json.dumps({"t": "equip"}), json.dumps({"t": "craft"}), json.dumps({"t": "craft", "item": ["x"]}),
                     json.dumps({"t": 5})):
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
        hub.world.drops[777] = Drop(777, "stinger:2", 1500.0, 1500.0)
        got = await self._next(first, "inv")      # first inv is the initial one
        while "stinger:2" not in got["got"]:
            got = await self._next(first, "inv")
        self.assertEqual(got["inv"]["stinger:2"], 1)
        player.kills_total = 3
        player.save_dirty = True
        await first.disconnect()
        self._open.remove(first)
        inventory, profile = await self._db_state("fl_carol")
        self.assertEqual(inventory, {"basic:0": 5, "stinger:2": 1})
        self.assertEqual(profile.kills_total, 3)

        second, _, _ = await self._connect(user)
        inv = await self._next(second, "inv")
        self.assertEqual(inv["inv"], {"basic:0": 5, "stinger:2": 1})
        self.assertEqual(inv["kt"], 3)

    @with_cleanup
    async def test_equip_over_the_socket_is_validated_and_persisted(self):
        user = await self._make_user("fl_dave")
        communicator, _, _ = await self._connect(user)
        welcome = await self._next(communicator, "welcome")
        player = hub.world.players[welcome["id"]]
        player.inventory["rose:1"] = 2
        await self._next(communicator, "inv")

        await communicator.send_to(text_data=json.dumps({"t": "equip", "slot": 1, "item": "stinger:0"}))   # not owned
        inv = await self._next(communicator, "inv")
        self.assertEqual(inv["lo"], ["basic:0"] * 5)
        await asyncio.sleep(w.EQUIP_COOLDOWN + 0.1)
        await communicator.send_to(text_data=json.dumps({"t": "equip", "slot": 1, "item": "rose:1"}))
        inv = await self._next(communicator, "inv")
        self.assertEqual(inv["lo"], ["basic:0", "rose:1", "basic:0", "basic:0", "basic:0"])
        await communicator.disconnect()
        self._open.remove(communicator)
        _, profile = await self._db_state("fl_dave")
        self.assertEqual(profile.loadout, "basic:0,rose:1,basic:0,basic:0,basic:0")

    @with_cleanup
    async def test_crafting_over_the_socket_persists_and_used_up_rows_are_deleted(self):
        user = await self._make_user("fl_craft")
        communicator, _, _ = await self._connect(user)
        welcome = await self._next(communicator, "welcome")
        player = hub.world.players[welcome["id"]]
        player.inventory["rose:0"] = w.CRAFT_COST            # exactly one craft's worth, none equipped
        await self._next(communicator, "inv")
        await communicator.send_to(text_data=json.dumps({"t": "craft", "item": "rose:0"}))
        inv = await self._next(communicator, "inv")
        self.assertEqual(inv["inv"], {"basic:0": 5, "rose:1": 1})
        self.assertEqual(inv["got"], ["rose:1"])
        await communicator.disconnect()
        self._open.remove(communicator)
        inventory, _ = await self._db_state("fl_craft")
        self.assertEqual(inventory, {"basic:0": 5, "rose:1": 1})
        # and nothing comes back from the dead on the next login
        again, _, _ = await self._connect(user)
        self.assertEqual((await self._next(again, "inv"))["inv"], {"basic:0": 5, "rose:1": 1})

    @with_cleanup
    async def test_periodic_flush_saves_dirty_players_without_a_disconnect(self):
        user = await self._make_user("fl_erin")
        communicator, _, _ = await self._connect(user)
        welcome = await self._next(communicator, "welcome")
        player = hub.world.players[welcome["id"]]
        player.inventory["heavy:3"] = 4
        player.save_dirty = True
        await hub._flush()
        inventory, _ = await self._db_state("fl_erin")
        self.assertEqual(inventory.get("heavy:3"), 4)
        self.assertFalse(player.save_dirty)

    @with_cleanup
    async def test_second_session_replaces_the_first_and_inherits_unsaved_progress(self):
        user = await self._make_user("fl_frank")
        first, _, _ = await self._connect(user)
        welcome = await self._next(first, "welcome")
        player = hub.world.players[welcome["id"]]
        player.inventory["rose:2"] = 3                # progress that was never flushed
        player.save_dirty = True

        second, _, _ = await self._connect(user)
        await self._next(second, "welcome")
        inv = await self._next(second, "inv")
        self.assertEqual(inv["inv"].get("rose:2"), 3)
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


class FlorrRanklistTests(TransactionTestCase):
    def _player(self, username, kills):
        user = User.objects.create_user(username=username, password="x")
        player = Player.objects.create(user=user, photo=f"http://x/{username}.png")
        if kills is not None:
            FlorrProfile.objects.create(player=player, kills_total=kills)
        return user

    def test_ranks_by_lifetime_kills_and_reports_the_caller(self):
        users = {name: self._player(name, kills) for name, kills in
                 (("fr_a", 50), ("fr_b", 200), ("fr_c", 50), ("fr_d", 0), ("fr_e", None), ("fr_f", 7))}
        data = self.client.get('/settings/florr_ranklist/').json()
        self.assertEqual(data['result'], 'success')
        self.assertEqual([(r['username'], r['kills']) for r in data['ranklist']],
                         [("fr_b", 200), ("fr_a", 50), ("fr_c", 50), ("fr_f", 7)], "no kills, no rank; ties by account age")
        self.assertEqual([r['rank'] for r in data['ranklist']], [1, 2, 3, 4])
        self.assertIsNone(data['current_user'], "anonymous callers have no rank")

        self.client.force_login(users["fr_c"])
        data = self.client.get('/settings/florr_ranklist/').json()
        self.assertEqual((data['current_user']['rank'], data['current_user']['kills']), (3, 50))
        self.client.force_login(users["fr_d"])
        self.assertIsNone(self.client.get('/settings/florr_ranklist/').json()['current_user'], "0 kills = not ranked")

    def test_list_is_capped(self):
        for i in range(25):
            self._player(f"fr_bulk{i}", i + 1)
        data = self.client.get('/settings/florr_ranklist/').json()
        self.assertEqual(len(data['ranklist']), 20)
        self.assertEqual(data['ranklist'][0]['kills'], 25)
