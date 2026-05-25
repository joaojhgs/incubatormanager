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
            "status",
            "notes",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class EquipmentAssignSerializer(serializers.Serializer):
    booking_id = serializers.UUIDField()
    company_id = serializers.UUIDField()


class EquipmentReleaseSerializer(serializers.Serializer):
    booking_id = serializers.UUIDField()
