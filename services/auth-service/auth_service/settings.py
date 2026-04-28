"""Django settings for the auth microservice."""

from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path

import dj_database_url
from ilb_common.bootstrap import shared_settings

BASE_DIR = Path(__file__).resolve().parent.parent

SHARED = shared_settings()

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "django-insecure-dev-only-change-me")

DEBUG = os.environ.get("DJANGO_DEBUG", "false").lower() in {"1", "true", "yes"}

ALLOWED_HOSTS = [
    h.strip() for h in os.environ.get("ALLOWED_HOSTS", "*").split(",") if h.strip()
] or ["*"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "rest_framework_simplejwt",
    "users",
    "core",
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

ROOT_URLCONF = "auth_service.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "auth_service.wsgi.application"

DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    ),
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]

LANGUAGE_CODE = "en-gb"
TIME_ZONE = SHARED["TIME_ZONE"]
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "users.User"

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_RATES": {
        "login_ip": "5/minute",
    },
}

SPECTACULAR_SETTINGS = {
    "TITLE": "ILB Auth Service API",
    "DESCRIPTION": "Authentication and identity API.",
    "VERSION": "0.1.0",
    # List OpenAPI + Swagger UI in the exported schema (plan: eight paths total).
    "SERVE_INCLUDE_SCHEMA": True,
}

# Default cache: JTI blocklist, login IP throttle, and DRF throttling share this backend.
CACHES = (
    {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": SHARED["REDIS_URL"],
        }
    }
    if SHARED.get("REDIS_URL")
    else {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "ilb-auth-cache",
        }
    }
)

_JWT_SIGNING_KEY = os.environ.get("AUTH_JWT_SECRET", "").strip() or SECRET_KEY

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(seconds=SHARED["JWT_ACCESS_TTL_SECONDS"]),
    "REFRESH_TOKEN_LIFETIME": timedelta(seconds=SHARED["JWT_REFRESH_TTL_SECONDS"]),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": False,
    "TOKEN_REFRESH_SERIALIZER": "core.serializers.ILBTokenRefreshSerializer",
    "SIGNING_KEY": _JWT_SIGNING_KEY,
}


# DRF may cache ``REST_FRAMEWORK`` before this module finishes assigning it; refresh once
# so ``DEFAULT_THROTTLE_RATES`` and ``DEFAULT_SCHEMA_CLASS`` match the values above.
def _reload_drf_api_settings() -> None:
    from rest_framework.settings import api_settings as drf_api_settings

    drf_api_settings.reload()


_reload_drf_api_settings()
