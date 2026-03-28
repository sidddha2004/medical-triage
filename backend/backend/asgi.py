import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

django_asgi = get_asgi_application()

# Import websocket routes after django_asgi to ensure models are loaded
from agent.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": django_asgi,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})
