"""Routes for the contract service."""

from __future__ import annotations

from django.urls import path

from core.views import (
    ContractActivateView,
    ContractCompanyListView,
    ContractDetailView,
    ContractListCreateView,
    ContractTerminateView,
    HealthView,
)

urlpatterns = [
    path("health/", HealthView.as_view(), name="health-root"),
    path("api/contracts/health/", HealthView.as_view(), name="health-contracts"),
    path("api/contracts/", ContractListCreateView.as_view(), name="contract-list"),
    path("api/contracts/<uuid:pk>/", ContractDetailView.as_view(), name="contract-detail"),
    path(
        "api/contracts/<uuid:pk>/activate/",
        ContractActivateView.as_view(),
        name="contract-activate",
    ),
    path(
        "api/contracts/<uuid:pk>/terminate/",
        ContractTerminateView.as_view(),
        name="contract-terminate",
    ),
    path(
        "api/contracts/company/<uuid:company_id>/",
        ContractCompanyListView.as_view(),
        name="contract-company-list",
    ),
]
