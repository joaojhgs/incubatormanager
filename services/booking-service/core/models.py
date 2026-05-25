"""Core data models for booking service."""

from __future__ import annotations

import uuid
from decimal import Decimal

from django.db import models


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = "Pending", "Pending"
        APPROVED = "Approved", "Approved"
        REJECTED = "Rejected", "Rejected"
        CANCELLED = "Cancelled", "Cancelled"
        COMPLETED = "Completed", "Completed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company_id = models.UUIDField(db_index=True)
    space_id = models.UUIDField(db_index=True)
    created_by_user_id = models.UUIDField(null=True, blank=True)
    created_by_role = models.CharField(max_length=24, blank=True)
    is_public = models.BooleanField(default=False, db_index=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    quoted_price = models.DecimalField(max_digits=12, decimal_places=2)
    equipment_ids = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["company_id", "status"], name="booking_company_status_idx"),
            models.Index(fields=["space_id", "status"], name="booking_space_status_idx"),
            models.Index(fields=["is_public", "status"], name="booking_public_status_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.company_id}/{self.space_id} ({self.status})"


class ProcessedEvent(models.Model):
    event_id = models.UUIDField(primary_key=True)
    event_type = models.CharField(max_length=100)
    processed_at = models.DateTimeField(auto_now_add=True)
