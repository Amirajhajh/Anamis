from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User

# خط زیر باید حذف شود: from .models import Chat, ChatMessage


class Chat(models.Model):
    PRIVATE = 'private'
    GROUP = 'group'
    CHAT_TYPE_CHOICES = [
        (PRIVATE, 'Private'),
        (GROUP, 'Group'),
    ]

    user1 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chats_as_user1',
        null=True,
        blank=True
    )
    user2 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chats_as_user2',
        null=True,
        blank=True
    )
    

    type = models.CharField(max_length=10, choices=CHAT_TYPE_CHOICES, default=PRIVATE)
    group_name = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    group = models.ForeignKey(
            'Group',
            on_delete=models.CASCADE,
            related_name='chat_link', # یا نام دلخواه دیگر
            null=True, blank=True
        )
    def __str__(self):
        if self.type == self.PRIVATE:
            if self.user1 and self.user2:
                return f"Private Chat: {self.user1.username} & {self.user2.username}"
            return f"Private Chat #{self.id}"
        return self.group_name or f"Group Chat #{self.id}"


class ChatMember(models.Model):

    chat = models.ForeignKey('chat.Chat', on_delete=models.CASCADE, related_name='user1_chats')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_memberships'
    )
    joined_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('chat', 'user')

    def __str__(self):
        return f"{self.user.username} in chat '{self.chat}'"


class Message(models.Model):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_chat_messages'
    )
    # اینجا هم اگر نیاز به ارجاع به Chat داری، از رشته استفاده کن
    chat = models.ForeignKey('Chat', on_delete=models.CASCADE, related_name='messages')
    content = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to='chat_files/%Y/%m/%d/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        sender_username = self.sender.get_username() if self.sender else "Unknown"
        # در اینجا هم اگر ارجاع به chat داری، مطمئن شو که از رشته استفاده نشده باشد چون خودِ مدل ChatMessage است.
        return f"Message from {sender_username} in {self.chat}"

class Group(models.Model):
    name = models.CharField(max_length=100)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='groups_member')
    DEFAULT_OWNER_ID = 1

    chat = models.OneToOneField(
            'Chat',
            on_delete=models.SET_NULL, # یا CASCADE, depending on your logic
            related_name='group_link',
            null=True, blank=True
        )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_groups',
        default=DEFAULT_OWNER_ID # اضافه کردن این خط
        )


    def __str__(self):
        return self.name

class Channel(models.Model):
    name = models.CharField(max_length=100)
    # فیلدهای دیگر در صورت نیاز

    def __str__(self):
        return self.name

class channels():
    pass
