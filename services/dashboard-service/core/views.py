"""Dashboard aggregation views."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from urllib.error import URLError
from urllib.request import Request as UrlRequest
from urllib.request import urlopen

from django.db.models import Count, DecimalField, Sum
from django.db.models.functions import Coalesce, TruncMonth
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from ilb_common.permissions import IsStaff
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import (
    BookingProjection,
    CompanyProjection,
    ContractProjection,
    DashboardSnapshot,
    EmployeeProjection,
    PaymentProjection,
)

SERVICE_DEFAULTS: dict[str, str] = {
    "company": "http://company-service:8002/api/companies/health/",
    "contract": "http://contract-service:8003/api/contracts/health/",
    "finance": "http://finance-service:8004/api/finance/health/",
    "space": "http://space-service:8005/api/spaces/health/",
    "booking": "http://booking-service:8006/api/bookings/health/",
    "inventory": "http://inventory-service:8007/api/inventory/health/",
    "ticket": "http://ticket-service:8008/api/tickets/health/",
    "document": "http://document-service:8010/api/documents/health/",
    "auth": "http://auth-service:8001/api/auth/health/",
}

METRIC_ENDPOINTS: dict[str, str] = {
    "company": "http://company-service:8002/api/companies/stats/",
    "finance": "http://finance-service:8004/api/finance/dashboard/",
    "ticket": "http://ticket-service:8008/api/tickets/metrics/",
}

ZERO = Decimal("0")


def _now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _env_url(prefix: str, name: str, default: str) -> str:
    key = f"{name.upper()}_{prefix}_URL"
    return os.environ.get(key, default)


def _forward_headers(request: Request) -> dict[str, str]:
    headers: dict[str, str] = {}
    for source, target in (
        ("HTTP_X_USER_ID", "X-User-Id"),
        ("HTTP_X_USER_ROLE", "X-User-Role"),
        ("HTTP_X_COMPANY_ID", "X-Company-Id"),
    ):
        value = request.META.get(source)
        if value:
            headers[target] = str(value)
    return headers


def _fetch_json(url: str, headers: dict[str, str], *, timeout: float = 0.35) -> tuple[bool, Any]:
    try:
        req = UrlRequest(url, headers=headers)
        with urlopen(req, timeout=timeout) as response:  # noqa: S310 - internal service URLs only
            body = response.read().decode("utf-8")
        return True, json.loads(body) if body else {}
    except (OSError, URLError, json.JSONDecodeError, TimeoutError) as exc:
        return False, {"error": exc.__class__.__name__}


def _sum_amount(queryset, field: str = "amount") -> Decimal:
    return queryset.aggregate(
        total=Coalesce(Sum(field), ZERO, output_field=DecimalField(max_digits=14, decimal_places=2))
    )["total"]


def _overview_kpis() -> dict[str, Any]:
    active_companies = CompanyProjection.objects.filter(is_active=True).count()
    occupied_spaces = (
        ContractProjection.objects.filter(is_active=True, space_id__isnull=False)
        .values("space_id")
        .distinct()
        .count()
    )
    known_spaces = max(
        occupied_spaces,
        ContractProjection.objects.filter(space_id__isnull=False)
        .values("space_id")
        .distinct()
        .count(),
        BookingProjection.objects.filter(space_id__isnull=False)
        .values("space_id")
        .distinct()
        .count(),
    )
    occupancy_percent = round((occupied_spaces / known_spaces) * 100, 2) if known_spaces else 0.0
    month_start = timezone.localdate().replace(day=1)
    revenue_mtd = _sum_amount(PaymentProjection.objects.filter(paid_at__date__gte=month_start))
    pending_bookings = BookingProjection.objects.filter(status="approved").count()
    finance_snapshot = DashboardSnapshot.objects.filter(source="finance").first()
    overdue_count = 0
    if isinstance(getattr(finance_snapshot, "payload", None), dict):
        overdue_count = int(finance_snapshot.payload.get("overdue") or 0)
    ticket_snapshot = DashboardSnapshot.objects.filter(source="ticket").first()
    open_tickets = 0
    if isinstance(getattr(ticket_snapshot, "payload", None), dict):
        open_tickets = int(ticket_snapshot.payload.get("open_count") or 0)

    return {
        "companies": active_companies,
        "employees_total": EmployeeProjection.objects.filter(is_active=True).count(),
        "occupancy_percent": occupancy_percent,
        "revenue_mtd": revenue_mtd,
        "overdue_count": overdue_count,
        "pending_bookings": pending_bookings,
        "open_tickets": open_tickets,
    }


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


class DashboardOverviewView(APIView):
    """Staff dashboard with materialized KPIs and downstream health snapshots."""

    permission_classes = [IsAuthenticated, IsStaff]

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request: Request) -> Response:
        headers = _forward_headers(request)
        services: dict[str, dict[str, Any]] = {}
        for name, default_url in SERVICE_DEFAULTS.items():
            ok, payload = _fetch_json(_env_url("HEALTH", name, default_url), headers)
            services[name] = {"status": "up" if ok else "down", "payload": payload}

        metrics: dict[str, Any] = {}
        for name, default_url in METRIC_ENDPOINTS.items():
            ok, payload = _fetch_json(_env_url("METRICS", name, default_url), headers)
            metrics[name] = payload if ok else {"available": False, **payload}

        return Response(
            {
                "generated_at": _now_iso(),
                "kpis": _overview_kpis(),
                "services": services,
                "metrics": metrics,
            }
        )


class DashboardCompaniesView(APIView):
    """Company analytics from materialized company and employee projections."""

    permission_classes = [IsAuthenticated, IsStaff]

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request: Request) -> Response:
        active = CompanyProjection.objects.filter(is_active=True)
        by_sector = list(
            active.values("cae_code").annotate(total=Count("company_id")).order_by("cae_code")
        )
        by_maturity = list(
            active.values("maturity_stage_name")
            .annotate(total=Count("company_id"))
            .order_by("maturity_stage_name")
        )
        employees_by_type = list(
            EmployeeProjection.objects.filter(is_active=True)
            .values("employee_type")
            .annotate(total=Count("employee_id"))
            .order_by("employee_type")
        )
        snapshot = DashboardSnapshot.objects.filter(source="company").first()
        return Response(
            {
                "total": active.count(),
                "inactive": CompanyProjection.objects.filter(is_active=False).count(),
                "by_sector": by_sector,
                "by_maturity": by_maturity,
                "employees_total": EmployeeProjection.objects.filter(is_active=True).count(),
                "employees_by_type": employees_by_type,
                "snapshot": snapshot.payload if snapshot else {},
            }
        )


class DashboardSpacesView(APIView):
    """Space utilization analytics from contract and booking projections."""

    permission_classes = [IsAuthenticated, IsStaff]

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request: Request) -> Response:
        occupied_contract_spaces = set(
            ContractProjection.objects.filter(is_active=True, space_id__isnull=False).values_list(
                "space_id", flat=True
            )
        )
        booked_spaces = set(
            BookingProjection.objects.filter(status="approved", space_id__isnull=False).values_list(
                "space_id", flat=True
            )
        )
        contract_spaces = ContractProjection.objects.filter(space_id__isnull=False).values_list(
            "space_id",
            flat=True,
        )
        booking_spaces = BookingProjection.objects.filter(space_id__isnull=False).values_list(
            "space_id",
            flat=True,
        )
        known_spaces = set(contract_spaces) | set(booking_spaces)
        occupied_spaces = occupied_contract_spaces | booked_spaces
        occupancy_percent = (
            round((len(occupied_spaces) / len(known_spaces)) * 100, 2) if known_spaces else 0.0
        )
        bookings_by_status = list(
            BookingProjection.objects.values("status")
            .annotate(total=Count("booking_id"))
            .order_by("status")
        )
        return Response(
            {
                "known_spaces": len(known_spaces),
                "occupied_spaces": len(occupied_spaces),
                "occupancy_percent": occupancy_percent,
                "active_contracts": ContractProjection.objects.filter(is_active=True).count(),
                "bookings_by_status": bookings_by_status,
            }
        )


class DashboardFinanceView(APIView):
    """Finance analytics from payment projections and cold-start finance snapshots."""

    permission_classes = [IsAuthenticated, IsStaff]

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request: Request) -> Response:
        paid = PaymentProjection.objects.all()
        month_start = timezone.localdate().replace(day=1)
        revenue_series = list(
            paid.annotate(month=TruncMonth("paid_at"))
            .values("month")
            .annotate(total=Coalesce(Sum("amount"), ZERO, output_field=DecimalField()))
            .order_by("month")
        )
        snapshot = DashboardSnapshot.objects.filter(source="finance").first()
        snapshot_payload = snapshot.payload if snapshot else {}
        return Response(
            {
                "revenue_total": _sum_amount(paid),
                "revenue_mtd": _sum_amount(paid.filter(paid_at__date__gte=month_start)),
                "revenue_series": revenue_series,
                "overdue_count": int(snapshot_payload.get("overdue") or 0)
                if isinstance(snapshot_payload, dict)
                else 0,
                "snapshot": snapshot_payload,
            }
        )


class DashboardReportsView(APIView):
    """Simple report projection for staff overview pages."""

    permission_classes = [IsAuthenticated, IsStaff]

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request: Request) -> Response:
        report_type = request.query_params.get("type", "service_health")
        headers = _forward_headers(request)
        if report_type == "finance":
            url = _env_url("METRICS", "finance", METRIC_ENDPOINTS["finance"])
            ok, payload = _fetch_json(url, headers)
            return Response({"type": report_type, "available": ok, "data": payload})

        rows = []
        for name, default_url in SERVICE_DEFAULTS.items():
            ok, payload = _fetch_json(_env_url("HEALTH", name, default_url), headers)
            rows.append({"service": name, "status": "up" if ok else "down", "payload": payload})
        return Response({"type": report_type, "rows": rows})
