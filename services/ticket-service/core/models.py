"""Core data models for ticket-service."""

from __future__ import annotations

import uuid

from django.db import models


class Ticket(models.Model):
    """Support ticket raised by a client company."""

    class Status(models.TextChoices):
        OPEN = "Open", "Open"
        IN_PROGRESS = "In progress", "In progress"
        WAITING_RESPONSE = "Waiting response", "Waiting response"
        RESOLVED = "Resolved", "Resolved"
        CLOSED = "Closed", "Closed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company_id = models.UUIDField(db_index=True)
    subject = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.OPEN,
        db_index=True,
    )
    assigned_to = models.UUIDField(null=True, blank=True, db_index=True)
    created_by_user_id = models.UUIDField()
    created_by_role = models.CharField(max_length=24)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-updated_at", "-created_at", "subject")
        indexes = [
            models.Index(fields=["company_id", "status"], name="core_ticket_company_status_idx"),
            models.Index(fields=["assigned_to", "status"], name="ticket_assignee_status_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.subject} ({self.status})"


class TicketMessage(models.Model):
    """Message belonging to a ticket thread."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    author_user_id = models.UUIDField()
    author_role = models.CharField(max_length=24)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at",)
        indexes = [
            models.Index(fields=["ticket_id", "created_at"], name="core_tmsg_ticket_created_idx"),
        ]

    def __str__(self) -> str:
        preview = self.content[:24].replace("\n", " ")
        return f"{self.ticket_id}::{preview}"
