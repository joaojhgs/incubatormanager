"""Routes for the core app."""

from __future__ import annotations

from django.urls import path

from core.views import DashboardOverviewView, DashboardReportsView, HealthView

urlpatterns = [
    path("health/", HealthView.as_view(), name="health-root"),
    path("api/dashboard/health/", HealthView.as_view(), name="health-dashboard"),
    path("api/dashboard/overview/", DashboardOverviewView.as_view(), name="dashboard-overview"),
    path("api/dashboard/reports/", DashboardReportsView.as_view(), name="dashboard-reports"),
]
