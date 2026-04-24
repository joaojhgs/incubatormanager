"""Public health endpoints for probes and gateway routing."""

from __future__ import annotations

from drf_spectacular.utils import extend_schema
from ilb_common.bootstrap import shared_settings
from minio import Minio
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


def _minio_configured(settings: dict) -> bool:
    return bool(
        settings["MINIO_ENDPOINT"]
        and settings["MINIO_ACCESS_KEY"]
        and settings["MINIO_SECRET_KEY"]
    )


def _probe_minio(settings: dict) -> bool:
    client = Minio(
        settings["MINIO_ENDPOINT"],
        access_key=settings["MINIO_ACCESS_KEY"],
        secret_key=settings["MINIO_SECRET_KEY"],
        secure=settings["MINIO_USE_SSL"],
    )
    client.list_buckets()
    return True


class HealthView(APIView):
    """Liveness/readiness-style health payload (includes MinIO when configured)."""

    authentication_classes = ()
    permission_classes = ()

    @extend_schema(
        responses={
            200: {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "example": "ok"},
                    "minio": {"type": "string", "example": "ok"},
                },
            },
            503: {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "example": "degraded"},
                    "minio": {"type": "string", "example": "unreachable"},
                },
            },
        }
    )
    def get(self, request: Request) -> Response:
        s = shared_settings()
        if not _minio_configured(s):
            return Response({"status": "ok"})

        try:
            _probe_minio(s)
        except Exception:
            return Response(
                {"status": "degraded", "minio": "unreachable"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response({"status": "ok", "minio": "ok"})
