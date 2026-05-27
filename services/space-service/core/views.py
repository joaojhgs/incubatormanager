"""Views for space service."""

from __future__ import annotations

from hashlib import sha256
from uuid import uuid4

from django.core.cache import cache
from django.db.models import Count, Max, Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from ilb_common.permissions import IsStaff
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Space, SpaceBookingRecord, SpaceContract, SpaceType
from core.serializers import (
    BookingEventSerializer,
    ContractEventSerializer,
    SpaceContractSerializer,
    SpaceOccupancySerializer,
    SpaceSerializer,
    SpaceTypeSerializer,
)
from core.services import apply_booking_event_dict, apply_contract_event, occupancy_for_space


def _role(request: Request) -> str:
    role = getattr(request.user, "role", "")
    return role if isinstance(role, str) else ""


def _company_id(request: Request) -> str | None:
    value = getattr(request.user, "company_id", None)
    return str(value) if value else None


def scoped_spaces(request: Request):
    qs = Space.objects.all()
    role = _role(request)
    if role in {"Staff", "Director"}:
        return qs
    if role == "Client" and _company_id(request):
        # Clients need their contracted spaces plus unassigned reservable spaces for
        # the portal booking flow. Keep occupied spaces from other companies hidden.
        return qs.filter(
            Q(company_id=_company_id(request))
            | Q(company_id__isnull=True, status=Space.Status.AVAILABLE, is_active=True)
        )
    return qs.none()


def scoped_contracts(request: Request):
    role = _role(request)
    if role in {"Staff", "Director"}:
        return SpaceContract.objects.all()
    if role == "Client" and _company_id(request):
        return SpaceContract.objects.filter(company_id=_company_id(request))
    return SpaceContract.objects.none()


class HealthView(APIView):
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


class SpaceTypeListCreateView(generics.ListCreateAPIView):
    serializer_class = SpaceTypeSerializer

    def get_queryset(self):  # type: ignore[override]
        return SpaceType.objects.all()

    def get_permissions(self):  # type: ignore[override]
        if self.request.method == "POST":
            return [IsAuthenticated(), IsStaff()]
        return [IsAuthenticated()]


class SpaceTypeDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SpaceTypeSerializer
    queryset = SpaceType.objects.all()
    lookup_url_kwarg = "type_id"

    def get_permissions(self):  # type: ignore[override]
        if self.request.method in {"PATCH", "PUT", "DELETE"}:
            return [IsAuthenticated(), IsStaff()]
        return [IsAuthenticated()]


class SpaceListCreateView(generics.ListCreateAPIView):
    serializer_class = SpaceSerializer

    def get_queryset(self):  # type: ignore[override]
        queryset = scoped_spaces(self.request)
        status = self.request.query_params.get("status")
        if status:
            queryset = queryset.filter(status=status)
        space_type = self.request.query_params.get("type") or self.request.query_params.get(
            "space_type"
        )
        if space_type:
            queryset = queryset.filter(space_type_id=space_type)
        return queryset

    def get_permissions(self):  # type: ignore[override]
        if self.request.method == "POST":
            return [IsAuthenticated(), IsStaff()]
        return [IsAuthenticated()]


class PublicSpaceListView(generics.ListAPIView):
    authentication_classes = ()
    permission_classes = ()
    serializer_class = SpaceSerializer

    def get_queryset(self):  # type: ignore[override]
        active_booking_space_ids = SpaceBookingRecord.objects.filter(
            status=SpaceBookingRecord.Status.APPROVED,
            end_time__gt=timezone.now(),
        ).values("space_id")
        return (
            Space.objects.filter(is_active=True, company_id__isnull=True)
            .exclude(status__in=[Space.Status.BLOCKED, Space.Status.MAINTENANCE])
            .filter(
                Q(status=Space.Status.AVAILABLE)
                | Q(id__in=active_booking_space_ids)
            )
            .order_by("name")
        )


class SpaceDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SpaceSerializer
    lookup_url_kwarg = "space_id"

    def get_queryset(self):  # type: ignore[override]
        return scoped_spaces(self.request)

    def get_permissions(self):  # type: ignore[override]
        if self.request.method in {"PATCH", "PUT", "DELETE"}:
            return [IsAuthenticated(), IsStaff()]
        return [IsAuthenticated()]


