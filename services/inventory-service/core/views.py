"""Views for equipment catalog and booking assignments."""

from __future__ import annotations

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema
from ilb_common.permissions import IsStaff

from core.models import Equipment, EquipmentAssignment, EquipmentType
from core.serializers import (
    EquipmentAssignSerializer,
    EquipmentReleaseSerializer,
    EquipmentSerializer,
    EquipmentTypeSerializer,
)
from core.services import apply_booking_event
from ilb_common.event_bus import EventEnvelope


def _role(request: Request) -> str:
    value = getattr(request.user, "role", "")
    return value if isinstance(value, str) else ""

from core.models import Equipment, EquipmentAssignment, EquipmentType
from core.serializers import (
    AssignmentSerializer,
    EquipmentAssignSerializer,
    EquipmentReleaseSerializer,
    EquipmentSerializer,
    EquipmentTypeSerializer,
)
from core.services import apply_booking_approved, apply_booking_state_changed


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
    def get(self, request: Request) -> Response:  # noqa: ARG002
        return Response({"status": "ok"})


class EquipmentTypeListCreateView(generics.ListCreateAPIView):
    serializer_class = EquipmentTypeSerializer
    queryset = EquipmentType.objects.all()

    def get_permissions(self):  # type: ignore[override]
        if self.request.method == "POST":
            return [IsAuthenticated(), IsStaff()]
        return [IsAuthenticated()]


class EquipmentTypeDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = EquipmentTypeSerializer
    queryset = EquipmentType.objects.all()
    lookup_url_kwarg = "type_id"

    def get_permissions(self):  # type: ignore[override]
        if self.request.method in {"PATCH", "PUT", "DELETE"}:
            return [IsAuthenticated(), IsStaff()]
        return [IsAuthenticated()]


class EquipmentListCreateView(generics.ListCreateAPIView):
    serializer_class = EquipmentSerializer
    queryset = Equipment.objects.all()

    def get_permissions(self):  # type: ignore[override]
        if self.request.method == "POST":
            return [IsAuthenticated(), IsStaff()]
        return [IsAuthenticated()]


class EquipmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = EquipmentSerializer
    queryset = Equipment.objects.all()
    lookup_url_kwarg = "equipment_id"

    def get_permissions(self):  # type: ignore[override]
        if self.request.method in {"PATCH", "PUT", "DELETE"}:
            return [IsAuthenticated(), IsStaff()]
        return [IsAuthenticated()]


class EquipmentAssignView(APIView):
    permission_classes = [IsAuthenticated, IsStaff]

    @extend_schema(request=EquipmentAssignSerializer, responses={200: EquipmentSerializer})
    def post(self, request: Request, equipment_id: str) -> Response:
        payload = EquipmentAssignSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        equipment = Equipment.objects.get(pk=equipment_id)
        assignment, _ = EquipmentAssignment.objects.update_or_create(
            equipment=equipment,
            booking_id=payload.validated_data["booking_id"],
            defaults={
                "company_id": payload.validated_data["company_id"],
                "status": EquipmentAssignment.Status.ASSIGNED,
            },
        )
        if equipment.status != Equipment.Status.IN_USE:
            equipment.status = Equipment.Status.IN_USE
            equipment.save(update_fields=["status", "updated_at"])
        _ = assignment
        return Response(EquipmentSerializer(equipment).data)


class EquipmentReleaseView(APIView):
    permission_classes = [IsAuthenticated, IsStaff]

    @extend_schema(request=EquipmentReleaseSerializer, responses={200: EquipmentSerializer})
    def post(self, request: Request, equipment_id: str) -> Response:
        payload = EquipmentReleaseSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        equipment = Equipment.objects.get(pk=equipment_id)
        EquipmentAssignment.objects.filter(
            equipment=equipment,
            booking_id=payload.validated_data["booking_id"],
            status=EquipmentAssignment.Status.ASSIGNED,
        ).update(status=EquipmentAssignment.Status.RELEASED)
        equipment.status = Equipment.Status.AVAILABLE
        equipment.save(update_fields=["status", "updated_at"])
        return Response(EquipmentSerializer(equipment).data)


class InventoryBookingEventView(APIView):
    permission_classes = [IsAuthenticated, IsStaff]

    def post(self, request: Request, event_type: str) -> Response:
        if event_type not in {"approved", "rejected", "cancelled", "completed"}:
            return Response({"detail": "unsupported event"}, status=400)
        payload = request.data
        event_id = request.headers.get("X-Event-Id")
        if not event_id:
            return Response({"detail": "Missing X-Event-Id"}, status=400)
        envelope: EventEnvelope = {
            "event_id": event_id,
            "event_type": f"booking.{event_type}",
            "occurred_at": request.headers.get("X-Event-Time", ""),
            "payload": payload,
        }
        apply_booking_event(envelope)
        return Response({"detail": "ok"})


class InventoryMyAssignmentsView(generics.ListAPIView):
    serializer_class = EquipmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):  # type: ignore[override]
        booking_id = self.request.query_params.get("booking")
        role = _role(self.request)
        qs = Equipment.objects.filter(assignments__isnull=False)
        if booking_id:
            qs = qs.filter(assignments__booking_id=booking_id)
        if role in {"Staff", "Director"}:
            return qs.distinct()
        if role == "Client":
            company_id = getattr(self.request.user, "company_id", None)
            if company_id is None:
                return Equipment.objects.none()
            return qs.filter(assignments__company_id=company_id).distinct()
        return Equipment.objects.none()
