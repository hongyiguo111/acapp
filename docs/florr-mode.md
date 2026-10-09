# 花瓣模式 (florr-style co-op mode)

A persistent, shared, server-authoritative world next to the original single/dual/multi modes.
Players move around a 3000x3000 map, petals orbit them and damage mobs on contact, mobs hurt players
and break petals, mobs drop petals, petals come in rarity tiers that can be crafted up, and progress is kept
in the database. Co-op only (no PvP).

## Layout
| Part | File |
|---|---|
| Simulation (pure Python, unit tested) | `game/consumers/florr/world.py` |
| Tick loop, connection registry, periodic save | `game/consumers/florr/hub.py` |
| Database load/save | `game/consumers/florr/store.py`, `game/models/florr/florr.py`, migrations `0010`, `0011` |
| WebSocket endpoint `/wss/florr/` | `game/consumers/florr/index.py`, `game/routing.py` |
| Kills ranking `GET /settings/florr_ranklist/` | `game/views/settings/florr_ranklist.py` |
| Client (own canvas + render loop, hotbar, bag, ranking panel) | `game/static/js/src/florr/zbase.js`, `game/static/css/florr.css` |
| Tests / tools | `game/tests.py` (`manage.py test game`), `scripts/florr_smoke.py` (needs `scripts/dev.ps1` running), `scripts/florr_balance_sim.py` |

## Items, rarity, crafting
An *item* is a petal kind plus a rarity tier, written `kind:rarity` (`rose:2`). Five tiers: 普通, 罕见, 稀有, 史诗, 传说.
Each tier multiplies petal hp / damage / heal by `PETAL_RARITY_POWER` (2.2) and grows the petal a little.
Crafting turns `CRAFT_COST` (5) *unequipped* copies of an item into one copy of the next tier (always succeeds, no gambling).
Kinds (`PETAL_TYPES`): basic, stinger (glass cannon), heavy (tanky), rose (heals the owner, weak damage).

## Zones and mobs
Distance from the map centre decides the zone: 草地 (outer, where everybody spawns), 森林, 沼泽, 深渊 (centre).
Mobs have a tier = the zone they were born in; per tier hp x`MOB_HP_MULT` (2.6), damage x`MOB_DPS_MULT` (1.45), size +12%.
`MOB_TARGETS` mobs of each tier are kept alive. Mob kinds: ladybug (passive), beetle (chases), wasp (fast chaser), rock (stationary).
Chasers stop at the body (`MOB_CONTACT_FACTOR`) instead of walking into the player's centre.
Drops: each mob kind has a table of (kind, chance); the chance is scaled by `DROP_CHANCE_SCALE` and `DROP_TIER_FALLOFF`^tier,
the rarity is the mob tier **minus one** (so depth alone does not skip crafting), with an 8% chance of one better. Drops lie on the
ground for 45 s; the first living player to touch one gets it.

## Combat rules
- Petals damage by overlap (per second); petals have hp and respawn 2 s after breaking.
- Hold left/Space = attack (+50% petal damage), right/Shift = defend (petals wear down at half speed). Orbit radius 76 / 64 / 46.
  Every ring must still reach the smallest chaser hugging the body (`test_every_ring_reaches_a_mob_hugging_the_body`).
- Death loses nothing (tunable). Kills are credited to the last player whose petals hit the mob.

## Balance tooling
`python scripts/florr_balance_sim.py 180 <seed>` plays a growing bot offline and prints when its whole loadout reached each rarity.
Rough numbers with the current constants (a bot that grinds without pause - humans are slower): average loadout rarity 1 after
~45 min, 2 after ~1.5 h, 3 after ~4 h, 4 (legendary) takes many hours. Retune `DROP_CHANCE_SCALE` / `DROP_TIER_FALLOFF` /
`MOB_HP_MULT` / `PETAL_RARITY_POWER`, rerun, and check that fights still cost sane hp.

## Protocol (JSON)
- client -> server: `{"t":"in","dx","dy","m"}`, `{"t":"respawn"}`, `{"t":"equip","slot":0-4,"item":"rose:1"|""}`, `{"t":"craft","item":"basic:0"}`
- server -> client: `welcome` once (constants, petal / rarity / zone / mob catalogue), `s` snapshots 20 times/s (entities within
  `VIEW_RADIUS`; items as `kind_index * 8 + rarity`; mobs carry `u` tier and `R` radius; `ds` = drops), and a private `inv` message
  (inventory `{item: count}`, loadout, lifetime kills, `got` = items just received) whenever it changes or a request was refused.
- close codes: 4401 not logged in, 4409 same account connected elsewhere (newer wins), 4500 failed to load progress.

Identity is the Django session user. Nothing the client sends is trusted: vectors are clamped, items parsed against the
catalogue, equip checks ownership (an item can be equipped at most as often as it is owned), swaps have a 0.4 s cooldown,
crafting only spends unequipped copies, messages over 512 bytes are dropped.

## Persistence
`FlorrProfile` (loadout, lifetime kills) and `FlorrPetal` (player, kind, rarity, count) hang off `Player`. New accounts get 5 basic
petals on first connect. Older saves without a rarity read as rarity 0. Progress is written when a player disconnects, every 5 s for
players with changes, and before a second session of the same account reads it. Rows for items that were used up (crafting) are
deleted on save. A crash can lose at most the last ~5 s.

## Deploying (needs the owner's approval - touches the production server)
- back up `db.sqlite3` first; `python manage.py migrate` (adds two tables and a column on one of them, nothing existing is modified);
  copy `static/`.
- restart daphne (drops connected players; the world and its mobs reset). daphne must stay a single process.

## Roadmap
1. (done) move, orbiting petals, mob, hp, death/respawn
2. (done) mob variety, drops, inventory and loadout with saved progress
3. (done) rarity tiers, crafting, zones, kills ranking
4. touch controls, sound, art; ideas: bosses in the abyss, a death penalty, more petal kinds (missile, web, wing), pets / sprites
