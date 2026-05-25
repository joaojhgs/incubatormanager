"""Core data models for the ticket service."""

from __future__ import annotations

import uuid

from django.db import models


class Ticket(models.Model):
    """Support ticket raised by a client or staff."""

    class Status(models.TextChoices):
        OPEN = "Open", "Open"
        AWAITING_RESPONSE = "AwaitingResponse", "Awaiting response"
        IN_PROGRESS = "InProgress", "In progress"
        CLOSED = "Closed", "Closed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company_id = models.UUIDField(db_index=True)
    created_by_id = models.UUIDField()
    created_by_role = models.CharField(max_length=32)
    subject = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-updated_at",)
        indexes = [
            models.Index(fields=["company_id"], name="ticket_company_idx"),
            models.Index(fields=["status"], name="ticket_status_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.subject} ({self.company_id})"


class TicketMessage(models.Model):
    """Conversation message on a ticket."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    sender_id = models.UUIDField()
    sender_role = models.CharField(max_length=32)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at",)
        indexes = [models.Index(fields=["ticket_id"], name="ticketmessage_ticket_idx")]

    def __str__(self) -> str:
        return f"{self.ticket_id}:{self.sender_id}"
