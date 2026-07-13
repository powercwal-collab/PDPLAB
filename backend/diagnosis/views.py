import json

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.db import transaction
from django.db.models import Max, Q
from django.http import JsonResponse
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from .models import (
    DiagnosisJob,
    DiagnosisVersion,
    NotificationPreference,
    PdpSource,
    Project,
    ScoringStandard,
)
from .scoring import DEFAULT_SCORING_RULES, map_overall_rating
from .tasks import run_diagnosis_job
from .adapters import get_diagnosis_adapter
from .runtime_config import get_runtime_integration_config
from .skill_runtime import resolve_scoring_standard


def home(request):
    return redirect("http://127.0.0.1:4173/")


def health(request):
    return JsonResponse({"status": "ok", "service": "pdp-lab-api"})


def diagnosis_config(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "请先登录"}, status=401)
    if request.method != "GET":
        return JsonResponse({"error": "仅支持 GET 请求"}, status=405)
    config = get_runtime_integration_config()
    active_adapter = config["adapter"]
    if active_adapter == "auto":
        active_adapter = "openai" if config["api_key"] else "mock"
    if config["skill_mode"] == "built_in":
        standard = ScoringStandard.objects.filter(version=DEFAULT_SCORING_RULES["version"]).first()
    else:
        standard = ScoringStandard.objects.filter(is_active=True).first()
    rules = standard.rules if standard else DEFAULT_SCORING_RULES
    return JsonResponse({
        "requested_adapter": config["adapter"],
        "active_adapter": active_adapter,
        "ai_protocol": config["protocol"],
        "model_name": config["model_name"] if active_adapter == "openai" else "pdp-methodology-mock-v1",
        "configured_model_name": config["model_name"],
        "openai_configured": bool(config["api_key"]),
        "mock_execution_allowed": settings.PDP_ALLOW_MOCK_DIAGNOSIS,
        "scoring_standard_version": standard.version if standard else DEFAULT_SCORING_RULES["version"],
        "source_skill": rules.get("source_skill", "pdp-detail-page-methodology"),
        "source_mode": rules.get("source_mode", "versioned_runtime_rules"),
        "source_revision": rules.get("source_revision", ""),
        "scoring_rules": {
            "version": rules.get("version", DEFAULT_SCORING_RULES["version"]),
            "coefficients": rules.get("coefficients", DEFAULT_SCORING_RULES["coefficients"]),
            "maturity_definitions": rules.get("maturity_definitions", DEFAULT_SCORING_RULES["maturity_definitions"]),
            "judgment_order": rules.get("judgment_order", DEFAULT_SCORING_RULES["judgment_order"]),
            "modules": rules.get("modules", DEFAULT_SCORING_RULES["modules"]),
            "star_bands": rules.get("star_bands", DEFAULT_SCORING_RULES["star_bands"]),
        },
        "confirmation_mode": "ai_auto",
        "config_source": config["source"],
        "ai_config_source": config["ai_config_source"],
        "skill_config_source": config["skill_config_source"],
        "skill_mode": config["skill_mode"],
        "skill_endpoint_url": config["skill_endpoint_url"],
    })


def _accessible_projects(request):
    return Project.objects.filter(Q(owner=request.user) | Q(owner__isnull=True))


def _normalized_diagnosis_rating(diagnosis):
    if diagnosis is None:
        return None
    standard = ScoringStandard.objects.filter(version=diagnosis.scoring_standard_version).first()
    rules = standard.rules if standard else DEFAULT_SCORING_RULES
    return float(map_overall_rating(diagnosis.total_score, rules))


