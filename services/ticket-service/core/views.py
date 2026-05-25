"""Views for ticket service."""

from __future__ import annotations

from uuid import UUID

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from ilb_common.permissions import IsClientOwner, IsStaff
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView, ListCreateAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import TicketMessage
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
            200: {"type": "object", "properties": {"status": {"type": "string", "example": "ok"}}}
        }
    )
    def get(self, request: Request) -> Response:
        return Response({"status": "ok"})


class TicketListCreateView(ListCreateAPIView):
    """List tickets (scoped by role) and create new tickets."""

    permission_classes = [IsAuthenticated]

    def get_queryset(self):  # type: ignore[override]
        qs = ticket_scope_for_user(self.request.user)
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)

        company_id = self.request.query_params.get("company_id")
        if company_id:
            try:
                company_uuid = UUID(str(company_id))
            except ValueError as exc:
                raise ValidationError({"company_id": "Must be a valid UUID."}) from exc
            qs = qs.filter(company_id=company_uuid)

        assigned_to = self.request.query_params.get("assigned_to")
        assigned_to = assigned_to or self.request.query_params.get("assigned_to_user_id")
        if assigned_to:
            if assigned_to == "unassigned":
                qs = qs.filter(assigned_to__isnull=True)
            else:
                try:
                    assigned_uuid = UUID(str(assigned_to))
                except ValueError as exc:
                    raise ValidationError(
                        {"assigned_to": "Must be a valid UUID or 'unassigned'."}
                    ) from exc
                qs = qs.filter(assigned_to=assigned_uuid)

        return qs.prefetch_related("messages")

    def get_serializer_class(self):  # type: ignore[override]
        if self.request.method == "POST":
            return TicketCreateSerializer
        return TicketSerializer

    def perform_create(self, serializer: TicketCreateSerializer) -> None:
        user = self.request.user
        role = getattr(user, "role", None)

        if role == "Client":
            company_id = getattr(user, "company_id", None)
            if company_id is None:
                raise ValidationError("Client users must be bound to a company")
            serializer.save(
                company_id=company_id,
                assigned_to=None,
                created_by_user_id=user.id,
                created_by_role=role,
            )
            return

        if role in {"Staff", "Director"}:
            company_id = serializer.validated_data.get("company_id")
            if company_id is None:
                raise ValidationError("staff tickets require company_id")
            serializer.save(company_id=company_id, created_by_user_id=user.id, created_by_role=role)
            return

        raise ValidationError("Unsupported role")


class TicketDetailView(RetrieveUpdateAPIView):
    """Ticket detail (clients read own, staff can update)."""

    permission_classes = [IsAuthenticated, IsTicketOwnerOrStaff]
    serializer_class = TicketSerializer
    lookup_url_kwarg = "ticket_id"

    def get_queryset(self):  # type: ignore[override]
        return ticket_scope_for_user(self.request.user).prefetch_related("messages")

    def get_permissions(self):  # type: ignore[override]
        if self.request.method in {"PATCH", "PUT"}:
            return [IsAuthenticated(), IsStaff()]
        return [IsAuthenticated(), IsTicketOwnerOrStaff()]


class MyTicketsView(ListAPIView):
    """Tickets owned by the caller's company (client-only)."""

    permission_classes = [IsAuthenticated, IsClientOwner]
    serializer_class = TicketSerializer

    def get_queryset(self):  # type: ignore[override]
        return ticket_scope_for_user(self.request.user).prefetch_related("messages")


class TicketMessageCreateView(APIView):
    """Append a message to a ticket thread."""

    permission_classes = [IsAuthenticated, IsTicketOwnerOrStaff]

    @extend_schema(request=TicketMessageCreateSerializer, responses={201: TicketMessageSerializer})
    def post(self, request: Request, ticket_id: UUID) -> Response:
        ticket = get_object_or_404(ticket_scope_for_user(request.user), id=ticket_id)
        self.check_object_permissions(request, ticket)

        serializer = TicketMessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = TicketMessage.objects.create(
            ticket=ticket,
            author_user_id=request.user.id,
            author_role=request.user.role,
            content=serializer.validated_data["content"],
        )
        return Response(TicketMessageSerializer(message).data, status=status.HTTP_201_CREATED)
