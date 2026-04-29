"""Django settings for the document microservice."""

from __future__ import annotations

import os
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

ROOT_URLCONF = "document_service.urls"

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

WSGI_APPLICATION = "document_service.wsgi.application"

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

LANGUAGE_CODE = "en-gb"
TIME_ZONE = SHARED["TIME_ZONE"]
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Allow bodies slightly above the 20 MiB app limit so we can return HTTP 413 in the view.
_DATA_CAP = 25 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = _DATA_CAP
FILE_UPLOAD_MAX_MEMORY_SIZE = _DATA_CAP

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "ilb_common.permissions.HeaderAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

SPECTACULAR_SETTINGS = {
    "TITLE": "ILB Document Service API",
    "DESCRIPTION": "Document bounded context API (upload, download, health).",
    "VERSION": "0.1.0",
    # Include OpenAPI and Swagger paths in exported schema.yml (parity with auth-service).
    "SERVE_INCLUDE_SCHEMA": True,
    # Do not run gateway header auth on schema UI (HeaderAuthentication requires X-User-Id).
    "SERVE_AUTHENTICATION": [],
}
