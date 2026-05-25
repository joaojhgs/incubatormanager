"""Serializers for contract resources."""

from __future__ import annotations

from rest_framework import serializers

from core.models import Contract


class ContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contract
        fields = [
            "id",
            "company_id",
            "space_id",
            "status",
            "area_sqm",
            "rate_per_sqm",
            "monthly_fee",
            "start_date",
            "end_date",
            "termination_reason",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ("id", "monthly_fee", "termination_reason", "created_at", "updated_at")

    def validate(self, attrs: dict) -> dict:
        area_sqm = attrs.get("area_sqm")
        if area_sqm is None:
            return attrs
        rate = attrs.get("rate_per_sqm")
        if rate is not None:
            if area_sqm <= 0:
                raise serializers.ValidationError({"area_sqm": "Must be greater than 0."})
            if rate <= 0:
                raise serializers.ValidationError({"rate_per_sqm": "Must be greater than 0."})
        return attrs

    def create(self, validated_data: dict) -> Contract:
        area = validated_data["area_sqm"]
        rate = validated_data["rate_per_sqm"]
        validated_data["monthly_fee"] = area * rate
        return Contract.objects.create(**validated_data)

    def update(self, instance: Contract, validated_data: dict) -> Contract:
        if any(key in validated_data for key in ("area_sqm", "rate_per_sqm", "monthly_fee")):
            raise serializers.ValidationError(
                "Monthly fee fields are immutable once the contract is created."
            )
        return super().update(instance, validated_data)
