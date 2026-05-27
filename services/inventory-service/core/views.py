"""Views for equipment catalog and booking assignments."""

from __future__ import annotations

from drf_spectacular.utils import extend_schema
from ilb_common.event_bus import EventEnvelope
from ilb_common.permissions import IsStaff
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Equipment, EquipmentAssignment, EquipmentType
from core.serializers import (
    EquipmentAssignmentSerializer,
    EquipmentAssignSerializer,
    EquipmentReleaseSerializer,
    EquipmentSerializer,
    EquipmentTypeSerializer,
)
from core.services import apply_booking_event


def _role(request: Request) -> str:
    value = getattr(request.user, "role", "")
    return value if isinstance(value, str) else ""


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

    def get_queryset(self):  # type: ignore[override]
        queryset = Equipment.objects.all()
        equipment_type = self.request.query_params.get("type") or self.request.query_params.get(
            "equipment_type"
        )
        if equipment_type:
            queryset = queryset.filter(equipment_type_id=equipment_type)
        status = self.request.query_params.get("status")
        if status:
            queryset = queryset.filter(status=status)
        space_id = self.request.query_params.get("space") or self.request.query_params.get(
            "assigned_space_id"
        )
        if space_id:
            queryset = queryset.filter(assigned_space_id=space_id)
        return queryset

    def get_permissions(self):  # type: ignore[override]
        if self.request.method == "POST":
            return [IsAuthenticated(), IsStaff()]
        return [IsAuthenticated()]


class PublicEquipmentListView(generics.ListAPIView):
    authentication_classes = ()
    permission_classes = ()
    serializer_class = EquipmentSerializer

    def get_queryset(self):  # type: ignore[override]
        return Equipment.objects.filter(
            is_active=True,
            status=Equipment.Status.AVAILABLE,
        ).order_by("name")


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
        if "assigned_space_id" in payload.validated_data:
            equipment.assigned_space_id = payload.validated_data["assigned_space_id"]
        if "booking_id" in payload.validated_data:
            assignment, _ = EquipmentAssignment.objects.update_or_create(
                equipment=equipment,
                booking_id=payload.validated_data["booking_id"],
                defaults={
                    "company_id": payload.validated_data["company_id"],
                    "assigned_space_id": payload.validated_data.get("assigned_space_id"),
                    "status": EquipmentAssignment.Status.ASSIGNED,
                },
            )
            equipment.status = Equipment.Status.IN_USE
            _ = assignment
        equipment.save(update_fields=["assigned_space_id", "status", "updated_at"])
        return Response(EquipmentSerializer(equipment).data)


class EquipmentReleaseView(APIView):
    permission_classes = [IsAuthenticated, IsStaff]

    @extend_schema(request=EquipmentReleaseSerializer, responses={200: EquipmentSerializer})
    def post(self, request: Request, equipment_id: str) -> Response:
        payload = EquipmentReleaseSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        equipment = Equipment.objects.get(pk=equipment_id)
        assignments = EquipmentAssignment.objects.filter(
            equipment=equipment,
            booking_id=payload.validated_data["booking_id"],
            status=EquipmentAssignment.Status.ASSIGNED,
        )
        released_space_ids = {
            assignment.assigned_space_id
            for assignment in assignments
            if assignment.assigned_space_id is not None
        }
        assignments.update(status=EquipmentAssignment.Status.RELEASED)
        remaining = EquipmentAssignment.objects.filter(
            equipment=equipment,
            status=EquipmentAssignment.Status.ASSIGNED,
        )
        update_fields = ["updated_at"]
        if equipment.assigned_space_id in released_space_ids and not remaining.exists():
            equipment.assigned_space_id = None
            update_fields.append("assigned_space_id")
        if not remaining.exists():
            equipment.status = Equipment.Status.AVAILABLE
            update_fields.append("status")
        if len(update_fields) > 1:
            equipment.save(update_fields=update_fields)
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


class InventoryAssignmentListView(generics.ListAPIView):
    """Assignment history scoped for staff or the authenticated client company."""

    serializer_class = EquipmentAssignmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):  # type: ignore[override]
        queryset = EquipmentAssignment.objects.select_related("equipment").all()
        role = _role(self.request)
        if role == "Client":
            company_id = getattr(self.request.user, "company_id", None)
            if company_id is None:
                return EquipmentAssignment.objects.none()
            queryset = queryset.filter(company_id=company_id)
        elif role not in {"Staff", "Director"}:
            return EquipmentAssignment.objects.none()

        booking_id = self.request.query_params.get("booking")
        if booking_id:
            queryset = queryset.filter(booking_id=booking_id)
        equipment_id = self.request.query_params.get("equipment")
        if equipment_id:
            queryset = queryset.filter(equipment_id=equipment_id)
        return queryset


class MetricsView(APIView):
    """Minimal operational metrics endpoint for local demos and probes."""

    authentication_classes = ()
    permission_classes = ()

    @extend_schema(
        responses={
            200: {
                "type": "object",
                "properties": {
                    "service": {"type": "string", "example": "inventory-service"},
                    "status": {"type": "string", "example": "ok"},
                    "metrics": {"type": "object"},
                },
            }
        }
    )
    def get(self, request: Request) -> Response:
        return Response({"service": "inventory-service", "status": "ok", "metrics": {}})
