from django import forms
from django.contrib import admin
from django.contrib.admin.forms import AdminAuthenticationForm
from django.core.exceptions import ValidationError
from types import MethodType
from .models import (
    AiModelSettings,
    DiagnosisJob,
    DiagnosisVersion,
    ModelRun,
    ModuleAssessment,
    NotificationPreference,
    PageEvidence,
    PdpSource,
    Project,
    PdpSkillSettings,
    ScoringStandard,
    UserProfile,
)


class SuperuserAdminAuthenticationForm(AdminAuthenticationForm):
    """Only superusers may authenticate into the operations admin."""

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.is_superuser:
            raise ValidationError("仅超级管理员可登录管理后台。", code="not_superuser")


def _superuser_only_has_permission(self, request):
    return bool(request.user.is_active and request.user.is_superuser)


admin.site.login_form = SuperuserAdminAuthenticationForm
admin.site.has_permission = MethodType(_superuser_only_has_permission, admin.site)


class AiModelSettingsAdminForm(forms.ModelForm):
    openai_api_key = forms.CharField(
        label="模型 API Key（OpenAI 兼容）",
        required=False,
        widget=forms.PasswordInput(render_value=False, attrs={"autocomplete": "new-password"}),
        help_text="留空则保留已保存 Key；数据库仅保存加密密文。",
    )
    clear_openai_api_key = forms.BooleanField(label="清除已保存模型 API Key", required=False)
    class Meta:
        model = AiModelSettings
        fields = "__all__"

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.cleaned_data.get("clear_openai_api_key"):
            instance.api_key_ciphertext = ""
        elif self.cleaned_data.get("openai_api_key"):
            instance.set_api_key(self.cleaned_data["openai_api_key"])
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class PdpSkillSettingsAdminForm(forms.ModelForm):
    skill_auth_token = forms.CharField(
        label="Skill 访问 Token",
        required=False,
        widget=forms.PasswordInput(render_value=False, attrs={"autocomplete": "new-password"}),
        help_text="可选；远程 HTTP Skill 需要 Bearer Token 时填写。",
    )
    clear_skill_auth_token = forms.BooleanField(label="清除已保存 Skill Token", required=False)

    class Meta:
        model = PdpSkillSettings
        fields = "__all__"

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.cleaned_data.get("clear_skill_auth_token"):
            instance.skill_token_ciphertext = ""
        elif self.cleaned_data.get("skill_auth_token"):
            instance.set_skill_token(self.cleaned_data["skill_auth_token"])
        if commit:
            instance.save()
            self.save_m2m()
        return instance


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "brand", "category", "updated_at")
    search_fields = ("name", "brand", "category")


@admin.register(DiagnosisVersion)
class DiagnosisVersionAdmin(admin.ModelAdmin):
    list_display = ("project", "version", "total_score", "overall_rating", "confirmation_mode", "status", "created_by", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("project__name", "created_by__username")
    readonly_fields = ("created_at",)


@admin.register(PdpSource)
class PdpSourceAdmin(admin.ModelAdmin):
    list_display = ("project", "original_name", "status", "created_at")
    search_fields = ("project__name", "original_name")


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "task_updates", "product_updates", "weekly_report", "updated_at")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "avatar", "updated_at")
    search_fields = ("user__username", "user__email", "user__first_name")


@admin.register(ScoringStandard)
class ScoringStandardAdmin(admin.ModelAdmin):
    list_display = ("name", "version", "is_active", "created_at")
    list_filter = ("is_active",)


@admin.register(DiagnosisJob)
class DiagnosisJobAdmin(admin.ModelAdmin):
    list_display = ("project", "status", "stage", "progress", "adapter", "model_name", "created_by", "created_at")
    list_filter = ("status", "stage", "adapter")
    search_fields = ("project__name", "source__original_name")


@admin.register(ModuleAssessment)
class ModuleAssessmentAdmin(admin.ModelAdmin):
    list_display = ("job", "module_name", "maturity", "score", "confidence", "auto_confirmed")
    list_filter = ("maturity", "auto_confirmed")


@admin.register(PageEvidence)
class PageEvidenceAdmin(admin.ModelAdmin):
    list_display = ("job", "module_code", "page_index", "evidence_type", "confidence")


@admin.register(ModelRun)
class ModelRunAdmin(admin.ModelAdmin):
    list_display = ("job", "provider", "model_name", "status", "duration_ms", "created_at")
    list_filter = ("provider", "status")


@admin.register(AiModelSettings)
class AiModelSettingsAdmin(admin.ModelAdmin):
    form = AiModelSettingsAdminForm
    list_display = ("name", "is_active", "ai_adapter", "ai_model_name", "api_key_status", "updated_at")
    list_filter = ("is_active", "ai_adapter")
    readonly_fields = ("api_key_status", "updated_by", "updated_at")
    fieldsets = (
        ("基础", {"fields": ("name", "is_active")} ),
        ("AI 模型 API", {"fields": (
            "ai_adapter", "ai_protocol", "ai_model_name", "ai_base_url", "ai_timeout_seconds",
            "api_key_status", "openai_api_key", "clear_openai_api_key",
        )}),
        ("审计", {"fields": ("updated_by", "updated_at")}),
    )

    @admin.display(description="API Key 状态", boolean=True)
    def api_key_status(self, obj):
        return bool(obj and obj.has_api_key)

    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    def has_add_permission(self, request):
        return not AiModelSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PdpSkillSettings)
class PdpSkillSettingsAdmin(admin.ModelAdmin):
    form = PdpSkillSettingsAdminForm
    list_display = ("name", "is_active", "skill_name", "skill_mode", "skill_endpoint_url", "skill_token_status", "updated_at")
    list_filter = ("is_active", "skill_mode")
    readonly_fields = ("skill_token_status", "updated_by", "updated_at")
    fieldsets = (
        ("基础", {"fields": ("name", "is_active")} ),
        ("PDP Skill 接入", {"fields": (
            "skill_name", "skill_mode", "skill_endpoint_url", "skill_timeout_seconds",
            "skill_token_status", "skill_auth_token", "clear_skill_auth_token",
        )}),
        ("审计", {"fields": ("updated_by", "updated_at")}),
    )

    @admin.display(description="Skill Token 状态", boolean=True)
    def skill_token_status(self, obj):
        return bool(obj and obj.has_skill_token)

    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    def has_add_permission(self, request):
        return not PdpSkillSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
