# Migration for MaturityStage model

import uuid
from decimal import Decimal

from django.db import migrations, models

STAGE_ROWS = [
    (
        uuid.UUID("11111111-1111-4111-8111-111111111111"),
        "Incubated",
        Decimal("100.00"),
        "Early-stage companies in the incubation program.",
        1,
    ),
    (
        uuid.UUID("22222222-2222-4222-8222-222222222222"),
        "Startup",
        Decimal("250.00"),
        "Startup companies with an established product or service.",
        2,
    ),
    (
        uuid.UUID("33333333-3333-4333-8333-333333333333"),
        "Intermediate",
        Decimal("500.00"),
        "Companies at an intermediate growth stage.",
        3,
    ),
    (
        uuid.UUID("44444444-4444-4444-8444-444444444444"),
        "Consolidated",
        Decimal("900.00"),
        "Established, consolidated companies.",
        4,
    ),
]


def seed_maturity_stages(apps, schema_editor) -> None:
    maturity_stage_model = apps.get_model("core", "MaturityStage")
    for stage_id, name, rate_per_sqm, description, display_order in STAGE_ROWS:
        maturity_stage_model.objects.update_or_create(
            name=name,
            defaults={
                "id": stage_id,
                "rate_per_sqm": rate_per_sqm,
                "description": description,
                "display_order": display_order,
            },
        )


def unseed_maturity_stages(apps, schema_editor) -> None:
    maturity_stage_model = apps.get_model("core", "MaturityStage")
    stage_ids = [stage_id for stage_id, *_ in STAGE_ROWS]
    maturity_stage_model.objects.filter(id__in=stage_ids).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0001_cae_model_seed"),
    ]

    operations = [
        migrations.CreateModel(
            name="MaturityStage",
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
                (
                    "name",
                    models.CharField(
                        choices=[
                            ("Incubated", "Incubated"),
                            ("Startup", "Startup"),
                            ("Intermediate", "Intermediate"),
                            ("Consolidated", "Consolidated"),
                        ],
                        max_length=32,
                        unique=True,
                    ),
                ),
                ("rate_per_sqm", models.DecimalField(decimal_places=2, max_digits=10)),
                ("description", models.CharField(blank=True, default="", max_length=255)),
                ("display_order", models.IntegerField(default=0)),
            ],
            options={
                "ordering": ("display_order",),
                "indexes": [
                    models.Index(fields=["display_order"], name="core_maturi_display_order_idx")
                ],
            },
        ),
        migrations.RunPython(seed_maturity_stages, unseed_maturity_stages),
    ]
