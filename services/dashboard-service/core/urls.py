"""Routes for the core app."""

from __future__ import annotations

from django.urls import path

from core.views import (
    DashboardCompaniesView,
    DashboardFinanceView,
    DashboardOverviewView,
    DashboardReportsView,
    DashboardSpacesView,
    HealthView,
    MetricsView,
)

urlpatterns = [
    path("metrics/", MetricsView.as_view(), name="metrics-root"),
    path("api/dashboard/metrics/", MetricsView.as_view(), name="metrics-dashboard"),
    path("health/", HealthView.as_view(), name="health-root"),
    path("api/dashboard/health/", HealthView.as_view(), name="health-dashboard"),
    path("api/dashboard/overview/", DashboardOverviewView.as_view(), name="dashboard-overview"),
    path("api/dashboard/companies/", DashboardCompaniesView.as_view(), name="dashboard-companies"),
    path("api/dashboard/spaces/", DashboardSpacesView.as_view(), name="dashboard-spaces"),
    path("api/dashboard/finance/", DashboardFinanceView.as_view(), name="dashboard-finance"),
    path("api/dashboard/reports/", DashboardReportsView.as_view(), name="dashboard-reports"),
    path(
        "dashboard/companies/",
        DashboardCompaniesView.as_view(),
        name="dashboard-companies-alias",
    ),
    path("dashboard/spaces/", DashboardSpacesView.as_view(), name="dashboard-spaces-alias"),
    path("dashboard/finance/", DashboardFinanceView.as_view(), name="dashboard-finance-alias"),
]
