import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async

# حذف ایمپورت از اینجا:
# from .models import Message 

class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        # اضافه کردن ایمپورت در اینجا:
        from .models import Message 

        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.room_group_name = f'chat_{self.chat_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # کوئری‌زدن با مدل
        messages = await sync_to_async(list)(
            Message.objects.filter(chat_id=self.chat_id, status="sent")
            .exclude(sender=self.scope["user"])
        )

        for message in messages:
            message.status = "delivered"
            await sync_to_async(message.save)()

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "message_status",
                    "message_id": message.id,
                    "status": "delivered"
                }
            )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def chat_message(self, event):
        # اضافه کردن ایمپورت در اینجا:
        from .models import Message 
        await self.send(text_data=json.dumps({
            "type": "message",
            "message_id": event["message_id"],
            "message": event["message"],
            "sender_id": event["sender_id"],
            "file_url": event.get("file_url"),
            "file_name": event.get("file_name"),
            "time": event["time"],
        }))

        if str(self.scope["user"].id) != str(event["sender_id"]):
            message = await sync_to_async(Message.objects.get)(id=event["message_id"])
            message.status = "delivered"
            await sync_to_async(message.save)()

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "message_status",
                    "message_id": event["message_id"],
                    "status": "delivered"
                }
            )

    async def message_status(self, event):
        await self.send(text_data=json.dumps({
            "type": "status",
            "message_id": event["message_id"],
            "status": event["status"]
        }))
