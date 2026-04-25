"""Document metadata (polymorphic company or contract attachment)."""

from __future__ import annotations

import uuid

from django.db import models


class Document(models.Model):
    """File metadata; ``entity_*`` reference owning aggregate in another service."""

    class EntityType(models.TextChoices):
        COMPANY = "Company", "Company"
        CONTRACT = "Contract", "Contract"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entity_type = models.CharField(max_length=16, choices=EntityType.choices, db_index=True)
    entity_id = models.UUIDField(db_index=True)
    file_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=1024)
    file_size = models.PositiveIntegerField(help_text="Size in bytes.")
    mime_type = models.CharField(max_length=128, blank=True)
    description = models.CharField(max_length=500, blank=True)
    uploaded_by = models.UUIDField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-uploaded_at",)
        indexes = [
            models.Index(fields=["entity_type", "entity_id"]),
        ]

    def __str__(self) -> str:
        return f"{self.file_name} ({self.entity_type})"
