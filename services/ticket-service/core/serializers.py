"""Serializers for ticket API request/response payloads."""

from __future__ import annotations

from core.models import Ticket, TicketMessage
from rest_framework import serializers


class TicketMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketMessage
        fields = [
            "id",
            "author_user_id",
            "author_role",
            "content",
            "created_at",
        ]
        read_only_fields = ["id", "author_user_id", "author_role", "created_at"]


class TicketSerializer(serializers.ModelSerializer):
    messages = TicketMessageSerializer(many=True, read_only=True)

    class Meta:
        model = Ticket
        fields = [
            "id",
            "company_id",
            "subject",
            "description",
            "status",
            "created_by_user_id",
            "created_by_role",
            "created_at",
            "updated_at",
            "messages",
        ]
        read_only_fields = ["id", "created_by_user_id", "created_by_role", "created_at", "updated_at", "messages"]


class TicketCreateSerializer(serializers.ModelSerializer):
    """Client-scoped create payload with optional explicit ``company_id`` for staff."""

    company_id = serializers.UUIDField(required=False)

    class Meta:
        model = Ticket
        fields = ["company_id", "subject", "description"]

    def validate(self, attrs: dict[str, object]) -> dict[str, object]:
        return attrs


class TicketMessageCreateSerializer(serializers.Serializer):
    content = serializers.CharField()
