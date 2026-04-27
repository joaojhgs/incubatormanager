"""URL configuration for auth_service."""

from __future__ import annotations

from core.schema_views import AuthSpectacularSwaggerView
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path(
        "api/auth/schema/",
        SpectacularAPIView.as_view(),
        name="auth-schema",
    ),
    path(
        "api/auth/schema/swagger/",
        AuthSpectacularSwaggerView.as_view(url_name="auth-schema"),
        name="auth-swagger-ui",
    ),
]
