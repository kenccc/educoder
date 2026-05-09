from django.urls import re_path

from .consumers import AttemptConsumer, ClassroomConsumer

websocket_urlpatterns = [
    re_path(r"^ws/classroom/(?P<classroom_id>\d+)/$", ClassroomConsumer.as_asgi()),
    re_path(r"^ws/attempt/(?P<attempt_id>\d+)/$",     AttemptConsumer.as_asgi()),
]