def _serialize_project(project):
    diagnoses = list(project.diagnoses.all())
    sources = list(project.sources.all())
    latest_diagnosis = diagnoses[0] if diagnoses else None
    cover_source = None
    if latest_diagnosis and latest_diagnosis.source_id:
        cover_source = next((source for source in sources if source.id == latest_diagnosis.source_id), None)
    cover_source = cover_source or (sources[0] if sources else None)
    cover_url = ""
    if cover_source and cover_source.original_name.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
        cover_url = cover_source.file.url
    normalized_rating = _normalized_diagnosis_rating(latest_diagnosis)
    activity_dates = [project.updated_at]
    if latest_diagnosis:
        activity_dates.append(latest_diagnosis.created_at)
    if cover_source:
        activity_dates.append(cover_source.created_at)
    return {
        "id": project.id,
        "name": project.name,
        "brand": project.brand,
        "category": project.category,
        "updated_at": max(activity_dates).isoformat(),
        "latest_score": float(latest_diagnosis.total_score) if latest_diagnosis else None,
        "overall_rating": normalized_rating,
        "diagnosis_version": latest_diagnosis.version if latest_diagnosis else None,
        "score_label": f"{normalized_rating:g} 星" if latest_diagnosis else "待诊断",
        "cover_url": cover_url,
        "source_name": cover_source.original_name if cover_source else "",
    }


@csrf_exempt
def project_list(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "请先登录"}, status=401)
    if request.method == "GET":
        projects = _accessible_projects(request).prefetch_related("diagnoses", "sources")
        return JsonResponse({"results": [_serialize_project(project) for project in projects]})
    if request.method == "POST":
        data = _payload(request)
        name = data.get("name", "").strip()
        if not name:
            return JsonResponse({"error": "项目名称不能为空"}, status=400)
        project = Project.objects.create(owner=request.user, name=name, brand=data.get("brand", "").strip(), category=data.get("category", "").strip())
        project = Project.objects.prefetch_related("diagnoses", "sources").get(pk=project.pk)
        return JsonResponse({"project": _serialize_project(project)}, status=201)
    return JsonResponse({"error": "不支持的请求方式"}, status=405)


def _payload(request):
    try:
        return json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return {}


@csrf_exempt
def login_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "仅支持 POST 请求"}, status=405)
    data = _payload(request)
    user = authenticate(request, username=data.get("username", ""), password=data.get("password", ""))
    if user is None:
        return JsonResponse({"error": "账号或密码不正确"}, status=400)
    login(request, user)
    return JsonResponse({"user": {"username": user.username, "nickname": user.first_name, "email": user.email}})


@csrf_exempt
def register_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "仅支持 POST 请求"}, status=405)
    data = _payload(request)
    username = data.get("username", "").strip()
    password = data.get("password", "")
    email = data.get("email", "").strip()
    if len(password) < 8:
        return JsonResponse({"error": "密码至少需要 8 位字符"}, status=400)
    User = get_user_model()
    if not username or User.objects.filter(username=username).exists():
        return JsonResponse({"error": "用户名为空或已被使用"}, status=400)
    user = User.objects.create_user(username=username, email=email, password=password, first_name=data.get("nickname", "").strip())
    login(request, user)
    return JsonResponse({"user": {"username": user.username, "nickname": user.first_name, "email": user.email}}, status=201)


@csrf_exempt
def logout_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "仅支持 POST 请求"}, status=405)
    logout(request)
    return JsonResponse({"status": "ok"})


def me_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({"authenticated": False}, status=401)
    return JsonResponse({"authenticated": True, "user": {"username": request.user.username, "nickname": request.user.first_name, "email": request.user.email}})


@csrf_exempt
def profile_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "请先登录"}, status=401)
    if request.method == "GET":
        return JsonResponse({"username": request.user.username, "nickname": request.user.first_name, "email": request.user.email})
    if request.method in {"POST", "PATCH"}:
        data = _payload(request)
        request.user.first_name = data.get("nickname", request.user.first_name).strip()
        request.user.email = data.get("email", request.user.email).strip()
        request.user.save(update_fields=["first_name", "email"])
        return JsonResponse({"username": request.user.username, "nickname": request.user.first_name, "email": request.user.email})
    return JsonResponse({"error": "不支持的请求方式"}, status=405)


