import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def split_integration_settings(apps, schema_editor):
    IntegrationSettings = apps.get_model("diagnosis", "IntegrationSettings")
    AiModelSettings = apps.get_model("diagnosis", "AiModelSettings")
    PdpSkillSettings = apps.get_model("diagnosis", "PdpSkillSettings")
    source = IntegrationSettings.objects.filter(is_active=True).order_by("-updated_at").first()
    if source is None:
        AiModelSettings.objects.create(name="PDP Lab 默认 AI 模型")
        PdpSkillSettings.objects.create(name="PDP Lab 默认 PDP Skill")
        return
    AiModelSettings.objects.create(
        name="PDP Lab 默认 AI 模型",
        is_active=True,
        ai_adapter=source.ai_adapter,
        ai_model_name=source.ai_model_name,
        ai_base_url=source.ai_base_url,
        ai_timeout_seconds=source.ai_timeout_seconds,
        api_key_ciphertext=source.api_key_ciphertext,
        updated_by_id=source.updated_by_id,
    )
    PdpSkillSettings.objects.create(
        name="PDP Lab 默认 PDP Skill",
        is_active=True,
        skill_name=source.skill_name,
        skill_mode=source.skill_mode,
        skill_endpoint_url=source.skill_endpoint_url,
        skill_timeout_seconds=source.skill_timeout_seconds,
        skill_token_ciphertext=source.skill_token_ciphertext,
        updated_by_id=source.updated_by_id,
    )


class Migration(migrations.Migration):
    dependencies = [
        ("diagnosis", "0009_sync_latest_pdp_rules"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.CreateModel(
            name="AiModelSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(default="PDP Lab 默认 AI 模型", max_length=100, verbose_name="配置名称")),
                ("is_active", models.BooleanField(default=True, verbose_name="当前启用")),
                ("ai_adapter", models.CharField(choices=[("auto", "自动选择"), ("openai", "OpenAI"), ("mock", "Mock 验证")], default="auto", max_length=32, verbose_name="AI 适配器")),
                ("ai_model_name", models.CharField(default="gpt-5.4-mini", max_length=100, verbose_name="AI 模型")),
                ("ai_base_url", models.URLField(blank=True, help_text="留空使用 OpenAI 官方地址", verbose_name="API Base URL")),
                ("ai_timeout_seconds", models.PositiveIntegerField(default=180, verbose_name="API 超时（秒）")),
                ("api_key_ciphertext", models.TextField(blank=True, editable=False, verbose_name="加密 API Key")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
                ("updated_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name="最后修改人")),
            ],
            options={"verbose_name": "AI 模型 API 设置", "verbose_name_plural": "AI 模型 API 设置"},
        ),
        migrations.CreateModel(
            name="PdpSkillSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(default="PDP Lab 默认 PDP Skill", max_length=100, verbose_name="配置名称")),
                ("is_active", models.BooleanField(default=True, verbose_name="当前启用")),
                ("skill_name", models.CharField(default="pdp-detail-page-methodology", max_length=120, verbose_name="Skill 名称")),
                ("skill_mode", models.CharField(choices=[("built_in", "内置版本化规则"), ("remote_http", "远程 HTTP Skill")], default="built_in", max_length=32, verbose_name="Skill 接入方式")),
                ("skill_endpoint_url", models.URLField(blank=True, help_text="例如 http://127.0.0.1:8765/v1/skills/pdp-detail-page-methodology/rules", verbose_name="Skill 接入地址 / 端口")),
                ("skill_timeout_seconds", models.PositiveIntegerField(default=30, verbose_name="Skill 超时（秒）")),
                ("skill_token_ciphertext", models.TextField(blank=True, editable=False, verbose_name="Skill 加密 Token")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
                ("updated_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name="最后修改人")),
            ],
            options={"verbose_name": "PDP Skill 接入设置", "verbose_name_plural": "PDP Skill 接入设置"},
        ),
        migrations.RunPython(split_integration_settings, migrations.RunPython.noop),
        migrations.DeleteModel(name="IntegrationSettings"),
    ]
