"""Serializers for inventory service payloads."""

from __future__ import annotations

from rest_framework import serializers

from core.models import Equipment, EquipmentType


class EquipmentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentType
        fields = ["id", "name", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class EquipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipment
        fields = [
            "id",
            "name",
            "equipment_type",
            "serial_number",
            "assigned_space_id",
            "rental_cost",
            "status",
            "notes",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class EquipmentAssignSerializer(serializers.Serializer):
    booking_id = serializers.UUIDField(required=False)
    company_id = serializers.UUIDField(required=False)
    assigned_space_id = serializers.UUIDField(required=False, allow_null=True)

    def validate(self, attrs):
        has_booking_assignment = "booking_id" in attrs and "company_id" in attrs
        has_space_assignment = "assigned_space_id" in attrs
        if not has_booking_assignment and not has_space_assignment:
            raise serializers.ValidationError(
                "Provide assigned_space_id or both booking_id and company_id"
            )
        if ("booking_id" in attrs) != ("company_id" in attrs):
            raise serializers.ValidationError("booking_id and company_id must be provided together")
        return attrs


class EquipmentReleaseSerializer(serializers.Serializer):
    booking_id = serializers.UUIDField()
