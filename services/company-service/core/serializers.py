"""Serializers for company-service core resources."""

from __future__ import annotations

from rest_framework import serializers

from core.models import CAE


class CAESerializer(serializers.ModelSerializer):
    class Meta:
        model = CAE
        fields = ["id", "code", "description"]
        read_only_fields = ["id"]
