"""Views for company-service."""

from __future__ import annotations

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiResponse, extend_schema
from drf_spectacular.utils import extend_schema
from drf_spectacular.utils import OpenApiResponse, extend_schema
from django.shortcuts import get_object_or_404
from ilb_common.permissions import IsDirector, IsStaff
from rest_framework import filters, generics, serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.filters import CompanyFilter
from core.models import CAE, Company, Employee, MaturityStage
from core.pagination import CompanyListPagination
from core.serializers import (
    CAESerializer,
    CompanyDetailSerializer,
    CompanyWriteSerializer,
    CompanyListSerializer,
    EmployeeSerializer,
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


class CompanyCreateUpdateView(generics.ListCreateAPIView):
    """Company CRUD surface for management operations."""

    serializer_class = CompanyWriteSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):  # type: ignore[override]
        user = self.request.user
        role = getattr(user, "role", None)
        cid = getattr(user, "company_id", None)
        cid_str = str(cid) if cid is not None else None
        role_str = role if isinstance(role, str) else ""
        return company_list_queryset(role_str, cid_str)

    def get_permissions(self):  # type: ignore[override]
        if self.request.method in {"POST", "PATCH", "PUT", "DELETE"}:
            return [IsAuthenticated(), IsStaff()]
        return [IsAuthenticated()]


class CompanyDetailUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve for scoped users; staff/director may patch or soft-delete."""

    serializer_class = CompanyWriteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):  # type: ignore[override]
        user = self.request.user
        role = getattr(user, "role", None)
        cid = getattr(user, "company_id", None)
        cid_str = str(cid) if cid is not None else None
        role_str = role if isinstance(role, str) else ""
        return company_detail_queryset(role_str, cid_str)

    def get_permissions(self):  # type: ignore[override]
        if self.request.method in {"PATCH", "PUT", "DELETE"}:
            return [IsAuthenticated(), IsStaff()]
        return [IsAuthenticated()]

    def perform_destroy(self, instance: Company) -> None:
        instance.is_active = False
        instance.save(update_fields=["is_active"])


class CompanyMaturityStageChangeView(APIView):
    """PATCH endpoint to swap maturity stage."""

    permission_classes = [IsAuthenticated, IsStaff]

    @extend_schema(
        request={"application/json": {"type": "object", "properties": {"maturity_stage": {"type": "string", "format": "uuid"}}},
        responses={
            200: CompanyDetailSerializer,
            400: OpenApiResponse(description="Validation error"),
            404: OpenApiResponse(description="Company not found"),
        },
    )
    def patch(self, request: Request, pk: str) -> Response:
        qs = company_detail_queryset(
            role=str(getattr(request.user, "role", "")),
            company_id=str(getattr(request.user, "company_id", "")) if getattr(request.user, "company_id", None) is not None else None,
        )
        company = get_object_or_404(qs, pk=pk)
        serializer = serializers.Serializer(
            data=request.data,
            context=self.get_serializer_context(),
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        stage_id = serializer.validated_data["maturity_stage"]
        try:
            stage = get_object_or_404(MaturityStage, pk=stage_id)
        except Exception as exc:  # pragma: no cover - safety for malformed payloads
            raise serializers.ValidationError({"maturity_stage": "Invalid maturity stage."}) from exc
        company.maturity_stage = stage
        company.save(update_fields=["maturity_stage"])
        return Response(CompanyDetailSerializer(company).data)


class CompanyEmployeeListCreateView(APIView):
    """Client-scoped employee listing and staff/director writes."""

    permission_classes = [IsAuthenticated]

    def get_serializer_context(self) -> dict[str, object]:
        return {"request": getattr(self, "request", None)}

    def get_permissions(self):  # type: ignore[override]
        if self.request.method in {"POST"}:
            return [IsAuthenticated(), IsStaff()]
        return [IsAuthenticated()]

    def _resolve_company(self, request: Request, company_id: str) -> Company:
        role = str(getattr(request.user, "role", ""))
        if role in {"Staff", "Director"}:
            return get_object_or_404(Company.active, pk=company_id)
        user_company_id = getattr(request.user, "company_id", None)
        if not user_company_id or str(user_company_id) != company_id:
            from django.http import Http404

            raise Http404
        return get_object_or_404(Company.active, pk=company_id)

    def get(self, request: Request, pk: str) -> Response:
        company = self._resolve_company(request, pk)
        employees = Employee.active.filter(company=company).order_by("name")
        serializer = EmployeeSerializer(employees, many=True)
        return Response(serializer.data)

    def post(self, request: Request, pk: str) -> Response:
        company = self._resolve_company(request, pk)
        serializer = EmployeeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = dict(serializer.validated_data)
        payload["company"] = company
        employee = Employee.objects.create(**payload)
        out = EmployeeSerializer(employee)
        return Response(out.data, status=status.HTTP_201_CREATED)


class CompanyEmployeeDetailView(APIView):
    """PATCH/DELETE employee by company scope."""

    permission_classes = [IsAuthenticated, IsStaff]

    def get_company_and_employee(self, request: Request, company_id: str, employee_id: str) -> Employee:
        company = get_object_or_404(Company.active, pk=company_id)
        return get_object_or_404(Employee.objects.filter(company=company), pk=employee_id)

    def patch(self, request: Request, company_id: str, employee_id: str) -> Response:
        employee = self.get_company_and_employee(request, company_id, employee_id)
        serializer = EmployeeSerializer(employee, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request: Request, company_id: str, employee_id: str) -> Response:
        employee = self.get_company_and_employee(request, company_id, employee_id)
        employee.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CompanyEmployeeStatsView(APIView):
    """Aggregate employee stats for scoped company access."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, pk: str) -> Response:
        company = self._resolve_company(request, pk)
        queryset = Employee.objects.filter(company=company)
        by_type = {
            key: queryset.filter(type=key).count()
            for key in Employee.Type.values
        }
        payload = {
            "total": queryset.count(),
            "active": queryset.filter(is_active=True).count(),
            "by_type": by_type,
        }
        return Response(payload)

    def _resolve_company(self, request: Request, company_id: str) -> Company:
        role = str(getattr(request.user, "role", ""))
        if role in {"Staff", "Director"}:
            return get_object_or_404(Company.active, pk=company_id)
        user_company_id = getattr(request.user, "company_id", None)
        if not user_company_id or str(user_company_id) != company_id:
            from django.http import Http404

            raise Http404
        return get_object_or_404(Company.active, pk=company_id)


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
