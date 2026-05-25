"""Views for company-service."""

from __future__ import annotations

from django.http import Http404
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiResponse, extend_schema
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
    CompanyWriteSerializer,
    EmployeeSerializer,
)
from core.services import company_detail_queryset, company_list_queryset


def _role_and_company(user: object) -> tuple[str, str | None]:
    role = str(getattr(user, "role", ""))
    company_id = getattr(user, "company_id", None)
    company_id_str = str(company_id) if company_id is not None else None
    return role, company_id_str


@extend_schema(
    description=(
        "Paginated company list with optional filters (`cae`, `maturity`, `is_active`) "
        "and `search` across name / tax ID / legal representative. Directors and Staff "
        "see all companies; Clients only see their row (`X-Company-Id`)."
    ),
)
class CompanyListCreateView(generics.ListCreateAPIView):
    """Company list (scoped) and create endpoint for staff/directors."""

    permission_classes = [IsAuthenticated]
    pagination_class = CompanyListPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = CompanyFilter
    search_fields = ("name", "tax_id", "legal_representative")

    def get_queryset(self):  # type: ignore[override]
        role, company_id_str = _role_and_company(self.request.user)
        return company_list_queryset(role, company_id_str)

    def get_serializer_class(self):  # type: ignore[override]
        if self.request.method == "POST":
            return CompanyWriteSerializer
        return CompanyListSerializer

    def get_permissions(self):  # type: ignore[override]
        if self.request.method == "POST":
            return [IsAuthenticated(), IsStaff()]
        return [IsAuthenticated()]


class CompanyDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Company detail with scoped reads and staff/director writes."""

    permission_classes = [IsAuthenticated]

    def get_queryset(self):  # type: ignore[override]
        role, company_id_str = _role_and_company(self.request.user)
        return company_detail_queryset(role, company_id_str)

    def get_serializer_class(self):  # type: ignore[override]
        if self.request.method in {"GET", "HEAD", "OPTIONS"}:
            return CompanyDetailSerializer
        return CompanyWriteSerializer

    def get_permissions(self):  # type: ignore[override]
        if self.request.method in {"PATCH", "PUT", "DELETE"}:
            return [IsAuthenticated(), IsStaff()]
        return [IsAuthenticated()]

    def perform_destroy(self, instance: Company) -> None:
        instance.is_active = False
        instance.save(update_fields=["is_active"])


class CompanyMaturityStageChangeView(APIView):
    """PATCH endpoint to change a company's maturity stage."""

    permission_classes = [IsAuthenticated, IsStaff]

    class _Payload(serializers.Serializer):
        maturity_stage = serializers.PrimaryKeyRelatedField(queryset=MaturityStage.objects.all())

    @extend_schema(
        request=_Payload,
        responses={
            200: CompanyDetailSerializer,
            400: OpenApiResponse(description="Validation error"),
            404: OpenApiResponse(description="Company not found"),
        },
    )
    def patch(self, request: Request, pk: str) -> Response:
        role, company_id_str = _role_and_company(request.user)
        qs = company_detail_queryset(role, company_id_str)
        company = get_object_or_404(qs, pk=pk)

        payload = self._Payload(data=request.data)
        payload.is_valid(raise_exception=True)
        company.maturity_stage = payload.validated_data["maturity_stage"]
        company.save(update_fields=["maturity_stage"])
        return Response(CompanyDetailSerializer(company).data)


class CompanyEmployeeListCreateView(APIView):
    """List and create employees for a company."""

    permission_classes = [IsAuthenticated]

    def get_permissions(self):  # type: ignore[override]
        if self.request.method == "POST":
            return [IsAuthenticated(), IsStaff()]
        return [IsAuthenticated()]

    def _resolve_company(self, request: Request, company_id: str) -> Company:
        role, user_company_id = _role_and_company(request.user)
        if role in {"Staff", "Director"}:
            return get_object_or_404(Company.active, pk=company_id)

        if not user_company_id or user_company_id != company_id:
            raise Http404

        return get_object_or_404(Company.active, pk=company_id)

    def get(self, request: Request, company_id: str) -> Response:
        company = self._resolve_company(request, company_id)
        employees = Employee.objects.filter(company=company).order_by("name")
        return Response(EmployeeSerializer(employees, many=True).data)

    def post(self, request: Request, company_id: str) -> Response:
        company = self._resolve_company(request, company_id)
        payload = EmployeeSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        employee = Employee.objects.create(company=company, **payload.validated_data)
        out = EmployeeSerializer(employee)
        return Response(out.data, status=status.HTTP_201_CREATED)


class CompanyEmployeeDetailView(APIView):
    """Patch or delete a company employee."""

    permission_classes = [IsAuthenticated, IsStaff]

    def get_company_and_employee(
        self,
        request: Request,
        company_id: str,
        employee_id: str,
    ) -> Employee:
        company = get_object_or_404(Company.active, pk=company_id)
        return get_object_or_404(Employee.objects.filter(company=company), pk=employee_id)

    def patch(self, request: Request, company_id: str, employee_id: str) -> Response:
        employee = self.get_company_and_employee(request, company_id, employee_id)
        payload = EmployeeSerializer(employee, data=request.data, partial=True)
        payload.is_valid(raise_exception=True)
        payload.save()
        return Response(payload.data)

    def delete(self, request: Request, company_id: str, employee_id: str) -> Response:
        employee = self.get_company_and_employee(request, company_id, employee_id)
        employee.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CompanyEmployeeStatsView(APIView):
    """Aggregate employee stats for a scoped company."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, company_id: str) -> Response:
        role, user_company_id = _role_and_company(request.user)
        if role not in {"Staff", "Director"}:
            if not user_company_id or user_company_id != company_id:
                raise Http404

        company = get_object_or_404(Company.active, pk=company_id)
        queryset = Employee.objects.filter(company=company)
        by_type = {choice: queryset.filter(type=choice).count() for choice in Employee.Type.values}

        return Response(
            {
                "total": queryset.count(),
                "active": queryset.filter(is_active=True).count(),
                "by_type": by_type,
            }
        )


@extend_schema(
    description=(
        "Liveness/readiness-style health endpoint for service probes and gateway checks."
    ),
)
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
