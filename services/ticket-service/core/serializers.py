"""Serializers for ticket resources."""

from __future__ import annotations

from rest_framework import serializers

from core.models import Ticket, TicketMessage


class TicketMessageSerializer(serializers.ModelSerializer):
    """Read/write representation for ticket conversation messages."""

    class Meta:
        model = TicketMessage
        fields = ["id", "sender_id", "sender_role", "body", "created_at"]
        read_only_fields = ["id", "sender_id", "sender_role", "created_at"]


class TicketMessageCreateSerializer(serializers.Serializer):
    """Payload accepted by /tickets/{id}/messages/."""

    body = serializers.CharField(min_length=1)


class TicketSerializer(serializers.ModelSerializer):
    """Ticket projection for list/detail endpoints."""

    messages = TicketMessageSerializer(many=True, read_only=True)

    class Meta:
        model = Ticket
        fields = [
            "id",
            "company_id",
            "created_by_id",
            "created_by_role",
            "subject",
            "description",
            "status",
            "created_at",
            "updated_at",
            "messages",
        ]
        read_only_fields = [
            "id",
            "created_by_id",
            "created_by_role",
            "created_at",
            "updated_at",
            "messages",
        ]


class TicketCreateSerializer(serializers.ModelSerializer):
    """Payload for creating tickets."""

    company_id = serializers.UUIDField(required=False)

    class Meta:
        model = Ticket
        fields = ["company_id", "subject", "description"]

    def validate_company_id(self, value: object) -> object:
        if value in {"", None}:
            raise serializers.ValidationError("company_id is required.")
        return value

    def create(self, validated_data: dict) -> Ticket:
        return super().create(validated_data)
