# PDP Lab Django API

后端使用项目根目录的 `.venv`，Vite 已把 `/api` 代理到 `127.0.0.1:8000`。

```bash
source .venv/bin/activate
python backend/manage.py migrate
python backend/manage.py runserver 127.0.0.1:8000
npm run dev:worker
```

基础入口：`GET /api/health/`、`GET /api/projects/`、`/admin/`。

## 异步诊断与模型 API

本地默认使用 `auto` 适配器：配置兼容 OpenAI SDK 的模型 API Key 后使用真实模型；未配置时会进入 Mock 安全阻断，普通上传不会创建评分任务，也不会生成固定假分。Mock 只允许自动化测试通过 `PDP_ALLOW_MOCK_DIAGNOSIS=1` 显式启用。

```bash
export OPENAI_API_KEY="sk-..."
export PDP_DIAGNOSIS_ADAPTER="openai"   # 可选；默认 auto 会自动选择
export PDP_MODEL_NAME="gpt-5.4-mini"     # 可按账户可用模型调整
export PDP_AI_PROTOCOL="responses"       # 或 chat_completions
export OPENAI_BASE_URL=""                # 兼容网关填写其 /v1/ 根地址
npm run dev:api
npm run dev:worker
```

也可以在 Django 管理后台分别使用“AI 模型 API 设置”和“PDP Skill 接入设置”两个独立入口。Key 与 Skill Token 使用由 `DJANGO_SECRET_KEY` 派生的密钥分别加密保存，不会通过配置 API 返回前端。生产环境必须固定 `DJANGO_SECRET_KEY`，不要提交真实密钥。

模型与 Skill 分别读取自己的启用配置。模型后台配置高于后端环境变量，并可独立选择 Responses 或 Chat Completions 协议；Skill 后台可选择内置 `pdp-v1`，也可填写远程 HTTP Skill 的完整 URL（含端口）、超时和 Bearer Token。当前 ModelVerse MiMo 验证配置使用 `https://api.modelverse.cn/v1/`、`mimo-v2.5` 与 `chat_completions`；该协议以 Data URL 读取 PNG/JPG，暂不接受 PDF。

任务 API：

- `POST /api/diagnosis-jobs/`：传入 `source_id` 创建诊断任务。
- `GET /api/diagnosis-jobs/<job_id>/`：获取进度、证据、模块评估和自动锁定版本。
- `GET /api/diagnosis-config/`：获取 PDP skill 规则来源、当前适配器、模型与 Key 配置状态（不返回 Key）。

前端会从该接口读取当前 11 模块权重、成熟度定义和 1~7 星区间，项目总览、诊断和人工修订因此与后台规则一致。
