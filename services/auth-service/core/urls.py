"""Routes for the core app."""

from __future__ import annotations

from django.urls import path

from core.views import HealthView, LoginView

urlpatterns = [
    path("health/", HealthView.as_view(), name="health-root"),
    path("api/auth/health/", HealthView.as_view(), name="health-auth"),
    path("api/auth/login/", LoginView.as_view(), name="auth-login"),
]
