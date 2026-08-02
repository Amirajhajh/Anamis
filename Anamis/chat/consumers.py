import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Chat, Message

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.room_group_name = f'chat_{self.chat_id}'

        # اضافه شدن به گروه چت
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # خروج از گروه
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # دریافت پیام از طریق WebSocket
    async def receive(self, text_data):
        data = json.loads(text_data)
        content = data.get('message')
        # توجه: برای ارسال فایل، بهتر است ابتدا فایل را با POST آپلود کنید 
        # و سپس پیام متنی یا لینک فایل را از طریق WebSocket بفرستید.
        
        # ذخیره در دیتابیس (به صورت Async)
        await self.save_message(content)

        # ارسال پیام به همه اعضای گروه
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': content,
                'sender_id': self.scope['user'].id,
                'sender_name': self.scope['user'].username,
            }
        )

    async def chat_message(self, event):
        # ارسال پیام به کلاینت (مرورگر)
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def save_message(self, content):
        # در اینجا منطق ذخیره سازی را قرار می‌دهیم
        # (نیاز به تکمیل بر اساس مدل خودتان دارد)
        pass

