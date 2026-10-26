import os
from pathlib import Path

from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured
from django.core.management.utils import get_random_secret_key

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DEBUG = os.getenv("DEBUG", "False").strip().lower() in {"1", "true", "yes"}
SECRET_KEY = os.getenv("SECRET_KEY", "").strip()
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured("Defina SECRET_KEY nas variáveis de ambiente.")
    SECRET_KEY = get_random_secret_key()
elif SECRET_KEY.startswith("django-insecure-") and not DEBUG:
    raise ImproperlyConfigured(
        "Configure uma SECRET_KEY segura antes de desativar DEBUG."
    )

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")
    if host.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework.authtoken",
    "tarefas",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "todoapi.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "todoapi.wsgi.application"
ASGI_APPLICATION = "todoapi.asgi.application"

supabase_db = {
    "NAME": os.getenv("SUPABASE_DB_NAME", "").strip(),
    "USER": os.getenv("SUPABASE_DB_USER", "").strip(),
    "PASSWORD": os.getenv("SUPABASE_DB_PASSWORD", ""),
    "HOST": os.getenv("SUPABASE_DB_HOST", "").strip(),
    "PORT": os.getenv("SUPABASE_DB_PORT", "").strip(),
}
configured_db_values = [bool(value) for value in supabase_db.values()]

if any(configured_db_values) and not all(configured_db_values):
    raise ValueError(
        "Configuração incompleta do Supabase. Defina "
        "SUPABASE_DB_NAME, SUPABASE_DB_USER, SUPABASE_DB_PASSWORD, "
        "SUPABASE_DB_HOST e SUPABASE_DB_PORT."
    )

if all(configured_db_values):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            **supabase_db,
            "OPTIONS": {"sslmode": "require"},
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}
