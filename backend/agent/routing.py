from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/triage/$', consumers.TriageConsumer.as_asgi()),
]
