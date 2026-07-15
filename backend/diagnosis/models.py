import base64
import hashlib
from urllib.parse import urlparse

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


def _secret_cipher():
    digest = hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def _encrypt_secret(value):
    return _secret_cipher().encrypt(value.encode("utf-8")).decode("ascii") if value else ""


def _decrypt_secret(value):
    if not value:
        return ""
    try:
        return _secret_cipher().decrypt(value.encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError):
        raise RuntimeError("集成密钥无法解密，请在后台重新保存")


class Project(models.Model):
    owner = models.ForeignKey(
        "auth.User",
        related_name="pdp_projects",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    name = models.CharField("项目名称", max_length=160)
    brand = models.CharField("品牌", max_length=100, blank=True)
    category = models.CharField("品类", max_length=100, blank=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.name


class PdpSource(models.Model):
    project = models.ForeignKey(Project, related_name="sources", on_delete=models.CASCADE)
    file = models.FileField("PDP 文件", upload_to="pdp_sources/%Y/%m/")
    original_name = models.CharField("原始文件名", max_length=255)
    status = models.CharField("处理状态", max_length=32, default="uploaded")
    created_at = models.DateTimeField("上传时间", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class NotificationPreference(models.Model):
    user = models.OneToOneField("auth.User", related_name="notification_preference", on_delete=models.CASCADE)
    task_updates = models.BooleanField(default=True)
    product_updates = models.BooleanField(default=True)
    weekly_report = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)


class UserProfile(models.Model):
    user = models.OneToOneField("auth.User", related_name="pdp_profile", on_delete=models.CASCADE)
    avatar = models.ImageField("用户头像", upload_to="user_avatars/%Y/%m/", blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} · 个人资料"


class DiagnosisVersion(models.Model):
    project = models.ForeignKey(Project, related_name="diagnoses", on_delete=models.CASCADE)
    version = models.PositiveIntegerField("评分版本", default=1)
    total_score = models.DecimalField("总分", max_digits=5, decimal_places=1)
    overall_rating = models.DecimalField("整体星级", max_digits=3, decimal_places=1)
    modules = models.JSONField("模块评分", default=list)
    source = models.ForeignKey(
        PdpSource,
        related_name="diagnosis_versions",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    scoring_standard_version = models.CharField("评分标准版本", max_length=32, default="pdp-v1")
    confirmation_mode = models.CharField("确认方式", max_length=32, default="manual")
    status = models.CharField("状态", max_length=32, default="locked")
    created_by = models.ForeignKey(
        "auth.User",
        related_name="diagnosis_versions",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["project", "version"], name="unique_project_diagnosis_version"),
        ]

    def __str__(self):
        return f"{self.project} · v{self.version} · {self.total_score} 分"


class ScoringStandard(models.Model):
    version = models.CharField("版本", max_length=32, unique=True)
    name = models.CharField("名称", max_length=100)
    rules = models.JSONField("评分规则", default=dict)
    is_active = models.BooleanField("当前启用", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} · {self.version}"


class DiagnosisJob(models.Model):
    project = models.ForeignKey(Project, related_name="diagnosis_jobs", on_delete=models.CASCADE)
    source = models.ForeignKey(PdpSource, related_name="diagnosis_jobs", on_delete=models.CASCADE)
    scoring_standard = models.ForeignKey(ScoringStandard, related_name="diagnosis_jobs", on_delete=models.PROTECT)
    created_by = models.ForeignKey(
        "auth.User",
        related_name="diagnosis_jobs",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    status = models.CharField("状态", max_length=32, default="queued")
    stage = models.CharField("阶段", max_length=32, default="queued")
    progress = models.PositiveSmallIntegerField("进度", default=0)
    adapter = models.CharField("模型适配器", max_length=64, default="mock")
    model_name = models.CharField("模型名称", max_length=100, blank=True)
    context = models.JSONField("诊断上下文", default=dict, blank=True)
    error_code = models.CharField("错误代码", max_length=64, blank=True)
    error_message = models.TextField("错误信息", blank=True)
    locked_version = models.OneToOneField(
        DiagnosisVersion,
        related_name="source_job",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.project} · {self.status} · {self.progress}%"


class PageEvidence(models.Model):
    job = models.ForeignKey(DiagnosisJob, related_name="evidence", on_delete=models.CASCADE)
    module_code = models.CharField("模块编码", max_length=64)
    page_index = models.PositiveIntegerField("页码", default=0)
    bbox = models.JSONField("页面坐标", default=dict, blank=True)
    evidence_type = models.CharField("证据类型", max_length=32, default="page_region")
    ocr_text = models.TextField("识别文字", blank=True)
    crop_image = models.FileField("证据截图", upload_to="pdp_evidence/%Y/%m/", blank=True)
    model_reason = models.TextField("模型解释", blank=True)
    confidence = models.DecimalField("置信度", max_digits=4, decimal_places=3, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["module_code", "page_index"]


class ModuleAssessment(models.Model):
    job = models.ForeignKey(DiagnosisJob, related_name="assessments", on_delete=models.CASCADE)
    module_code = models.CharField("模块编码", max_length=64)
    module_name = models.CharField("模块名称", max_length=100)
    weight = models.DecimalField("权重", max_digits=5, decimal_places=1)
    coefficient = models.DecimalField("评分系数", max_digits=2, decimal_places=1)
    score = models.DecimalField("得分", max_digits=5, decimal_places=1)
    maturity = models.CharField("成熟度", max_length=8)
    judgment = models.TextField("判断")
    confidence = models.DecimalField("置信度", max_digits=4, decimal_places=3, default=0)
    auto_confirmed = models.BooleanField("AI 自动确认", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(fields=["job", "module_code"], name="unique_job_module_assessment"),
        ]


class ModelRun(models.Model):
    job = models.ForeignKey(DiagnosisJob, related_name="model_runs", on_delete=models.CASCADE)
    provider = models.CharField("供应商", max_length=64)
    model_name = models.CharField("模型", max_length=100)
    prompt_version = models.CharField("提示词版本", max_length=64, default="pdp-score-v1")
    status = models.CharField("状态", max_length=32, default="running")
    request_id = models.CharField("请求 ID", max_length=128, blank=True)
    usage = models.JSONField("用量", default=dict, blank=True)
    duration_ms = models.PositiveIntegerField("耗时毫秒", default=0)
    error_message = models.TextField("错误信息", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class AiModelSettings(models.Model):
    ADAPTER_CHOICES = (("auto", "自动选择"), ("openai", "OpenAI"), ("mock", "Mock 验证"))
    PROTOCOL_CHOICES = (("responses", "Responses API"), ("chat_completions", "Chat Completions"))

    name = models.CharField("配置名称", max_length=100, default="PDP Lab 默认 AI 模型")
    is_active = models.BooleanField("当前启用", default=True)
    ai_adapter = models.CharField("AI 适配器", max_length=32, choices=ADAPTER_CHOICES, default="auto")
    ai_protocol = models.CharField("API 协议", max_length=32, choices=PROTOCOL_CHOICES, default="responses")
    ai_model_name = models.CharField("AI 模型", max_length=100, default="gpt-5.4-mini")
    ai_base_url = models.URLField("API Base URL", blank=True, help_text="留空使用 OpenAI 官方地址")
    ai_timeout_seconds = models.PositiveIntegerField("API 超时（秒）", default=180)
    api_key_ciphertext = models.TextField("加密 API Key", blank=True, editable=False)
    updated_by = models.ForeignKey(
        "auth.User",
        verbose_name="最后修改人",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "AI 模型 API 设置"
        verbose_name_plural = "AI 模型 API 设置"

    def __str__(self):
        return self.name

    def clean(self):
        if self.ai_timeout_seconds < 10 or self.ai_timeout_seconds > 900:
            raise ValidationError({"ai_timeout_seconds": "超时时间需在 10~900 秒之间"})

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_active:
            type(self).objects.exclude(pk=self.pk).filter(is_active=True).update(is_active=False)

    @property
    def has_api_key(self):
        return bool(self.api_key_ciphertext)

    def set_api_key(self, value):
        self.api_key_ciphertext = _encrypt_secret(value)

    def get_api_key(self):
        return _decrypt_secret(self.api_key_ciphertext)


class PdpSkillSettings(models.Model):
    SKILL_MODE_CHOICES = (("built_in", "内置版本化规则"), ("remote_http", "远程 HTTP Skill"))

    name = models.CharField("配置名称", max_length=100, default="PDP Lab 默认 PDP Skill")
    is_active = models.BooleanField("当前启用", default=True)
    skill_name = models.CharField("Skill 名称", max_length=120, default="pdp-detail-page-methodology")
    skill_mode = models.CharField("Skill 接入方式", max_length=32, choices=SKILL_MODE_CHOICES, default="built_in")
    skill_endpoint_url = models.URLField(
        "Skill 接入地址 / 端口",
        blank=True,
        help_text="例如 http://127.0.0.1:8765/v1/skills/pdp-detail-page-methodology/rules",
    )
    skill_timeout_seconds = models.PositiveIntegerField("Skill 超时（秒）", default=30)
    skill_token_ciphertext = models.TextField("Skill 加密 Token", blank=True, editable=False)
    updated_by = models.ForeignKey(
        "auth.User",
        verbose_name="最后修改人",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "PDP Skill 接入设置"
        verbose_name_plural = "PDP Skill 接入设置"

    def __str__(self):
        return self.name

    def clean(self):
        if self.skill_timeout_seconds < 1 or self.skill_timeout_seconds > 120:
            raise ValidationError({"skill_timeout_seconds": "Skill 超时需在 1~120 秒之间"})
        if self.skill_mode == "remote_http" and not self.skill_endpoint_url:
            raise ValidationError({"skill_endpoint_url": "选择远程 HTTP Skill 时必须填写接入地址与端口"})
        if self.skill_endpoint_url:
            parsed = urlparse(self.skill_endpoint_url)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                raise ValidationError({"skill_endpoint_url": "Skill 地址必须是完整的 HTTP/HTTPS URL"})

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_active:
            type(self).objects.exclude(pk=self.pk).filter(is_active=True).update(is_active=False)

    @property
    def has_skill_token(self):
        return bool(self.skill_token_ciphertext)

    def set_skill_token(self, value):
        self.skill_token_ciphertext = _encrypt_secret(value)

    def get_skill_token(self):
        return _decrypt_secret(self.skill_token_ciphertext)
