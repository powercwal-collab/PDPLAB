import json
from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import AiModelSettings, DiagnosisJob, DiagnosisVersion, PdpSkillSettings, PdpSource, Project, ScoringStandard
from .adapters.openai import EvidenceSuggestion, ModuleSuggestion, OpenAIDiagnosisAdapter, PdpDiagnosisOutput
from .runtime_config import get_runtime_integration_config
from .scoring import map_overall_rating
from .skill_runtime import _validate_remote_rules
from .tasks import run_diagnosis_job


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

    def test_diagnosis_config_reports_skill_link_and_active_adapter(self):
        user = get_user_model().objects.create_user("config-user", password="12345678")
        self.client.force_login(user)
        response = self.client.get(reverse("diagnosis-config"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["source_skill"], "pdp-detail-page-methodology")
        self.assertEqual(response.json()["scoring_standard_version"], "pdp-v1")
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
        rules = ScoringStandard.objects.get(version="pdp-v1").rules
        _validate_remote_rules(rules)
        self.assertEqual(rules["coefficients"], {"弱": 0, "中": 0.5, "强": 1})
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
        project = Project.objects.create(name="Nike Kids", brand="Nike", category="童鞋")
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
        self.assertIn("/media/pdp_sources/", result["cover_url"])
        self.assertTrue(result["cover_url"].endswith(".png"))

    def test_register_login_and_logout(self):
        register = self.client.post(
            reverse("auth-register"),
            data='{"username":"designer","nickname":"设计师","email":"designer@example.com","password":"12345678"}',
            content_type="application/json",
        )
        self.assertEqual(register.status_code, 201)
        self.client.post(reverse("auth-logout"))
        login = self.client.post(
            reverse("auth-login"),
            data='{"username":"designer","password":"12345678"}',
            content_type="application/json",
        )
        self.assertEqual(login.status_code, 200)

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
        project = Project.objects.create(name="上传验证")
        upload = self.client.post(
            reverse("uploads"),
            {"project_id": project.id, "file": SimpleUploadedFile("pdp.png", b"fake-png", content_type="image/png")},
        )
        self.assertEqual(upload.status_code, 201)
        self.assertEqual(upload.json()["source"]["original_name"], "pdp.png")

    def test_complete_diagnosis_is_versioned_and_incomplete_diagnosis_is_rejected(self):
        user = get_user_model().objects.create_user("reviewer", password="12345678")
        self.client.force_login(user)
        project = Project.objects.create(name="评分验证")
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
        self.assertEqual(float(diagnosis.total_score), 58.5)
        self.assertEqual(float(diagnosis.overall_rating), 4.5)
        self.client.force_login(user)
        history = self.client.get(reverse("diagnosis-list"), {"project_id": project.id})
        serialized_module = history.json()["results"][0]["modules"][0]
        self.assertEqual(serialized_module["judgment"], "有产品封面与基础主张，但首屏缺少更清晰的系列定位与利益点排序。")
        self.assertEqual(len(serialized_module["evidence"]), 1)
        self.assertEqual(serialized_module["evidence"][0]["model_reason"], serialized_module["judgment"])

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
                ModuleSuggestion(module_code=item["code"], coefficient=0.5, judgment=f"{item['name']} 证据中等", confidence=0.86)
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
            file=SimpleUploadedFile("openai.png", b"fake-png", content_type="image/png"),
        )
        result = OpenAIDiagnosisAdapter(client=fake_client).analyze(source=source, context={"channel": "tmall"}, scoring_rules=rules)
        self.assertEqual(len(result["modules"]), 11)
        self.assertEqual(len(result["evidence"]), 11)
        self.assertEqual(result["request_id"], "resp_test")
        self.assertTrue(result["usage"]["external_api"])
        self.assertEqual(fake_client.files.purpose, "vision")
        self.assertEqual(fake_client.files.deleted, ["file_test"])
        self.assertFalse(fake_client.responses.kwargs["store"])

    def test_chat_completions_adapter_uses_data_url_and_structured_output(self):
        rules = ScoringStandard.objects.get(version="pdp-v1").rules
        parsed = PdpDiagnosisOutput(
            modules=[
                ModuleSuggestion(module_code=item["code"], coefficient=0.5, judgment=f"{item['name']} 证据中等", confidence=0.86)
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
            file=SimpleUploadedFile("chat.png", b"fake-png", content_type="image/png"),
        )
        adapter = OpenAIDiagnosisAdapter(client=fake_client, runtime_config={
            "model_name": "mimo-v2.5",
            "protocol": "chat_completions",
        })
        result = adapter.analyze(source=source, context={"channel": "tmall"}, scoring_rules=rules)
        content = completions.kwargs["messages"][1]["content"]
        self.assertTrue(content[1]["image_url"]["url"].startswith("data:image/png;base64,"))
        self.assertEqual(len(result["modules"]), 11)
        self.assertEqual(len(result["evidence"]), 11)
        self.assertEqual(result["usage"]["mode"], "chat_completions")