@csrf_exempt
def preference_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "请先登录"}, status=401)
    preference, _ = NotificationPreference.objects.get_or_create(user=request.user)
    if request.method in {"POST", "PATCH"}:
        data = _payload(request)
        for field in ("task_updates", "product_updates", "weekly_report"):
            if field in data:
                setattr(preference, field, bool(data[field]))
        preference.save()
    if request.method not in {"GET", "POST", "PATCH"}:
        return JsonResponse({"error": "不支持的请求方式"}, status=405)
    return JsonResponse({"task_updates": preference.task_updates, "product_updates": preference.product_updates, "weekly_report": preference.weekly_report})


@csrf_exempt
def upload_source(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "请先登录"}, status=401)
    if request.method != "POST":
        return JsonResponse({"error": "仅支持 POST 请求"}, status=405)
    project_id = request.POST.get("project_id")
    uploaded = request.FILES.get("file")
    if not project_id or uploaded is None:
        return JsonResponse({"error": "项目和文件不能为空"}, status=400)
    if uploaded.size > 30 * 1024 * 1024:
        return JsonResponse({"error": "文件不能超过 30MB"}, status=400)
    if uploaded.content_type not in {"image/png", "image/jpeg", "application/pdf"}:
        return JsonResponse({"error": "仅支持 PNG、JPG 或 PDF 文件"}, status=400)
    try:
        project = _accessible_projects(request).get(pk=project_id)
    except Project.DoesNotExist:
        return JsonResponse({"error": "项目不存在"}, status=404)
    source = PdpSource.objects.create(project=project, file=uploaded, original_name=uploaded.name)
    return JsonResponse({"source": {"id": source.id, "project_id": project.id, "original_name": source.original_name, "status": source.status}}, status=201)


def _serialize_diagnosis(diagnosis):
    modules = [dict(module) for module in diagnosis.modules]
    try:
        source_job = diagnosis.source_job
    except DiagnosisJob.DoesNotExist:
        source_job = None
    if source_job is not None:
        evidence_by_module = {}
        for evidence in source_job.evidence.all():
            evidence_by_module.setdefault(evidence.module_code, []).append({
                "id": evidence.id,
                "page_index": evidence.page_index,
                "bbox": evidence.bbox,
                "evidence_type": evidence.evidence_type,
                "ocr_text": evidence.ocr_text,
                "image_url": evidence.crop_image.url if evidence.crop_image else source_job.source.file.url,
                "model_reason": evidence.model_reason,
                "confidence": float(evidence.confidence),
            })
        assessments = {assessment.module_code: assessment for assessment in source_job.assessments.all()}
        for module in modules:
            module_code = module.get("code") or module.get("module_code")
            assessment = assessments.get(module_code)
            if assessment is not None and not module.get("judgment"):
                module["judgment"] = assessment.judgment
            module["evidence"] = evidence_by_module.get(module_code, [])
    return {
        "id": diagnosis.id,
        "project_id": diagnosis.project_id,
        "project_name": diagnosis.project.name,
        "version": diagnosis.version,
        "total_score": float(diagnosis.total_score),
        "overall_rating": _normalized_diagnosis_rating(diagnosis),
        "modules": modules,
        "status": diagnosis.status,
        "confirmation_mode": diagnosis.confirmation_mode,
        "scoring_standard_version": diagnosis.scoring_standard_version,
        "created_by": diagnosis.created_by.username if diagnosis.created_by else "",
        "created_at": diagnosis.created_at.isoformat(),
    }


