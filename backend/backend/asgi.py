import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.db import database_sync_to_async
from urllib.parse import parse_qs

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

django_asgi = get_asgi_application()

# Import websocket routes after django_asgi to ensure models are loaded
from agent.routing import websocket_urlpatterns


class TokenAuthMiddleware:
    """Custom middleware to authenticate WebSocket connections via token query param."""

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        # Parse query string to get token
        query_string = scope.get('query_string', b'').decode('utf-8')
        params = parse_qs(query_string)
        token = params.get('token', [None])[0]

        # Create anonymous user by default
        from django.contrib.auth.models import AnonymousUser
        scope['user'] = AnonymousUser()

        if token:
            # Get user from JWT token
            user = await self.get_user_from_token(token)
            if user:
                scope['user'] = user
                print(f'WebSocket authenticated user: {user.email}')
            else:
                print('WebSocket token invalid')

        return await self.inner(scope, receive, send)

    @database_sync_to_async
    def get_user_from_token(self, token_str):
        from rest_framework_simplejwt.tokens import AccessToken
        from django.contrib.auth.models import User
        try:
            access_token = AccessToken(token_str)
            user_id = access_token.get('user_id')
            user = User.objects.get(id=user_id)
            return user
        except Exception as e:
            print(f'Error getting user from token: {e}')
            return None


application = ProtocolTypeRouter({
    "http": django_asgi,
    "websocket": TokenAuthMiddleware(
        URLRouter(websocket_urlpatterns)
    ),
})
