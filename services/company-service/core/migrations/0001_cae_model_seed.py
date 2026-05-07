"""Create CAE model and seed baseline sector codes."""

from __future__ import annotations

import uuid

from django.db import migrations, models

CAE_SEED: tuple[tuple[str, str], ...] = (
    ("0111", "Growing of cereals (except rice), leguminous crops and oil seeds"),
    ("1011", "Processing and preserving of meat"),
    ("1413", "Manufacture of other outerwear"),
    ("1812", "Other printing"),
    ("2042", "Manufacture of perfumes and toilet preparations"),
    ("2611", "Manufacture of electronic components"),
    ("6201", "Computer programming activities"),
    ("7022", "Business and other management consultancy activities"),
    (
        "7219",
        "Other research and experimental development on natural sciences and engineering",
    ),
    ("8559", "Other education n.e.c."),
)


def seed_cae_codes(apps, schema_editor) -> None:  # type: ignore[no-untyped-def]
    CAE = apps.get_model("core", "CAE")
    db_alias = schema_editor.connection.alias
    for code, description in CAE_SEED:
        CAE.objects.using(db_alias).get_or_create(
            code=code,
            defaults={"id": uuid.uuid4(), "description": description},
        )


def unseed_cae_codes(apps, schema_editor) -> None:  # type: ignore[no-untyped-def]
    CAE = apps.get_model("core", "CAE")
    db_alias = schema_editor.connection.alias
    CAE.objects.using(db_alias).filter(code__in=[code for code, _ in CAE_SEED]).delete()


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="CAE",
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
                ("code", models.CharField(db_index=True, max_length=16, unique=True)),
                ("description", models.CharField(max_length=255)),
            ],
            options={"ordering": ("code",)},
        ),
        migrations.RunPython(seed_cae_codes, unseed_cae_codes),
    ]
