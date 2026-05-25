"""Dashboard aggregation views."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from typing import Any
from urllib.error import URLError
from urllib.request import Request as UrlRequest
from urllib.request import urlopen

from drf_spectacular.utils import extend_schema
from ilb_common.permissions import IsStaff
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

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
    "ticket": "http://ticket-service:8008/api/tickets/",
}


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
    """Staff dashboard with downstream health and lightweight metric snapshots."""

    permission_classes = [IsAuthenticated, IsStaff]

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
                "services": services,
                "metrics": metrics,
            }
        )


class DashboardReportsView(APIView):
    """Simple report projection for staff overview pages."""

    permission_classes = [IsAuthenticated, IsStaff]

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
