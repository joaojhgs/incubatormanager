"""Contract API views and lifecycle actions."""

from __future__ import annotations

from uuid import UUID

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from ilb_common.permissions import IsStaff
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated as DRFIsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.events import (
    publish_contract_activated,
    publish_contract_terminated,
)
from core.models import Contract
from core.serializers import ContractSerializer


def _role(user: object) -> str:
    return str(getattr(user, "role", ""))


def _company_id(user: object) -> str | None:
    company_id = getattr(user, "company_id", None)
    return str(company_id) if company_id is not None else None


def _requires_company_scope(user: object) -> str:
    company_id = _company_id(user)
    if company_id is None:
        raise PermissionDenied("Missing X-Company-Id")
    return company_id


def _contract_queryset_for_role(user: object):
    role = _role(user)
    if role in {"Director", "Staff"}:
        return Contract.objects.all()

    if role == "Client":
        return Contract.objects.filter(company_id=_requires_company_scope(user))

    return Contract.objects.none()


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


class ContractListCreateView(generics.ListCreateAPIView):
    """List all visible contracts, or create a staff-managed contract."""

    serializer_class = ContractSerializer
    permission_classes = [DRFIsAuthenticated]

    def get_permissions(self):  # type: ignore[override]
        if self.request.method == "POST":
            return [DRFIsAuthenticated(), IsStaff()]
        return [DRFIsAuthenticated()]

    def get_queryset(self):  # type: ignore[override]
        return _contract_queryset_for_role(self.request.user)

    @extend_schema(
        responses={
            200: ContractSerializer(many=True),
            201: ContractSerializer,
        }
    )
    def perform_create(self, serializer: ContractSerializer) -> None:
        serializer.save()


class ContractDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Contract detail with client-owner scope and staff-managed writes."""

    serializer_class = ContractSerializer
    queryset = Contract.objects.all()
    lookup_url_kwarg = "pk"

    def get_permissions(self):  # type: ignore[override]
        if self.request.method in {"PATCH", "PUT", "DELETE"}:
            return [DRFIsAuthenticated(), IsStaff()]
        return [DRFIsAuthenticated()]

    def get_queryset(self):  # type: ignore[override]
        queryset = _contract_queryset_for_role(self.request.user)
        if self.request.method in {"PATCH", "PUT", "DELETE"}:
            return queryset
        if _role(self.request.user) == "Client":
            # Enforce object ownership for client detail requests.
            return queryset.filter(company_id=_requires_company_scope(self.request.user))
        return queryset


class ContractActivateView(APIView):
    """Activate contract and emit contract.activated."""

    permission_classes = [DRFIsAuthenticated, IsStaff]

    @extend_schema(
        request=ContractSerializer,
        responses={200: ContractSerializer},
    )
    def patch(self, request: Request, pk: str) -> Response:
        qs = _contract_queryset_for_role(request.user)
        contract = get_object_or_404(qs, pk=pk)

        if contract.status == Contract.Status.ACTIVE:
            return Response(ContractSerializer(contract).data)

        if contract.status == Contract.Status.TERMINATED:
            return Response(
                {"detail": "Cannot activate a terminated contract"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if contract.status == Contract.Status.EXPIRED:
            return Response(
                {"detail": "Cannot activate an expired contract"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        contract.activate()
        publish_contract_activated(contract)
        return Response(ContractSerializer(contract).data)


class ContractTerminateView(APIView):
    """Terminate contract with optional reason and emit contract.terminated."""

    permission_classes = [DRFIsAuthenticated, IsStaff]

    @extend_schema(
        request={
            "application/json": {
                "type": "object",
                "properties": {"reason": {"type": "string"}},
            }
        },
        responses={200: ContractSerializer},
    )
    def patch(self, request: Request, pk: str) -> Response:
        qs = _contract_queryset_for_role(request.user)
        contract = get_object_or_404(qs, pk=pk)

        if contract.status == Contract.Status.TERMINATED:
            return Response(ContractSerializer(contract).data)

        if contract.status == Contract.Status.EXPIRED:
            return Response(
                {"detail": "Cannot terminate an expired contract"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reason = (request.data or {}).get("reason", "")
        contract.terminate(reason=str(reason))
        publish_contract_terminated(contract)
        return Response(ContractSerializer(contract).data)


class ContractCompanyListView(generics.ListAPIView):
    """List contracts for a specific company with role-aware scoping."""

    serializer_class = ContractSerializer
    permission_classes = [DRFIsAuthenticated]
    lookup_url_kwarg = "company_id"

    def get_queryset(self):  # type: ignore[override]
        company_id = str(self.kwargs["company_id"])
        role = _role(self.request.user)

        if role in {"Director", "Staff"}:
            return Contract.objects.filter(company_id=UUID(company_id))

        if role != "Client":
            return Contract.objects.none()

        if _requires_company_scope(self.request.user) != company_id:
            raise PermissionDenied("Company mismatch")

        return Contract.objects.filter(company_id=UUID(company_id))
