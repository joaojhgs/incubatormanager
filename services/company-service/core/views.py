"""Views for company-service."""

from __future__ import annotations

import os
from typing import cast
from uuid import UUID

from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from ilb_common import event_bus
from ilb_common.permissions import IsDirector, IsStaff
from rest_framework import filters, generics, status
from rest_framework.exceptions import NotFound, PermissionDenied
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
    EmployeeWriteSerializer,
)
from core.services import company_detail_queryset, company_list_queryset


def _scope_role_key(user: object) -> str:
    role = getattr(user, "role", None)
    return role if isinstance(role, str) else ""


def _scope_company_id(user: object) -> str | None:
    company_id = getattr(user, "company_id", None)
    return str(company_id) if company_id is not None else None


def _resolve_company_for_client_or_staff(user: object, company_id: str | UUID) -> str | None:
    company_id_str = str(company_id)
    role = _scope_role_key(user)
    if role == "Client":
        scope = _scope_company_id(user)
        return company_id_str if scope == company_id_str else None
    if role in {"Director", "Staff"}:
        return company_id_str
    return None


def _publish_company_created(company: Company) -> None:
    rabbitmq_url = os.environ.get("RABBITMQ_URL", "")
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
        lambda: event_bus.publish(rabbitmq_url, "company.created", payload)
    )


def _publish_employee_changed(employee: Employee, *, action: str) -> None:
    rabbitmq_url = os.environ.get("RABBITMQ_URL", "")
    if not rabbitmq_url:
        return

    payload = {
        "company_id": str(employee.company_id),
        "employee_id": str(employee.id),
        "action": action,
        "employee_type": employee.type,
    }
    transaction.on_commit(
        lambda: event_bus.publish(rabbitmq_url, "employee.changed", payload)
    )


@extend_schema(
    description=(
        "Paginated company list with optional filters (`cae`, `maturity`, `is_active`) "
        "and `search` across name / tax ID / legal representative. Directors and Staff "
        "see all companies; Clients only see their row (`X-Company-Id`)."
    ),
)
class CompanyCreateUpdateView(generics.ListCreateAPIView):
    serializer_class = CompanyListSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CompanyListPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = CompanyFilter
    search_fields = ("name", "tax_id", "legal_representative")

    def get_permissions(self):  # type: ignore[override]
        if self.request.method == "POST":
            return [IsAuthenticated(), IsStaff()]
        return [IsAuthenticated()]

    def get_queryset(self):  # type: ignore[override]
        role = _scope_role_key(self.request.user)
        company_id = _scope_company_id(self.request.user)
        return company_list_queryset(role, company_id)

    def get_serializer_class(self):  # type: ignore[override]
        if self.request is not None and self.request.method == "POST":
            return CompanyWriteSerializer
        return CompanyListSerializer

    def perform_create(self, serializer):  # type: ignore[override]
        company = cast("Company", serializer.save())
        _publish_company_created(company)


@extend_schema(
    description=(
        "Company detail including CAE and maturity-stage relations (select_related) and "
        "active employees (prefetch_related). Uses active companies only. Staff and "
        "Directors may retrieve any active company by id. Clients only retrieve their "
        "company (`X-Company-Id`)."
    ),
)
class CompanyDetailUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CompanyDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):  # type: ignore[override]
        if self.request.method in {"PATCH", "DELETE"}:
            return [IsAuthenticated(), IsStaff()]
        return [IsAuthenticated()]

    def get_queryset(self):  # type: ignore[override]
        role = _scope_role_key(self.request.user)
        company_id = _scope_company_id(self.request.user)
        return company_detail_queryset(role, company_id)

    def get_serializer_class(self):  # type: ignore[override]
        if self.request is not None and self.request.method in {"PATCH", "PUT"}:
            return CompanyWriteSerializer
        return CompanyDetailSerializer

    def perform_destroy(self, instance):  # type: ignore[override]
        instance.is_active = False
        instance.save(update_fields=("is_active",))


