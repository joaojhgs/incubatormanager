"""Serializers for company-service core resources."""

from __future__ import annotations

from rest_framework import serializers

from core.models import CAE, Company, Employee, MaturityStage
from core.services import create_maturity_stage, update_maturity_stage


class CAESerializer(serializers.ModelSerializer):
    class Meta:
        model = CAE
        fields = ["id", "code", "description"]
        read_only_fields = ["id"]


class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ["id", "name", "type", "start_date", "end_date", "is_active"]
        read_only_fields = ["id", "name", "type", "start_date", "end_date", "is_active"]


class MaturityStageSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaturityStage
        fields = ["id", "name", "rate_per_sqm", "description", "display_order"]
        read_only_fields = ["id"]

    def create(self, validated_data: dict) -> MaturityStage:
        return create_maturity_stage(**validated_data)

    def update(self, instance: MaturityStage, validated_data: dict) -> MaturityStage:
        return update_maturity_stage(instance, **validated_data)


class CompanyListSerializer(serializers.ModelSerializer):
    """Company row for GET /companies; nested FKs via select_related (no employee list)."""

    cae = CAESerializer(read_only=True)
    maturity_stage = MaturityStageSerializer(read_only=True)

    class Meta:
        model = Company
        fields = [
            "id",
            "name",
            "tax_id",
            "address",
            "phone",
            "email",
            "legal_representative",
            "description",
            "is_active",
            "created_at",
            "updated_at",
            "cae",
            "maturity_stage",
        ]
        read_only_fields = fields


class CompanyDetailSerializer(CompanyListSerializer):
    """Full company projection with nested CAE, maturity stage, and active employees."""

    employees = EmployeeSerializer(many=True, read_only=True)

    class Meta(CompanyListSerializer.Meta):
        fields = [*CompanyListSerializer.Meta.fields, "employees"]
