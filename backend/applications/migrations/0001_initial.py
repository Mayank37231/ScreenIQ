# Generated for the ScreenIQ submission.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Application",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("job_description", models.TextField()),
                ("resume", models.TextField()),
                ("candidate_name", models.CharField(blank=True, max_length=255)),
                ("ai_score", models.DecimalField(decimal_places=1, max_digits=3)),
                ("ai_reasons", models.JSONField(default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "created_by",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
