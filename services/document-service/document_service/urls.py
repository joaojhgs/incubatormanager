"""URL configuration for document_service."""

from __future__ import annotations

from core.schema_views import DocumentSpectacularSwaggerView
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path(
        "api/documents/schema/",
        SpectacularAPIView.as_view(),
        name="documents-schema",
    ),
    path(
        "api/documents/schema/swagger/",
        DocumentSpectacularSwaggerView.as_view(url_name="documents-schema"),
        name="documents-swagger-ui",
    ),
]
