# chat/routing.py
from django.urls import re_path
from . import consumers
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import chat_app.routing

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<room_name>[^/]+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/group_chat/(?P<group_id>\d+)/$', consumers.GroupChatConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    "websocket": AuthMiddlewareStack(
        URLRouter(
            chat_app.routing.websocket_urlpatterns
        )
    ),
})
