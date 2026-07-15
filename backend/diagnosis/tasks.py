import hashlib
import time

from celery import shared_task
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from .adapters import get_diagnosis_adapter
from .models import DiagnosisJob, DiagnosisVersion, ModelRun, ModuleAssessment, PageEvidence, PdpSource, Project
from .scoring import apply_evidence_guards, calculate_assessments


def _update_job(job_id, *, status="processing", stage, progress):
    DiagnosisJob.objects.filter(pk=job_id).update(status=status, stage=stage, progress=progress)


def _source_fingerprint(source):
    if source.content_sha256:
        return source.content_sha256
    digest = hashlib.sha256()
    with source.file.open("rb") as source_file:
        for chunk in iter(lambda: source_file.read(1024 * 1024), b""):
            digest.update(chunk)
    fingerprint = digest.hexdigest()
    PdpSource.objects.filter(pk=source.pk).update(content_sha256=fingerprint)
    source.content_sha256 = fingerprint
    return fingerprint


def _reusable_result(job, adapter, fingerprint):
    """Reuse a completed identical diagnosis to make reruns reproducible.

    A cache hit is scoped to identical bytes, scoring-standard version, adapter,
    model and prompt.  A new scoring version is still created for the project;
    only the non-deterministic remote model call is skipped.
    """
    cached = DiagnosisJob.objects.filter(
        status="completed",
        source__content_sha256=fingerprint,
        scoring_standard=job.scoring_standard,
        adapter=adapter.provider,
        model_name=adapter.model_name,
        model_runs__status="succeeded",
        model_runs__prompt_version=adapter.prompt_version,
    ).exclude(pk=job.pk).prefetch_related("assessments", "evidence").order_by("-completed_at").first()
    if cached is None:
        return None
    return {
        "modules": [{
            "module_code": item.module_code,
            "coefficient": float(item.coefficient),
            "judgment": item.judgment,
            "confidence": float(item.confidence),
        } for item in cached.assessments.all()],
        "evidence": [{
            "module_code": item.module_code,
            "page_index": item.page_index,
            "bbox": item.bbox,
            "evidence_type": item.evidence_type,
            "ocr_text": item.ocr_text,
            "reason": item.model_reason,
            "confidence": float(item.confidence),
        } for item in cached.evidence.all()],
        "usage": {"mode": "reused_identical_analysis", "external_api": False, "source_job_id": cached.id},
        "request_id": f"reused:{cached.id}",
    }


def _public_error(error):
    raw = str(error)
    if "payload too large" in raw.lower() or "载荷过大" in raw:
        return "MODEL_PAYLOAD_TOO_LARGE", "上传图片尺寸或内容过大，系统已停止生成评分。请重新上传；系统将自动使用压缩切片重试。"
    if "502" in raw or "bad gateway" in raw.lower() or "cloudflare" in raw.lower():
        return "MODEL_GATEWAY_UNAVAILABLE", "AI 模型服务暂时不可用（网关 502），本次未生成评分。请稍后重试；系统不会写入不完整的评分版本。"
    return error.__class__.__name__, raw[:1200]


def _is_retryable_model_error(error):
    raw = str(error).lower()
    return any(token in raw for token in ("502", "bad gateway", "cloudflare", "429", "rate limit", "timeout", "temporarily unavailable"))


