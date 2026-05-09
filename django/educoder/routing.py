"""Aggregate websocket URL patterns from each app."""
from apps.realtime.routing import websocket_urlpatterns as realtime_ws

websocket_urlpatterns = []
websocket_urlpatterns += realtime_ws