@csrf_exempt
def diagnosis_list(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "请先登录"}, status=401)

    if request.method == "GET":
        diagnoses = DiagnosisVersion.objects.select_related(
            "project",
            "created_by",
            "source",
            "source_job",
            "source_job__source",
        ).prefetch_related(
            "source_job__assessments",
            "source_job__evidence",
        ).filter(project__in=_accessible_projects(request))
        project_id = request.GET.get("project_id")
        if project_id:
            diagnoses = diagnoses.filter(project_id=project_id)
        return JsonResponse({"results": [_serialize_diagnosis(item) for item in diagnoses]})

    if request.method != "POST":
        return JsonResponse({"error": "不支持的请求方式"}, status=405)

    data = _payload(request)
    try:
        project = _accessible_projects(request).get(pk=data.get("project_id"))
    except (Project.DoesNotExist, TypeError, ValueError):
        return JsonResponse({"error": "项目不存在"}, status=404)

    modules = data.get("modules")
    if not isinstance(modules, list) or len(modules) != 11:
        return JsonResponse({"error": "必须提交完整的 11 个评分模块"}, status=400)
    if any(not isinstance(module, dict) or not module.get("checked") for module in modules):
        return JsonResponse({"error": "请先确认全部评分模块"}, status=400)

    allowed_maturity = {"弱", "中", "强"}
    calculated_total = 0.0
    for module in modules:
        try:
            score = float(module["score"])
            maximum = float(module["max"])
        except (KeyError, TypeError, ValueError):
            return JsonResponse({"error": "模块得分格式不正确"}, status=400)
        if module.get("maturity") not in allowed_maturity or maximum <= 0 or score < 0 or score > maximum:
            return JsonResponse({"error": "模块成熟度或得分超出范围"}, status=400)
        calculated_total += score

    submitted_total = data.get("total_score")
    try:
        submitted_total = float(submitted_total)
    except (TypeError, ValueError):
        return JsonResponse({"error": "总分格式不正确"}, status=400)
    if abs(calculated_total - submitted_total) > 0.01:
        return JsonResponse({"error": "总分与模块得分不一致"}, status=400)

    overall_rating = map_overall_rating(submitted_total)
    with transaction.atomic():
        latest = DiagnosisVersion.objects.filter(project=project).aggregate(value=Max("version"))["value"] or 0
        diagnosis = DiagnosisVersion.objects.create(
            project=project,
            version=latest + 1,
            total_score=submitted_total,
            overall_rating=overall_rating,
            modules=modules,
            scoring_standard_version="pdp-v1",
            confirmation_mode="manual",
            status="locked",
            created_by=request.user,
        )
    return JsonResponse({"diagnosis": _serialize_diagnosis(diagnosis)}, status=201)


@csrf_exempt
def diagnosis_detail(request, diagnosis_id):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "请先登录"}, status=401)
    if request.method != "DELETE":
        return JsonResponse({"error": "仅支持 DELETE 请求"}, status=405)

    try:
        diagnosis = DiagnosisVersion.objects.select_related("project").get(
            pk=diagnosis_id,
            project__in=_accessible_projects(request),
        )
    except DiagnosisVersion.DoesNotExist:
        return JsonResponse({"error": "评分记录不存在"}, status=404)

    project = diagnosis.project
    deleted_version = diagnosis.version
    diagnosis.delete()
    latest = DiagnosisVersion.objects.select_related(
        "project",
        "created_by",
        "source",
        "source_job",
        "source_job__source",
    ).prefetch_related(
        "source_job__assessments",
        "source_job__evidence",
    ).filter(project=project).first()
    return JsonResponse({
        "deleted_id": diagnosis_id,
        "deleted_version": deleted_version,
        "latest_diagnosis": _serialize_diagnosis(latest) if latest else None,
    })


