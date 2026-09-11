
import json
from django.utils import timezone
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = self.scope["url_route"]["kwargs"]["chat_id"]
        self.user = self.scope["user"]

        if self.user.is_anonymous:
            await self.close(code=4001)
            return

        if not await self.user_can_access_chat():
            await self.close(code=4003)
            return

        self.room_group_name = f"chat_{self.chat_id}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        ids = await self.mark_messages_as_delivered()

        for message_id in ids:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "message_status",
                    "message_id": message_id,
                    "status": "delivered",
                }
            )
        

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except (json.JSONDecodeError, TypeError):
            return

        if data.get("type") == "seen":
            ids = await self.mark_messages_as_seen()

            for message_id in ids:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "message_status",
                        "message_id": message_id,
                        "status": "seen",
                    }
                )
            return

        message_id = data.get("message_id")

        if not message_id:
            return

        message = await self.get_message(message_id)

        if not message:
            return

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message_id": message.id,
                "sender_id": message.sender_id,
            }
        )

    async def chat_message(self, event):
        message = await self.get_message(event["message_id"])

        if not message:
            return

        data = {
            "message_id": message.id,
            "sender_id": message.sender_id,
            "sender_name": (
                message.sender.get_full_name()
                or message.sender.username
            ),
            "message": message.content or "",
            "time": message.created_at.strftime("%H:%M"),
            "status": message.status,
            "file_url": await self.get_file_url(message),
            "file_name": await self.get_file_name(message),
            "reply_to": (
                {
                    "id": message.reply_to_id,
                    "message": message.reply_to.content or "",
                }
                if message.reply_to else None
            ),
        }
        print("WS CHAT MESSAGE:", data)

        await self.send(text_data=json.dumps(data))

        if message.sender_id != self.user.id:
            changed = await self.set_message_delivered(message.id)

            if changed:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "message_status",
                        "message_id": message.id,
                        "status": "delivered",
                    }
                )

    async def message_status(self, event):
        await self.send(text_data=json.dumps({
            "type": "status",
            "message_id": event["message_id"],
            "status": event["status"],
        }))

    @database_sync_to_async
    def user_can_access_chat(self):
        from .models import Chat, ChatMember

        try:
            chat = Chat.objects.get(id=self.chat_id)
        except Chat.DoesNotExist:
            return False

        if chat.type == Chat.PRIVATE:
            return (
                chat.user1_id == self.user.id
                or chat.user2_id == self.user.id
            )

        return ChatMember.objects.filter(
            chat_id=chat.id,
            user_id=self.user.id
        ).exists()

    @database_sync_to_async
    def get_message(self, message_id):
        from .models import Message

        return (
            Message.objects
            .select_related("sender", "reply_to")
            .filter(
                id=message_id,
                chat_id=self.chat_id
            )
            .first()
        )

    @database_sync_to_async
    def get_file_url(self, message):
        if not message.file:
            return None
        return message.file.url

    @database_sync_to_async
    def get_file_name(self, message):
        if not message.file:
            return None
        return message.file.name.split("/")[-1]

    @database_sync_to_async
    def set_message_delivered(self, message_id):
        from .models import Message

        updated = (
            Message.objects
            .filter(
                id=message_id,
                chat_id=self.chat_id
            )
            .exclude(sender_id=self.user.id)
            .exclude(status="seen")
            .update(status="delivered")
        )

        return updated > 0

    @database_sync_to_async
    def mark_messages_as_delivered(self):
        from .models import Message

        ids = list(
            Message.objects
            .filter(
                chat_id=self.chat_id,
                status="sent"
            )
            .exclude(sender_id=self.user.id)
            .values_list("id", flat=True)
        )

        if ids:
            Message.objects.filter(
                id__in=ids
            ).update(status="delivered")

        return ids

    @database_sync_to_async
    def mark_messages_as_seen(self):
        from .models import Message

        ids = list(
            Message.objects
            .filter(chat_id=self.chat_id)
            .exclude(sender_id=self.user.id)
            .exclude(status="seen")
            .values_list("id", flat=True)
        )

        if ids:
            Message.objects.filter(
                id__in=ids
            ).update(
                status="seen",
                seen_at=timezone.now()
            )

        return ids

