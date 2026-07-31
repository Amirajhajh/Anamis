from django.db import models
from django.contrib.auth.models import AbstractUser
from chat.models import Chat, Message


class User(AbstractUser):
    # ... (فیلدهای قبلی مثل username, email, ...)

    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    bio = models.CharField(max_length=255, blank=True, null=True)

    # --- فیلدهای جدید ---
    online_status = models.BooleanField(default=False) # True یعنی آنلاین، False یعنی آفلاین
    last_seen = models.DateTimeField(null=True, blank=True) # زمان آخرین بازدید

    # اگر فیلد دیفالتی دیگری دارید، اینجا اضافه کنید
    # ...

    def __str__(self):
        return self.username
