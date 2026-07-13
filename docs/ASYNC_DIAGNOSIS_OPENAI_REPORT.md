# PDP Lab 异步诊断与模型 API 接入报告

> 完成日期：2026-07-13  
> 结论：PDP 规则诊断主链路已可在本地完整运行；ModelVerse MiMo V2.5 已通过真实长图、11 模块、11 证据与服务端计分契约验证。AI 评分无需人工确认，通过服务端校验后自动锁定。

## 0. Codex 账号接入结论

- 已暂停“直接复用本地 Codex/ChatGPT 登录账号作为网站 API 凭证”的实现。Codex 登录会话不是可供 Django 服务调用的通用 API Key，且 ChatGPT/Codex 订阅与 API 平台的凭据、用量和账单彼此独立。
- 项目不会读取 Codex 的本地登录文件、Cookie、Token 或其他会话凭证，也不会把它们写入后台配置。
- 当前模型判断使用独立配置的 OpenAI 兼容 API；内置 `pdp-detail-page-methodology` 仍是唯一计分规则。后台未配置真实 API Key 时，Mock 会阻断普通上传，不会生成虚假评分。
- 当前会话中由 Codex 按同一 PDP Skill 完成的视觉复核，必须以 `confirmation_mode=codex_verified` 独立标识，不能伪装为 `ai_auto`。

推荐后续选择：

1. **生产方案（当前已验证）**：在独立“AI 模型 API 设置”中保存兼容 OpenAI SDK 的服务端 Key，按供应商选择 Responses 或 Chat Completions，并用基准详情页验证真实模型结果。
2. **本地实验方案**：另建 Local Agent/任务桥接器，由用户显式授权本机任务。该方案只适合本地或企业受控环境，不可把 Codex 登录态当作云端部署凭据；实施前还需要任务协议、权限、审计、超时和失败回退设计。

## 1. 已实现链路

```text
上传 PNG/JPG/PDF
  → 创建 PdpSource
  → POST /api/diagnosis-jobs/
  → Celery 异步 Worker
  → 模型适配器（auto / mock / openai-compatible）
  → 11 模块判断 + 页面证据
  → 服务端确定性计分
  → DiagnosisVersion(ai_auto, locked)
  → 前端评分记录与项目总览
```

## 2. 数据结构

- `ScoringStandard`：保存 11 模块权重、弱/中/强系数和 1~7 星分段。
- `DiagnosisJob`：任务状态、阶段、进度、适配器、模型和错误信息。
- `PageEvidence`：模块、页码、归一化 bbox、OCR 文字、模型解释和置信度。
- `ModuleAssessment`：权重、系数、得分、成熟度、判断和置信度。
- `ModelRun`：供应商、模型、提示词版本、请求 ID、Token 用量、耗时和错误。
- `DiagnosisVersion`：保存最终快照，AI 版本使用 `confirmation_mode=ai_auto`。
- `AiModelSettings`：独立维护适配器、模型、API Base URL、超时与加密 API Key。
- `PdpSkillSettings`：独立维护 Skill 名称、内置/远程模式、接入 URL/端口、超时与加密 Token。

## 3. 模型 API 适配原则

1. 使用 OpenAI SDK 兼容接口和 Pydantic 结构化校验；可选择 Responses 或 Chat Completions 协议。
2. Responses 协议中 PNG/JPG 使用 `input_image`、PDF 使用 `input_file`；Chat Completions 中 PNG/JPG 使用 Data URL，PDF 明确拒绝。
3. 模型仅返回模块系数、证据、判断和置信度，不信任模型返回的总分。
4. 后端强制校验：11 模块不多不少、每模块有证据、系数只能为 `0 / 0.5 / 1`、bbox 必须为 0~1。
5. Responses 路径的临时文件在响应或失败后都尝试删除。
6. Responses 请求设置 `store=False`；Key 仅在后端环境变量或后台加密字段中保存，绝不返回前端。

## 4. 配置与切换

管理后台提供两个相互独立的入口：

- AI 模型 API：`/admin/diagnosis/aimodelsettings/`，只维护适配器、协议、模型、API Base URL、超时和兼容 API Key。
- PDP Skill：`/admin/diagnosis/pdpskillsettings/`，只维护内置/远程模式、完整 URL（含端口）、超时和 Bearer Token。
- 生效优先级：启用的后台配置高于环境变量；后台未保存 Key 时仍可回退读取后端环境变量。
- 修改配置后，API 读取会即时更新；Celery Worker 的下一项任务也会重新读取配置。

环境变量仍可作为部署兜底：`OPENAI_API_KEY`、`PDP_DIAGNOSIS_ADAPTER`、`PDP_AI_PROTOCOL`、`PDP_MODEL_NAME`、`OPENAI_BASE_URL`、`OPENAI_TIMEOUT_SECONDS`。

- `PDP_DIAGNOSIS_ADAPTER=auto`：有 Key 用真实模型，无 Key 进入 Mock 安全阻断。
- `PDP_DIAGNOSIS_ADAPTER=openai`：强制兼容模型，无 Key 时明确失败。
- `PDP_DIAGNOSIS_ADAPTER=mock`：普通上传默认阻断；仅自动化测试可显式放开。

