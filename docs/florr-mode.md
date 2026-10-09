# 花瓣模式 (florr-style co-op mode)

A persistent, shared, server-authoritative world next to the original single/dual/multi modes.
Players move around a 3000x3000 map, petals orbit them and damage mobs on contact, mobs hurt players
and break petals. Co-op only (no PvP).

## Layout
| Part | File |
|---|---|
| Simulation (pure Python, unit tested) | `game/consumers/florr/world.py` |
| Tick loop + connection registry | `game/consumers/florr/hub.py` |
| WebSocket endpoint `/wss/florr/` | `game/consumers/florr/index.py`, `game/routing.py` |
| Client (own canvas + render loop) | `game/static/js/src/florr/zbase.js`, `game/static/css/florr.css` |
| Tests | `game/tests.py` (`manage.py test game`), `scripts/florr_smoke.py` (needs `scripts/dev.ps1` running) |

## Protocol (JSON)
- client -> server: `{"t":"in","dx":-1..1,"dy":-1..1,"m":-1|0|1}` (move vector; `m` 1 = petals out, -1 = petals in), `{"t":"respawn"}`
- server -> client: `{"t":"welcome", ...constants}` once, then `{"t":"s","me":id,"ps":[players],"ms":[mobs]}` 20 times/s,
  only entities within `VIEW_RADIUS` of the receiving player.
- close codes: 4401 not logged in, 4409 same account connected elsewhere (newer wins).

The identity of a connection is the Django session user. Nothing the client sends is trusted: vectors are
clamped, modes whitelisted, messages over 512 bytes dropped.

## Constraints
- The world lives in the memory of the ASGI process, so `daphne` must stay a single process.
- Restarting the ASGI process drops everyone and resets the world (phase 1 persists nothing).

## Roadmap
1. (done) move, orbiting petals, one mob (beetle), hp, death/respawn, kill counter
2. mob variety, drops, inventory and loadout (needs DB models; progress is kept across runs)
3. rarity, crafting, zones, leaderboard integration
4. touch controls, sound, art
