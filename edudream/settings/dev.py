from datetime import timedelta
from .base import *

SECRET_KEY = env('SECRET_KEY')

DEBUG = True

ALLOWED_HOSTS = ["*"]

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8080",
    "http://localhost:4200",
    "http://localhost:80",
    "http://localhost:3000",
    "http://localhost",
    "https://edudream.tm-dev.xyz",
    "https://edu-dream.netlify.app",
    "http://127.0.0.1"
]

# from corsheaders.defaults import default_headers

CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS


# Database
DATABASES = {
    'default': {
        'ENGINE': env('DATABASE_ENGINE', None),
        'NAME': env('DATABASE_NAME', None),
        'USER': env('DATABASE_USER', None),
        'PASSWORD': env('DATABASE_PASSWORD', None),
        'HOST': env('DATABASE_HOST', None),
        'PORT': env('DATABASE_PORT', None),
    },
}
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

# EMAIL SETTINGS
EMAIL_URL = env('EMAIL_URL', None)
EMAIL_API_KEY = env('EMAIL_API_KEY', None)
EMAIL_FROM = env('EMAIL_FROM', None)

# STRIPE KEY
STRIPE_API_KEY = env('STRIPE_API_KEY', None)

# WEBEX
WEBEX_API_KEY = env('WEBEX_API_KEY', None)
WEBEX_BASE_URL = env('WEBEX_BASE_URL', None)

# Simple JWT
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=3),
    'UPDATE_LAST_LOGIN': True,
    'AUTH_HEADER_TYPES': ('Bearer', 'Token',),
}

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {module} {thread:d} - {message}',
            'style': '{',
            'datefmt': '%d-%m-%Y %H:%M:%S'
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOG_DIR, 'edudream.log'),
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.server': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}



