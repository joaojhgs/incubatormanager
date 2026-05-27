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
            "requester_name",
            "requester_email",
            "requester_phone",
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
    company_id = serializers.UUIDField(required=False, allow_null=True)

    class Meta:
        model = Booking
        fields = [
            "company_id",
            "space_id",
            "requester_name",
            "requester_email",
            "requester_phone",
            "start_time",
            "end_time",
            "quoted_price",
            "equipment_ids",
            "notes",
        ]

    def validate(self, attrs):
        if attrs["start_time"] >= attrs["end_time"]:
            raise serializers.ValidationError("start_time must be before end_time")
        overlaps = Booking.objects.filter(
            space_id=attrs["space_id"],
            status__in=[Booking.Status.PENDING, Booking.Status.APPROVED],
            start_time__lt=attrs["end_time"],
            end_time__gt=attrs["start_time"],
        )
        if overlaps.exists():
            raise serializers.ValidationError(
                "The selected space is already reserved for that time period"
            )
        return attrs


class PublicBookingSerializer(BookingCreateSerializer):
    company_id = serializers.UUIDField(required=False, allow_null=True)
    requester_name = serializers.CharField(required=True, allow_blank=False)
    requester_email = serializers.EmailField(required=True, allow_blank=False)
    requester_phone = serializers.CharField(required=True, allow_blank=False)


class BookingCommandSerializer(serializers.Serializer):
    booking_id = serializers.UUIDField()


class BookingApproveSerializer(serializers.Serializer):
    company_id = serializers.UUIDField(required=False, allow_null=True)
    quoted_price = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True
    )
    equipment_ids = serializers.ListField(
        child=serializers.UUIDField(), required=False, allow_empty=True
    )
