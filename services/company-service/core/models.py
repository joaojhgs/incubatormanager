"""Core data models for company-service."""

from __future__ import annotations

import uuid

from django.db import models


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
