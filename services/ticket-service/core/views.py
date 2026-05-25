"""Ticket API endpoints (tickets, messages, health)."""

from __future__ import annotations

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from ilb_common.permissions import IsClientOwner, IsStaff
from rest_framework import generics, serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Ticket, TicketMessage
from core.permissions import IsTicketOwnerOrStaff
from core.serializers import (
    TicketCreateSerializer,
    TicketMessageCreateSerializer,
    TicketMessageSerializer,
    TicketSerializer,
)
from core.services import ticket_scope_for_user


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


class TicketListCreateView(generics.ListCreateAPIView):
    """List tickets (staff) or create a ticket (staff/client)."""

    permission_classes = [IsAuthenticated]
    queryset = Ticket.objects.all().prefetch_related("messages").order_by("-updated_at")

    def get_permissions(self):  # type: ignore[override]
        if self.request.method == "GET":
            return [IsAuthenticated(), IsStaff()]
        return [IsAuthenticated()]

    def get_queryset(self):  # type: ignore[override]
        return (
            ticket_scope_for_user(self.request.user)
            .prefetch_related("messages")
            .order_by("-updated_at")
        )

    def get_serializer_class(self):  # type: ignore[override]
        if self.request.method == "POST":
            return TicketCreateSerializer
        return TicketSerializer

    def perform_create(self, serializer: TicketCreateSerializer) -> Ticket:
        user = self.request.user
        role = getattr(user, "role", "")
        if role == "Client":
            if getattr(user, "company_id", None) is None:
                raise serializers.ValidationError(
                    {"company_id": "X-Company-Id is required for client users."}
                )
            return Ticket.objects.create(
                company_id=user.company_id,
                created_by_id=user.id,
                created_by_role=role,
                subject=serializer.validated_data["subject"],
                description=serializer.validated_data["description"],
            )
        if "company_id" not in serializer.validated_data:
            raise serializers.ValidationError({"company_id": "company_id is required."})
        return Ticket.objects.create(
            company_id=serializer.validated_data["company_id"],
            created_by_id=user.id,
            created_by_role=role,
            subject=serializer.validated_data["subject"],
            description=serializer.validated_data["description"],
        )

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ticket = self.perform_create(serializer)
        return Response(TicketSerializer(ticket).data, status=status.HTTP_201_CREATED)


class TicketDetailView(generics.RetrieveUpdateAPIView):
    """Ticket detail and staff status updates."""

    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated, IsTicketOwnerOrStaff]
    queryset = Ticket.objects.all().prefetch_related("messages")
    lookup_field = "id"
    lookup_url_kwarg = "ticket_id"

    def get_queryset(self):  # type: ignore[override]
        return (
            ticket_scope_for_user(self.request.user)
            .prefetch_related("messages")
            .select_related()
        )

    def patch(self, request: Request, *args, **kwargs) -> Response:
        if request.user.role not in {"Staff", "Director"}:
            return Response({"detail": "Only staff may update tickets."}, status=403)
        return super().patch(request, *args, **kwargs)


class MyTicketsView(generics.ListAPIView):
    """List tickets for an authenticated client company."""

    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated, IsClientOwner]

    def get_queryset(self):  # type: ignore[override]
        user = self.request.user
        if user.company_id is None:
            return Ticket.objects.none()
        return (
            Ticket.objects.filter(company_id=user.company_id)
            .prefetch_related("messages")
            .order_by("-updated_at")
        )


class TicketMessageCreateView(APIView):
    """Append a message to a ticket."""

    permission_classes = [IsAuthenticated, IsTicketOwnerOrStaff]

    @extend_schema(
        request=TicketMessageCreateSerializer,
        responses={201: TicketMessageSerializer},
    )
    def post(self, request: Request, ticket_id: str) -> Response:
        user = request.user
        ticket = get_object_or_404(ticket_scope_for_user(user), pk=ticket_id)
        self.check_object_permissions(request, ticket)
        serializer = TicketMessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = TicketMessage.objects.create(
            ticket=ticket,
            sender_id=user.id,
            sender_role=getattr(user, "role", ""),
            body=serializer.validated_data["body"],
        )
        return Response(
            TicketMessageSerializer(message).data,
            status=status.HTTP_201_CREATED,
        )
