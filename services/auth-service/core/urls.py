"""Routes for the core app."""

from __future__ import annotations

from django.urls import path

from core.views import (
    HealthView,
    IntrospectView,
    LoginView,
    LogoutView,
    MetricsView,
    RefreshView,
    UserDetailView,
    UserListView,
    VerifyView,
)

urlpatterns = [
    path("metrics/", MetricsView.as_view(), name="metrics-root"),
    path("api/auth/metrics/", MetricsView.as_view(), name="metrics-auth"),
    path("health/", HealthView.as_view(), name="health-root"),
    path("api/auth/health/", HealthView.as_view(), name="health-auth"),
    path("api/auth/login/", LoginView.as_view(), name="auth-login"),
    path("api/auth/refresh/", RefreshView.as_view(), name="auth-refresh"),
    path("api/auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("api/auth/users/", UserListView.as_view(), name="auth-users"),
    path(
        "api/auth/users/<uuid:pk>/",
        UserDetailView.as_view(),
        name="auth-users-detail",
    ),
    path("auth/verify/", VerifyView.as_view(), name="auth-verify"),
    path("auth/introspect/", IntrospectView.as_view(), name="auth-introspect"),
]
