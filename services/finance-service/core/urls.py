"""Routes for the core app."""

from __future__ import annotations

from django.urls import path

from core import views

urlpatterns = [
    path("health/", views.HealthView.as_view(), name="health-root"),
    path("api/finance/health/", views.HealthView.as_view(), name="health-finance"),
    path("api/finance/payments/", views.PaymentListView.as_view(), name="finance-payment-list"),
    path(
        "api/finance/payments/<uuid:payment_id>/",
        views.PaymentDetailView.as_view(),
        name="finance-payment-detail",
    ),
    path(
        "api/finance/payments/company/<uuid:company_id>/",
        views.CompanyPaymentListView.as_view(),
        name="finance-payments-by-company",
    ),
    path("api/finance/dashboard/", views.FinanceDashboardView.as_view(), name="finance-dashboard"),
    path("api/finance/reports/", views.FinanceReportsView.as_view(), name="finance-reports"),
]
