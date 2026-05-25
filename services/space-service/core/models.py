"""Core data models for space-service."""

from __future__ import annotations

import uuid

from django.db import models


class SpaceType(models.Model):
    """Reusable space classification (for example, Coworking or Office)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class Space(models.Model):
    """Physical space metadata used by booking and occupancy handlers."""

    class Status(models.TextChoices):
        AVAILABLE = "available", "Available"
        BLOCKED = "blocked", "Blocked"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    space_type = models.ForeignKey(
        SpaceType,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="spaces",
    )
    name = models.CharField(max_length=255)
    capacity = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=24,
        choices=Status.choices,
        default=Status.AVAILABLE,
        db_index=True,
    )
    is_active = models.BooleanField(default=True, db_index=True)
    company_id = models.UUIDField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    active = ActiveManager()

    class Meta:
        ordering = ("name",)
        indexes = [
            models.Index(fields=["is_active"], name="space_type_active"),
        ]

    def __str__(self) -> str:
        return self.name


class Space(models.Model):
    """Physical office space metadata."""

    class Status(models.TextChoices):
        AVAILABLE = "Available", "Available"
        MAINTENANCE = "Maintenance", "Maintenance"
        BLOCKED = "Blocked", "Blocked"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    space_type = models.ForeignKey(
        SpaceType,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="spaces",
    )
    capacity = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=24,
        choices=Status.choices,
        default=Status.AVAILABLE,
        db_index=True,
    )
    company_id = models.UUIDField(null=True, blank=True, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)
        indexes = [
            models.Index(fields=["is_active"], name="space_is_active_idx"),
            models.Index(fields=["company_id", "is_active"], name="space_company_active"),
            models.Index(fields=["status"], name="space_status_idx"),
        ]

    def __str__(self) -> str:
        return self.name


class SpaceContract(models.Model):
    """Projection of contract lifecycle state per space."""

    class Status(models.TextChoices):
        ACTIVE = "Active", "Active"
        EXPIRED = "Expired", "Expired"
        TERMINATED = "Terminated", "Terminated"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract_id = models.UUIDField(unique=True, db_index=True)
    company_id = models.UUIDField(db_index=True)
    space = models.ForeignKey(Space, on_delete=models.CASCADE, related_name="contracts")
    status = models.CharField(max_length=24, choices=Status.choices)
    area_sqm = models.DecimalField(max_digits=10, decimal_places=2)
    rate_per_sqm = models.DecimalField(max_digits=10, decimal_places=2)
    monthly_fee = models.DecimalField(max_digits=12, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()
    termination_reason = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-updated_at",)
        indexes = [
            models.Index(fields=["company_id", "status"], name="space_contract_c_status"),
            models.Index(fields=["space", "status"], name="space_contract_s_status"),
        ]


class SpaceBookingRecord(models.Model):
    """Booking projection for occupancy and calendar state."""

    class Status(models.TextChoices):
        APPROVED = "Approved", "Approved"
        REJECTED = "Rejected", "Rejected"
        CANCELLED = "Cancelled", "Cancelled"
        COMPLETED = "Completed", "Completed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking_id = models.UUIDField(db_index=True, unique=True)
    space = models.ForeignKey(Space, on_delete=models.CASCADE, related_name="bookings")
    company_id = models.UUIDField(db_index=True)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.APPROVED, db_index=True)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    quoted_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    equipment_ids = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-start_time", "-created_at")
        indexes = [
            models.Index(fields=["space", "status"], name="space_book_space_status"),
            models.Index(fields=["company_id", "status"], name="space_book_company_status"),
        ]


class ProcessedEvent(models.Model):
    event_id = models.UUIDField(primary_key=True)
    event_type = models.CharField(max_length=100)
    processed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-processed_at",)
