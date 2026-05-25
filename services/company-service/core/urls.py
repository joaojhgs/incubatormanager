"""Routes for the core app."""

from __future__ import annotations

from django.urls import path
from rest_framework.routers import DefaultRouter

from core.maturity_views import MaturityStageViewSet
from core.views import (
    CAEListCreateView,
    CompanyCreateUpdateView,
    CompanyDetailUpdateDeleteView,
    CompanyEmployeeDetailView,
    CompanyEmployeeListCreateView,
    CompanyEmployeeStatsView,
    CompanyMaturityStageChangeView,
    CompanyStatsView,
    HealthView,
)

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
    path("api/companies/stats/", CompanyStatsView.as_view(), name="company-stats"),
    path(
        "api/companies/<uuid:company_id>/employees/",
        CompanyEmployeeListCreateView.as_view(),
        name="company-employee-list-create",
    ),
    path(
        "api/companies/<uuid:company_id>/employees/<uuid:employee_id>/",
        CompanyEmployeeDetailView.as_view(),
        name="company-employee-detail",
    ),
    path(
        "api/companies/<uuid:company_id>/employees/stats/",
        CompanyEmployeeStatsView.as_view(),
        name="company-employee-stats",
    ),
    path(
        "api/companies/<uuid:pk>/",
        CompanyDetailUpdateDeleteView.as_view(),
        name="company-detail",
    ),
    path(
        "api/companies/",
        CompanyCreateUpdateView.as_view(),
        name="company-list",
    ),
    *router.urls,
]