def _serialize_job(job, include_result=False):
    data = {
        "id": job.id,
        "project_id": job.project_id,
        "source_id": job.source_id,
        "source_name": job.source.original_name,
        "source_url": job.source.file.url,
        "status": job.status,
        "stage": job.stage,
        "progress": job.progress,
        "adapter": job.adapter,
        "model_name": job.model_name,
        "context": job.context,
        "error_code": job.error_code,
        "error_message": job.error_message,
        "created_at": job.created_at.isoformat(),
        "updated_at": job.updated_at.isoformat(),
    }
    if job.locked_version_id:
        data["diagnosis"] = _serialize_diagnosis(job.locked_version)
    if include_result:
        evidence_by_module = {}
        for evidence in job.evidence.all():
            evidence_by_module.setdefault(evidence.module_code, []).append({
                "id": evidence.id,
                "page_index": evidence.page_index,
                "bbox": evidence.bbox,
                "evidence_type": evidence.evidence_type,
                "ocr_text": evidence.ocr_text,
                "image_url": evidence.crop_image.url if evidence.crop_image else job.source.file.url,
                "model_reason": evidence.model_reason,
                "confidence": float(evidence.confidence),
            })
        data["assessments"] = [{
            "module_code": assessment.module_code,
            "name": assessment.module_name,
            "max": float(assessment.weight),
            "weight": float(assessment.weight),
            "coefficient": float(assessment.coefficient),
            "score": float(assessment.score),
            "maturity": assessment.maturity,
            "judgment": assessment.judgment,
            "confidence": float(assessment.confidence),
            "checked": assessment.auto_confirmed,
            "evidence": evidence_by_module.get(assessment.module_code, []),
        } for assessment in job.assessments.all()]
    return data


@csrf_exempt
def diagnosis_job_list(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "请先登录"}, status=401)
    if request.method == "GET":
        jobs = DiagnosisJob.objects.select_related("project", "source", "locked_version").filter(project__in=_accessible_projects(request))
        project_id = request.GET.get("project_id")
        if project_id:
            jobs = jobs.filter(project_id=project_id)
        return JsonResponse({"results": [_serialize_job(job) for job in jobs[:50]]})
    if request.method != "POST":
        return JsonResponse({"error": "不支持的请求方式"}, status=405)
    data = _payload(request)
    try:
        source = PdpSource.objects.select_related("project").get(
            pk=data.get("source_id"),
            project__in=_accessible_projects(request),
        )
    except (PdpSource.DoesNotExist, TypeError, ValueError):
        return JsonResponse({"error": "PDP 文件不存在或无权访问"}, status=404)
    try:
        standard = resolve_scoring_standard()
        adapter = get_diagnosis_adapter()
    except RuntimeError as error:
        return JsonResponse({"error": str(error)}, status=503)
    if adapter.provider == "mock" and not settings.PDP_ALLOW_MOCK_DIAGNOSIS:
        return JsonResponse({
            "code": "MOCK_ADAPTER_ACTIVE",
            "error": "当前为 Mock 模式，系统已停止创建评分，避免生成未经真实模型分析的信息。请先配置并验证可用的模型 API。",
        }, status=503)
    job = DiagnosisJob.objects.create(
        project=source.project,
        source=source,
        scoring_standard=standard,
        created_by=request.user,
        adapter=adapter.provider,
        model_name=adapter.model_name,
        context=data.get("context") if isinstance(data.get("context"), dict) else {},
    )
    PdpSource.objects.filter(pk=source.id).update(status="queued")
    transaction.on_commit(lambda: run_diagnosis_job.delay(job.id))
    return JsonResponse({"job": _serialize_job(job)}, status=202)


@csrf_exempt
def diagnosis_job_detail(request, job_id):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "请先登录"}, status=401)
    if request.method != "GET":
        return JsonResponse({"error": "仅支持 GET 请求"}, status=405)
    try:
        job = DiagnosisJob.objects.select_related("project", "source", "locked_version", "locked_version__project", "locked_version__created_by").prefetch_related("assessments", "evidence").get(
            pk=job_id,
            project__in=_accessible_projects(request),
        )
    except DiagnosisJob.DoesNotExist:
        return JsonResponse({"error": "诊断任务不存在"}, status=404)
    return JsonResponse({"job": _serialize_job(job, include_result=True)})
