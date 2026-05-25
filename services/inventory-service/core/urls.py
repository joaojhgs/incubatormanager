"""Routes for the core app."""

from __future__ import annotations

from django.urls import path

from core.views import (
    EquipmentAssignView,
    EquipmentDetailView,
    EquipmentListCreateView,
    EquipmentReleaseView,
    EquipmentTypeDetailView,
    EquipmentTypeListCreateView,
    HealthView,
    InventoryAssignmentListView,
    InventoryBookingEventView,
    InventoryMyAssignmentsView,
)

urlpatterns = [
    path("health/", HealthView.as_view(), name="health-root"),
    path("api/inventory/health/", HealthView.as_view(), name="health-inventory"),
    path(
        "api/inventory/equipment-types/",
        EquipmentTypeListCreateView.as_view(),
        name="equipment-type-list-create",
    ),
    path(
        "api/inventory/equipment-types/<uuid:type_id>/",
        EquipmentTypeDetailView.as_view(),
        name="equipment-type-detail",
    ),
    path(
        "api/inventory/equipment/", EquipmentListCreateView.as_view(), name="equipment-list-create"
    ),
    path(
        "api/inventory/equipment/<uuid:equipment_id>/",
        EquipmentDetailView.as_view(),
        name="equipment-detail",
    ),
    path(
        "api/inventory/equipment/<uuid:equipment_id>/assign/",
        EquipmentAssignView.as_view(),
        name="equipment-assign",
    ),
    path(
        "api/inventory/equipment/<uuid:equipment_id>/release/",
        EquipmentReleaseView.as_view(),
        name="equipment-release",
    ),
    path(
        "api/inventory/bookings/<str:event_type>/",
        InventoryBookingEventView.as_view(),
        name="inventory-booking-events",
    ),
    path(
        "api/inventory/my-assignments/",
        InventoryMyAssignmentsView.as_view(),
        name="inventory-my-assignments",
    ),
    path(
        "api/inventory/assignments/",
        InventoryAssignmentListView.as_view(),
        name="inventory-assignments",
    ),
]
