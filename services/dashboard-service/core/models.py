"""Materialized dashboard read models maintained from integration events."""

from __future__ import annotations

import uuid

from django.db import models


class ProcessedEvent(models.Model):
    """Idempotency marker for consumed RabbitMQ envelopes."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_id = models.CharField(max_length=128, unique=True)
    event_type = models.CharField(max_length=128, db_index=True)
    occurred_at = models.DateTimeField(blank=True, null=True)
    processed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-processed_at",)


class CompanyProjection(models.Model):
    """Company attributes needed for dashboard analytics."""

    company_id = models.UUIDField(primary_key=True)
    name = models.CharField(max_length=255, blank=True)
    cae_code = models.CharField(max_length=64, blank=True, db_index=True)
    maturity_stage_name = models.CharField(max_length=128, blank=True, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    archived_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name", "company_id")


class EmployeeProjection(models.Model):
    """Employee membership projection keyed by upstream employee id."""

    employee_id = models.UUIDField(primary_key=True)
    company_id = models.UUIDField(db_index=True)
    employee_type = models.CharField(max_length=64, blank=True, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["company_id", "is_active"], name="dash_emp_company_active_idx")
        ]


class ContractProjection(models.Model):
    """Contract/space projection used for occupancy and recurring revenue."""

    contract_id = models.UUIDField(primary_key=True)
    company_id = models.UUIDField(db_index=True)
    space_id = models.UUIDField(blank=True, null=True, db_index=True)
    area_sqm = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    rate_per_sqm = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    monthly_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=24, default="active", db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(
                fields=["space_id", "is_active"],
                name="dash_contract_space_active_idx",
            )
        ]


class BookingProjection(models.Model):
    """Booking lifecycle projection used for pending and utilization counts."""

    booking_id = models.UUIDField(primary_key=True)
    company_id = models.UUIDField(blank=True, null=True, db_index=True)
    space_id = models.UUIDField(blank=True, null=True, db_index=True)
    status = models.CharField(max_length=24, db_index=True)
    quoted_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    start_time = models.DateTimeField(blank=True, null=True)
    end_time = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["status", "space_id"], name="dash_booking_status_space_idx")
        ]


class PaymentProjection(models.Model):
    """Paid payment projection emitted by finance-service."""

    payment_id = models.UUIDField(primary_key=True)
    company_id = models.UUIDField(blank=True, null=True, db_index=True)
    contract_id = models.UUIDField(blank=True, null=True)
    booking_id = models.UUIDField(blank=True, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid_at = models.DateTimeField(db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["company_id", "paid_at"], name="dash_payment_company_paid_idx")
        ]


class DashboardSnapshot(models.Model):
    """Cold-start snapshot payload from upstream REST endpoints."""

    source = models.CharField(max_length=64, unique=True)
    payload = models.JSONField(default=dict, blank=True)
    refreshed_at = models.DateTimeField(auto_now=True)
