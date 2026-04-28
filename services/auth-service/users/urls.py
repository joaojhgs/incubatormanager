"""URL configuration for the users app."""

from __future__ import annotations

from django.urls import path

from users.views import UserProfileView

urlpatterns = [
    path("api/users/me/", UserProfileView.as_view(), name="user-self-profile"),
]
