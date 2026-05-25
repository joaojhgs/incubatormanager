"""Routes for the core app."""

from __future__ import annotations

from django.urls import path

from core.views import (
    BookingApproveView,
    BookingCancelView,
    BookingCalendarView,
    BookingCompleteView,
    BookingDetailView,
    BookingListCreateView,
    BookingRejectView,
    HealthView,
    MyBookingsView,
    PublicBookingCreateView,
)

urlpatterns = [
    path("health/", HealthView.as_view(), name="health-root"),
    path("api/bookings/health/", HealthView.as_view(), name="health-bookings"),

    path("api/bookings/", BookingListCreateView.as_view(), name="booking-list-create"),
    path("api/bookings/external/", PublicBookingCreateView.as_view(), name="booking-public-create"),
    path(
        "api/bookings/<uuid:booking_id>/",
        BookingDetailView.as_view(),
        name="booking-detail",
    ),
    path(
        "api/bookings/<uuid:booking_id>/approve/",
        BookingApproveView.as_view(),
        name="booking-approve",
    ),
    path(
        "api/bookings/<uuid:booking_id>/reject/",
        BookingRejectView.as_view(),
        name="booking-reject",
    ),
    path(
        "api/bookings/<uuid:booking_id>/cancel/",
        BookingCancelView.as_view(),
        name="booking-cancel",
    ),
    path(
        "api/bookings/<uuid:booking_id>/complete/",
        BookingCompleteView.as_view(),
        name="booking-complete",
    ),
    path("api/bookings/calendar/", BookingCalendarView.as_view(), name="booking-calendar"),
    path("api/bookings/my/", MyBookingsView.as_view(), name="booking-my"),
]
