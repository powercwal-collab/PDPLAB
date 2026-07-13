import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("diagnosis", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="PdpSource",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("file", models.FileField(upload_to="pdp_sources/%Y/%m/", verbose_name="PDP 文件")),
                ("original_name", models.CharField(max_length=255, verbose_name="原始文件名")),
                ("status", models.CharField(default="uploaded", max_length=32, verbose_name="处理状态")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="上传时间")),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sources", to="diagnosis.project")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="NotificationPreference",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("task_updates", models.BooleanField(default=True)),
                ("product_updates", models.BooleanField(default=True)),
                ("weekly_report", models.BooleanField(default=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="notification_preference", to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
