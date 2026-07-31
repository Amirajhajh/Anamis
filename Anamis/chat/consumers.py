import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.exceptions import PermissionDenied

# فرض می‌کنیم مدل‌ها در مسیرهای زیر هستند
from chat.models import Chat, Message, ChatMember

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.chat_group_name = f'chat_{self.chat_id}'
        self.user = self.scope['user']

        # ۱. بررسی احراز هویت
        if self.user.is_anonymous:
            await self.close()
            return

        # ۲. بررسی سطح دسترسی (Security Check)
        # آیا کاربر عضو این چت هست؟
        is_allowed = await self.check_user_membership(self.chat_id, self.user)
        
        if not is_allowed:
            # اگر کاربر عضو نبود، اتصال را قطع کن
            await self.close()
            return

        await self.channel_layer.group_add(
            self.chat_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.chat_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_text = data.get('message', '').strip()
            
            if not message_text:
                return 

            # ذخیره در دیتابیس
            message = await self.create_message(int(self.chat_id), self.user, message_text)

            if message:
                # ارسال پیام به همه اعضای گروه (از جمله خود کاربر)
                await self.channel_layer.group_send(
                    self.chat_group_name,
                    {
                        'type': 'chat_message',
                        'message': message.content,
                        'sender': message.sender.username,
                        'timestamp': message.created_at.isoformat(),
                        'message_id': message.id,
                    }
                )
        except Exception as e:
            print(f"Error in receive: {e}")

    async def chat_message(self, event):
        # ارسال پیام به WebSocket کلاینت
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender': event.get('sender'),
            'timestamp': event.get('timestamp'),
            'message_id': event.get('message_id'),
        }))

    # --- متدهای کمکی دیتابیس (Sync to Async) ---

    @database_sync_to_async
    def check_user_membership(self, chat_id, user):
        """بررسی اینکه آیا کاربر عضو این چت است یا خیر"""
        try:
            chat = Chat.objects.get(id=chat_id)
            # اگر چت خصوصی بود
            if chat.type == Chat.PRIVATE:
                return chat.user1 == user or chat.user2 == user
            # اگر چت گروهی بود
            return ChatMember.objects.filter(chat=chat, user=user).exists()
        except Chat.DoesNotExist:
            return False

    @database_sync_to_async
    def create_message(self, chat_id, sender, content):
        try:
            chat = Chat.objects.get(id=chat_id)
            return Message.objects.create(chat=chat, sender=sender, content=content)
        except Exception as e:
            print(f"Error creating message: {e}")
            return None

