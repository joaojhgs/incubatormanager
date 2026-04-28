"""Permission classes for gateway-injected identity headers."""

from __future__ import annotations

from typing import Any

from rest_framework.permissions import BasePermission
from rest_framework.request import Request


class IsGatewayDirector(BasePermission):
    """
    Allow only when Nginx forwarded ``X-User-Role: Director`` from ``auth_request``.
    Other services trust these headers; auth-service applies the same for admin APIs.
    """

    message = "You do not have permission to perform this action."

    def has_permission(self, request: Request, view: Any) -> bool:
        return request.META.get("HTTP_X_USER_ROLE") == "Director"

    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        return self.has_permission(request, view)
