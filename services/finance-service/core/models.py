"""Core finance models."""

from __future__ import annotations

import datetime as dt
import uuid

from django.db import models


class BillingContract(models.Model):
    """Persisted snapshot of activated contracts for monthly billing."""

    class Meta:
        ordering = ("company_id", "contract_id")
        indexes = [
            models.Index(fields=["company_id", "is_active"], name="bcontract_company_active_idx")
        ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract_id = models.UUIDField(unique=True)
    company_id = models.UUIDField(db_index=True)
    space_id = models.UUIDField()
    area_sqm = models.DecimalField(max_digits=10, decimal_places=2)
    rate_per_sqm = models.DecimalField(max_digits=12, decimal_places=2)
    monthly_fee = models.DecimalField(max_digits=12, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_covered(self, *, on_date: dt.date) -> bool:
        """Return whether the contract is active for the given date."""

        if not self.is_active:
            return False
        if self.start_date > on_date:
            return False
        return self.end_date is None or self.end_date >= on_date


class Payment(models.Model):
    """Payment line item for contract or booking-based invoices."""

    class Source(models.TextChoices):
        CONTRACT = "contract", "contract"
        BOOKING = "booking", "booking"

    class Status(models.TextChoices):
        PENDING = "pending", "pending"
        PAID = "paid", "paid"
        OVERDUE = "overdue", "overdue"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company_id = models.UUIDField(db_index=True)
    contract_id = models.UUIDField(blank=True, null=True)
    booking_id = models.UUIDField(blank=True, null=True)
    source = models.CharField(max_length=16, choices=Source.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=8, default="EUR")
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    due_date = models.DateField(blank=True, null=True, db_index=True)
    paid_at = models.DateTimeField(blank=True, null=True)
    period_start = models.DateField(blank=True, null=True)
    period_end = models.DateField(blank=True, null=True)
    reference_id = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["company_id", "status"], name="pay_company_status_idx"),
            models.Index(fields=["contract_id", "period_start"], name="pay_contract_period_idx"),
            models.Index(fields=["booking_id", "source"], name="pay_booking_source_idx"),
        ]

    def can_mark_paid(self) -> bool:
        return self.status != self.Status.PAID

    def mark_paid(self, paid_at: dt.datetime | None = None) -> bool:
        """Mark payment paid when needed; returns whether state changed."""

        if not self.can_mark_paid():
            return False

        self.status = self.Status.PAID
        self.paid_at = paid_at or dt.datetime.now(tz=dt.UTC)
        self.save(update_fields=("status", "paid_at", "updated_at"))
        return True


class ProcessedEvent(models.Model):
    """Idempotency store for consumed integration events."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_id = models.CharField(max_length=128, unique=True)
    event_type = models.CharField(max_length=128)
    processed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-processed_at",)
        indexes = [models.Index(fields=["event_type"], name="core_processed_event_type_idx")]
