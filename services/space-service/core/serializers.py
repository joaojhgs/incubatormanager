"""Serializers for space API payloads."""

from __future__ import annotations

from rest_framework import serializers

from core.models import Space, SpaceContract, SpaceType


class SpaceTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpaceType
        fields = [
            "id",
            "name",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class SpaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Space
        fields = [
            "id",
            "name",
            "space_type",
            "capacity",
            "status",
            "company_id",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class SpaceContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpaceContract
        fields = [
            "id",
            "contract_id",
            "company_id",
            "space",
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
        read_only_fields = ["id", "created_at", "updated_at"]


class BookingEventSerializer(serializers.Serializer):
    booking_id = serializers.UUIDField()
    company_id = serializers.UUIDField(required=False, allow_null=True)
    space_id = serializers.UUIDField()
    start_time = serializers.DateTimeField(required=False, allow_null=True)
    end_time = serializers.DateTimeField(required=False, allow_null=True)
    quoted_price = serializers.CharField(required=False, allow_null=True)
    equipment_ids = serializers.ListField(
        child=serializers.UUIDField(), required=False, default=list
    )


class ContractEventSerializer(serializers.Serializer):
    contract_id = serializers.UUIDField()
    company_id = serializers.UUIDField()
    space_id = serializers.UUIDField()
    area_sqm = serializers.DecimalField(max_digits=10, decimal_places=2)
    rate_per_sqm = serializers.DecimalField(max_digits=10, decimal_places=2)
    monthly_fee = serializers.DecimalField(max_digits=12, decimal_places=2)
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    reason = serializers.CharField(required=False, allow_blank=True)


class SpaceOccupancySerializer(serializers.Serializer):
    space_id = serializers.UUIDField()
    space_name = serializers.CharField()
    capacity = serializers.IntegerField()
    occupied = serializers.IntegerField()
    occupancy_percent = serializers.DecimalField(max_digits=5, decimal_places=2)
    status = serializers.CharField()
