import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("diagnosis", "0002_pdpsource_notificationpreference"),
    ]

    operations = [
        migrations.CreateModel(
            name="DiagnosisVersion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("version", models.PositiveIntegerField(default=1, verbose_name="评分版本")),
                ("total_score", models.DecimalField(decimal_places=1, max_digits=5, verbose_name="总分")),
                ("overall_rating", models.DecimalField(decimal_places=1, max_digits=3, verbose_name="整体星级")),
                ("modules", models.JSONField(default=list, verbose_name="模块评分")),
                ("status", models.CharField(default="locked", max_length=32, verbose_name="状态")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="diagnosis_versions", to=settings.AUTH_USER_MODEL)),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="diagnoses", to="diagnosis.project")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddConstraint(
            model_name="diagnosisversion",
            constraint=models.UniqueConstraint(fields=("project", "version"), name="unique_project_diagnosis_version"),
        ),
    ]
