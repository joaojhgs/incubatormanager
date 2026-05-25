"""Serializers for finance API payloads."""

from __future__ import annotations

from rest_framework import serializers

from core.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    company_id = serializers.UUIDField()
    contract_id = serializers.UUIDField(required=False, allow_null=True)
    booking_id = serializers.UUIDField(required=False, allow_null=True)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    due_date = serializers.DateField(required=False, allow_null=True)
    paid_at = serializers.DateTimeField(required=False, allow_null=True)
    period_start = serializers.DateField(required=False, allow_null=True)
    period_end = serializers.DateField(required=False, allow_null=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "company_id",
            "contract_id",
            "booking_id",
            "source",
            "payment_type",
            "amount",
            "currency",
            "status",
            "due_date",
            "paid_at",
            "period_start",
            "period_end",
            "reference_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "company_id",
            "contract_id",
            "booking_id",
            "source",
            "payment_type",
            "amount",
            "currency",
            "created_at",
            "updated_at",
            "reference_id",
            "period_start",
            "period_end",
        ]


class PaymentPatchSerializer(serializers.Serializer):
    """Writable fields for partial payment updates."""

    status = serializers.ChoiceField(choices=Payment.Status.choices)
    paid_at = serializers.DateTimeField(required=False, allow_null=True)
    reference_id = serializers.CharField(required=False, allow_blank=True, max_length=255)

    def validate(self, attrs: dict[str, object]) -> dict[str, object]:
        status = attrs["status"]
        if status == Payment.Status.PAID:
            return attrs

        # Allow payment-specific fields only when marking paid.
        paid_at = attrs.get("paid_at")
        if paid_at is not None:
            raise serializers.ValidationError({"paid_at": "can only be set when status is paid"})
        if attrs.get("reference_id"):
            raise serializers.ValidationError(
                {"reference_id": "can only be set when status is paid"}
            )
        return attrs


class DashboardSerializer(serializers.Serializer):
    total_payments = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    paid = serializers.IntegerField()
    paid_amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    pending = serializers.IntegerField()
    pending_amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    overdue = serializers.IntegerField()
    overdue_amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    status_breakdown = serializers.ListField(child=serializers.DictField(), required=False)
    source_breakdown = serializers.ListField(child=serializers.DictField(), required=False)
    payment_type_breakdown = serializers.ListField(child=serializers.DictField(), required=False)
    by_sector = serializers.ListField(child=serializers.DictField(), required=False)


class ReportSerializer(serializers.Serializer):
    company_id = serializers.UUIDField(required=False, allow_null=True)
    total = serializers.IntegerField()
    paid = serializers.IntegerField()
    pending = serializers.IntegerField()
    overdue = serializers.IntegerField()
    collected_amount = serializers.DecimalField(max_digits=14, decimal_places=2)

    def to_representation(self, instance: object) -> dict[str, object]:
        if isinstance(instance, dict):
            return dict(super().to_representation(instance))
        return super().to_representation(instance)


class BillingGenerateSerializer(serializers.Serializer):
    as_of = serializers.DateField(required=False)


class BillingGenerateResultSerializer(serializers.Serializer):
    created = serializers.IntegerField()
    existing_skipped = serializers.IntegerField()
    inactive_skipped = serializers.IntegerField()
    period_start = serializers.DateField()
    period_end = serializers.DateField()


class NextDuePaymentSerializer(serializers.Serializer):
    payment_id = serializers.UUIDField(allow_null=True)
    company_id = serializers.UUIDField(allow_null=True)
    due_date = serializers.DateField(allow_null=True)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True)
    status = serializers.CharField(allow_blank=True)
    source = serializers.CharField(allow_blank=True)
    payment_type = serializers.CharField(allow_blank=True)


class FinanceReportQuerySerializer(serializers.Serializer):
    type = serializers.ChoiceField(
        choices=[
            "revenue_by_company",
            "revenue_by_maturity",
            "payment_status_summary",
            "cash_flow_trend",
        ],
        required=False,
        default="revenue_by_company",
    )
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    group_by = serializers.ChoiceField(choices=["day", "month"], required=False, default="month")
