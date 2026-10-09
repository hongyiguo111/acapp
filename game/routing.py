from django.urls import path
from game.consumers.multiplayer.index import MultiPlayer
from game.consumers.dual.index import DualPlayer
from game.consumers.chatroom.index import ChatRoomConsumer
from game.consumers.florr.index import FlorrPlayer

websocket_urlpatterns = [
    path("wss/multiplayer/", MultiPlayer.as_asgi(), name="wss_multiplayer"),
    path("wss/dual/", DualPlayer.as_asgi(), name="wss_dual"),
    path("wss/chatroom/", ChatRoomConsumer.as_asgi(), name="wss_chatroom"),
    path("wss/florr/", FlorrPlayer.as_asgi(), name="wss_florr"),
]
