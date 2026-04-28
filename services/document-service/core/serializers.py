"""Serializers for document API responses."""

from __future__ import annotations

from rest_framework import serializers

from core.models import Document


class DocumentMetadataSerializer(serializers.ModelSerializer):
    """Metadata returned after upload or on detail-style reads."""

    class Meta:
        model = Document
        fields = (
            "id",
            "entity_type",
            "entity_id",
            "file_name",
            "file_size",
            "mime_type",
            "description",
            "uploaded_by",
            "uploaded_at",
        )
