import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from .models import Message, Chat


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):

        self.chat_id = self.scope['url_route']['kwargs']['chat_id']

        self.room_group_name = f"chat_{self.chat_id}"


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



    async def receive(self, text_data):

        data = json.loads(text_data)

        content = data.get("message")


        message = await self.save_message(content)


        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": message.content,
                "time": message.created_at.strftime("%H:%M"),
                "sender": message.sender.username
            }
        )



    async def chat_message(self, event):

        await self.send(
            text_data=json.dumps({
                "message": event["message"],
                "time": event["time"],
                "sender": event["sender"]
            })
        )



    @database_sync_to_async
    def save_message(self, content):

        user = self.scope["user"]

        chat = Chat.objects.get(
            id=self.chat_id
        )


        return Message.objects.create(
            sender=user,
            chat=chat,
            content=content
        )
