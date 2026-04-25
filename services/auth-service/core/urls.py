"""Routes for the core app."""

from __future__ import annotations

from django.urls import path

from core.views import HealthView, IntrospectView, LoginView, LogoutView, RefreshView

urlpatterns = [
    path("health/", HealthView.as_view(), name="health-root"),
    path("api/auth/health/", HealthView.as_view(), name="health-auth"),
    path("api/auth/login/", LoginView.as_view(), name="auth-login"),
    path("api/auth/refresh/", RefreshView.as_view(), name="auth-refresh"),
    path("api/auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("auth/introspect/", IntrospectView.as_view(), name="auth-introspect"),
]
