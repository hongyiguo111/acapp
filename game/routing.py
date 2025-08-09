from django.urls import path
from game.consumers.multiplayer.index import MultiPlayer
from game.consumers.chatroom.index import ChatRoomConsumer

websocket_urlpatterns = [
        path("wss/multiplayer/", MultiPlayer.as_asgi(), name = "wss_multiplayer"),
        path("wss/chatroom/", ChatRoomConsumer.as_asgi(), name = "wss_chatroom"),
        ]
