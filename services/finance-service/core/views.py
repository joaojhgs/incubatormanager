"""Finance API views."""

from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.db.models import Count, DecimalField, Q, Sum
from django.db.models.functions import Coalesce, TruncDay, TruncMonth
from django.http import Http404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from ilb_common.permissions import IsDirector, IsStaff
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.billing import generate_monthly_billing, parse_as_of
from core.handlers import publish_payment_recorded
from core.models import Payment
from core.serializers import (
    BillingGenerateResultSerializer,
    BillingGenerateSerializer,
    DashboardSerializer,
    FinanceReportQuerySerializer,
    NextDuePaymentSerializer,
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
        queryset = payment_scope_for_user(self.request.user)
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        source = self.request.query_params.get("source")
        if source:
            queryset = queryset.filter(source=source)
        payment_type = self.request.query_params.get("payment_type")
        if payment_type:
            queryset = queryset.filter(payment_type=payment_type)
        company_id = self.request.query_params.get("company_id")
        if company_id and getattr(self.request.user, "role", None) in {"Director", "Staff"}:
            queryset = queryset.filter(company_id=company_id)
        date_from = self.request.query_params.get("date_from")
        if date_from:
            queryset = queryset.filter(due_date__gte=date_from)
        date_to = self.request.query_params.get("date_to")
        if date_to:
            queryset = queryset.filter(due_date__lte=date_to)
        return queryset


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
        reference_id = serializer.validated_data.get("reference_id")

        if desired_status == Payment.Status.PAID:
            if payment.mark_paid(paid_at, reference_id=reference_id) and rabbitmq_url():
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
            "status_breakdown": list(
                qs.values("status")
                .annotate(
                    count=Count("id"),
                    amount=Coalesce(Sum("amount"), Decimal("0"), output_field=DecimalField()),
                )
                .order_by("status")
            ),
            "source_breakdown": list(
                qs.values("source")
                .annotate(
                    count=Count("id"),
                    amount=Coalesce(Sum("amount"), Decimal("0"), output_field=DecimalField()),
                )
                .order_by("source")
            ),
            "payment_type_breakdown": list(
                qs.values("payment_type")
                .annotate(
                    count=Count("id"),
                    amount=Coalesce(Sum("amount"), Decimal("0"), output_field=DecimalField()),
                )
                .order_by("payment_type")
            ),
            # Sector is not stored in the finance bounded context; keep a stable
            # report shape so dashboards can render a fallback group.
            "by_sector": [
                {
                    "sector": "unknown",
                    "count": qs.count(),
                    "amount": qs.aggregate(
                        total=Coalesce(Sum("amount"), Decimal("0"), output_field=DecimalField())
                    )["total"],
                }
            ],
        }

        serializer = DashboardSerializer(payload)
        return Response(serializer.data)


class FinanceReportsView(APIView):
    """Aggregate payment reports by requested Week-3 report type."""

    permission_classes = [IsAuthenticated]

    @extend_schema(parameters=[FinanceReportQuerySerializer], responses=ReportSerializer(many=True))
    def get(self, request: Request) -> Response:
        query = FinanceReportQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        data = query.validated_data
        report_type = data["type"]
        qs = payment_scope_for_user(request.user)
        if date_from := data.get("date_from"):
            qs = qs.filter(created_at__date__gte=date_from)
        if date_to := data.get("date_to"):
            qs = qs.filter(created_at__date__lte=date_to)

        if report_type == "payment_status_summary":
            rows = list(
                qs.values("status")
                .annotate(
                    total=Count("id"),
                    amount=Coalesce(Sum("amount"), Decimal("0"), output_field=DecimalField()),
                )
                .order_by("status")
            )
            return Response({"type": report_type, "results": rows})

        if report_type == "cash_flow_trend":
            trunc = TruncDay("paid_at") if data["group_by"] == "day" else TruncMonth("paid_at")
            rows = list(
                qs.filter(status=Payment.Status.PAID, paid_at__isnull=False)
                .annotate(period=trunc)
                .values("period")
                .annotate(
                    collected_amount=Coalesce(
                        Sum("amount"), Decimal("0"), output_field=DecimalField()
                    ),
                    total=Count("id"),
                )
                .order_by("period")
            )
            for row in rows:
                row["period"] = row["period"].date().isoformat() if row["period"] else None
            return Response({"type": report_type, "group_by": data["group_by"], "results": rows})

        if report_type == "revenue_by_maturity":
            paid = qs.filter(status=Payment.Status.PAID)
            row = {
                "maturity_stage": "unknown",
                "total": paid.count(),
                "collected_amount": paid.aggregate(
                    total=Coalesce(Sum("amount"), Decimal("0"), output_field=DecimalField())
                )["total"],
            }
            return Response({"type": report_type, "results": [row]})

        rows = (
            qs.values("company_id")
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
        return Response({"type": report_type, "results": serializer.data})


class BillingGenerateView(APIView):
    """Director-only wrapper around the idempotent monthly billing command."""

    permission_classes = [IsAuthenticated, IsDirector]

    @extend_schema(
        request=BillingGenerateSerializer,
        responses={200: BillingGenerateResultSerializer},
    )
    def post(self, request: Request) -> Response:
        serializer = BillingGenerateSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        as_of_value = serializer.validated_data.get("as_of")
        result = generate_monthly_billing(
            as_of=as_of_value if as_of_value is not None else parse_as_of(None)
        )
        return Response(result, status=status.HTTP_200_OK)


class NextDuePaymentView(APIView):
    """Return the earliest unpaid payment visible to the caller."""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses=NextDuePaymentSerializer)
    def get(self, request: Request) -> Response:
        payment = (
            payment_scope_for_user(request.user)
            .filter(
                status__in=[Payment.Status.PENDING, Payment.Status.OVERDUE],
                due_date__isnull=False,
            )
            .order_by("due_date", "created_at")
            .first()
        )
        if payment is None:
            return Response(
                {
                    "payment_id": None,
                    "company_id": None,
                    "due_date": None,
                    "amount": None,
                    "status": "",
                    "source": "",
                    "payment_type": "",
                }
            )

        return Response(
            NextDuePaymentSerializer(
                {
                    "payment_id": payment.id,
                    "company_id": payment.company_id,
                    "due_date": payment.due_date,
                    "amount": payment.amount,
                    "status": payment.status,
                    "source": payment.source,
                    "payment_type": payment.payment_type,
                }
            ).data
        )


class MetricsView(APIView):
    """Minimal operational metrics endpoint for local demos and probes."""

    authentication_classes = ()
    permission_classes = ()

    @extend_schema(
        responses={
            200: {
                "type": "object",
                "properties": {
                    "service": {"type": "string", "example": "finance-service"},
                    "status": {"type": "string", "example": "ok"},
                    "metrics": {"type": "object"},
                },
            }
        }
    )
    def get(self, request: Request) -> Response:
        return Response({"service": "finance-service", "status": "ok", "metrics": {}})
