from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path, re_path

from .consumers import ClassroomConsumer

# application = ProtocolTypeRouter({
#     "websocket": URLRouter([
#         path("webclassroom", ClassroomConsumer.as_asgi()),
#     ]),
# })

websocket_urlpatterns = [
    path("webclassroom/", ClassroomConsumer.as_asgi())
    # re_path(r"webclassroom/", ClassroomConsumer.as_asgi())
]

