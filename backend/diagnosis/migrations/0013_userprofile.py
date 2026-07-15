from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("diagnosis", "0012_claim_legacy_projects"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("avatar", models.ImageField(blank=True, upload_to="user_avatars/%Y/%m/", verbose_name="用户头像")),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="pdp_profile", to="auth.user")),
            ],
        ),
    ]
