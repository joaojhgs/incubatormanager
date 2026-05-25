"""Core models for inventory service."""

from __future__ import annotations

import uuid

from django.db import models


class EquipmentType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)
        indexes = [models.Index(fields=["is_active"], name="inventory_type_active_idx")]

    def __str__(self) -> str:
        return self.name


class Equipment(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = "Available", "Available"
        IN_USE = "In use", "In use"
        MAINTENANCE = "Maintenance", "Maintenance"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    equipment_type = models.ForeignKey(
        EquipmentType,
        on_delete=models.PROTECT,
        related_name="equipment",
    )
    serial_number = models.CharField(max_length=128, blank=True, default="")
    status = models.CharField(
        max_length=24,
        choices=Status.choices,
        default=Status.AVAILABLE,
        db_index=True,
    )
    notes = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)
        indexes = [
            models.Index(fields=["equipment_type", "status"], name="inv_eq_type_status"),
            models.Index(fields=["is_active", "status"], name="inv_eq_active_status"),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.status})"


class EquipmentAssignment(models.Model):
    class Status(models.TextChoices):
        ASSIGNED = "Assigned", "Assigned"
        RELEASED = "Released", "Released"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    equipment = models.ForeignKey(
        Equipment,
        on_delete=models.CASCADE,
        related_name="assignments",
    )
    booking_id = models.UUIDField(db_index=True)
    company_id = models.UUIDField(db_index=True)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.ASSIGNED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["equipment", "booking_id"],
                name="booking_equipment_unique",
            )
        ]
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["equipment", "status"], name="inv_assign_eq_status"),
            models.Index(fields=["booking_id", "status"], name="inv_assign_booking"),
        ]

    def __str__(self) -> str:
        return f"{self.equipment_id}:{self.booking_id}:{self.status}"


class ProcessedEvent(models.Model):
    event_id = models.UUIDField(primary_key=True)
    event_type = models.CharField(max_length=100)
    processed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-processed_at",)
