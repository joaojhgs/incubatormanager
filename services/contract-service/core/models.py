"""Core domain models for the contract service."""

from __future__ import annotations

import uuid

from django.db import models
from django.utils import timezone


class Contract(models.Model):
    """Contract aggregate with lifecycle status and immutable pricing snapshot."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        TERMINATED = "terminated", "Terminated"
        EXPIRED = "expired", "Expired"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company_id = models.UUIDField(db_index=True)
    space_id = models.UUIDField(db_index=True)
    area_sqm = models.DecimalField(max_digits=10, decimal_places=2)
    rate_per_sqm = models.DecimalField(max_digits=10, decimal_places=2)
    monthly_fee = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )
    termination_reason = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["company_id", "status"], name="cont_company_status_idx"),
            models.Index(fields=["space_id", "status"], name="cont_space_status_idx"),
        ]

    def __str__(self) -> str:
        return f"Contract {self.id} for company {self.company_id}"

    def activate(self) -> None:
        self.status = self.Status.ACTIVE
        self.updated_at = timezone.now()
        self.save(update_fields=("status", "updated_at"))

    def terminate(self, reason: str) -> None:
        self.status = self.Status.TERMINATED
        self.termination_reason = reason
        self.updated_at = timezone.now()
        self.save(update_fields=("status", "termination_reason", "updated_at"))

    def expire(self) -> None:
        self.status = self.Status.EXPIRED
        self.updated_at = timezone.now()
        self.save(update_fields=("status", "updated_at"))
