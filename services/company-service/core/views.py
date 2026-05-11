"""Views for company-service."""

from __future__ import annotations

from drf_spectacular.utils import OpenApiExample, extend_schema, extend_schema_view
from ilb_common.permissions import IsDirector
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import CAE
from core.serializers import CAESerializer, CompanyDetailSerializer
from core.services import company_detail_queryset


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


_DETAIL_EXAMPLES = OpenApiExample(
    "detail",
    value={
        "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "name": "Acme Incubada Lda.",
        "tax_id": "PT513133999",
        "address": "",
        "phone": "",
        "email": "",
        "legal_representative": "Ada Lovelace",
        "description": "",
        "is_active": True,
        "cae": {
            "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            "code": "62010",
            "description": "Programming activities",
        },
        "maturity_stage": {
            "id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            "name": "Startup",
            "rate_per_sqm": "42.50",
            "description": "",
            "display_order": 1,
        },
        "employees": [],
        "created_at": "2026-05-11T14:04:52.456789Z",
        "updated_at": "2026-05-11T14:04:52.456789Z",
    },
)


@extend_schema_view(
    retrieve=extend_schema(
        responses={200: CompanyDetailSerializer},
        examples=[_DETAIL_EXAMPLES],
        description=(
            "Company detail including CAE and maturity-stage relations "
            "(select_related) and active employees (prefetch_related). "
            "Staff and Directors may retrieve any active company by id. Clients "
            "only retrieve their company (X-Company-Id)."
        ),
    )
)
class CompanyDetailView(generics.RetrieveAPIView):
    """Optimized company retrieve (select_related CAE/stage + prefetch employees)."""

    serializer_class = CompanyDetailSerializer

    def get_queryset(self):  # type: ignore[override]
        qs = company_detail_queryset()
        user = self.request.user
        role = getattr(user, "role", None)
        if role in {"Director", "Staff"}:
            return qs
        if role == "Client":
            cid = getattr(user, "company_id", None)
            return qs.none() if cid is None else qs.filter(pk=cid)
        return qs.none()
