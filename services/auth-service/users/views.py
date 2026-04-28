"""Views for /users/me — self-profile read and update."""

from __future__ import annotations

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from users.models import User
from users.serializers import UserProfileSerializer, UserProfileUpdateSerializer


@extend_schema_view(
    get=extend_schema(
        summary="Get own profile",
        description="Return the authenticated user's full profile. Role and company are read-only.",
        responses={200: UserProfileSerializer},
    ),
    patch=extend_schema(
        summary="Update own profile",
        description=(
            "Update first name, last name, or change password. "
            "Role, company, email, and active status are immutable."
        ),
        request=UserProfileUpdateSerializer,
        responses={200: UserProfileSerializer},
    ),
)
class UserProfileView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /users/me/ — self-profile for the authenticated user."""

    http_method_names = ["get", "patch"]
    authentication_classes = [JWTAuthentication]
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self) -> User:
        return self.request.user  # type: ignore[return-value]

    def get_serializer_class(
        self,
    ) -> type[UserProfileSerializer] | type[UserProfileUpdateSerializer]:
        if self.request.method == "PATCH":
            return UserProfileUpdateSerializer
        return UserProfileSerializer

    def update(self, request: Request, *args: object, **kwargs: object) -> Response:
        """Override to return the full profile serializer after a successful PATCH."""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Return the full profile, not just the update fields.
        return Response(UserProfileSerializer(instance).data)
