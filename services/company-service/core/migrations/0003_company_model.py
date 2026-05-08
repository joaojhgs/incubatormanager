"""Create Company model."""

from __future__ import annotations

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0002_maturity_stage_model"),
    ]

    operations = [
        migrations.CreateModel(
            name="Company",
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
                ("name", models.CharField(max_length=255)),
                ("tax_id", models.CharField(db_index=True, max_length=20, unique=True)),
                ("address", models.CharField(blank=True, default="", max_length=255)),
                ("phone", models.CharField(blank=True, default="", max_length=32)),
                ("email", models.EmailField(blank=True, default="")),
                ("legal_representative", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True, default="")),
                ("is_active", models.BooleanField(db_index=True, default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "cae",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="companies",
                        to="core.cae",
                    ),
                ),
                (
                    "maturity_stage",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="companies",
                        to="core.maturitystage",
                    ),
                ),
            ],
            options={
                "ordering": ("name",),
            },
        ),
        migrations.AddIndex(
            model_name="company",
            index=models.Index(fields=["is_active"], name="core_company_is_active_idx"),
        ),
        migrations.AddIndex(
            model_name="company",
            index=models.Index(fields=["cae_id"], name="core_company_cae_id_idx"),
        ),
        migrations.AddIndex(
            model_name="company",
            index=models.Index(fields=["maturity_stage_id"], name="core_company_mstage_idx"),
        ),
    ]
