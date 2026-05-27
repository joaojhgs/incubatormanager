"""Serializers for inventory service payloads."""

from __future__ import annotations

from rest_framework import serializers

from core.models import Equipment, EquipmentAssignment, EquipmentType


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
            "rental_cost_unit",
            "status",
            "notes",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class EquipmentAssignmentSerializer(serializers.ModelSerializer):
    equipment_id = serializers.UUIDField(source="equipment.id", read_only=True)
    equipment_name = serializers.CharField(source="equipment.name", read_only=True)

    class Meta:
        model = EquipmentAssignment
        fields = [
            "id",
            "equipment_id",
            "equipment_name",
            "booking_id",
            "company_id",
            "assigned_space_id",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


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
