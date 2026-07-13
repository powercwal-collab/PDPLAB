# PDP Lab 完整 Flow 与部署确认稿

> 状态：本地交互已实现，尚未部署。  
> 当前基线：1.1（1.0 视觉 + 独立诊断进度页）。

## 1. 用户体验 Flow

```text
首页
├─ 选择最近项目
│  └─ 项目总览
└─ 上传 PDP / 新建诊断项目
   └─ 选择项目
      └─ 上传 PDP 内容
         └─ 诊断进度
            ├─ 文件解析
            ├─ 页面切片与 OCR
            ├─ 11 模块映射
            └─ 评分与优化推演
               └─ AI 评分自动锁定
                  └─ 评分记录 / 项目总览
                     ├─ 评分诊断详情
                     ├─ 优化路线
                     │  └─ 品牌资产匹配
                     │     └─ AI 页面生成
                     │        └─ 最终优化页面
                     │           └─ 复评分
                     │              ├─ 返回项目总览
                     │              └─ 下一轮优化
                     ├─ 快速切换项目
                     └─ 返回首页
```

## 2. 页面与状态转换

| 当前页面 | 用户动作/系统事件 | 下一页面 | 需要保存的数据 |
|---|---|---|---|
| 首页 | 选择最近项目 | 项目总览 | `projectId` |
| 首页 | 上传 PDP | 导入 PDP | 新建/已有项目意图 |
| 导入 PDP | 选择项目并上传 | 诊断进度 | `projectId`, `pdpSourceId` |
| 诊断进度 | 后端任务完成 | 评分记录 | `diagnosisJobId`, `diagnosisVersionId`, 证据与 AI 评分 |
| 评分记录 | 查看 AI 自动锁定版本 | 项目总览 | 当前评分版本 |
| 可选人工修订 | 调整 11 模块并保存 | 评分记录 | 新的 manual 版本 |
| 项目总览 | 查看模块 | 评分诊断详情 | 模块与证据 ID |
| 项目总览 | 查看优化路线 | 优化路线 | 当前评分版本 |
| 优化路线 | 选择任务 | 品牌资产匹配 | `optimizationTaskIds` |
| 品牌资产匹配 | 应用资产 | AI 生成 | `brandAssetIds` |
| AI 生成 | 生成完成 | 最终优化页面 | `generationJobId`, 候选版本 |
| 最终优化页面 | 发起复评 | 复评分 | `optimizedVersionId` |
| 复评分 | 完成本轮 | 项目总览 | 新评分、增益、归档状态 |

## 3. 诊断进度页逻辑

当前本地版本已接入 Celery 异步任务：

1. 上传文件后创建 `PdpSource`。
2. 调用 `POST /diagnosis-jobs` 创建诊断任务。
3. 前端保存 `diagnosisJobId` 并进入诊断进度页。
4. 前端使用短轮询获取任务状态；生产规模增大时可替换为 SSE/WebSocket。
5. 后端按阶段返回 `queued / processing / completed / failed`。
6. 模型适配器返回 11 模块系数、判断、置信度与页面证据。
7. 后端验证证据完整性，用版本化评分规则计算得分和星级，自动锁定 `ai_auto` 版本。
8. 人工确认不是主链路必选项；人工修订时另建新版本。

建议的任务状态：

```text
queued
→ parsing
→ slicing_ocr
→ module_mapping
→ scoring
→ completed

任一阶段可进入 failed，并携带 retryable 与 errorCode。
```

## 4. 前后端模块边界

### 前端

- 首页、上传、诊断进度和工作台页面。
- 项目切换与路由状态。
- 任务进度展示与失败重试。
- 评分证据确认。
- 品牌资产选择和生成版本比较。

### API 服务

- 项目、文件、诊断、评分、优化任务和版本管理。
- 生成签名上传地址。
- 将供应商/DAM 数据转换为统一 `BrandAsset`。
- 创建异步任务，不在普通 HTTP 请求中执行长时间 OCR 或生图。

### 异步 Worker

- PDP 图片/PDF 解析。
- OCR、页面切片和模块识别。
- 评分模型调用。
- 品牌资产匹配。
- AI 图片/页面生成。
- 复评分。

### 数据与文件

- 数据库：项目、任务、评分、资产引用、版本和审计记录。
- 对象存储：用户上传文件、缩略图、生成结果和导出文件。
- 队列：诊断与生成任务。

## 5. 建议 API

```text
POST   /projects
GET    /projects
GET    /projects/:projectId

POST   /uploads/sign
POST   /pdp-sources

POST   /diagnosis-jobs
GET    /diagnosis-jobs/:jobId
POST   /diagnoses/:diagnosisId/confirm

GET    /projects/:projectId/optimization-tasks
PATCH  /optimization-tasks/:taskId

POST   /brand-assets/search
POST   /generation-jobs
GET    /generation-jobs/:jobId

POST   /optimized-versions/:versionId/rescore
GET    /projects/:projectId/versions
```

## 6. 部署分阶段方案

### 阶段 A：交互验证版

- 部署 Vite 静态前端。
- 保留 mock 数据和本地计时进度。
- 不开放真实文件持久化、OCR、品牌资产库或 AI 生成。
- 用途：内部体验、Flow 确认和设计评审。

### 阶段 B：可用 MVP

- 静态前端部署到 Web Hosting/CDN。
- 独立 API 服务处理项目和任务。
- 对象存储保存上传与生成文件。
- 数据库保存项目、评分、版本和任务状态。
- Worker + 队列执行 OCR、评分和生成任务。
- 品牌资产库先做只读搜索与引用，不直接覆盖 DAM 原文件。

### 阶段 C：生产版

- 用户登录、组织、角色和项目权限。
- 品牌资产版权、有效期和使用范围校验。
- 评分版本锁定与完整审计日志。
- 生成内容人工审核与发布审批。
- 监控、告警、任务重试、限流和成本统计。
- 数据备份、文件生命周期和删除策略。

## 7. 推荐部署拓扑

```text
浏览器
  ↓
静态前端 CDN
  ↓
API 网关 / API 服务
  ├─ PostgreSQL
  ├─ 对象存储
  ├─ 品牌资产库适配器
  └─ 任务队列
       ↓
     Worker
       ├─ OCR / 页面解析
       ├─ PDP 评分模型
       ├─ 资产匹配
       └─ AI 生成与复评分
```

不要将大文件、OCR 或生图直接放在静态前端；不要让普通 Serverless 请求等待完整生成流程。

## 8. 部署前需要用户确认

1. **首个部署目标**：只部署交互验证版，还是直接做可上传的 MVP？
2. **托管平台**：Netlify、Vercel，或企业现有云平台？
3. **登录要求**：第一版是否需要账号和组织权限？
4. **文件策略**：是否允许把 PDP 文件上传到云端；保留多久？
5. **品牌资产库**：DAM 厂商、鉴权方式、只读或可回写？
6. **AI 服务**：OCR、文本模型和生图服务使用哪一套供应商？
7. **人工审核**：生成结果是否必须审核后才能导出或发布？
8. **数据区域**：是否有境内存储、跨境或品牌合规要求？

在以上问题确认前，不执行生产部署。
