"""Create stub Space model and seed three fixed rows for contract FK resolution."""

from __future__ import annotations

import uuid

from django.db import migrations, models

# Stable UUIDs for incubator seed data; contract-service stores these as UUID references only.
SPACE_STUB_SEED: tuple[tuple[uuid.UUID, str], ...] = (
    (uuid.UUID("22222222-2222-4222-8222-222222222201"), "Seed stub space 1"),
    (uuid.UUID("22222222-2222-4222-8222-222222222202"), "Seed stub space 2"),
    (uuid.UUID("22222222-2222-4222-8222-222222222203"), "Seed stub space 3"),
)


def seed_stub_spaces(apps, schema_editor) -> None:  # type: ignore[no-untyped-def]
    Space = apps.get_model("core", "Space")
    db_alias = schema_editor.connection.alias
    for space_id, name in SPACE_STUB_SEED:
        Space.objects.using(db_alias).get_or_create(
            id=space_id,
            defaults={"name": name, "is_active": True},
        )


def unseed_stub_spaces(apps, schema_editor) -> None:  # type: ignore[no-untyped-def]
    Space = apps.get_model("core", "Space")
    db_alias = schema_editor.connection.alias
    Space.objects.using(db_alias).filter(
        id__in=[row[0] for row in SPACE_STUB_SEED],
    ).delete()


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Space",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        primary_key=True,
                        default=uuid.uuid4,
                        editable=False,
                        serialize=False,
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("is_active", models.BooleanField(db_index=True, default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ("name",),
            },
        ),
        migrations.AddIndex(
            model_name="space",
            index=models.Index(fields=["is_active"], name="core_space_is_active_idx"),
        ),
        migrations.RunPython(seed_stub_spaces, unseed_stub_spaces),
    ]
