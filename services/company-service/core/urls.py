"""Routes for the core app."""

from __future__ import annotations

from django.urls import path

from core.views import CAEListCreateView, HealthView

urlpatterns = [
    path("health/", HealthView.as_view(), name="health-root"),
    path("api/companies/health/", HealthView.as_view(), name="health-companies"),
    path("api/companies/cae/", CAEListCreateView.as_view(), name="cae-list-create"),
]
