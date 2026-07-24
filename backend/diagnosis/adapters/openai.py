import base64
from io import BytesIO
import json
import math
from pathlib import Path
from typing import Literal

from django.conf import settings
from openai import OpenAI
from PIL import Image, ImageOps
from pydantic import BaseModel, Field

from .base import DiagnosisModelAdapter


class ModuleSuggestion(BaseModel):
    module_code: str
    coefficient: Literal[0, 0.25, 0.5, 0.75, 1]
    information_level: Literal["none", "shallow", "complete", "proven"]
    visual_tier: Literal["none", "t2", "t1", "t0"]
    integration: Literal["isolated", "matched"]
    judgment: str = Field(min_length=4, max_length=800)
    confidence: float = Field(ge=0, le=1)


class EvidenceSuggestion(BaseModel):
    module_code: str
    page_index: int = Field(ge=0)
    bbox: dict[str, float] = Field(default_factory=dict)
    evidence_type: Literal[
        "missing_content", "generic_or_decorative", "empty_shell", "template_block", "generic_icon_row",
        "hero_copy_only", "logo_only", "studio_model_view", "product_hero_visual", "campaign_cover",
        "real_use_scene", "lifestyle_scene", "sport_scene", "movement_scene", "styling_scene",
        "product_proof", "detail_view", "basic_information", "measurement_method", "fit_advice",
        "model_body_profile", "tryon_feedback", "series_comparison", "size_chart", "body_type_guidance",
        "wearing_preference", "personalized_fit_guidance", "fit_visualization", "service_policy",
        "generic_platform_service", "product_specific_care", "product_specific_return_boundary",
        "tryon_policy", "customization_policy", "product_warranty", "installation_guidance",
        "premium_service_proof", "scene_benefit_link",
        "related_product_recommendation", "series_recommendation", "outfit_recommendation", "certification",
        "award", "institutional_endorsement", "technology_source", "attributable_review", "brand_asset_proof",
        "page_structure", "dynamic_demo",
        "designed_model_only", "designed_product_only", "designed_model_product_composite",
        "pagewide_designed_model_product_sequence", "product_3d_structure_explanation",
        "product_specific_art_illustration",
    ] = "missing_content"
    ocr_text: str = ""
    reason: str = Field(min_length=4, max_length=800)
    confidence: float = Field(ge=0, le=1)


class PdpDiagnosisOutput(BaseModel):
    modules: list[ModuleSuggestion]
    evidence: list[EvidenceSuggestion]


