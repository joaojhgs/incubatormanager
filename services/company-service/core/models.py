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
