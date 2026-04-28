"""Routes for the core app."""

from __future__ import annotations

from django.urls import path

from core.document_views import (
    DocumentDestroyView,
    DocumentDownloadView,
    DocumentListView,
    DocumentUploadView,
)
from core.views import HealthView

urlpatterns = [
    path("health/", HealthView.as_view(), name="health-root"),
    path("api/documents/health/", HealthView.as_view(), name="health-documents"),
    path("api/documents/upload/", DocumentUploadView.as_view(), name="document-upload"),
    path(
        "api/documents/<uuid:document_id>/download/",
        DocumentDownloadView.as_view(),
        name="document-download",
    ),
    path(
        "api/documents/<uuid:document_id>/",
        DocumentDestroyView.as_view(),
        name="document-delete",
    ),
    path("api/documents/", DocumentListView.as_view(), name="document-list"),
]
