"""Views for company-service."""

from __future__ import annotations

from drf_spectacular.utils import extend_schema
from ilb_common.permissions import IsDirector
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import CAE
from core.serializers import CAESerializer


class HealthView(APIView):
    """Liveness/readiness-style health payload."""

    authentication_classes = ()
    permission_classes = ()

    @extend_schema(
        responses={
            200: {
                "type": "object",
                "properties": {"status": {"type": "string", "example": "ok"}},
            }
        }
    )
    def get(self, request: Request) -> Response:
        return Response({"status": "ok"})


class CAEListCreateView(APIView):
    """List CAE codes for any authenticated user; create is Director-only."""

    def get_permissions(self):  # type: ignore[override]
        if self.request.method == "POST":
            return [IsAuthenticated(), IsDirector()]
        return [IsAuthenticated()]

    @extend_schema(responses={200: CAESerializer(many=True)})
    def get(self, request: Request) -> Response:
        qs = CAE.objects.all()
        serializer = CAESerializer(qs, many=True)
        return Response(serializer.data)

    @extend_schema(request=CAESerializer, responses={201: CAESerializer})
    def post(self, request: Request) -> Response:
        serializer = CAESerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
