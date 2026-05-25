"""URL configuration for booking_service."""

from __future__ import annotations

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("api/bookings/schema/", SpectacularAPIView.as_view(), name="booking-schema"),
    path(
        "api/bookings/schema/swagger/",
        SpectacularSwaggerView.as_view(url_name="booking-schema"),
        name="booking-swagger-ui",
    ),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