class SpaceOccupancyMapView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: SpaceOccupancySerializer(many=True)})
    def get(self, request: Request) -> Response:
        spaces = scoped_spaces(request)
        space_signature = spaces.aggregate(updated=Max("updated_at"), total=Count("id"))
        booking_signature = SpaceBookingRecord.objects.aggregate(
            updated=Max("updated_at"),
            total=Count("id"),
        )
        cache_source = (
            f"{_role(request)}:{_company_id(request) or 'staff'}:"
            f"{space_signature['updated']}:{space_signature['total']}:"
            f"{booking_signature['updated']}:{booking_signature['total']}"
        )
        cache_key = f"space-occupancy:{sha256(cache_source.encode()).hexdigest()}"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        result = []
        for space in spaces:
            occupancy = occupancy_for_space(space)
            occupancy_percent = occupancy["occupancy_percent"]
            result.append(
                {
                    "space_id": occupancy["space_id"],
                    "space_name": occupancy["space_name"],
                    "capacity": occupancy["capacity"],
                    "occupied": occupancy["occupied"],
                    "occupancy_percent": occupancy_percent,
                    "status": space.status,
                }
            )
        serializer = SpaceOccupancySerializer(data=result, many=True)
        serializer.is_valid(raise_exception=True)
        cache.set(cache_key, serializer.data, timeout=10)
        return Response(serializer.data)


class SpaceContractEventView(APIView):
    permission_classes = [IsAuthenticated, IsStaff]

    @extend_schema(request=ContractEventSerializer)
    def post(self, request: Request, event_type: str) -> Response:
        if event_type not in {"activated", "terminated", "expired"}:
            return Response({"detail": "Unsupported event type"}, status=400)
        event_payload = {
            "event_id": request.headers.get("X-Event-Id") or str(uuid4()),
            "event_type": f"contract.{event_type}",
            "occurred_at": request.headers.get("X-Event-Time", ""),
            "payload": request.data,
        }
        apply_contract_event(event_payload)  # type: ignore[arg-type]
        return Response({"detail": "ok"})


class SpaceBookingEventView(APIView):
    permission_classes = [IsAuthenticated, IsStaff]

    @extend_schema(request=BookingEventSerializer)
    def post(self, request: Request, event_type: str) -> Response:
        if event_type not in {"approved", "rejected", "cancelled", "completed"}:
            return Response({"detail": "Unsupported event type"}, status=400)
        event_payload = {
            "event_id": request.headers.get("X-Event-Id") or str(uuid4()),
            "event_type": f"booking.{event_type}",
            "occurred_at": request.headers.get("X-Event-Time", ""),
            "payload": request.data,
        }
        apply_booking_event_dict(event_payload)  # type: ignore[arg-type]
        return Response({"detail": "ok"})


class SpaceContractListView(generics.ListAPIView):
    serializer_class = SpaceContractSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):  # type: ignore[override]
        return scoped_contracts(self.request)


class SpaceBookingRecordListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):  # type: ignore[override]
        if _role(self.request) in {"Staff", "Director"}:
            return SpaceBookingRecord.objects.all().order_by("start_time", "space")
        if _role(self.request) == "Client" and _company_id(self.request):
            return SpaceBookingRecord.objects.filter(company_id=_company_id(self.request)).order_by(
                "start_time"
            )
        return SpaceBookingRecord.objects.none()

    def get(self, request: Request) -> Response:
        queryset = self.get_queryset()
        payload = []
        for record in queryset:
            payload.append(
                {
                    "id": str(record.booking_id),
                    "space_id": str(record.space_id),
                    "company_id": str(record.company_id),
                    "status": record.status,
                    "start_time": record.start_time,
                    "end_time": record.end_time,
                    "quoted_price": str(record.quoted_price)
                    if record.quoted_price is not None
                    else None,
                    "equipment_ids": record.equipment_ids,
                }
            )
        return Response(payload)


class MetricsView(APIView):
    """Minimal operational metrics endpoint for local demos and probes."""

    authentication_classes = ()
    permission_classes = ()

    @extend_schema(
        responses={
            200: {
                "type": "object",
                "properties": {
                    "service": {"type": "string", "example": "space-service"},
                    "status": {"type": "string", "example": "ok"},
                    "metrics": {"type": "object"},
                },
            }
        }
    )
    def get(self, request: Request) -> Response:
        return Response({"service": "space-service", "status": "ok", "metrics": {}})
