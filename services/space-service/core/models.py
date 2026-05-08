"""Core data models for space-service."""

from __future__ import annotations

import uuid

from django.db import models


class ActiveManager(models.Manager):
    def get_queryset(self) -> models.QuerySet:
        return super().get_queryset().filter(is_active=True)


class Space(models.Model):
    """Minimal stub space row; contracts reference ``id`` as a UUID only (separate service DB)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    active = ActiveManager()

    class Meta:
        ordering = ("name",)
        indexes = [
            models.Index(fields=["is_active"], name="core_space_is_active_idx"),
        ]

    def __str__(self) -> str:
        return self.name
