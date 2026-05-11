"""Views for company-service."""

from __future__ import annotations

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from ilb_common.permissions import IsDirector
from rest_framework import filters, generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.filters import CompanyFilter
from core.models import CAE
from core.pagination import CompanyListPagination
from core.serializers import (
    CAESerializer,
    CompanyDetailSerializer,
    CompanyListSerializer,
)
from core.services import company_detail_queryset, company_list_queryset


@extend_schema(
    description=(
        "Paginated company list with optional filters (`cae`, `maturity`, `is_active`) "
        "and `search` across name / tax ID / legal representative. Directors and Staff "
        "see all companies; Clients only see their row (`X-Company-Id`)."
    ),
)
class CompanyListView(generics.ListAPIView):
    serializer_class = CompanyListSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CompanyListPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = CompanyFilter
    search_fields = ("name", "tax_id", "legal_representative")

    def get_queryset(self):  # type: ignore[override]
        user = self.request.user
        role = getattr(user, "role", None)
        cid = getattr(user, "company_id", None)
        cid_str = str(cid) if cid is not None else None
        role_str = role if isinstance(role, str) else ""
        return company_list_queryset(role_str, cid_str)


@extend_schema(
    description=(
        "Company detail including CAE and maturity-stage relations (select_related) and "
        "active employees (prefetch_related). Uses active companies only. Staff and "
        "Directors may retrieve any active company by id. Clients only retrieve their "
        "company (`X-Company-Id`)."
    ),
)
class CompanyDetailView(generics.RetrieveAPIView):
    serializer_class = CompanyDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):  # type: ignore[override]
        user = self.request.user
        role = getattr(user, "role", None)
        cid = getattr(user, "company_id", None)
        cid_str = str(cid) if cid is not None else None
        role_str = role if isinstance(role, str) else ""
        return company_detail_queryset(role_str, cid_str)


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
