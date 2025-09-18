import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
# Look for .env in the main project root (two levels up from this settings.py file)
# Structure: WorkNomads/.env and WorkNomads/backend_server/backend_server/settings.py
PROJECT_ROOT = BASE_DIR.parent.parent  # Go up two levels: backend_server -> WorkNomads
dotenv_path = PROJECT_ROOT / '.env'
load_dotenv(dotenv_path)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('BACKEND_SECRET_KEY', 'django-insecure-fallback-key-change-immediately')

# JWT signing key must be shared between auth and backend services
JWT_SIGNING_KEY = os.getenv('JWT_SIGNING_KEY', 'fallback-jwt-key-change-immediately')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Parse ALLOWED_HOSTS from environment variable (comma-separated)
ALLOWED_HOSTS = []
hosts_env = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1')
if hosts_env:
    ALLOWED_HOSTS = [host.strip() for host in hosts_env.split(',')]

# Add local network IP if provided
local_ip = os.getenv('LOCAL_NETWORK_IP')
if local_ip and local_ip not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(local_ip)

# -------------------------------------------------------------------
# Applications
# -------------------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',
    'corsheaders',
    'media_handler',
    'drf_spectacular',
    'django_extensions',
]

# -------------------------------------------------------------------
# Middleware
# -------------------------------------------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',   # add corsheaders
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'backend_server.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'backend_server.wsgi.application'

# -------------------------------------------------------------------
# Database (use Postgres in production)
# -------------------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.postgresql'),
        'NAME': os.getenv('BACKEND_DB_NAME', 'backend_db'),
        'USER': os.getenv('DB_USER', 'django_user'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'password'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# -------------------------------------------------------------------
# REST Framework + JWT
# -------------------------------------------------------------------

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "media_handler.auth.JWTAuthentication",  # 👈 must be this
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Media Handler API",
    "DESCRIPTION": "Media backend (media records and collections)",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SECURITY": [{"bearerAuth": []}],
    "SECURITY_DEFINITIONS": {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.getenv('JWT_ACCESS_TOKEN_LIFETIME_MINUTES', '30'))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(os.getenv('JWT_REFRESH_TOKEN_LIFETIME_DAYS', '7'))),
    "ROTATE_REFRESH_TOKENS": os.getenv('JWT_ROTATE_REFRESH_TOKENS', 'True').lower() == 'true',
    "BLACKLIST_AFTER_ROTATION": os.getenv('JWT_BLACKLIST_AFTER_ROTATION', 'True').lower() == 'true',
    "AUTH_HEADER_TYPES": ("Bearer",),
    "SIGNING_KEY": JWT_SIGNING_KEY,  
}

# CORS Configuration
CORS_ALLOW_ALL_ORIGINS = os.getenv('CORS_ALLOW_ALL_ORIGINS', 'True').lower() == 'true'

# Parse CORS allowed origins if CORS_ALLOW_ALL_ORIGINS is False
if not CORS_ALLOW_ALL_ORIGINS:
    cors_origins = os.getenv('CORS_ALLOWED_ORIGINS', '')
    if cors_origins:
        CORS_ALLOWED_ORIGINS = [origin.strip() for origin in cors_origins.split(',')]
    else:
        CORS_ALLOWED_ORIGINS = []

# -------------------------------------------------------------------
# Password validation
# -------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# -------------------------------------------------------------------
# Internationalization
# -------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# -------------------------------------------------------------------
# Static & Media
# -------------------------------------------------------------------
STATIC_URL = "/static/"
MEDIA_URL = "/media/"
# Use the repository's `media/` folder (backend_server/media/) for development storage
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# -------------------------------------------------------------------
# CORS
# -------------------------------------------------------------------
CORS_ALLOW_ALL_ORIGINS = True  # for dev, restrict in prod

# Add this to your LOGGING configuration in settings.py:
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': True,
        },
        'media_handler': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

APPEND_SLASH = False

# -------------------------------------------------------------------
# File Upload Settings
# -------------------------------------------------------------------
# Maximum size for file uploads (10MB)
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

# Maximum allowed size for the entire request body (10MB)
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

# Maximum number of GET/POST parameters that will be read
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000

# Temporary file directory for uploads
FILE_UPLOAD_TEMP_DIR = None  # Use system default

# File upload permissions (Unix-style)
FILE_UPLOAD_PERMISSIONS = 0o644

# Directory permissions for uploaded files
FILE_UPLOAD_DIRECTORY_PERMISSIONS = None

# Handler for file uploads
FILE_UPLOAD_HANDLERS = [
    'django.core.files.uploadhandler.MemoryFileUploadHandler',
    'django.core.files.uploadhandler.TemporaryFileUploadHandler',
]
