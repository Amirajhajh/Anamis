#consumers.py
import json

from channels.generic.websocket import AsyncWebsocketConsumer

class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):

        self.chat_id = self.scope['url_route']['kwargs']['chat_id']

        self.room_group_name = f'chat_{self.chat_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def chat_message(self, event):

        await self.send(text_data=json.dumps({
            "message_id": event["message_id"],
            "message": event["message"],
            "sender_id": event["sender_id"],
            "time": event["time"]
        }))
