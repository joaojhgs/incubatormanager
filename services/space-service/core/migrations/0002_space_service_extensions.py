"""Add space-space-type, contract, and booking-record tables."""

from __future__ import annotations

import uuid

from django.db import migrations, models
from django.db.models import deletion


def normalize_space_defaults(apps, schema_editor) -> None:
    Space = apps.get_model("core", "Space")
    db_alias = schema_editor.connection.alias
    Space.objects.using(db_alias).update(status="available", capacity=1)


class Migration(migrations.Migration):
    dependencies = [("core", "0001_space_model_and_seed")]

    operations = [
        migrations.CreateModel(
            name="SpaceType",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("name", models.CharField(max_length=120, unique=True)),
                ("description", models.TextField(blank=True)),
                ("is_active", models.BooleanField(db_index=True, default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ("name",)},
        ),
        migrations.CreateModel(
            name="SpaceBookingRecord",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("booking_id", models.UUIDField(unique=True)),
                ("company_id", models.UUIDField()),
                ("state", models.CharField(choices=[("approved", "Approved"), ("rejected", "Rejected"), ("cancelled", "Cancelled"), ("completed", "Completed")], max_length=16)),
                ("start_time", models.DateTimeField()),
                ("end_time", models.DateTimeField()),
                ("space", models.ForeignKey(on_delete=deletion.CASCADE, related_name="booking_records", to="core.space")),
            ],
            options={"ordering": ("-start_time",)},
        ),
        migrations.CreateModel(
            name="SpaceContract",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("contract_id", models.UUIDField(unique=True)),
                ("company_id", models.UUIDField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("active", "Active"),
                            ("terminated", "Terminated"),
                            ("expired", "Expired"),
                        ],
                        default="active",
                        max_length=16,
                    ),
                ),
                ("activated_at", models.DateTimeField(blank=True, null=True)),
                ("ended_at", models.DateTimeField(blank=True, null=True)),
                ("reason", models.CharField(blank=True, max_length=255)),
                ("space", models.ForeignKey(on_delete=deletion.CASCADE, related_name="contracts", to="core.space")),
            ],
            options={"ordering": ("-activated_at", "-ended_at")},
        ),
        migrations.AddField(
            model_name="space",
            name="capacity",
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddField(
            model_name="space",
            name="company_id",
            field=models.UUIDField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name="space",
            name="space_type",
            field=models.ForeignKey(blank=True, null=True, on_delete=deletion.SET_NULL, related_name="spaces", to="core.spacetype"),
        ),
        migrations.AddField(
            model_name="space",
            name="status",
            field=models.CharField(
                choices=[("available", "Available"), ("blocked", "Blocked")],
                default="available",
                max_length=24,
            ),
        ),
        migrations.AddIndex(
            model_name="space",
            index=models.Index(fields=["status", "is_active"], name="core_space_status_active_idx"),
        ),
        migrations.AddIndex(
            model_name="space",
            index=models.Index(fields=["space_type", "is_active"], name="core_space_type_active_idx"),
        ),
        migrations.AddIndex(
            model_name="spacebookingrecord",
            index=models.Index(fields=["space", "state"], name="core_space_booking_state_idx"),
        ),
        migrations.AddIndex(
            model_name="spacecontract",
            index=models.Index(fields=["contract_id"], name="core_space_contract_id_idx"),
        ),
        migrations.AddIndex(
            model_name="spacecontract",
            index=models.Index(fields=["space", "status"], name="core_space_contract_status_idx"),
        ),
        migrations.RunPython(normalize_space_defaults, migrations.RunPython.noop),
    ]
