"""Serializers for document API responses."""

from __future__ import annotations

from rest_framework import serializers

from core.models import Document


class DocumentMetadataSerializer(serializers.ModelSerializer):
    """Metadata returned after upload or on detail-style reads."""

    download_url = serializers.SerializerMethodField()

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
            "download_url",
        )

    def get_download_url(self, obj: Document) -> str:
        request = self.context.get("request")
        path = f"/api/documents/{obj.id}/download/"
        if request is None:
            return path
        return request.build_absolute_uri(path)


class DocumentPresignedUrlSerializer(DocumentMetadataSerializer):
    """Metadata plus a direct object-storage URL for download handoff."""

    presigned_url = serializers.SerializerMethodField()

    class Meta(DocumentMetadataSerializer.Meta):
        fields = (*DocumentMetadataSerializer.Meta.fields, "presigned_url")

    def get_presigned_url(self, obj: Document) -> str:
        return str(self.context.get("presigned_url", ""))
