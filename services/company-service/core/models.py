"""Core data models for company-service."""

from __future__ import annotations

import uuid

from django.db import models


class ActiveManager(models.Manager):
    def get_queryset(self) -> models.QuerySet:
        return super().get_queryset().filter(is_active=True)


class CAE(models.Model):
    """Portuguese economic activity classification code."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=16, unique=True, db_index=True)
    description = models.CharField(max_length=255)

    class Meta:
        ordering = ("code",)

    def __str__(self) -> str:
        return f"{self.code} - {self.description}"


class MaturityStage(models.Model):
    """Company maturity stage with a configured per-sqm billing rate."""

    class Name(models.TextChoices):
        INCUBATED = "Incubated", "Incubated"
        STARTUP = "Startup", "Startup"
        INTERMEDIATE = "Intermediate", "Intermediate"
        CONSOLIDATED = "Consolidated", "Consolidated"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=32, choices=Name.choices, unique=True)
    rate_per_sqm = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255, blank=True, default="")
    display_order = models.IntegerField(default=0)

    class Meta:
        ordering = ("display_order",)
        indexes = [models.Index(fields=["display_order"], name="core_maturi_display_order_idx")]

    def __str__(self) -> str:
        return self.name


class Company(models.Model):
    """Incubated company entity."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    tax_id = models.CharField(max_length=20, unique=True, db_index=True)
    address = models.CharField(max_length=255, blank=True, default="")
    phone = models.CharField(max_length=32, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    legal_representative = models.CharField(max_length=255)
    cae = models.ForeignKey(CAE, on_delete=models.PROTECT, related_name="companies")
    maturity_stage = models.ForeignKey(
        MaturityStage, on_delete=models.PROTECT, related_name="companies"
    )
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    active = ActiveManager()

    class Meta:
        ordering = ("name",)
        indexes = [
            models.Index(fields=["is_active"], name="core_company_is_active_idx"),
            models.Index(fields=["cae_id"], name="core_company_cae_id_idx"),
            models.Index(fields=["maturity_stage_id"], name="core_company_mstage_idx"),
        ]

    def __str__(self) -> str:
        return self.name


class Employee(models.Model):
    """Employee record for an incubated company (class-er §1.5)."""

    class Type(models.TextChoices):
        REGULAR = "Regular", "Regular"
        INTERN = "Intern", "Intern"
        PHD = "PhD", "PhD"
        DESIGNER = "Designer", "Designer"
        JUNIOR = "Junior", "Junior"
        SENIOR = "Senior", "Senior"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="employees")
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=32, choices=Type.choices)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    active = ActiveManager()

    class Meta:
        ordering = ("company", "name")
        indexes = [
            models.Index(fields=["company_id"], name="core_employee_company_id_idx"),
            models.Index(fields=["is_active"], name="core_employee_is_active_idx"),
            models.Index(fields=["type"], name="core_employee_type_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.company.name})"
