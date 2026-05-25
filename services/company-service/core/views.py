"""Views for company-service."""

from __future__ import annotations

from django.conf import settings
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiResponse, extend_schema
from ilb_common.event_bus import publish
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
    CompanyListSerializer,
    CompanyMaturityStageUpdateSerializer,
    CompanyWriteSerializer,
    EmployeeSerializer,
)
from core.services import company_detail_queryset, company_list_queryset


def _scope_role_key(value: object | None) -> str:
    return str(value) if isinstance(value, str) else ""


def _scope_company_id(user: object) -> str | None:
    cid = getattr(user, "company_id", None)
    return str(cid) if cid is not None else None


def _resolve_company_for_client_or_staff(request: Request, company_id: str) -> Company:
    role = _scope_role_key(getattr(request.user, "role", None))
    if role in {"Staff", "Director"}:
        return get_object_or_404(Company.active, pk=company_id)

    requested_company_id = str(company_id)
    user_company_id = _scope_company_id(request.user)
    if not user_company_id or user_company_id != requested_company_id:
        raise Http404
    return get_object_or_404(Company.active, pk=company_id)


def _publish_company_created(company: Company) -> None:
    rabbitmq_url = getattr(settings, "RABBITMQ_URL", "")
    if not rabbitmq_url:
        return

    payload = {
        "company_id": str(company.id),
        "name": company.name,
        "cae_id": str(company.cae_id),
        "cae_code": company.cae.code,
        "maturity_stage_id": str(company.maturity_stage_id),
        "maturity_stage_name": company.maturity_stage.name,
    }

    transaction.on_commit(
        lambda: publish(
            rabbitmq_url,
            "company.created",
            payload,
            routing_key="company.created",
        )
    )


def _publish_employee_changed(employee: Employee, action: str) -> None:
    rabbitmq_url = getattr(settings, "RABBITMQ_URL", "")
    if not rabbitmq_url:
        return

    payload = {
        "company_id": str(employee.company_id),
        "employee_id": str(employee.id),
        "action": action,
        "employee_type": employee.type,
    }

    transaction.on_commit(
        lambda: publish(
            rabbitmq_url,
            "employee.changed",
            payload,
            routing_key="employee.changed",
        )
    )


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
        role = _scope_role_key(getattr(user, "role", None))
        company_id = _scope_company_id(user)
        return company_list_queryset(role, company_id)


class CompanyCreateUpdateView(generics.ListCreateAPIView):
    """Company create/list operations for management endpoints."""

    permission_classes = [IsAuthenticated]
    pagination_class = CompanyListPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = CompanyFilter
    search_fields = ("name", "tax_id", "legal_representative")

    def get_serializer_class(self):
        if self.request.method == "GET":
            return CompanyListSerializer
        return CompanyWriteSerializer

    def get_queryset(self):  # type: ignore[override]
        user = self.request.user
        role = _scope_role_key(getattr(user, "role", None))
        company_id = _scope_company_id(user)
        return company_list_queryset(role, company_id)

    def get_permissions(self):  # type: ignore[override]
        if self.request.method == "POST":
            return [IsAuthenticated(), IsStaff()]
        return [IsAuthenticated()]

    def perform_create(self, serializer: CompanyWriteSerializer) -> None:
        company = serializer.save()
        _publish_company_created(company)


class CompanyDetailUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, patch, or soft-delete company rows."""

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return CompanyDetailSerializer
        return CompanyWriteSerializer

    def get_queryset(self):  # type: ignore[override]
        user = self.request.user
        role = _scope_role_key(getattr(user, "role", None))
        company_id = _scope_company_id(user)
        return company_detail_queryset(role, company_id)

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
        request=CompanyMaturityStageUpdateSerializer,
        responses={
            200: CompanyDetailSerializer,
            400: OpenApiResponse(description="Validation error"),
            404: OpenApiResponse(description="Company not found"),
        },
    )
    def patch(self, request: Request, pk: str) -> Response:
        company_id = str(getattr(request.user, "company_id", "")) if getattr(
            request.user, "company_id", None
        ) is not None else None
        company = get_object_or_404(
            company_detail_queryset(
                role=_scope_role_key(getattr(request.user, "role", None)),
                company_id=company_id,
            ),
            pk=pk,
        )
        serializer = CompanyMaturityStageUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        stage = get_object_or_404(MaturityStage, pk=serializer.validated_data["maturity_stage"])
        company.maturity_stage = stage
        company.save(update_fields=["maturity_stage"])
        return Response(CompanyDetailSerializer(company).data)


class CompanyEmployeeListCreateView(APIView):
    """Client-scoped employee listing and staff/director writes."""

    permission_classes = [IsAuthenticated]

    def get_serializer_context(self) -> dict[str, object]:
        return {"request": getattr(self, "request", None)}

    def get_permissions(self):  # type: ignore[override]
        if self.request.method == "POST":
            return [IsAuthenticated(), IsStaff()]
        return [IsAuthenticated()]

    def get(self, request: Request, pk: str) -> Response:
        company = _resolve_company_for_client_or_staff(request, pk)
        employees = Employee.active.filter(company=company).order_by("name")
        serializer = EmployeeSerializer(employees, many=True)
        return Response(serializer.data)

    def post(self, request: Request, pk: str) -> Response:
        company = _resolve_company_for_client_or_staff(request, pk)
        serializer = EmployeeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = dict(serializer.validated_data)
        payload["company"] = company
        employee = Employee.objects.create(**payload)
        _publish_employee_changed(employee, "created")
        out = EmployeeSerializer(employee)
        return Response(out.data, status=status.HTTP_201_CREATED)


class CompanyEmployeeDetailView(APIView):
    """PATCH/DELETE employee by company scope."""

    permission_classes = [IsAuthenticated, IsStaff]

    def get_company_and_employee(
        self, request: Request, company_id: str, employee_id: str
    ) -> Employee:
        company = get_object_or_404(Company.active, pk=company_id)
        return get_object_or_404(Employee.objects.filter(company=company), pk=employee_id)

    def patch(self, request: Request, company_id: str, employee_id: str) -> Response:
        employee = self.get_company_and_employee(request, company_id, employee_id)
        serializer = EmployeeSerializer(employee, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = serializer.save()
        _publish_employee_changed(updated, "updated")
        return Response(serializer.data)

    def delete(self, request: Request, company_id: str, employee_id: str) -> Response:
        employee = self.get_company_and_employee(request, company_id, employee_id)
        _publish_employee_changed(employee, "deleted")
        employee.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CompanyEmployeeStatsView(APIView):
    """Aggregate employee stats for scoped company access."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, pk: str) -> Response:
        company = _resolve_company_for_client_or_staff(request, pk)
        queryset = Employee.objects.filter(company=company)
        by_type = {key: queryset.filter(type=key).count() for key in Employee.Type.values}
        payload = {
            "company_id": str(company.id),
            "total": queryset.count(),
            "active": queryset.filter(is_active=True).count(),
            "inactive": queryset.filter(is_active=False).count(),
            "by_type": by_type,
        }
        return Response(payload)


class CompanyStatsView(APIView):
    """Company-wide snapshot with role-aware scoping."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        role = _scope_role_key(getattr(request.user, "role", None))

        if role in {"Staff", "Director"}:
            companies_qs = Company.objects.all()
        else:
            company_id = _scope_company_id(request.user)
            if not company_id:
                raise Http404
            companies_qs = Company.active.filter(pk=company_id)

        employees_qs = Employee.objects.filter(company__in=companies_qs)
        payload = {
            "company_count": companies_qs.count(),
            "active_companies": companies_qs.filter(is_active=True).count(),
            "inactive_companies": companies_qs.filter(is_active=False).count(),
            "total_employees": employees_qs.count(),
            "active_employees": employees_qs.filter(is_active=True).count(),
            "inactive_employees": employees_qs.filter(is_active=False).count(),
        }
        return Response(payload)


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
        role = _scope_role_key(getattr(user, "role", None))
        company_id = _scope_company_id(user)
        return company_detail_queryset(role, company_id)


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
