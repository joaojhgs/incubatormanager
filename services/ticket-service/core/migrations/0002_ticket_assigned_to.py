# Generated manually for W5 ticket assignment filters.

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="ticket",
            name="assigned_to",
            field=models.UUIDField(blank=True, db_index=True, null=True),
        ),
        migrations.AddIndex(
            model_name="ticket",
            index=models.Index(
                fields=["assigned_to", "status"],
                name="ticket_assignee_status_idx",
            ),
        ),
    ]