@extend_schema(description="Patch the maturity stage for an active company by uuid.")
class CompanyMaturityStageChangeView(APIView):
    permission_classes = [IsAuthenticated, IsStaff]

    def patch(self, request: Request, pk: str) -> Response:
        serializer = CompanyMaturityStageUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        stage_id = serializer.validated_data["maturity_stage"]

        role = _scope_role_key(request.user)
        scope_company_id = _scope_company_id(request.user)
        qs = company_detail_queryset(role, scope_company_id)
        company = get_object_or_404(qs, id=pk)

        stage = MaturityStage.objects.filter(id=stage_id).first()
        if stage is None:
            raise NotFound("Maturity stage not found")

        company.maturity_stage = stage
        company.save(update_fields=("maturity_stage", "updated_at"))
        return Response(CompanyDetailSerializer(company).data)


@extend_schema(
    description=(
        "List or create employees for a company. Staff and Directors can manage "
        "employees; other roles are denied."
    ),
)
class CompanyEmployeeListCreateView(generics.ListCreateAPIView):
    serializer_class = EmployeeSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):  # type: ignore[override]
        return [IsAuthenticated(), IsStaff()]

    def get_queryset(self):  # type: ignore[override]
        company_id = self.kwargs["company_id"]
        scoped_company = _resolve_company_for_client_or_staff(
            self.request.user,
            company_id,
        )
        if scoped_company is None:
            return Employee.objects.none()
        return Employee.objects.select_related("company").filter(company_id=scoped_company)

    def get_serializer_class(self):  # type: ignore[override]
        if self.request is not None and self.request.method == "POST":
            return EmployeeWriteSerializer
        return EmployeeSerializer

    def perform_create(self, serializer):  # type: ignore[override]
        company = Company.objects.get(pk=self.kwargs["company_id"])
        employee = cast("Employee", serializer.save(company=company))
        _publish_employee_changed(employee, action="created")


@extend_schema(
    description=(
        "Patch or delete an employee. PATCH and DELETE are staff/director-only. "
        "PATCH returns a full row payload."
    ),
)
class CompanyEmployeeDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = EmployeeSerializer
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = "employee_id"

    def get_permissions(self):  # type: ignore[override]
        if self.request.method in {"PATCH", "DELETE"}:
            return [IsAuthenticated(), IsStaff()]
        return [IsAuthenticated(), IsStaff()]

    def get_serializer_class(self):  # type: ignore[override]
        if self.request is not None and self.request.method in {"PATCH", "PUT"}:
            return EmployeeWriteSerializer
        return EmployeeSerializer

    def get_queryset(self):  # type: ignore[override]
        scoped_company = _resolve_company_for_client_or_staff(
            self.request.user,
            self.kwargs["company_id"],
        )
        if scoped_company is None:
            return Employee.objects.none()
        return Employee.objects.filter(company_id=scoped_company)

    def perform_update(self, serializer):  # type: ignore[override]
        employee = cast("Employee", serializer.save())
        _publish_employee_changed(employee, action="updated")

    def perform_destroy(self, instance):  # type: ignore[override]
        _publish_employee_changed(instance, action="deleted")
        instance.delete()


class CompanyEmployeeStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, pk: str) -> Response:
        scoped_company = _resolve_company_for_client_or_staff(request.user, pk)
        if scoped_company is None:
            raise NotFound("Employee stats for this company are unavailable")

        stats = (
            Employee.objects.filter(company_id=scoped_company)
            .values("type")
            .annotate(total=Count("id"))
        )
        by_type = {row["type"]: row["total"] for row in stats}
        active = Employee.objects.filter(company_id=scoped_company, is_active=True).count()
        inactive = Employee.objects.filter(company_id=scoped_company, is_active=False).count()
        total = active + inactive
        return Response(
            {
                "company_id": str(scoped_company),
                "total": total,
                "active": active,
                "inactive": inactive,
                "by_type": by_type,
            }
        )


class CompanyStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        role = _scope_role_key(request.user)
        if role == "Client":
            scope = _scope_company_id(request.user)
            if scope is None:
                raise PermissionDenied("Missing X-Company-Id")
            company_qs = Company.objects.filter(pk=scope)
        elif role in {"Director", "Staff"}:
            company_qs = Company.objects.all()
        else:
            company_qs = Company.objects.none()

        total = company_qs.count()
        active = company_qs.filter(is_active=True).count()
        inactive = company_qs.filter(is_active=False).count()
        return Response(
            {
                "total": total,
                "active": active,
                "inactive": inactive,
            }
        )


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
