"""ASGI config for ticket_service."""

from __future__ import annotations

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ticket_service.settings")

application = get_asgi_application()
