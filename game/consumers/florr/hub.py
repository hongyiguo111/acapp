"""Runs the single shared florr world inside the ASGI process.

The world lives in memory of the process that serves /wss/florr/, so the ASGI server must run as
ONE process (daphne already does). Consumers talk to the hub directly; the Redis channel layer is
not involved for this mode.
"""
import asyncio
import json
import logging
import time

from .world import World, TICK_RATE

logger = logging.getLogger(__name__)

TICK = 1.0 / TICK_RATE
MAX_DT = 0.1  # a stalled loop must not teleport everything


class FlorrHub:
    def __init__(self):
        self.world = World()
        self.clients = {}       # player id -> consumer
        self.by_name = {}       # username -> player id (one session per account)
        self._task = None

    def join(self, name, consumer):
        """Register a consumer; returns (player id, previous consumer of the same account or None)."""
        old_consumer = None
        old_pid = self.by_name.get(name)
        if old_pid is not None:
            old_consumer = self.clients.get(old_pid)
            self.leave(old_pid)
        player = self.world.add_player(name)
        self.clients[player.id] = consumer
        self.by_name[name] = player.id
        self._ensure_running()
        return player.id, old_consumer

    def leave(self, pid):
        consumer = self.clients.pop(pid, None)
        player = self.world.players.get(pid)
        if player is not None and self.by_name.get(player.name) == pid:
            del self.by_name[player.name]
        self.world.remove_player(pid)
        return consumer

    def _ensure_running(self):
        if self._task is None or self._task.done():
            self._task = asyncio.get_running_loop().create_task(self._run())

    async def _run(self):
        last = time.monotonic()
        while self.clients:
            started = time.monotonic()
            dt = min(started - last, MAX_DT)
            last = started
            try:
                self.world.step(dt)
                await self._broadcast()
            except Exception:  # keep the world alive no matter what one tick does
                logger.exception("florr tick failed")
            await asyncio.sleep(max(0.001, TICK - (time.monotonic() - started)))
        self._task = None

    async def _broadcast(self):
        for pid, consumer in list(self.clients.items()):
            snap = self.world.snapshot_for(pid)
            if snap is None:
                continue
            try:
                await consumer.send(text_data=json.dumps(snap, separators=(",", ":")))
            except Exception:
                logger.debug("dropping florr client %s after failed send", pid)
                self.leave(pid)


hub = FlorrHub()
