"""Routes for the core app."""

from __future__ import annotations

from django.urls import path

from core.views import (
    HealthView,
    SpaceBookingEventView,
    SpaceBookingRecordListView,
    SpaceContractEventView,
    SpaceContractListView,
    SpaceDetailView,
    SpaceListCreateView,
    SpaceOccupancyMapView,
    SpaceTypeDetailView,
    SpaceTypeListCreateView,
)

urlpatterns = [
    path("health/", HealthView.as_view(), name="health-root"),
    path("api/spaces/health/", HealthView.as_view(), name="health-spaces"),

    path("api/space-types/", SpaceTypeListCreateView.as_view(), name="space-type-list-create"),
    path(
        "api/space-types/<uuid:type_id>/",
        SpaceTypeDetailView.as_view(),
        name="space-type-detail",
    ),

    path("api/spaces/", SpaceListCreateView.as_view(), name="space-list-create"),
    path("api/spaces/<uuid:space_id>/", SpaceDetailView.as_view(), name="space-detail"),
    path("api/spaces/occupancy-map/", SpaceOccupancyMapView.as_view(), name="space-occupancy"),

    path(
        "api/spaces/contracts/",
        SpaceContractListView.as_view(),
        name="space-contracts",
    ),
    path(
        "api/spaces/contracts/<str:event_type>/",
        SpaceContractEventView.as_view(),
        name="space-contracts-events",
    ),
    path(
        "api/spaces/bookings/<str:event_type>/",
        SpaceBookingEventView.as_view(),
        name="space-booking-events",
    ),
    path(
        "api/spaces/bookings/records/",
        SpaceBookingRecordListView.as_view(),
        name="space-booking-records",
    ),
]
