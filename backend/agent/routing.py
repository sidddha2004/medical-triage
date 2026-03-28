from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/triage/$', consumers.SimpleTriageConsumer.as_asgi()),
    re_path(r'ws/triage/(?P<session_id>\d+)/$', consumers.TriageConsumer.as_asgi()),
]
