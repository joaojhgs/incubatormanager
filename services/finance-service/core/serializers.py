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

    def validate(self, attrs: dict[str, object]) -> dict[str, object]:
        status = attrs["status"]
        if status == Payment.Status.PAID:
            return attrs

        # Allow explicit paid_at only when marking paid.
        paid_at = attrs.get("paid_at")
        if paid_at is not None:
            raise serializers.ValidationError({"paid_at": "can only be set when status is paid"})
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
