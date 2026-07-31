
import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

import chat.routing # import routing file

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "messenger_project.settings")

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack( # برای احراز هویت کاربر از طریق WebSocket
        URLRouter(
            chat.routing.websocket_urlpatterns
        )
    ),
})
