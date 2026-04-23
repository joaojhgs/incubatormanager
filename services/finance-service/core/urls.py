"""Routes for the core app."""

from __future__ import annotations

from django.urls import path

from core.views import HealthView

urlpatterns = [
    path("health/", HealthView.as_view(), name="health-root"),
    path("api/finance/health/", HealthView.as_view(), name="health-finance"),
]
