from channels.generic.websocket import AsyncWebsocketConsumer
import json


class ChatRoomConsumer(AsyncWebsocketConsumer):
    online_users = {}

    async def connect(self):
        self.room_group_name = 'chatroom'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        if self.channel_name in self.online_users:
            username = self.online_users[self.channel_name]['username']
            del self.online_users[self.channel_name]

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_leave',
                    'username': username,
                }
            )

            await self.send_users_list();

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        event = data['event']

        if event == 'join':
            await self.handle_join(data)
        elif event == 'message':
            await self.handle_message(data)
        elif event == 'leave':
            await self.handle_leave(data)

    async def handle_join(self, data):
        self.online_users[self.channel_name] = {
            'username': data['username'],
            'photo': data['photo'],
        }

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_join',
                'username': data['username'],
            }
        )

        await self.send_users_list();

    async def handle_message(self, data):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'username': data['username'],
                'message': data['message'],
            }
        )

    async def handle_leave(self, data):
        if self.channel_name in self.online_users:
            del self.online_users[self.channel_name]

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_leave',
                    'username': data['username'],
                }
            )

            await self.send_users_list();

    async def send_users_list(self):
        users_list = list(self.online_users.values())

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'users_list_update',
                'users': users_list
            }
        )

    async def user_join(self, event):
        await self.send(text_data=json.dumps({
            'event': 'join',
            'username': event['username'],
        }))

    async def user_leave(self, event):
        await self.send(text_data=json.dumps({
            'event': 'leave',
            'username': event['username'],
        }))

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'event': 'message',
            'username': event['username'],
            'message': event['message'],
        }))

    async def users_list_update(self, event):
        await self.send(text_data=json.dumps({
            'event': 'users_list',
            'users': event['users'],
        }))