"""Serializers for company-service core resources."""

from __future__ import annotations

from rest_framework import serializers

from core.models import CAE, MaturityStage
from core.services import create_maturity_stage, update_maturity_stage


class CAESerializer(serializers.ModelSerializer):
    class Meta:
        model = CAE
        fields = ["id", "code", "description"]
        read_only_fields = ["id"]


class MaturityStageSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaturityStage
        fields = ["id", "name", "rate_per_sqm", "description", "display_order"]
        read_only_fields = ["id"]

    def create(self, validated_data: dict) -> MaturityStage:
        return create_maturity_stage(**validated_data)

    def update(self, instance: MaturityStage, validated_data: dict) -> MaturityStage:
        return update_maturity_stage(instance, **validated_data)
