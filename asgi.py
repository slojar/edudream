import os
import django
from decouple import config

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from home.routing import websocket_urlpatterns

with open('.env', 'a+') as f:
    f.close()


def main():
    """Run administrative tasks."""
    if config('env', '') == 'prod' or os.getenv('env', 'dev') == 'prod':
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edudream.settings.prod')
    else:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edudream.settings.dev')

    # Initialize Django ASGI application early to ensure the AppRegistry
    # is populated before importing code that may import ORM models.
    # django_asgi_app = get_asgi_application()

    django.setup()

    application = ProtocolTypeRouter({
        "http": get_asgi_application(),
        "websocket": URLRouter(websocket_urlpatterns)
        # Just HTTP for now. (We can add other protocols later.)
    })


if __name__ == '__main__':
    main()
