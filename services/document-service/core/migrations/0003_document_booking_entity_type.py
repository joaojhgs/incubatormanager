# Generated manually for W5 booking document support.

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0002_document_soft_delete_is_active"),
    ]

    operations = [
        migrations.AlterField(
            model_name="document",
            name="entity_type",
            field=models.CharField(
                choices=[
                    ("Company", "Company"),
                    ("Contract", "Contract"),
                    ("Booking", "Booking"),
                ],
                db_index=True,
                max_length=16,
            ),
        ),
    ]
