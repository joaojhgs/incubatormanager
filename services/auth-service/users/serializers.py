"""Serializers for the User model — self-profile read and update."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    """Read-only representation of the authenticated user's profile."""

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "role",
            "company_id",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Write serializer for PATCH /users/me/.

    Allows updating ``first_name``, ``last_name``, and ``password``.
    ``role``, ``company_id``, ``email``, and ``is_active`` are immutable
    through this endpoint.
    """

    old_password = serializers.CharField(
        write_only=True,
        required=False,
        help_text="Current password — required when setting a new password.",
    )
    new_password = serializers.CharField(
        write_only=True,
        required=False,
        help_text="New password. Must satisfy all Django password validators.",
    )

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "old_password",
            "new_password",
        ]

    def validate(self, attrs: dict) -> dict:
        old_password = attrs.get("old_password")
        new_password = attrs.get("new_password")

        if new_password and not old_password:
            raise serializers.ValidationError(
                {"old_password": "Current password is required when setting a new password."}
            )

        if old_password and not new_password:
            raise serializers.ValidationError(
                {"new_password": "New password is required when old password is provided."}
            )

        if new_password and old_password:
            user = self.instance
            if not user.check_password(old_password):
                raise serializers.ValidationError(
                    {"old_password": "Current password is incorrect."}
                )
            validate_password(new_password, user=user)

        return attrs

    def update(self, instance: User, validated_data: dict) -> User:
        validated_data.pop("old_password", None)
        new_password = validated_data.pop("new_password", None)

        # Update scalar fields
        instance = super().update(instance, validated_data)

        # Update password if provided
        if new_password:
            instance.set_password(new_password)
            instance.save(update_fields=["password", "updated_at"])

        return instance
