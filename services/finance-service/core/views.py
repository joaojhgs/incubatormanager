"""Finance API views."""

from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.db.models import Count, DecimalField, Q, Sum
from django.db.models.functions import Coalesce
from django.http import Http404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from ilb_common.permissions import IsStaff
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.handlers import publish_payment_recorded
from core.models import Payment
from core.serializers import (
    DashboardSerializer,
    PaymentPatchSerializer,
    PaymentSerializer,
    ReportSerializer,
)
from core.services import payment_scope_for_user
from core.utils import rabbitmq_url


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


class PaymentListView(generics.ListAPIView):
    """List payments visible to the caller."""

    permission_classes = [IsAuthenticated]
    serializer_class = PaymentSerializer

    def get_queryset(self):  # type: ignore[override]
        return payment_scope_for_user(self.request.user)


class PaymentDetailView(generics.RetrieveUpdateAPIView):
    """Retrieve or patch a payment."""

    permission_classes = [IsAuthenticated]
    serializer_class = PaymentSerializer
    lookup_url_kwarg = "payment_id"

    def get_queryset(self):  # type: ignore[override]
        return payment_scope_for_user(self.request.user)

    def get_serializer_class(self):  # type: ignore[override]
        if self.request is not None and self.request.method in {"PATCH", "PUT"}:
            return PaymentPatchSerializer
        return PaymentSerializer

    def get_permissions(self):  # type: ignore[override]
        if self.request is not None and self.request.method in {"PATCH", "PUT"}:
            return [IsAuthenticated(), IsStaff()]
        return [IsAuthenticated()]

    def perform_update(self, serializer: PaymentPatchSerializer) -> None:
        payment = self.get_object()
        desired_status = serializer.validated_data["status"]
        paid_at = serializer.validated_data.get("paid_at")

        if desired_status == Payment.Status.PAID:
            if payment.mark_paid(paid_at) and rabbitmq_url():
                transaction.on_commit(
                    lambda: publish_payment_recorded(
                        payment_id=payment.id,
                        amount=payment.amount,
                        company_id=payment.company_id,
                        contract_id=payment.contract_id,
                        booking_id=payment.booking_id,
                        paid_at=payment.paid_at or timezone.now(),
                    )
                )
            serializer.instance = payment
            return

        if desired_status != Payment.Status.PAID:
            payment.paid_at = None
        payment.status = desired_status
        payment.save(update_fields=("status", "paid_at", "updated_at"))
        serializer.instance = payment


class CompanyPaymentListView(generics.ListAPIView):
    """List payments for a specific company."""

    permission_classes = [IsAuthenticated]
    serializer_class = PaymentSerializer

    def get_queryset(self):  # type: ignore[override]
        company_id = self.kwargs.get("company_id")
        role = getattr(self.request.user, "role", None)
        user_company_id = getattr(self.request.user, "company_id", None)

        if role in {"Director", "Staff"}:
            return payment_scope_for_user(self.request.user).filter(company_id=company_id)

        if role == "Client" and company_id is not None and str(user_company_id) == str(company_id):
            return payment_scope_for_user(self.request.user)

        return Payment.objects.none()

    def get(self, request: Request, *args: object, **kwargs: object) -> Response:
        role = getattr(request.user, "role", None)
        if role == "Client":
            company_id = str(kwargs.get("company_id"))
            if not company_id or str(getattr(request.user, "company_id", "")) != company_id:
                raise Http404
        return super().get(request, *args, **kwargs)


class FinanceDashboardView(APIView):
    """Summary totals for dashboard cards."""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses=DashboardSerializer)
    def get(self, request: Request) -> Response:
        qs = payment_scope_for_user(request.user)
        paid_qs = qs.filter(status=Payment.Status.PAID)
        pending_qs = qs.filter(status=Payment.Status.PENDING)
        overdue_qs = qs.filter(status=Payment.Status.OVERDUE)

        payload = {
            "total_payments": qs.count(),
            "paid": paid_qs.count(),
            "pending": pending_qs.count(),
            "overdue": overdue_qs.count(),
            "total_amount": qs.aggregate(
                total=Coalesce(Sum("amount"), Decimal("0"), output_field=DecimalField())
            )["total"],
            "paid_amount": paid_qs.aggregate(
                total=Coalesce(Sum("amount"), Decimal("0"), output_field=DecimalField())
            )["total"],
            "pending_amount": pending_qs.aggregate(
                total=Coalesce(Sum("amount"), Decimal("0"), output_field=DecimalField())
            )["total"],
            "overdue_amount": overdue_qs.aggregate(
                total=Coalesce(Sum("amount"), Decimal("0"), output_field=DecimalField())
            )["total"],
        }

        serializer = DashboardSerializer(payload)
        return Response(serializer.data)


class FinanceReportsView(APIView):
    """Aggregate payment reports by company and status."""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses=ReportSerializer(many=True))
    def get(self, request: Request) -> Response:
        rows = (
            payment_scope_for_user(request.user)
            .values("company_id")
            .annotate(
                total=Count("id"),
                paid=Count("id", filter=Q(status=Payment.Status.PAID)),
                pending=Count("id", filter=Q(status=Payment.Status.PENDING)),
                overdue=Count("id", filter=Q(status=Payment.Status.OVERDUE)),
                collected_amount=Coalesce(
                    Sum("amount", filter=Q(status=Payment.Status.PAID)),
                    Decimal("0"),
                    output_field=DecimalField(),
                ),
            )
            .order_by("company_id")
        )

        serializer = ReportSerializer(data=list(rows), many=True)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)
