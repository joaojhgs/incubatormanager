"""Routes for the core app."""

from __future__ import annotations

from django.urls import path
from rest_framework.routers import DefaultRouter

from core.maturity_views import MaturityStageViewSet
from core.views import CAEListCreateView, HealthView

router = DefaultRouter()
router.register(
    "api/companies/maturity-stages",
    MaturityStageViewSet,
    basename="maturity-stage",
)

urlpatterns = [
    path("health/", HealthView.as_view(), name="health-root"),
    path("api/companies/health/", HealthView.as_view(), name="health-companies"),
    path("api/companies/cae/", CAEListCreateView.as_view(), name="cae-list-create"),
    *router.urls,
]