@shared_task(bind=True, name="diagnosis.run_diagnosis_job", max_retries=2)
def run_diagnosis_job(self, job_id):
    job = DiagnosisJob.objects.select_related("source", "project", "scoring_standard", "created_by").get(pk=job_id)
    started = time.monotonic()
    adapter = get_diagnosis_adapter(job.adapter)
    model_run = ModelRun.objects.create(
        job=job,
        provider=adapter.provider,
        model_name=adapter.model_name,
        prompt_version=adapter.prompt_version,
        status="running",
    )
    DiagnosisJob.objects.filter(pk=job_id).update(
        status="processing",
        stage="parsing",
        progress=8,
        started_at=timezone.now(),
        model_name=adapter.model_name,
        error_code="",
        error_message="",
    )
    try:
        for stage, progress in (("parsing", 18), ("slicing_ocr", 42), ("module_mapping", 68)):
            _update_job(job_id, stage=stage, progress=progress)
            time.sleep(0.18)

        fingerprint = _source_fingerprint(job.source)
        result = _reusable_result(job, adapter, fingerprint)
        if result is None:
            result = adapter.analyze(
                source=job.source,
                context=job.context,
                scoring_rules=job.scoring_standard.rules,
            )
        _update_job(job_id, stage="scoring", progress=84)
        trusted_suggestions = apply_evidence_guards(
            result["modules"], result.get("evidence", []), job.scoring_standard.rules,
        )
        modules, total_score, overall_rating = calculate_assessments(trusted_suggestions, job.scoring_standard.rules)

        with transaction.atomic():
            locked_project = Project.objects.select_for_update().get(pk=job.project_id)
            job = DiagnosisJob.objects.select_for_update().get(pk=job_id)
            job.evidence.all().delete()
            job.assessments.all().delete()
            evidence_by_module = {}
            for item in result.get("evidence", []):
                evidence = PageEvidence.objects.create(
                    job=job,
                    module_code=item["module_code"],
                    page_index=item.get("page_index", 0),
                    bbox=item.get("bbox", {}),
                    evidence_type=item.get("evidence_type", "page_region"),
                    ocr_text=item.get("ocr_text", ""),
                    model_reason=item.get("reason", ""),
                    confidence=item.get("confidence", 0),
                )
                evidence_by_module.setdefault(item["module_code"], []).append(evidence.id)

            snapshot_modules = []
            for module in modules:
                ModuleAssessment.objects.create(
                    job=job,
                    module_code=module["code"],
                    module_name=module["name"],
                    weight=module["weight"],
                    coefficient=module["coefficient"],
                    score=module["score"],
                    maturity=module["maturity"],
                    judgment=module["judgment"],
                    confidence=module["confidence"],
                    auto_confirmed=True,
                )
                snapshot_modules.append({
                    **module,
                    "evidence_ids": evidence_by_module.get(module["code"], []),
                })

            latest = DiagnosisVersion.objects.filter(project=locked_project).aggregate(value=Max("version"))["value"] or 0
            diagnosis = DiagnosisVersion.objects.create(
                project=locked_project,
                source=job.source,
                version=latest + 1,
                total_score=total_score,
                overall_rating=overall_rating,
                modules=snapshot_modules,
                scoring_standard_version=job.scoring_standard.version,
                confirmation_mode="ai_auto",
                status="locked",
                created_by=job.created_by,
            )
            job.locked_version = diagnosis
            job.status = "completed"
            job.stage = "completed"
            job.progress = 100
            job.completed_at = timezone.now()
            job.save(update_fields=["locked_version", "status", "stage", "progress", "completed_at", "updated_at"])
            PdpSource.objects.filter(pk=job.source_id).update(status="diagnosed")

        model_run.status = "succeeded"
        model_run.usage = result.get("usage", {})
        model_run.request_id = result.get("request_id", "")
        model_run.duration_ms = int((time.monotonic() - started) * 1000)
        model_run.save(update_fields=["status", "usage", "request_id", "duration_ms"])
        return diagnosis.id
    except Exception as error:
        error_code, public_message = _public_error(error)
        if _is_retryable_model_error(error) and self.request.retries < self.max_retries:
            model_run.status = "retrying"
            model_run.error_message = str(error)
            model_run.duration_ms = int((time.monotonic() - started) * 1000)
            model_run.save(update_fields=["status", "error_message", "duration_ms"])
            DiagnosisJob.objects.filter(pk=job_id).update(
                status="queued",
                stage="retrying",
                progress=18,
                error_code=error_code,
                error_message="AI 模型服务短暂波动，系统正在自动重试（最多 2 次）。",
            )
            raise self.retry(exc=error, countdown=10 * (self.request.retries + 1))
        model_run.status = "failed"
        model_run.error_message = str(error)
        model_run.duration_ms = int((time.monotonic() - started) * 1000)
        model_run.save(update_fields=["status", "error_message", "duration_ms"])
        DiagnosisJob.objects.filter(pk=job_id).update(
            status="failed",
            stage="failed",
            error_code=error_code,
            error_message=public_message,
            completed_at=timezone.now(),
        )
        PdpSource.objects.filter(pk=job.source_id).update(status="failed")
        raise
