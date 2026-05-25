"""Routes for the core app."""

from __future__ import annotations

from django.urls import path

from core.views import (
    HealthView,
    MetricsView,
    MyTicketsView,
    TicketDetailView,
    TicketListCreateView,
    TicketMessageCreateView,
    TicketMetricsView,
)

urlpatterns = [
    path("metrics/", MetricsView.as_view(), name="metrics-root"),
    path("health/", HealthView.as_view(), name="health-root"),
    path("api/tickets/health/", HealthView.as_view(), name="health-tickets"),
    path("api/tickets/metrics/", TicketMetricsView.as_view(), name="ticket-metrics"),
    path("api/tickets/my/", MyTicketsView.as_view(), name="ticket-list-mine"),
    path("api/tickets/<uuid:ticket_id>/", TicketDetailView.as_view(), name="ticket-detail"),
    path(
        "api/tickets/<uuid:ticket_id>/messages/",
        TicketMessageCreateView.as_view(),
        name="ticket-messages",
    ),
    path("api/tickets/", TicketListCreateView.as_view(), name="ticket-list-create"),
]
