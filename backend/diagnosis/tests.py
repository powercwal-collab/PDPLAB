import base64
from io import BytesIO
import json
import tempfile
from types import SimpleNamespace

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .models import AiModelSettings, DiagnosisJob, DiagnosisVersion, PdpSkillSettings, PdpSource, Project, ScoringStandard, UserProfile
from .adapters.openai import EvidenceSuggestion, ModuleSuggestion, OpenAIDiagnosisAdapter, PdpDiagnosisOutput
from .runtime_config import get_runtime_integration_config
from .scoring import apply_evidence_guards, calculate_assessments, map_overall_rating
from .skill_runtime import _validate_remote_rules
from .tasks import _public_error, run_diagnosis_job


def valid_png_bytes(width=1, height=1):
    image = Image.new("RGB", (width, height), color=(24, 117, 232))
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


class DiagnosisApiTests(TestCase):
    def test_root_redirects_to_frontend(self):
        response = self.client.get(reverse("home"))
        self.assertRedirects(
            response,
            "http://127.0.0.1:4173/",
            fetch_redirect_response=False,
        )

    def test_health_endpoint(self):
        response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_readiness_checks_database_and_cache(self):
        response = self.client.get(reverse("readiness"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ready")
        self.assertEqual(response.json()["checks"], {"database": True, "cache": True})

    def test_write_endpoints_require_csrf_when_enforced(self):
        user = get_user_model().objects.create_user("csrf-user", password="12345678")
        client = Client(enforce_csrf_checks=True)
        client.force_login(user)
        blocked = client.post(
            reverse("project-list"),
            data='{"name":"应被阻止"}',
            content_type="application/json",
        )
        self.assertEqual(blocked.status_code, 403)
        csrf_response = client.get(reverse("auth-csrf"))
        token = csrf_response.cookies["csrftoken"].value
        allowed = client.post(
            reverse("project-list"),
            data='{"name":"CSRF 通过"}',
            content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(allowed.status_code, 201)

    def test_local_frontend_origin_is_trusted_in_development(self):
        self.assertIn("http://127.0.0.1:4173", settings.CSRF_TRUSTED_ORIGINS)
        self.assertIn("http://localhost:4173", settings.CSRF_TRUSTED_ORIGINS)

    def test_diagnosis_config_reports_skill_link_and_active_adapter(self):
        user = get_user_model().objects.create_user("config-user", password="12345678")
        self.client.force_login(user)
        response = self.client.get(reverse("diagnosis-config"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["source_skill"], "pdp-detail-page-methodology")
        self.assertEqual(response.json()["scoring_standard_version"], "pdp-v5")
        self.assertIn(response.json()["ai_protocol"], {"responses", "chat_completions"})
        self.assertEqual(response.json()["confirmation_mode"], "ai_auto")
        self.assertIn(response.json()["active_adapter"], {"mock", "openai"})
        self.assertEqual(response.json()["configured_model_name"], "gpt-5.4-mini")
        self.assertEqual(response.json()["config_source"], "admin")
        self.assertEqual(response.json()["ai_config_source"], "admin")
        self.assertEqual(response.json()["skill_config_source"], "admin")
        self.assertEqual(response.json()["skill_mode"], "built_in")
        self.assertEqual(len(response.json()["scoring_rules"]["modules"]), 11)
        self.assertEqual(sum(module["weight"] for module in response.json()["scoring_rules"]["modules"]), 100)
        self.assertTrue(response.json()["source_revision"].startswith("sha256:"))

    def test_admin_ai_and_skill_settings_are_independent_and_encrypted(self):
        ai_settings = AiModelSettings.objects.get(name="PDP Lab 默认 AI 模型")
        skill_settings = PdpSkillSettings.objects.get(name="PDP Lab 默认 PDP Skill")
        ai_settings.ai_adapter = "openai"
        ai_settings.ai_model_name = "gpt-test-model"
        ai_settings.set_api_key("sk-private-test-value")
        skill_settings.set_skill_token("skill-private-test-value")
        ai_settings.save()
        skill_settings.save()
        ai_settings.refresh_from_db()
        skill_settings.refresh_from_db()
        self.assertNotIn("sk-private-test-value", ai_settings.api_key_ciphertext)
        self.assertNotIn("skill-private-test-value", skill_settings.skill_token_ciphertext)
        self.assertEqual(ai_settings.get_api_key(), "sk-private-test-value")
        self.assertEqual(skill_settings.get_skill_token(), "skill-private-test-value")
        runtime = get_runtime_integration_config()
        self.assertEqual(runtime["source"], "admin")
        self.assertEqual(runtime["ai_config_source"], "admin")
        self.assertEqual(runtime["skill_config_source"], "admin")
        self.assertEqual(runtime["model_name"], "gpt-test-model")
        self.assertEqual(runtime["api_key"], "sk-private-test-value")

    def test_latest_builtin_rules_pass_remote_skill_contract_validation(self):
        rules = ScoringStandard.objects.get(version="pdp-v5").rules
        _validate_remote_rules(rules)
        self.assertEqual(rules["coefficients"], {"弱": 0, "较弱": 0.25, "中": 0.5, "强": 0.75, "极强": 1})
        self.assertEqual(len(rules["star_bands"]), 13)
        self.assertTrue(all(module.get("strong_standard") for module in rules["modules"]))

    def test_admin_exposes_independent_ai_and_skill_setting_entries(self):
        admin_user = get_user_model().objects.create_superuser("settings-admin", password="12345678")
        self.client.force_login(admin_user)
        ai_page = self.client.get(reverse("admin:diagnosis_aimodelsettings_changelist"))
        skill_page = self.client.get(reverse("admin:diagnosis_pdpskillsettings_changelist"))
        self.assertEqual(ai_page.status_code, 200)
        self.assertEqual(skill_page.status_code, 200)
        self.assertContains(ai_page, "AI 模型 API 设置")
        self.assertNotContains(ai_page, "Skill 接入地址 / 端口")
        self.assertContains(skill_page, "PDP Skill 接入设置")
        self.assertNotContains(skill_page, "OpenAI API Key")

    def test_legacy_combined_settings_url_redirects_to_ai_settings(self):
        admin_user = get_user_model().objects.create_superuser("legacy-admin", password="12345678")
        self.client.force_login(admin_user)
        response = self.client.get("/admin/diagnosis/integrationsettings/")
        self.assertRedirects(
            response,
            reverse("admin:diagnosis_aimodelsettings_changelist"),
            fetch_redirect_response=False,
        )
        detail_response = self.client.get("/admin/diagnosis/integrationsettings/1/change/")
        self.assertRedirects(
            detail_response,
            reverse("admin:diagnosis_aimodelsettings_changelist"),
            fetch_redirect_response=False,
        )

    def test_project_list_endpoint(self):
        user = get_user_model().objects.create_user("project-user", password="12345678")
        self.client.force_login(user)
        project = Project.objects.create(name="Nike Kids", brand="Nike", category="童鞋", owner=user)
        source = PdpSource.objects.create(
            project=project,
            original_name="cover.png",
            file=SimpleUploadedFile("cover.png", b"fake-png", content_type="image/png"),
        )
        DiagnosisVersion.objects.create(
            project=project,
            source=source,
            version=1,
            total_score=87,
            overall_rating=6.5,
            modules=[],
            created_by=user,
        )
        response = self.client.get(reverse("project-list"))
        self.assertEqual(response.status_code, 200)
        result = response.json()["results"][0]
        self.assertEqual(result["name"], "Nike Kids")
        self.assertEqual(result["latest_score"], 87)
        self.assertEqual(result["overall_rating"], 6.5)
        self.assertEqual(result["score_label"], "6.5 星")
        self.assertEqual(result["cover_url"], reverse("project-cover", args=[project.id]))

    def test_project_cover_endpoint_returns_mobile_safe_thumbnail(self):
        user = get_user_model().objects.create_user("cover-user", password="12345678")
        self.client.force_login(user)
        project = Project.objects.create(name="超长 PDP", owner=user)
        source_image = Image.new("RGB", (750, 15000), color=(46, 124, 232))
        image_bytes = BytesIO()
        source_image.save(image_bytes, format="JPEG")
        PdpSource.objects.create(
            project=project,
            original_name="long-pdp.jpg",
            file=SimpleUploadedFile("long-pdp.jpg", image_bytes.getvalue(), content_type="image/jpeg"),
        )

        response = self.client.get(reverse("project-cover", args=[project.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/jpeg")
        thumbnail = Image.open(BytesIO(b"".join(response.streaming_content)))
        self.assertEqual(thumbnail.size, (960, 540))

    def test_project_cover_is_private_to_project_owner(self):
        owner = get_user_model().objects.create_user("cover-owner", password="12345678")
        outsider = get_user_model().objects.create_user("cover-outsider", password="12345678")
        project = Project.objects.create(name="私有封面", owner=owner)
        self.client.force_login(outsider)
        response = self.client.get(reverse("project-cover", args=[project.id]))
        self.assertEqual(response.status_code, 404)

    def test_project_owner_can_rename_and_delete_project(self):
        user = get_user_model().objects.create_user("project-manager", password="12345678")
        self.client.force_login(user)
        project = Project.objects.create(name="旧项目名", category="旧类型", owner=user)
        renamed = self.client.patch(
            reverse("project-detail", args=[project.id]),
            data='{"name":"新项目名","category":"新类型"}',
            content_type="application/json",
        )
        self.assertEqual(renamed.status_code, 200)
        self.assertEqual(renamed.json()["project"]["name"], "新项目名")
        self.assertEqual(renamed.json()["project"]["category"], "新类型")
        unchanged = self.client.patch(
            reverse("project-detail", args=[project.id]),
            data='{"name":"","category":""}',
            content_type="application/json",
        )
        self.assertEqual(unchanged.status_code, 200)
        self.assertEqual(unchanged.json()["project"]["name"], "新项目名")
        self.assertEqual(unchanged.json()["project"]["category"], "新类型")
        deleted = self.client.delete(reverse("project-detail", args=[project.id]))
        self.assertEqual(deleted.status_code, 200)
        self.assertFalse(Project.objects.filter(pk=project.id).exists())

    def test_project_management_is_limited_to_owner(self):
        owner = get_user_model().objects.create_user("project-owner", password="12345678")
        outsider = get_user_model().objects.create_user("project-outsider", password="12345678")
        project = Project.objects.create(name="私有项目", owner=owner)
        self.client.force_login(outsider)
        rename = self.client.patch(
            reverse("project-detail", args=[project.id]),
            data='{"name":"越权修改"}',
            content_type="application/json",
        )
        self.assertEqual(rename.status_code, 404)
        self.assertEqual(self.client.delete(reverse("project-detail", args=[project.id])).status_code, 404)
        self.assertTrue(Project.objects.filter(pk=project.id, name="私有项目").exists())

    def test_project_owner_can_batch_delete_selected_projects(self):
        user = get_user_model().objects.create_user("batch-project-manager", password="12345678")
        other = get_user_model().objects.create_user("batch-project-other", password="12345678")
        first = Project.objects.create(name="批量项目一", owner=user)
        second = Project.objects.create(name="批量项目二", owner=user)
        foreign = Project.objects.create(name="其他账号项目", owner=other)
        self.client.force_login(user)
        forbidden = self.client.post(
            reverse("project-batch-delete"),
            data=json.dumps({"project_ids": [first.id, foreign.id]}),
            content_type="application/json",
        )
        self.assertEqual(forbidden.status_code, 404)
        self.assertTrue(Project.objects.filter(pk=first.id).exists())
        deleted = self.client.post(
            reverse("project-batch-delete"),
            data=json.dumps({"project_ids": [first.id, second.id]}),
            content_type="application/json",
        )
        self.assertEqual(deleted.status_code, 200)
        self.assertFalse(Project.objects.filter(pk__in=[first.id, second.id]).exists())
        self.assertTrue(Project.objects.filter(pk=foreign.id).exists())

    def test_register_login_and_logout(self):
        register = self.client.post(
            reverse("auth-register"),
            data='{"username":"designer","nickname":"设计师","email":"designer@example.com","password":"12345678"}',
            content_type="application/json",
        )
        self.assertEqual(register.status_code, 201)
        self.assertEqual(register.json()["user"]["nickname"], "设计师")
        self.assertEqual(register.json()["user"]["avatar_url"], "")
        self.assertFalse(register.json()["user"]["is_staff"])
        self.assertFalse(register.json()["user"]["is_superuser"])
        registered_user = get_user_model().objects.get(username="designer")
        self.assertFalse(registered_user.is_staff)
        self.assertFalse(registered_user.is_superuser)
        session_user = self.client.get(reverse("auth-me"))
        self.assertEqual(session_user.status_code, 200)
        self.assertEqual(session_user.json()["user"]["username"], "designer")
        self.assertFalse(session_user.json()["user"]["is_staff"])
        self.assertFalse(session_user.json()["user"]["is_superuser"])
        self.assertRedirects(
            self.client.get("/admin/"),
            "/admin/login/?next=/admin/",
            fetch_redirect_response=False,
        )
        self.client.post(reverse("auth-logout"))
        login = self.client.post(
            reverse("auth-login"),
            data='{"username":"designer","password":"12345678"}',
            content_type="application/json",
        )
        self.assertEqual(login.status_code, 200)

        self.client.post(reverse("auth-logout"))
        email_login = self.client.post(
            reverse("auth-login"),
            data='{"username":"designer@example.com","password":"12345678"}',
            content_type="application/json",
        )
        self.assertEqual(email_login.status_code, 200)

    def test_admin_rejects_staff_user_without_superuser_permission(self):
        staff_user = get_user_model().objects.create_user(
            username="operator",
            email="operator@example.com",
            password="12345678",
            is_staff=True,
            is_superuser=False,
        )
        self.client.force_login(staff_user)
        self.assertRedirects(
            self.client.get("/admin/"),
            "/admin/login/?next=/admin/",
            fetch_redirect_response=False,
        )
        self.client.logout()
        login = self.client.post(
            "/admin/login/?next=/admin/",
            {"username": "operator", "password": "12345678", "next": "/admin/"},
        )
        self.assertEqual(login.status_code, 200)
        self.assertContains(login, "仅超级管理员可登录管理后台")
        self.assertNotIn("_auth_user_id", self.client.session)

        superuser = get_user_model().objects.create_superuser(
            username="admin-check",
            email="admin-check@example.com",
            password="12345678",
        )
        self.client.force_login(superuser)
        self.assertEqual(self.client.get("/admin/").status_code, 200)

    def test_register_rejects_invalid_or_duplicate_email(self):
        invalid = self.client.post(
            reverse("auth-register"),
            data='{"username":"invalid-email","nickname":"测试","email":"invalid.example.com","password":"12345678"}',
            content_type="application/json",
        )
        self.assertEqual(invalid.status_code, 400)
        self.assertEqual(invalid.json()["error"], "请输入有效的电子邮箱")

        get_user_model().objects.create_user("existing", email="used@example.com", password="12345678")
        duplicate = self.client.post(
            reverse("auth-register"),
            data='{"username":"duplicate-email","nickname":"测试","email":"USED@example.com","password":"12345678"}',
            content_type="application/json",
        )
        self.assertEqual(duplicate.status_code, 400)
        self.assertEqual(duplicate.json()["error"], "该电子邮箱已被注册")

    def test_new_user_starts_empty_and_projects_are_isolated_by_owner(self):
        first_user = get_user_model().objects.create_user("first-owner", password="12345678")
        second_user = get_user_model().objects.create_user("second-owner", password="12345678")
        first_project = Project.objects.create(name="账号一项目", owner=first_user)
        Project.objects.create(name="历史无主项目")

        self.client.force_login(second_user)
        self.assertEqual(self.client.get(reverse("project-list")).json()["results"], [])
        forbidden_upload = self.client.post(
            reverse("uploads"),
            {"project_id": first_project.id, "file": SimpleUploadedFile("private.png", b"private", content_type="image/png")},
        )
        self.assertEqual(forbidden_upload.status_code, 404)

        created = self.client.post(
            reverse("project-list"),
            data=json.dumps({"name": "账号二项目", "brand": "Test"}),
            content_type="application/json",
        )
        self.assertEqual(created.status_code, 201)
        second_project = Project.objects.get(pk=created.json()["project"]["id"])
        self.assertEqual(second_project.owner, second_user)

        self.client.force_login(first_user)
        first_results = self.client.get(reverse("project-list")).json()["results"]
        self.assertEqual([item["id"] for item in first_results], [first_project.id])

    def test_legacy_project_rating_is_normalized_to_current_star_bands(self):
        user = get_user_model().objects.create_user("legacy-rating-user", password="12345678")
        self.client.force_login(user)
        project = Project.objects.create(name="旧版星级项目", owner=user)
        DiagnosisVersion.objects.create(
            project=project,
            version=1,
            total_score=65.5,
            overall_rating=4.9,
            modules=[],
            scoring_standard_version="pdp-v1",
            created_by=user,
        )
        projects = self.client.get(reverse("project-list")).json()["results"]
        serialized_project = next(item for item in projects if item["id"] == project.id)
        self.assertEqual(serialized_project["overall_rating"], 5)
        self.assertEqual(serialized_project["score_label"], "5 星")
        history = self.client.get(reverse("diagnosis-list"), {"project_id": project.id}).json()["results"]
        self.assertEqual(history[0]["overall_rating"], 5)

    def test_profile_preferences_and_upload_require_a_working_session(self):
        user = get_user_model().objects.create_user("power", password="12345678", email="old@example.com")
        self.client.force_login(user)
        profile = self.client.patch(
            reverse("profile"),
            data=json.dumps({"nickname": "Power", "email": "power@example.com"}),
            content_type="application/json",
        )
        self.assertEqual(profile.status_code, 200)
        self.assertEqual(profile.json()["nickname"], "Power")
        preferences = self.client.patch(
            reverse("preferences"),
            data=json.dumps({"task_updates": False, "weekly_report": True}),
            content_type="application/json",
        )
        self.assertEqual(preferences.status_code, 200)
        self.assertFalse(preferences.json()["task_updates"])
        project = Project.objects.create(name="上传验证", owner=user)
        upload = self.client.post(
            reverse("uploads"),
            {"project_id": project.id, "file": SimpleUploadedFile("pdp.png", b"fake-png", content_type="image/png")},
        )
        self.assertEqual(upload.status_code, 201)
        self.assertEqual(upload.json()["source"]["original_name"], "pdp.png")

    def test_avatar_upload_is_persisted_and_returned_by_session_endpoints(self):
        user = get_user_model().objects.create_user(
            "avatar-user",
            password="12345678",
            email="avatar@example.com",
            first_name="KK",
        )
        self.client.force_login(user)
        png = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
        )
        with tempfile.TemporaryDirectory() as media_root, self.settings(MEDIA_ROOT=media_root):
            response = self.client.post(
                reverse("profile-avatar"),
                {"avatar": SimpleUploadedFile("avatar.png", png, content_type="image/png")},
            )
            self.assertEqual(response.status_code, 200)
            self.assertIn("/media/user_avatars/", response.json()["avatar_url"])
            profile = UserProfile.objects.get(user=user)
            self.assertTrue(profile.avatar.name.endswith(".png"))
            first_avatar_name = profile.avatar.name

            replacement = self.client.post(
                reverse("profile-avatar"),
                {"avatar": SimpleUploadedFile("replacement.png", png, content_type="image/png")},
            )
            self.assertEqual(replacement.status_code, 200)
            profile.refresh_from_db()
            self.assertNotEqual(profile.avatar.name, first_avatar_name)
            self.assertFalse(profile.avatar.storage.exists(first_avatar_name))

            me = self.client.get(reverse("auth-me"))
            self.assertEqual(me.status_code, 200)
            self.assertEqual(me.json()["user"]["avatar_url"], replacement.json()["avatar_url"])
            self.assertEqual(me.json()["user"]["nickname"], "KK")

            delete = self.client.delete(reverse("profile-avatar"))
            self.assertEqual(delete.status_code, 200)
            self.assertEqual(delete.json()["avatar_url"], "")

    def test_avatar_upload_rejects_non_image_content(self):
        user = get_user_model().objects.create_user("bad-avatar", password="12345678")
        self.client.force_login(user)
        response = self.client.post(
            reverse("profile-avatar"),
            {"avatar": SimpleUploadedFile("avatar.txt", b"not-an-image", content_type="text/plain")},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "头像仅支持 JPG、PNG 或 WebP")

    def test_complete_diagnosis_is_versioned_and_incomplete_diagnosis_is_rejected(self):
        user = get_user_model().objects.create_user("reviewer", password="12345678")
        self.client.force_login(user)
        project = Project.objects.create(name="评分验证", owner=user)
        modules = [
            {"name": f"模块 {index + 1}", "max": 10, "coefficient": 0.5, "score": 5, "maturity": "中", "checked": True}
            for index in range(11)
        ]
        payload = {"project_id": project.id, "total_score": 55, "overall_rating": 4.4, "modules": modules}
        first = self.client.post(reverse("diagnosis-list"), data=json.dumps(payload), content_type="application/json")
        second = self.client.post(reverse("diagnosis-list"), data=json.dumps(payload), content_type="application/json")
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)
        self.assertEqual(second.json()["diagnosis"]["version"], 2)
        self.assertEqual(DiagnosisVersion.objects.filter(project=project).count(), 2)
        history = self.client.get(reverse("diagnosis-list"), {"project_id": project.id})
        self.assertEqual(history.status_code, 200)
        self.assertEqual(len(history.json()["results"]), 2)

        modules[0]["checked"] = False
        incomplete = self.client.post(reverse("diagnosis-list"), data=json.dumps(payload), content_type="application/json")
        self.assertEqual(incomplete.status_code, 400)

    def test_diagnosis_record_can_be_deleted_and_latest_version_is_returned(self):
        user = get_user_model().objects.create_user("history-owner", password="12345678")
        other_user = get_user_model().objects.create_user("history-other", password="12345678")
        project = Project.objects.create(name="评分删除验证", owner=user)
        first = DiagnosisVersion.objects.create(
            project=project,
            version=1,
            total_score=65,
            overall_rating=5,
            modules=[],
            created_by=user,
        )
        second = DiagnosisVersion.objects.create(
            project=project,
            version=2,
            total_score=80,
            overall_rating=6,
            modules=[],
            created_by=user,
        )

        self.client.force_login(other_user)
        denied = self.client.delete(reverse("diagnosis-detail", args=[second.id]))
        self.assertEqual(denied.status_code, 404)

        self.client.force_login(user)
        deleted_latest = self.client.delete(reverse("diagnosis-detail", args=[second.id]))
        self.assertEqual(deleted_latest.status_code, 200)
        self.assertEqual(deleted_latest.json()["deleted_version"], 2)
        self.assertEqual(deleted_latest.json()["latest_diagnosis"]["id"], first.id)
        self.assertFalse(DiagnosisVersion.objects.filter(pk=second.id).exists())

        deleted_last = self.client.delete(reverse("diagnosis-detail", args=[first.id]))
        self.assertEqual(deleted_last.status_code, 200)
        self.assertIsNone(deleted_last.json()["latest_diagnosis"])
        self.assertFalse(DiagnosisVersion.objects.filter(project=project).exists())

    def test_skill_star_bands_are_used_instead_of_linear_formula(self):
        self.assertEqual(map_overall_rating(64.9), 4.5)
        self.assertEqual(map_overall_rating(65), 5)
        self.assertEqual(map_overall_rating(80), 6)
        self.assertEqual(map_overall_rating(90), 7)

    def test_five_level_coefficients_preserve_quarter_scores(self):
        rules = ScoringStandard.objects.get(version="pdp-v5").rules
        coefficients = [0, 0.25, 0.5, 0.75, 1, 0, 0.25, 0.5, 0.75, 1, 0.25]
        suggestions = [
            {"module_code": definition["code"], "coefficient": coefficient, "judgment": "五级评分回归", "confidence": 0.9}
            for definition, coefficient in zip(rules["modules"], coefficients)
        ]
        modules, total, _stars = calculate_assessments(suggestions, rules)
        self.assertEqual([item["maturity"] for item in modules[:5]], ["弱", "较弱", "中", "强", "极强"])
        self.assertEqual(modules[9]["score"], 5)
        self.assertEqual(modules[10]["score"], 1.25)
        self.assertEqual(total, 44)

    def test_visual_tier_axes_apply_deterministic_score_ceilings(self):
        rules = ScoringStandard.objects.get(version="pdp-v5").rules
        base = [{
            "module_code": item["code"], "coefficient": 1, "information_level": "proven",
            "visual_tier": "t0", "integration": "matched", "judgment": "完整", "confidence": 0.9,
        } for item in rules["modules"]]
        by_code = {item["module_code"]: item for item in base}
        by_code["selling_point_proof"].update(visual_tier="t2")
        by_code["detail_review"].update(visual_tier="t1")
        by_code["service"].update(information_level="shallow", integration="isolated")
        evidence = [{"module_code": item["code"], "evidence_type": "product_proof"} for item in rules["modules"]]
        evidence.extend([
            {"module_code": "product_kv", "evidence_type": "product_hero_visual"},
            {"module_code": "scenario", "evidence_type": "sport_scene"},
            {"module_code": "recommendation", "evidence_type": "series_recommendation"},
            {"module_code": "endorsement", "evidence_type": "technology_source"},
            {"module_code": "fit_comparison", "evidence_type": "measurement_method"},
            {"module_code": "fit_comparison", "evidence_type": "fit_advice"},
        ])
        guarded = {item["module_code"]: item for item in apply_evidence_guards(base, evidence, rules)}
        self.assertEqual(guarded["selling_point_proof"]["coefficient"], 0.5)
        self.assertEqual(guarded["detail_review"]["coefficient"], 0.75)
        self.assertEqual(guarded["service"]["coefficient"], 0.25)

    def test_evidence_gates_override_formal_presence_without_qualifying_visuals(self):
        rules = ScoringStandard.objects.get(version="pdp-v5").rules
        suggestions = [
            {"module_code": item["code"], "coefficient": 1, "information_level": "proven", "visual_tier": "t0", "integration": "matched", "judgment": "模型认为完整", "confidence": 0.9}
            for item in rules["modules"]
        ]
        evidence = []
        for item in rules["modules"]:
            code = item["code"]
            evidence_type = "product_proof"
            if code == "product_kv":
                evidence_type = "hero_copy_only"
            elif code == "scenario":
                evidence_type = "studio_model_view"
            elif code == "recommendation":
                evidence_type = "generic_or_decorative"
            elif code == "endorsement":
                evidence_type = "logo_only"
            elif code == "fit_comparison":
                evidence_type = "measurement_method"
            evidence.append({"module_code": code, "evidence_type": evidence_type})

        guarded = {item["module_code"]: item for item in apply_evidence_guards(suggestions, evidence, rules)}
        self.assertEqual(guarded["product_kv"]["coefficient"], 0.25)
        self.assertEqual(guarded["scenario"]["coefficient"], 0.25)
        self.assertEqual(guarded["recommendation"]["coefficient"], 0)
        self.assertEqual(guarded["endorsement"]["coefficient"], 0)
        self.assertEqual(guarded["fit_comparison"]["coefficient"], 0.5)
        self.assertEqual(guarded["page_rhythm"]["coefficient"], 0.5)
        modules, total, stars = calculate_assessments(list(guarded.values()), rules)
        self.assertEqual(len(modules), 11)
        self.assertLess(total, 100)
        self.assertLess(stars, 7)

    def test_special_background_requires_model_product_composite_for_t0(self):
        rules = ScoringStandard.objects.get(version="pdp-v5").rules
        suggestions = [
            {"module_code": item["code"], "coefficient": 1, "information_level": "proven", "visual_tier": "t0", "integration": "matched", "judgment": "完整", "confidence": 0.9}
            for item in rules["modules"]
        ]
        evidence = [{"module_code": item["code"], "evidence_type": "product_proof"} for item in rules["modules"]]
        evidence.extend([
            {"module_code": "product_kv", "evidence_type": "product_hero_visual"},
            {"module_code": "scenario", "evidence_type": "sport_scene"},
            {"module_code": "recommendation", "evidence_type": "series_recommendation"},
            {"module_code": "endorsement", "evidence_type": "technology_source"},
            {"module_code": "fit_comparison", "evidence_type": "measurement_method"},
            {"module_code": "fit_comparison", "evidence_type": "fit_advice"},
            {"module_code": "detail_review", "evidence_type": "designed_product_only"},
            {"module_code": "selling_point_proof", "evidence_type": "designed_model_product_composite"},
            {"module_code": "basic_information", "evidence_type": "designed_product_only"},
            {"module_code": "basic_information", "evidence_type": "pagewide_designed_model_product_sequence"},
        ])

        guarded = {item["module_code"]: item for item in apply_evidence_guards(suggestions, evidence, rules)}
        self.assertEqual(guarded["detail_review"]["coefficient"], 0.75)
        self.assertEqual(guarded["selling_point_proof"]["coefficient"], 1)
        self.assertEqual(guarded["basic_information"]["coefficient"], 1)

    def test_latest_skill_t0_special_design_evidence_remains_eligible(self):
        rules = ScoringStandard.objects.get(version="pdp-v5").rules
        suggestions = [
            {
                "module_code": item["code"],
                "coefficient": 1,
                "information_level": "proven",
                "visual_tier": "t0",
                "integration": "matched",
                "judgment": "信息完整且视觉证据匹配",
                "confidence": 0.9,
            }
            for item in rules["modules"]
        ]
        evidence = [{"module_code": item["code"], "evidence_type": "product_proof"} for item in rules["modules"]]
        evidence.extend([
            {"module_code": "product_kv", "evidence_type": "product_hero_visual"},
            {"module_code": "scenario", "evidence_type": "sport_scene"},
            {"module_code": "recommendation", "evidence_type": "series_recommendation"},
            {"module_code": "endorsement", "evidence_type": "technology_source"},
            {"module_code": "fit_comparison", "evidence_type": "measurement_method"},
            {"module_code": "fit_comparison", "evidence_type": "fit_advice"},
            {"module_code": "selling_point_proof", "evidence_type": "product_3d_structure_explanation"},
            {"module_code": "page_rhythm", "evidence_type": "product_specific_art_illustration"},
        ])

        guarded = {item["module_code"]: item for item in apply_evidence_guards(suggestions, evidence, rules)}
        self.assertEqual(guarded["selling_point_proof"]["coefficient"], 1)
        self.assertEqual(guarded["page_rhythm"]["coefficient"], 1)
        self.assertEqual(
            rules["visual_tier_rules"]["t0_eligible_evidence"],
            [
                "designed_model_product_composite",
                "pagewide_designed_model_product_sequence",
                "product_3d_structure_explanation",
                "product_specific_art_illustration",
            ],
        )

    def test_evidence_gates_accept_qualifying_kv_scene_recommendation_and_backing(self):
        rules = ScoringStandard.objects.get(version="pdp-v5").rules
        suggestions = [
            {"module_code": item["code"], "coefficient": 1, "information_level": "proven", "visual_tier": "t0", "integration": "matched", "judgment": "证据充分", "confidence": 0.9}
            for item in rules["modules"]
        ]
        types = {
            "product_kv": "product_hero_visual", "scenario": "sport_scene",
            "recommendation": "outfit_recommendation", "endorsement": "technology_source",
            "fit_comparison": "measurement_method",
        }
        evidence = []
        for item in rules["modules"]:
            evidence.append({"module_code": item["code"], "evidence_type": types.get(item["code"], "product_proof")})
        evidence.append({"module_code": "fit_comparison", "evidence_type": "fit_advice"})
        guarded = {item["module_code"]: item for item in apply_evidence_guards(suggestions, evidence, rules)}
        self.assertEqual(guarded["product_kv"]["coefficient"], 1)
        self.assertEqual(guarded["scenario"]["coefficient"], 1)
        self.assertEqual(guarded["recommendation"]["coefficient"], 1)
        self.assertEqual(guarded["endorsement"]["coefficient"], 1)
        self.assertEqual(guarded["fit_comparison"]["coefficient"], 1)

    def test_async_job_worker_creates_evidence_and_auto_locked_version(self):
        user = get_user_model().objects.create_user("auto-reviewer", password="12345678")
        project = Project.objects.create(name="自动评分项目", owner=user)
        source = PdpSource.objects.create(
            project=project,
            original_name="auto.png",
            file=SimpleUploadedFile("auto.png", b"fake-png", content_type="image/png"),
        )
        standard = ScoringStandard.objects.get(version="pdp-v1")
        job = DiagnosisJob.objects.create(
            project=project,
            source=source,
            scoring_standard=standard,
            created_by=user,
            adapter="mock",
        )
        diagnosis_id = run_diagnosis_job(job.id)
        job.refresh_from_db()
        diagnosis = DiagnosisVersion.objects.get(pk=diagnosis_id)
        self.assertEqual(job.status, "completed")
        self.assertEqual(job.progress, 100)
        self.assertEqual(job.assessments.count(), 11)
        self.assertEqual(job.evidence.count(), 11)
        self.assertEqual(diagnosis.confirmation_mode, "ai_auto")
        self.assertEqual(float(diagnosis.total_score), 52.25)
        self.assertEqual(float(diagnosis.overall_rating), 4.0)
        self.client.force_login(user)
        history = self.client.get(reverse("diagnosis-list"), {"project_id": project.id})
        serialized_module = history.json()["results"][0]["modules"][0]
        self.assertEqual(serialized_module["judgment"], "有产品封面与基础主张，但首屏缺少更清晰的系列定位与利益点排序。")
        self.assertEqual(len(serialized_module["evidence"]), 1)
        self.assertEqual(serialized_module["evidence"][0]["model_reason"], serialized_module["judgment"])

    def test_identical_source_reuses_completed_model_analysis(self):
        user = get_user_model().objects.create_user("stable-score", password="12345678")
        project = Project.objects.create(name="稳定评分", owner=user)
        standard = ScoringStandard.objects.get(version="pdp-v1")
        first_source = PdpSource.objects.create(
            project=project,
            original_name="same.png",
            file=SimpleUploadedFile("same.png", b"identical-pdp-content", content_type="image/png"),
        )
        first = DiagnosisJob.objects.create(project=project, source=first_source, scoring_standard=standard, created_by=user, adapter="mock")
        run_diagnosis_job(first.id)
        first.refresh_from_db()
        second_source = PdpSource.objects.create(
            project=project,
            original_name="same-copy.png",
            file=SimpleUploadedFile("same-copy.png", b"identical-pdp-content", content_type="image/png"),
        )
        second = DiagnosisJob.objects.create(project=project, source=second_source, scoring_standard=standard, created_by=user, adapter="mock")
        run_diagnosis_job(second.id)
        second.refresh_from_db()
        self.assertEqual(second.status, "completed")
        self.assertEqual(second.locked_version.total_score, first.locked_version.total_score)
        self.assertEqual(second.model_runs.get().usage["mode"], "reused_identical_analysis")

    def test_gateway_errors_are_sanitized_for_the_user(self):
        code, message = _public_error(RuntimeError("<html><h1>502 Bad Gateway</h1>cloudflare"))
        self.assertEqual(code, "MODEL_GATEWAY_UNAVAILABLE")
        self.assertNotIn("<html>", message)
        code, message = _public_error(RuntimeError("payload too large"))
        self.assertEqual(code, "MODEL_PAYLOAD_TOO_LARGE")
        self.assertNotIn("payload too large", message.lower())

    @override_settings(PDP_ALLOW_MOCK_DIAGNOSIS=False)
    def test_mock_adapter_is_blocked_from_creating_user_diagnosis_job(self):
        user = get_user_model().objects.create_user("mock-blocked", password="12345678")
        self.client.force_login(user)
        project = Project.objects.create(name="禁止 Mock 正式评分", owner=user)
        source = PdpSource.objects.create(
            project=project,
            original_name="mock.png",
            file=SimpleUploadedFile("mock.png", b"fake-png", content_type="image/png"),
        )
        response = self.client.post(
            reverse("diagnosis-job-list"),
            data=json.dumps({"source_id": source.id, "context": {}}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["code"], "MOCK_ADAPTER_ACTIVE")
        self.assertEqual(DiagnosisJob.objects.filter(source=source).count(), 0)

    def test_openai_adapter_uses_structured_evidence_and_deletes_remote_file(self):
        rules = ScoringStandard.objects.get(version="pdp-v1").rules
        parsed = PdpDiagnosisOutput(
            modules=[
                ModuleSuggestion(module_code=item["code"], coefficient=0.5, information_level="complete", visual_tier="t2", integration="matched", judgment=f"{item['name']} 证据中等", confidence=0.86)
                for item in rules["modules"]
            ],
            evidence=[
                EvidenceSuggestion(
                    module_code=item["code"],
                    page_index=index,
                    bbox={"x": 0.1, "y": 0.1, "width": 0.8, "height": 0.12},
                    ocr_text=item["name"],
                    reason=f"{item['name']} 可见证据",
                    confidence=0.86,
                )
                for index, item in enumerate(rules["modules"])
            ],
        )

        class FakeFiles:
            def __init__(self):
                self.deleted = []

            def create(self, **kwargs):
                self.purpose = kwargs["purpose"]
                return SimpleNamespace(id="file_test")

            def delete(self, file_id):
                self.deleted.append(file_id)

        class FakeResponses:
            def parse(self, **kwargs):
                self.kwargs = kwargs
                return SimpleNamespace(
                    id="resp_test",
                    output_parsed=parsed,
                    usage=SimpleNamespace(model_dump=lambda: {"input_tokens": 123, "output_tokens": 45}),
                )

        fake_client = SimpleNamespace(files=FakeFiles(), responses=FakeResponses())
        user = get_user_model().objects.create_user("openai-adapter", password="12345678")
        project = Project.objects.create(name="OpenAI 适配器", owner=user)
        source = PdpSource.objects.create(
            project=project,
            original_name="openai.png",
            file=SimpleUploadedFile("openai.png", valid_png_bytes(), content_type="image/png"),
        )
        result = OpenAIDiagnosisAdapter(client=fake_client).analyze(source=source, context={"channel": "tmall"}, scoring_rules=rules)
        self.assertEqual(len(result["modules"]), 11)
        self.assertEqual(len(result["evidence"]), 11)
        self.assertEqual(result["request_id"], "resp_test")
        self.assertTrue(result["usage"]["external_api"])
        self.assertFalse(hasattr(fake_client.files, "purpose"))
        self.assertEqual(fake_client.files.deleted, [])
        self.assertFalse(fake_client.responses.kwargs["store"])

    def test_responses_adapter_uploads_pdf_using_binary_file_tuple(self):
        rules = ScoringStandard.objects.get(version="pdp-v5").rules
        parsed = PdpDiagnosisOutput(
            modules=[ModuleSuggestion(module_code=item["code"], coefficient=0, information_level="none", visual_tier="none", integration="isolated", judgment="未发现有效内容", confidence=0.8) for item in rules["modules"]],
            evidence=[EvidenceSuggestion(module_code=item["code"], page_index=0, reason="未发现有效内容", confidence=0.8) for item in rules["modules"]],
        )

        class FakeFiles:
            def create(self, **kwargs):
                self.kwargs = kwargs
                return SimpleNamespace(id="pdf_test")

            def delete(self, _file_id):
                return None

        class FakeResponses:
            def parse(self, **_kwargs):
                return SimpleNamespace(id="pdf_response", output_parsed=parsed, usage=None)

        fake_files = FakeFiles()
        user = get_user_model().objects.create_user("pdf-adapter", password="12345678")
        project = Project.objects.create(name="PDF 适配器", owner=user)
        source = PdpSource.objects.create(
            project=project,
            original_name="page.pdf",
            file=SimpleUploadedFile("page.pdf", b"%PDF-1.4\nminimal", content_type="application/pdf"),
        )
        adapter = OpenAIDiagnosisAdapter(client=SimpleNamespace(files=fake_files, responses=FakeResponses()))
        adapter.analyze(source=source, context={}, scoring_rules=rules)
        uploaded = fake_files.kwargs["file"]
        self.assertEqual(uploaded[0], "page.pdf")
        self.assertEqual(fake_files.kwargs["purpose"], "user_data")

    def test_openai_adapter_normalizes_missing_evidence_to_weak(self):
        rules = ScoringStandard.objects.get(version="pdp-v5").rules
        missing_code = "interactive_content"
        parsed = PdpDiagnosisOutput(
            modules=[
                ModuleSuggestion(
                    module_code=item["code"], coefficient=0.75,
                    information_level="complete", visual_tier="t1",
                    integration="matched", judgment="模型建议为较强表现",
                    confidence=0.8,
                ) for item in rules["modules"]
            ],
            evidence=[
                EvidenceSuggestion(
                    module_code=item["code"], page_index=0,
                    evidence_type="product_proof", reason="存在可定位页面证据",
                    confidence=0.8,
                ) for item in rules["modules"] if item["code"] != missing_code
            ],
        )

        normalized = OpenAIDiagnosisAdapter(client=SimpleNamespace())._normalize_missing_evidence(parsed, rules)
        module = next(item for item in normalized.modules if item.module_code == missing_code)
        evidence = next(item for item in normalized.evidence if item.module_code == missing_code)
        self.assertEqual(module.coefficient, 0)
        self.assertEqual(module.information_level, "none")
        self.assertEqual(module.visual_tier, "none")
        self.assertEqual(module.integration, "isolated")
        self.assertEqual(evidence.evidence_type, "missing_content")
        self.assertEqual(evidence.confidence, 0)
        OpenAIDiagnosisAdapter(client=SimpleNamespace())._validate_output(normalized, rules)

    def test_chat_completions_adapter_uses_data_url_and_structured_output(self):
        rules = ScoringStandard.objects.get(version="pdp-v1").rules
        parsed = PdpDiagnosisOutput(
            modules=[
                ModuleSuggestion(module_code=item["code"], coefficient=0.5, information_level="complete", visual_tier="t2", integration="matched", judgment=f"{item['name']} 证据中等", confidence=0.86)
                for item in rules["modules"]
            ],
            evidence=[
                EvidenceSuggestion(
                    module_code=item["code"],
                    page_index=index,
                    bbox={"x": 0.1, "y": 0.1, "width": 0.8, "height": 0.12},
                    ocr_text=item["name"],
                    reason=f"{item['name']} 可见证据",
                    confidence=0.86,
                )
                for index, item in enumerate(rules["modules"])
            ],
        )

        class FakeChatCompletions:
            def create(self, **kwargs):
                self.kwargs = kwargs
                return SimpleNamespace(
                    id="chat_test",
                    choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(parsed.model_dump())))],
                    usage=SimpleNamespace(model_dump=lambda: {"prompt_tokens": 123, "completion_tokens": 45}),
                )

        completions = FakeChatCompletions()
        fake_client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
        user = get_user_model().objects.create_user("chat-adapter", password="12345678")
        project = Project.objects.create(name="Chat 适配器", owner=user)
        source = PdpSource.objects.create(
            project=project,
            original_name="chat.png",
            file=SimpleUploadedFile("chat.png", valid_png_bytes(), content_type="image/png"),
        )
        adapter = OpenAIDiagnosisAdapter(client=fake_client, runtime_config={
            "model_name": "mimo-v2.5",
            "protocol": "chat_completions",
        })
        result = adapter.analyze(source=source, context={"channel": "tmall"}, scoring_rules=rules)
        content = completions.kwargs["messages"][1]["content"]
        self.assertTrue(content[1]["image_url"]["url"].startswith("data:image/jpeg;base64,"))
        self.assertEqual(completions.kwargs["temperature"], 0)
        self.assertEqual(completions.kwargs["extra_body"], {"thinking": {"type": "disabled"}})
        self.assertEqual(len(result["modules"]), 11)
        self.assertEqual(len(result["evidence"]), 11)
        self.assertEqual(result["usage"]["mode"], "chat_completions")

    def test_kimi_k3_uses_required_temperature_without_disabling_thinking(self):
        adapter = OpenAIDiagnosisAdapter(client=SimpleNamespace(), runtime_config={
            "model_name": "Kimi-K3",
            "protocol": "chat_completions",
        })

        options = adapter._chat_completion_options()

        self.assertEqual(options, {"temperature": 0.6})
        self.assertNotIn("extra_body", options)

    def test_chat_adapter_slices_tall_pdp_before_sending_to_model(self):
        user = get_user_model().objects.create_user("slice-adapter", password="12345678")
        project = Project.objects.create(name="切片适配器", owner=user)
        source = PdpSource.objects.create(
            project=project,
            original_name="tall-pdp.png",
            file=SimpleUploadedFile("tall-pdp.png", valid_png_bytes(720, 4200), content_type="image/png"),
        )
        adapter = OpenAIDiagnosisAdapter(client=SimpleNamespace(), runtime_config={
            "model_name": "mimo-v2.5",
            "protocol": "chat_completions",
        })
        rules = ScoringStandard.objects.get(version="pdp-v5").rules
        messages = adapter._chat_input_content(source, {"business_context": {}, "scoring_rules": rules})
        content = messages[1]["content"]
        self.assertEqual(len(content), 4)  # one instruction + three 1400px slices
        self.assertIn("3 个连续切片", content[0]["text"])
        self.assertTrue(all(item["image_url"]["url"].startswith("data:image/jpeg;base64,") for item in content[1:]))
