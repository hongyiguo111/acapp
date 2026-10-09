import json
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from . import store
from . import world as w
from .hub import hub

logger = logging.getLogger(__name__)

MAX_MESSAGE_BYTES = 512


class FlorrPlayer(AsyncWebsocketConsumer):
    """One websocket per logged-in player. Identity comes from the Django session, never from the client."""

    pid = None

    async def connect(self):
        user = self.scope.get("user")
        if user is None or not user.is_authenticated:
            await self.close(code=4401)
            return
        name = user.get_username()
        # a still-connected older session of this account must reach the database before we read it
        await hub.save_account(name)
        try:
            state = await database_sync_to_async(store.load)(name)
        except Exception:
            logger.exception("loading florr progress of %s failed", name)
            await self.close(code=4500)
            return
        await self.accept()
        self.pid, previous = hub.join(name, self, **state)
        # welcome must be queued before anything else yields, so it always precedes the first snapshot
        await self.send(text_data=json.dumps({"t": "welcome", "id": self.pid, **w.welcome_info()}))
        if previous is not None:  # same account opened in another tab: the newer one wins
            await previous.close(code=4409)

    async def disconnect(self, close_code):
        # a replaced session must not remove its successor
        if self.pid is not None and hub.clients.get(self.pid) is self:
            await hub.save_player(self.pid)
            hub.leave(self.pid)
        self.pid = None

    async def receive(self, text_data=None, bytes_data=None):
        if self.pid is None or not text_data or len(text_data) > MAX_MESSAGE_BYTES:
            return
        try:
            msg = json.loads(text_data)
        except ValueError:
            return
        if not isinstance(msg, dict):
            return
        kind = msg.get("t")
        if kind == "in":
            hub.world.set_input(self.pid, msg.get("dx", 0), msg.get("dy", 0), msg.get("m", 0))
        elif kind == "respawn":
            hub.world.respawn(self.pid)
        elif kind == "equip":
            hub.world.equip(self.pid, msg.get("slot"), msg.get("item"))
        elif kind == "craft":
            hub.world.craft(self.pid, msg.get("item"))
