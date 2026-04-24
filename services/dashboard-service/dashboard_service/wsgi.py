"""WSGI config for dashboard_service."""

from __future__ import annotations

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dashboard_service.settings")

application = get_wsgi_application()