如果通过环境变量修改配置，API 和 Worker 需使用相同变量并同时重启。

## 5. PDP 规则与前端同步

- 当前规则：`pdp-detail-page-methodology / pdp-v1`。
- 规则来源校验：`scoring-standard.md` SHA-256 为 `14b427e36ad81f75706f2e4fa2d76e5f087915a066e72221e59c1cd4c368a670`。
- 11 模块权重合计 100，成熟度系数固定为弱 `0` / 中 `0.5` / 强 `1`，包含 13 个 1~7 星区间。
- 前端项目总览、评分诊断、人工修订和设置页均读取 `/api/diagnosis-config/`，不再独立维护权重与星级区间。
- 远程 Skill 必须通过同一 11 模块、权重、系数和星级区间契约校验，未通过时诊断任务不会启动。

## 6. 验证结果

- Django system check：通过。
- Django 测试：16/16 通过。
- 配置状态接口：可识别 `pdp-detail-page-methodology / pdp-v1`、当前模型适配器和 OpenAI Key 是否已配置。
- 模型适配器契约测试：通过（Responses 结构化证据、`store=False`、文件删除；Chat Completions Data URL 与结构化输出）。
- Celery 跨进程 smoke test：通过。
- smoke 结果：11 模块、11 证据、58.5 分、4.5 星、`ai_auto`。
- Vite 生产构建：通过。
- 数据迁移：`0008`、`0009` 与拆分配置的 `0010_split_ai_and_skill_settings` 已应用。
- 运行时状态：后台配置源已启用；当前使用 `mimo-v2.5 / chat_completions`，密钥已加密保存且配置接口不返回明文。
- 已创建持久化验证项目 `Nike Vomero 18｜缓震跑鞋详情页`：87 分、6.5 星、11 个模块、11 条证据，评分方式为 `codex_verified`。
- 首页项目卡读取后端真实分值和上传原图封面；项目总览读取同一评分版本。
- 上传建任务失败或异步任务无法调用模型/Skill 时，前端会弹出“未成功生成评分”，并展示后端错误及配置检查提示。
- Mock 已改为安全阻断模式：普通上传检测到 Mock 时前端立即弹窗并停止上传建任务；后端再次返回 `MOCK_ADAPTER_ACTIVE`，默认不会写入 Mock 评分。仅自动化测试可用 `PDP_ALLOW_MOCK_DIAGNOSIS=1` 显式开启。
- 项目总览星级轴展示 3–7 星五个核心段位，页面名称来自当前后端评分规则；定位按星级而非总分百分比计算。

## 6.1 ModelVerse MiMo V2.5 本地验证

- 接口依据：[ModelVerse OpenAI 兼容接口](https://www.compshare.cn/docs/modelverse/models/text_api/openai_compatible)；模型能力依据：[Xiaomi MiMo 模型说明](https://mimo.mi.com/docs/en-US/quick-start/model)。
- Base URL 为 `https://api.modelverse.cn/v1/`，协议为 `chat_completions`，模型为 `mimo-v2.5`；`/models` 鉴权成功并识别到该模型。
- Key 已保存到 `AiModelSettings` 加密字段，前端及状态接口不会返回明文。
- 真实长图识别正确读到 Nike 与 Vomero 18；简单结构化 JSON 探针通过。
- 完整契约验证返回 11 个模块与 11 条证据，全部系数均为 `0 / 0.5 / 1`，服务端确定性计算为 89.5 分、6.5 星。
- 与现有 Codex 复核版逐项比较为 10/11 模块一致、整体星级一致；唯一差异是“使用说明/服务事项”由 MiMo 判强、Codex 判中，因此相差 2.5 分。系统保留真实模型差异，不用硬编码强行对齐单一样本。
- Chat Completions 使用 `temperature=0` 降低同一输入的随机波动；最终一致性仍需通过多品类基准集衡量，而不能只看一个 Nike 案例。
- 验证为 `validation_only`，未创建或覆盖 `DiagnosisVersion`；现有 Nike 项目的 87 分、6.5 星 Codex 复核版本保持不变。
- 结论：**该配置已可用于本地 PNG/JPG 正式评分**。PDF 在该协议下会明确报错；上线前仍需完成评测集、生产数据库、队列和对象存储改造。

## 7. 部署前仍需完成

- 将开发环境 SQLite 替换为 PostgreSQL。
- 将 Celery SQLite broker 替换为 Redis 或 RabbitMQ。
- 将用户文件从本地 media 切换到对象存储，并配置文件保留和删除策略。
- 为任务增加重试、死信、超时和成本告警。
- 恢复正式 CSRF 保护，并添加组织/RBAC 和审计权限。
- 运行少量真实 PDP 的模型评测集，比较证据召回率、模块一致性和人工修订率后，再确定生产默认模型。
- 生产环境必须配置稳定的 `DJANGO_SECRET_KEY`；该值用于解密后台密钥，变更后需在后台重新保存 API Key/Token。
