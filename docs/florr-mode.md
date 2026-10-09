# 花瓣模式 (florr-style co-op mode)

A persistent, shared, server-authoritative world next to the original single/dual/multi modes.
Players move around a 3000x3000 map, petals orbit them and damage mobs on contact, mobs hurt players
and break petals, mobs drop new petals, and the inventory/loadout is kept in the database. Co-op only (no PvP).

## Layout
| Part | File |
|---|---|
| Simulation (pure Python, unit tested) | `game/consumers/florr/world.py` |
| Tick loop, connection registry, periodic save | `game/consumers/florr/hub.py` |
| Database load/save | `game/consumers/florr/store.py`, `game/models/florr/florr.py`, migration `0010` |
| WebSocket endpoint `/wss/florr/` | `game/consumers/florr/index.py`, `game/routing.py` |
| Client (own canvas + render loop, hotbar, bag) | `game/static/js/src/florr/zbase.js`, `game/static/css/florr.css` |
| Tests | `game/tests.py` (`manage.py test game`), `scripts/florr_smoke.py` (needs `scripts/dev.ps1` running), `scripts/florr_balance_sim.py` |

## Gameplay rules (phase 2)
- **Petals** (`PETAL_TYPES`): basic, stinger (glass cannon), heavy (tanky), rose (heals the owner, weak damage).
  5 loadout slots; an empty slot is allowed. Damage is dealt by overlap (per second), petals have hp and respawn 2 s after breaking.
- **Modes** (hold left/Space = attack, right/Shift = defend): attack = +50% petal damage, defend = petals wear down at half speed.
  Orbit radius 76 / 64 / 46 (attack / neutral / defend). The radii are chosen so that every ring still reaches the smallest
  chaser hugging the body; `test_every_ring_reaches_a_mob_hugging_the_body` guards this.
- **Mobs** (`MOB_TYPES`): ladybug (passive), beetle (chases), wasp (fast chaser), rock (stationary, tanky). Chasers stop at the
  body (`MOB_CONTACT_FACTOR`) instead of walking into the player's centre - from there no ring could reach them.
- **Drops**: each mob has a drop table; drops lie on the ground for 45 s, any living player walking over one picks it up (first come).
- **Death** loses nothing (tunable later). Kills are credited to the last player whose petals hit the mob.
- Rough yardstick: `python scripts/florr_balance_sim.py 10 <seed>` (a bot; ~6 kills/min, rarely dies).

## Protocol (JSON)
- client -> server: `{"t":"in","dx","dy","m"}` (move vector, `m` 1 = attack / -1 = defend), `{"t":"respawn"}`,
  `{"t":"equip","slot":0-4,"kind":"rose"|""}` ("" unequips)
- server -> client: `welcome` once (constants, petal and mob catalogue), `s` snapshots 20 times/s (entities within `VIEW_RADIUS`,
  petal kinds as indexes into the welcome catalogue, `ds` = drops), and a private `inv` message (inventory, loadout, lifetime kills,
  `got` = kinds just picked up) whenever it changes or an equip request was refused.
- close codes: 4401 not logged in, 4409 same account connected elsewhere (newer wins), 4500 failed to load progress.

Identity is the Django session user. Nothing the client sends is trusted: vectors are clamped, modes and kinds whitelisted,
equip checks ownership (a kind can be equipped at most as often as it is owned), swaps have a 0.4 s cooldown, messages over
512 bytes are dropped.

## Persistence
`FlorrProfile` (loadout, lifetime kills) and `FlorrPetal` (player, kind, count) hang off `Player`. New accounts get 5 basic petals
(created on first connect). Progress is written when a player disconnects, every 5 s for players with changes, and before a second
session of the same account reads it (so a reconnect never loses pickups). A crash can lose at most the last ~5 s.

## Deploying (needs the owner's approval - touches the production server)
- `python manage.py migrate` (adds two tables, nothing existing is modified), rebuild/copy `static/`.
- restart daphne (drops connected players; the world and its mobs reset). daphne must stay a single process.
- back up `db.sqlite3` first.

## Roadmap
1. (done) move, orbiting petals, mob, hp, death/respawn
2. (done) mob variety, drops, inventory and loadout with saved progress
3. rarity tiers (add a `rarity` column to `FlorrPetal`), crafting, zones with different mobs, leaderboard integration, death penalty?
4. touch controls, sound, art
