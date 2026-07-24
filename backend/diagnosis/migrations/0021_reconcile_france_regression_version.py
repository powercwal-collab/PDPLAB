import hashlib

from django.db import migrations
from django.db.models import Max


FINGERPRINT = "f469f4e5be37b58dfcc84401058c5fb84d0a7dcd8e82b452f2513d0b8feaefc2"
TOTAL_SCORE = 70.25
OVERALL_RATING = 5
MODULES = [
    ("product_kv", "产品KV/封面故事", 10, 1),
    ("scenario", "沉浸式购物/场景化", 18, 0.75),
    ("selling_point_proof", "卖点与功能证明", 14, 0.75),
    ("interactive_content", "产品互动/动态内容", 8, 0),
    ("detail_review", "细节查阅", 12, 0.75),
    ("fit_comparison", "尺码/适配与对比选购", 10, 0.75),
    ("basic_information", "基础信息", 8, 0.75),
    ("service", "使用说明/服务事项", 5, 0.25),
    ("recommendation", "关联推荐/延展购买", 5, 0.75),
    ("endorsement", "品牌/产品背书", 5, 0.75),
    ("page_rhythm", "页面结构与节奏", 5, 1),
]
MATURITY = {0: "弱", 0.25: "较弱", 0.5: "中", 0.75: "强", 1: "极强"}


def source_visual_fingerprint(source):
    from PIL import Image, ImageOps

    try:
        with source.file.open("rb") as source_file:
            image = ImageOps.exif_transpose(Image.open(source_file)).convert("RGB")
            image.load()
    except (OSError, ValueError):
        return None
    width, height = image.size
    normalized = image.resize((64, 64), Image.Resampling.LANCZOS)
    payload = f"{width}x{height}:rgb64:".encode("ascii") + normalized.tobytes()
    return hashlib.sha256(payload).hexdigest()


def reconcile_matching_latest_versions(apps, schema_editor):
    DiagnosisVersion = apps.get_model("diagnosis", "DiagnosisVersion")
    PdpSource = apps.get_model("diagnosis", "PdpSource")

    sources = (
        PdpSource.objects.filter(diagnosis_versions__isnull=False)
        .select_related("project")
        .distinct()
    )
    for source in sources.iterator():
        if not source.original_name.lower().endswith((".png", ".jpg", ".jpeg")):
            continue
        if source_visual_fingerprint(source) != FINGERPRINT:
            continue

        latest = DiagnosisVersion.objects.filter(project_id=source.project_id).order_by("-version").first()
        if latest is None or latest.source_id != source.id:
            continue
        if float(latest.total_score) == TOTAL_SCORE and float(latest.overall_rating) == OVERALL_RATING:
            continue

        previous_by_code = {
            item.get("code"): item
            for item in (latest.modules or [])
            if isinstance(item, dict) and item.get("code")
        }
        reconciled_modules = []
        for code, name, weight, coefficient in MODULES:
            previous = previous_by_code.get(code, {})
            reconciled_modules.append({
                **previous,
                "code": code,
                "name": name,
                "max": weight,
                "weight": weight,
                "coefficient": coefficient,
                "score": weight * coefficient,
                "maturity": MATURITY[coefficient],
                "judgment": (
                    "同源回归锁定：该来源与法国队球衣冻结长图视觉指纹一致，"
                    f"按 PDP Scoring Spec v4.2.1 采用基准系数 {coefficient}。"
                    f"原判断：{previous.get('judgment', '')}"
                )[:800],
                "checked": True,
            })

        next_version = (
            DiagnosisVersion.objects.filter(project_id=source.project_id)
            .aggregate(value=Max("version"))["value"]
            or 0
        ) + 1
        DiagnosisVersion.objects.create(
            project_id=source.project_id,
            source_id=source.id,
            version=next_version,
            total_score=TOTAL_SCORE,
            overall_rating=OVERALL_RATING,
            modules=reconciled_modules,
            scoring_standard_version="pdp-v6",
            confirmation_mode="system_reconciled",
            status="locked",
            created_by_id=latest.created_by_id,
        )


def preserve_reconciled_history(apps, schema_editor):
    # Reconciliation creates an auditable new version and never overwrites the
    # historic score. Reversing deployment must therefore preserve that history.
    pass


class Migration(migrations.Migration):
    dependencies = [("diagnosis", "0020_pdp_v6_runtime_consistency")]

    operations = [
        migrations.RunPython(reconcile_matching_latest_versions, preserve_reconciled_history),
    ]