class OpenAIDiagnosisAdapter(DiagnosisModelAdapter):
    provider = "openai"
    prompt_version = "pdp-score-openai-v8-full-height-evidence"
    # Preserve long-page text readability by constraining width only. Every
    # resulting vertical slice is sent in order; if the explicit safety limit is
    # exceeded, fail visibly instead of silently shrinking or omitting evidence.
    MAX_IMAGE_WIDTH = 960
    SLICE_HEIGHT = 1400
    MAX_IMAGE_SLICES = 24
    JPEG_QUALITY = 82

    def __init__(self, client=None, runtime_config=None):
        config = runtime_config or {
            "model_name": settings.PDP_MODEL_NAME,
            "protocol": settings.PDP_AI_PROTOCOL,
            "api_key": settings.OPENAI_API_KEY,
            "base_url": settings.OPENAI_BASE_URL,
            "timeout_seconds": settings.OPENAI_TIMEOUT_SECONDS,
        }
        self.model_name = config["model_name"]
        self.protocol = config.get("protocol", "responses")
        if client is not None:
            self.client = client
            return
        if not config["api_key"]:
            raise RuntimeError("OPENAI_API_KEY 未配置，无法使用 OpenAI 诊断适配器")
        kwargs = {
            "api_key": config["api_key"],
            "timeout": config["timeout_seconds"],
            "max_retries": 2,
        }
        if config["base_url"]:
            kwargs["base_url"] = config["base_url"]
        self.client = OpenAI(**kwargs)

    def _instructions(self, scoring_rules):
        modules = [{
            "module_code": item["code"],
            "name": item["name"],
            "weight": item["weight"],
            "strong_standard": item.get("strong_standard", ""),
        } for item in scoring_rules["modules"]]
        return (
            "你是电商 PDP 详情页诊断引擎。仅根据上传文件中可见的内容和用户上下文评估。"
            "对每个模块必须返回且只返回一条结果：0=弱，0.25=较弱，0.5=中，0.75=强，1=极强。"
            "不要计算总分或星级，服务端将用版本化评分规则计算。"
            "每个模块至少返回一条证据；若未观察到对应内容，必须返回一条 missing_content 证据并说明缺口。"
            "用于满足同一模块多个边界条件时，每一种独立 evidence_type 都必须单独返回一条证据，禁止合并成一条泛化证据。"
            "例如尺码表、模特数据、测量方法、版本对比必须分别返回；产品专属护理与退换边界也必须分别返回。"
            "evidence_type 必须从以下枚举中选择，不得使用 page_region 或自造类型："
            "missing_content、generic_or_decorative、empty_shell、template_block、generic_icon_row、hero_copy_only、logo_only、studio_model_view、"
            "product_hero_visual、campaign_cover、real_use_scene、lifestyle_scene、sport_scene、movement_scene、styling_scene、product_proof、detail_view、"
            "basic_information、measurement_method、fit_advice、model_body_profile、tryon_feedback、series_comparison、size_chart、"
            "body_type_guidance、wearing_preference、personalized_fit_guidance、fit_visualization、service_policy、generic_platform_service、"
            "product_specific_care、product_specific_return_boundary、tryon_policy、customization_policy、product_warranty、"
            "installation_guidance、premium_service_proof、scene_benefit_link、"
            "related_product_recommendation、series_recommendation、outfit_recommendation、certification、award、institutional_endorsement、"
            "technology_source、attributable_review、brand_asset_proof、page_structure、dynamic_demo、designed_model_only、designed_product_only、designed_model_product_composite、pagewide_designed_model_product_sequence、product_3d_structure_explanation、product_specific_art_illustration。"
            "强制规则：标题、占位、通用/装饰素材、空壳、通用 icon 行或单独 Logo 不能证明模块存在，系数必须为0。"
            "产品相关文案/口号但缺少产品主导英雄视觉时标 hero_copy_only，最高0.25；有 product_hero_visual 或 campaign_cover 后再按结合质量判断。"
            "白灰底模特、孤立试穿、正背面图标 studio_model_view，若缺少真实场景与信息结合最高0.25；真实使用/运动/生活/穿搭场景才可继续升档。"
            "场景模块即使是高完成度 campaign/editorial 大片，缺少 scene_benefit_link 时最高0.75；系数1还必须覆盖至少两类相关场景，并明确场景中的产品利益。"
            "视觉层级补充：特殊设计的非白底/灰底画面中，模特与产品在同一模块形成有意图的联合构图时标 designed_model_product_composite，可作为 T0 视觉依据；若只有模特或只有单产品，分别标 designed_model_only 或 designed_product_only，即使背景设计特殊也最高为 T1，不能单独支撑极强。"
            "若整页通过连续模块把特殊非白底/灰底的模特画面与产品画面有逻辑地穿插编排，形成统一产品叙事、使用场景或品牌世界，标 pagewide_designed_model_product_sequence，也可作为相关模块的 T0 视觉依据；零散出现、无关联拼接或仅改变背景色不算。"
            "若模块内包含与该产品直接对应的特殊设计图，例如 3D 结构图、完整结构剖析图或技术解释系统，标 product_3d_structure_explanation，可作为 T0 视觉依据；不要求必须与模特同画面，但装饰性 3D、背景特效或与产品无关的结构图不算。"
            "若艺术手绘插图页明确围绕该产品表达结构、功能、使用场景、系列故事或品牌世界，标 product_specific_art_illustration，可作为 T0 视觉依据；通用装饰插画或与具体产品无关的艺术图不算。"
            "推荐模块的颜色、尺码、SKU 选项不是推荐；仅 related_product_recommendation、series_recommendation 或 outfit_recommendation 可计分。"
            "背书模块的单独 Logo 不可计分；必须有认证、机构、科技来源、可归因评价或品牌资产证明。"
            "尺码表必须标 size_chart。尺码模块达到0.75必须有 size_chart，并在模特数据、适配建议、测量方法、版本对比、身型指导或穿着偏好中至少有两类；"
            "版本对比+模特数据+尺码表可计0.75。系数1还需要个性化/身型指导、适配可视化或消费者试穿证据，以及完整版本对比。"
            "服务模块的平台配送、发票、客服时间、通用七天退换标 generic_platform_service，单独出现计0。"
            "产品专属护理、退换限制、试用、定制、质保、安装分别使用对应 evidence_type；只有一类时最高0.25，通用服务与有限专属信息混合最高0.5。"
            "系数1还需要至少三类完整产品专属服务和 premium_service_proof。service_policy 仅保留兼容用途，不可作为产品专属证据。"
            "bbox 使用 0~1 归一化坐标，包含 x/y/width/height；无法定位时可为空对象。"
            "输出必须是单个 JSON 对象，顶层只允许 modules 与 evidence 两个数组，禁止用模块编码作为顶层键。"
            "modules 每项必须包含 module_code、coefficient、information_level、visual_tier、integration、judgment、confidence；"
            "evidence 每项必须包含 module_code、page_index、bbox、evidence_type、ocr_text、reason、confidence。"
            "为避免冗长输出，judgment 与 reason 各不超过120个中文字符，ocr_text 不超过200个字符。"
            "特别注意：weight 是服务端权重，只供你理解重要性，绝对不能填入 coefficient。"
            "information_level 只能是 none/shallow/complete/proven；visual_tier 只能是 none/t2/t1/t0；integration 只能是 isolated/matched。"
            "判定关系：无有效模块=0；单一信息或视觉=0.25；信息+T2匹配=0.5；完整信息+T1匹配=0.75；完整可信信息+T0匹配=1。"
            "T0 视觉单独存在不能超过0.25；T1 表达最高0.75；judgment 必须是解释判断的中文字符串。"
            "格式示例：{\"modules\":[{\"module_code\":\"product_kv\",\"coefficient\":0.5,"
            "\"information_level\":\"complete\",\"visual_tier\":\"t2\",\"integration\":\"matched\","
            "\"judgment\":\"有主视觉但利益点证明一般\",\"confidence\":0.82}],"
            "\"evidence\":[{\"module_code\":\"product_kv\",\"page_index\":0,"
            "\"bbox\":{\"x\":0.1,\"y\":0.1,\"width\":0.8,\"height\":0.2},"
            "\"evidence_type\":\"product_hero_visual\",\"ocr_text\":\"可见文字\","
            "\"reason\":\"该区域支持当前判断\",\"confidence\":0.82}]}。"
            f"\n成熟度定义：{json.dumps(scoring_rules.get('maturity_definitions', {}), ensure_ascii=False)}"
            f"\n判断顺序：{json.dumps(scoring_rules.get('judgment_order', []), ensure_ascii=False)}"
            f"\n统一裁决协议：{json.dumps(scoring_rules.get('adjudication_protocol', []), ensure_ascii=False)}"
            f"\n模块边界锁：{json.dumps(scoring_rules.get('boundary_locks', {}), ensure_ascii=False)}"
            f"\n评分模块：{json.dumps(modules, ensure_ascii=False)}"
        )

    def _prepared_image_urls(self, source):
        """Return deterministically resized, vertically ordered PDP image slices."""
        suffix = Path(source.original_name).suffix.lower()
        if suffix not in {".png", ".jpg", ".jpeg"}:
            raise ValueError("当前模型仅支持 PNG、JPG 或 PDF 文件。")
        with source.file.open("rb") as source_file:
            image = ImageOps.exif_transpose(Image.open(source_file)).convert("RGB")

        width, height = image.size
        scale = min(1, self.MAX_IMAGE_WIDTH / max(width, 1))
        target_size = (max(1, round(width * scale)), max(1, round(height * scale)))
        if image.size != target_size:
            image = image.resize(target_size, Image.Resampling.LANCZOS)
        slice_count = math.ceil(image.height / self.SLICE_HEIGHT)
        if slice_count > self.MAX_IMAGE_SLICES:
            raise ValueError(
                f"图片完整切片需要 {slice_count} 段，超过安全上限 {self.MAX_IMAGE_SLICES} 段；"
                "请拆分长图后重新上传，系统不会省略或压缩后续证据。"
            )

        urls = []
        for top in range(0, image.height, self.SLICE_HEIGHT):
            tile = image.crop((0, top, image.width, min(top + self.SLICE_HEIGHT, image.height)))
            encoded = BytesIO()
            tile.save(encoded, format="JPEG", quality=self.JPEG_QUALITY, optimize=True)
            urls.append("data:image/jpeg;base64," + base64.b64encode(encoded.getvalue()).decode("ascii"))
        return urls

    def _input_content(self, source, context, file_id=None):
        suffix = Path(source.original_name).suffix.lower()
        content = [{
            "type": "input_text",
            "text": "请诊断这份 PDP 文件。业务上下文：" + json.dumps(context or {}, ensure_ascii=False),
        }]
        if suffix == ".pdf":
            content.append({"type": "input_file", "file_id": file_id})
        else:
            image_urls = self._prepared_image_urls(source)
            content[0]["text"] += f"。图片已按页面从上至下切为 {len(image_urls)} 个连续切片，page_index 从 0 开始对应切片序号。"
            content.extend({"type": "input_image", "image_url": image_url, "detail": "high"} for image_url in image_urls)
        return [{"role": "user", "content": content}]

    def _chat_input_content(self, source, context):
        suffix = Path(source.original_name).suffix.lower()
        if suffix == ".pdf":
            raise ValueError("当前 Chat Completions 模型暂不支持 PDF 诊断，请上传 PNG 或 JPG。")
        image_urls = self._prepared_image_urls(source)
        return [{
            "role": "system",
            "content": self._instructions(context["scoring_rules"]),
        }, {
            "role": "user",
            "content": [{
                "type": "text",
                "text": "请诊断这份 PDP 图片。业务上下文：" + json.dumps(context.get("business_context") or {}, ensure_ascii=False)
                + f"。图片已按页面从上至下切为 {len(image_urls)} 个连续切片，page_index 从 0 开始对应切片序号。",
            }] + [{
                "type": "image_url",
                "image_url": {"url": image_url, "detail": "high"},
            } for image_url in image_urls],
        }]

    def _chat_completion_options(self):
        """Return provider-specific options without weakening output validation."""
        if self.model_name.strip().lower() == "kimi-k3":
            # Kimi K3 defaults to a 131072-token completion budget and always
            # reasons. Do not override its fixed temperature or send the legacy
            # K2.x ``thinking.type=disabled`` option.
            return {"reasoning_effort": "high"}
        return {
            "max_completion_tokens": 12000,
            "temperature": 0,
            "extra_body": {"thinking": {"type": "disabled"}},
        }

    def _chat_response_format(self):
        return {"type": "json_object"}

    def _validate_output(self, parsed, scoring_rules):
        expected = [item["code"] for item in scoring_rules["modules"]]
        module_codes = [item.module_code for item in parsed.modules]
        if len(module_codes) != len(expected) or set(module_codes) != set(expected):
            raise ValueError("OpenAI 结果必须包含且仅包含 11 个规定评分模块")
        evidence_codes = {item.module_code for item in parsed.evidence}
        missing_evidence = set(expected) - evidence_codes
        if missing_evidence:
            raise ValueError(f"OpenAI 结果缺少模块证据：{', '.join(sorted(missing_evidence))}")
        for evidence in parsed.evidence:
            if evidence.module_code not in expected:
                raise ValueError(f"OpenAI 结果含未知证据模块：{evidence.module_code}")
            for key, value in evidence.bbox.items():
                if key not in {"x", "y", "width", "height"} or not 0 <= float(value) <= 1:
                    raise ValueError("证据 bbox 必须使用 0~1 归一化 x/y/width/height")

    def _normalize_missing_evidence(self, parsed, scoring_rules):
        """Turn omitted evidence into an explicit, conservative zero-score result.

        Some OpenAI-compatible vision gateways occasionally return all module
        judgments but omit the evidence row for a module that is not present on
        the page.  An omission must never become positive evidence, but it also
        should not discard an otherwise valid diagnosis.  Record the omission as
        ``missing_content`` and force that module to the PDP-v3 ``弱`` state.
        """
        expected = [item["code"] for item in scoring_rules["modules"]]
        evidence_codes = {item.module_code for item in parsed.evidence}
        missing = [code for code in expected if code not in evidence_codes]
        if not missing:
            return parsed

        modules = []
        missing_set = set(missing)
        for item in parsed.modules:
            if item.module_code in missing_set:
                item = item.model_copy(update={
                    "coefficient": 0,
                    "information_level": "none",
                    "visual_tier": "none",
                    "integration": "isolated",
                    "judgment": "模型未返回可定位的页面证据，按模块缺失与“弱”处理。",
                    "confidence": 0,
                })
            modules.append(item)

        evidence = list(parsed.evidence)
        evidence.extend(EvidenceSuggestion(
            module_code=code,
            page_index=0,
            bbox={},
            evidence_type="missing_content",
            ocr_text="",
            reason="模型未返回该模块的可定位页面证据，按无有效证据处理。",
            confidence=0,
        ) for code in missing)
        return parsed.model_copy(update={"modules": modules, "evidence": evidence})

    def analyze(self, *, source, context, scoring_rules):
        if self.protocol == "chat_completions":
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=self._chat_input_content(source, {
                    "business_context": context,
                    "scoring_rules": scoring_rules,
                }),
                response_format=self._chat_response_format(),
                **self._chat_completion_options(),
            )
            choice = response.choices[0]
            if getattr(choice, "finish_reason", None) == "length":
                raise ValueError("兼容模型输出达到 Token 上限，未返回完整的 PDP 诊断 JSON")
            raw_content = (choice.message.content or "").strip()
            if raw_content.startswith("```"):
                raw_content = raw_content.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            if not raw_content:
                raise ValueError("兼容模型未返回可解析的 PDP 诊断结果")
            parsed = PdpDiagnosisOutput.model_validate_json(raw_content)
            parsed = self._normalize_missing_evidence(parsed, scoring_rules)
            self._validate_output(parsed, scoring_rules)
            usage = response.usage.model_dump() if response.usage else {}
            return {
                "modules": [item.model_dump() for item in parsed.modules],
                "evidence": [item.model_dump() for item in parsed.evidence],
                "usage": {**usage, "mode": "chat_completions", "external_api": True},
                "request_id": response.id,
            }

        suffix = Path(source.original_name).suffix.lower()
        remote_file = None
        try:
            if suffix == ".pdf":
                # Django's FieldFile is not an io.IOBase.  Pass the actual opened
                # binary stream in an OpenAI SDK-supported filename/file tuple.
                source.file.open("rb")
                try:
                    remote_file = self.client.files.create(
                        file=(source.original_name, source.file.file),
                        purpose="user_data",
                    )
                finally:
                    source.file.close()
            response = self.client.responses.parse(
                model=self.model_name,
                instructions=self._instructions(scoring_rules),
                input=self._input_content(source, context, remote_file.id if remote_file else None),
                text_format=PdpDiagnosisOutput,
                store=False,
            )
            parsed = response.output_parsed
            if parsed is None:
                raise ValueError("OpenAI 未返回可解析的 PDP 诊断结果")
            parsed = self._normalize_missing_evidence(parsed, scoring_rules)
            self._validate_output(parsed, scoring_rules)
            usage = response.usage.model_dump() if response.usage else {}
            return {
                "modules": [item.model_dump() for item in parsed.modules],
                "evidence": [item.model_dump() for item in parsed.evidence],
                "usage": {**usage, "mode": "openai", "external_api": True},
                "request_id": response.id,
            }
        finally:
            if remote_file is not None:
                try:
                    self.client.files.delete(remote_file.id)
                except Exception:
                    pass
