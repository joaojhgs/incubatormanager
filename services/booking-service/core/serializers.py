"""Serializers for booking service payloads."""

from __future__ import annotations

from rest_framework import serializers

from core.models import Booking


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = [
            "id",
            "company_id",
            "space_id",
            "created_by_user_id",
            "created_by_role",
            "is_public",
            "start_time",
            "end_time",
            "quoted_price",
            "equipment_ids",
            "status",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_by_user_id",
            "created_by_role",
            "is_public",
            "status",
            "created_at",
            "updated_at",
        ]


class BookingCreateSerializer(serializers.ModelSerializer):
    company_id = serializers.UUIDField(required=False)

    class Meta:
        model = Booking
        fields = [
            "company_id",
            "space_id",
            "start_time",
            "end_time",
            "quoted_price",
            "equipment_ids",
            "notes",
        ]

    def validate(self, attrs):
        if attrs["start_time"] >= attrs["end_time"]:
            raise serializers.ValidationError("start_time must be before end_time")
        return attrs


class PublicBookingSerializer(BookingCreateSerializer):
    company_id = serializers.UUIDField()


class BookingCommandSerializer(serializers.Serializer):
    booking_id = serializers.UUIDField()
