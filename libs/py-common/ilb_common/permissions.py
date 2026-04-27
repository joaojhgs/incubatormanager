"""DRF permission and authentication classes that trust gateway-injected headers.

Only ``auth-service`` validates JWTs. The Nginx gateway performs
``auth_request`` to ``auth-service:/auth/introspect``, then injects
``X-User-Id``, ``X-User-Role``, and ``X-Company-Id`` headers into the
upstream request. All other services **trust** these headers and never
re-validate the JWT.

Usage in a service ``settings.py``::

    REST_FRAMEWORK = {
        "DEFAULT_AUTHENTICATION_CLASSES": [
            "ilb_common.permissions.HeaderAuthentication",
        ],
        "DEFAULT_PERMISSION_CLASSES": [
            "rest_framework.permissions.IsAuthenticated",
        ],
    }

Usage in a view::

    from ilb_common.permissions import IsDirector, IsStaff, IsClientOwner

    class CompanyViewSet(viewsets.ModelViewSet):
        permission_classes = [IsAuthenticated, IsStaff]

    class MaturityStageCreateView(APIView):
        permission_classes = [IsAuthenticated, IsDirector]

    class MyBookingsView(APIView):
        permission_classes = [IsAuthenticated, IsClientOwner]
"""

from __future__ import annotations

from uuid import UUID

from rest_framework.authentication import BaseAuthentication
from rest_framework.permissions import BasePermission
from rest_framework.request import Request

from ilb_common.auth_headers import AuthHeaders, parse


class RequestUser:
    """Lightweight user object created from trusted gateway headers.

    Implements the ``request.user`` contract expected by DRF:
    ``is_authenticated`` is always ``True`` (the gateway already
    validated the JWT), and identity fields are populated from the
    ``X-User-*`` headers.

    Attributes:
        id: UUID of the authenticated user.
        role: One of ``"Director"``, ``"Staff"``, ``"Client"``.
        company_id: UUID of the user's company, or ``None`` for
            Staff/Director roles.
    """

    def __init__(self, auth_headers: AuthHeaders) -> None:
        self.id: UUID = auth_headers.user_id
        self.role: str = auth_headers.role
        self.company_id: UUID | None = auth_headers.company_id

    @property
    def is_authenticated(self) -> bool:  # noqa: D401 – DRF contract
        """Always ``True`` — the gateway already validated the JWT."""
        return True

    def __str__(self) -> str:
        return f"{self.role}:{self.id}"

    def __repr__(self) -> str:
        return f"RequestUser(id={self.id!r}, role={self.role!r}, company_id={self.company_id!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RequestUser):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)


class HeaderAuthentication(BaseAuthentication):
    """DRF authentication class that trusts gateway-injected headers.

    Parses ``X-User-Id``, ``X-User-Role``, and ``X-Company-Id`` from
    the request (Django ``META`` style) and returns a
    :class:`RequestUser`. If the headers are missing or malformed,
    authentication fails and the request is treated as anonymous.
    """

    def authenticate(self, request: Request) -> tuple[RequestUser, None]:
        """Return ``(RequestUser, None)`` from gateway headers.

        Raises ``AuthenticationFailed`` when headers are missing or
        invalid, which causes DRF to treat the request as unauthenticated.
        """
        from rest_framework.exceptions import AuthenticationFailed

        try:
            auth_headers = parse(request.META)
        except ValueError as exc:
            raise AuthenticationFailed(str(exc)) from exc

        user = RequestUser(auth_headers)
        return user, None


class IsDirector(BasePermission):
    """Allow access only to users with the ``Director`` role."""

    def has_permission(self, request: Request, view: object) -> bool:
        user = request.user
        return getattr(user, "role", None) == "Director"


class IsStaff(BasePermission):
    """Allow access to users with the ``Staff`` or ``Director`` role.

    Directors are included because they have at least the same
    privileges as Staff in the ILB permission model.
    """

    def has_permission(self, request: Request, view: object) -> bool:
        user = request.user
        return getattr(user, "role", None) in {"Staff", "Director"}


class IsClientOwner(BasePermission):
    """Allow access to ``Client`` users whose company owns the resource.

    For list endpoints (``has_permission``), any authenticated Client
    is allowed — the view's queryset must filter by ``X-Company-Id``.

    For detail / object-level endpoints (``has_object_permission``),
    the object must expose a ``company_id`` attribute (or property)
    that matches the user's ``company_id``.
    """

    def has_permission(self, request: Request, view: object) -> bool:
        user = request.user
        return getattr(user, "role", None) == "Client"

    def has_object_permission(self, request: Request, view: object, obj: object) -> bool:
        user = request.user
        if getattr(user, "role", None) != "Client":
            return False
        obj_company = getattr(obj, "company_id", None)
        if obj_company is None:
            return False
        # Compare as strings to handle both UUID and str representations.
        return str(obj_company) == str(user.company_id)
