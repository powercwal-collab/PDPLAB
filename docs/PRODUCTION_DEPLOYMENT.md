# PDP Lab 生产部署手册

> 目标基线：阿里云 ECS，Ubuntu 22.04，2 vCPU / 8 GiB，80 GiB ESSD，5 Mbps。  
> GitHub 目标仓库：`git@github.com:powercwal-collab/PDPLAB.git`。  
> 本文不保存服务器密码、SSH 私钥、模型 API Key 或生产数据库密码。

## 1. 生产架构

```text
浏览器
  │ HTTPS :443
  ▼
Nginx
  ├─ /                 React / Vite 静态文件
  ├─ /api、/admin      Django + Gunicorn
  ├─ /static           Django collectstatic
  └─ /media            本地持久卷，或切换阿里云 OSS
                         │
             ┌───────────┼───────────┐
             ▼           ▼           ▼
       PostgreSQL      Redis      Celery Worker
       RDS 优先       队列/缓存    AI + PDP Skill
                                      │
                                      ▼
                              外部模型 API
```

当前评分 Skill 使用后端内置的版本化 `pdp-v1` 规则，不要求 ECS 安装本地 Codex Skill。AI 模型通过后台独立配置的 OpenAI 兼容 API 调用；Mock 在生产默认禁止。

## 2. 已完成的生产改造

- Django 设置由 `PDP_ENV` 切换开发/生产；生产强制要求独立 `DJANGO_SECRET_KEY`、合法主机、PostgreSQL 和 Redis。
- PostgreSQL 使用 `DATABASE_URL`，连接复用和健康检查已启用。
- Redis 同时承载 Django 缓存、Celery broker 和可选 result backend。
- Gunicorn 作为 WSGI 服务；Celery 独立 Worker；均使用非 root 容器用户。
- 写接口恢复 Django CSRF 保护；前端自动获取并附带 CSRF Token。
- 登录失败按 IP + 用户名限制为 10 分钟内最多 5 次；生产注册启用 Django 密码校验器。
- 新增 `/api/health/ready/`，同时验证数据库与缓存。
- 支持 `filesystem` 持久卷和 `oss` 两种媒体存储；OSS Key 仅通过服务器环境变量注入。
- Nginx 统一提供前端、API、后台、静态文件和媒体文件，并限制上传为 35 MB。
- SimpleUI 管理后台使用同源 iframe，`X-Frame-Options` 由 Nginx 统一设置为 `SAMEORIGIN`；不允许跨域嵌入。
- 提供 HTTP 首次验收配置和 TLS 正式配置；正式上线必须启用 TLS。
- 提供 Docker Compose、Ubuntu 初始化、部署、健康检查、回滚脚本。
- GitHub Actions 已包含 CI 和手动 ECS 发布工作流。

## 3. GitHub 仓库准备

本地仓库已经存在，不要再次执行 `git init`。GitHub 新仓库建议设为 Private，且创建时不要自动生成 README、License 或 `.gitignore`。

```bash
git remote add origin git@github.com:powercwal-collab/PDPLAB.git
git push -u origin main
git push origin --tags
```

GitHub 侧建议开启：

1. `main` 分支保护，CI 通过后才能合并。
2. Secret scanning、Dependabot alerts。
3. `production` Environment，并为发布增加人工批准。
4. 在 ECS 上安装仓库级 GitHub Actions self-hosted runner，并添加标签 `pdp-lab-production`。Runner 仅需主动访问 GitHub HTTPS，不需要向 GitHub 开放 SSH。

不要把 `.env.production`、数据库、`backend/media/`、API Key 或 SSH 私钥上传到 GitHub。

## 4. ECS 首次初始化

安全组只开放：

- `22/tcp`：仅管理员固定公网 IP，不允许 `0.0.0.0/0`。
- `80/tcp`：公网，用于首次验证和 HTTPS 跳转。
- `443/tcp`：公网，正式业务。
- 不开放 `8000`、`5432`、`6379`。

将仓库中的 `deploy/bootstrap-ubuntu.sh` 上传到服务器后执行：

```bash
sudo PDP_DEPLOY_USER=pdplab bash deploy/bootstrap-ubuntu.sh
```

脚本会安装 Docker Engine、Compose 插件、Git、rsync，创建非 root 部署用户和以下目录：

```text
/srv/pdp-lab/
├── current -> releases/<commit>
├── releases/
└── shared/
    ├── .env.production
    └── tls/
        ├── fullchain.pem
        └── privkey.pem
```

重新登录 `pdplab` 用户后确认：

```bash
docker version
docker compose version
```

随后在 GitHub 仓库 `Settings → Actions → Runners → New self-hosted runner` 中选择 Linux x64，按 GitHub 页面给出的临时命令将 Runner 安装到 `/home/pdplab/actions-runner`，并添加自定义标签 `pdp-lab-production`。建议将 Runner 安装为 systemd 服务。不要把 Runner registration token 写入仓库或部署文档。

## 5. 生产环境变量

在服务器执行：

```bash
cp /srv/pdp-lab/current/.env.production.example /srv/pdp-lab/shared/.env.production
chmod 600 /srv/pdp-lab/shared/.env.production
```

至少替换：

- `DJANGO_SECRET_KEY`：50 位以上随机字符串，正式使用后保持不变。
- `DJANGO_ALLOWED_HOSTS`：正式域名。
- `DJANGO_CSRF_TRUSTED_ORIGINS`：带 `https://` 的正式域名。
- `PDP_FRONTEND_URL`：正式站点 URL。
- `DATABASE_URL`：推荐同地域/同 VPC 的 RDS PostgreSQL 内网地址。
- `OPENAI_BASE_URL`、`PDP_MODEL_NAME`：实际模型网关参数。
- 模型 API Key：推荐上线后在 Django 后台重新录入，不迁移本地密文。

生成 Django Secret：

```bash
python3 -c 'import secrets; print(secrets.token_urlsafe(64))'
```

本地数据库中的模型 Key 密文由本地 `DJANGO_SECRET_KEY` 派生，不能在更换 Secret 后直接复制。此前在聊天或开发环境中出现过的 API Key 上线前必须撤销并轮换。

## 6. 数据库与文件方案

### 推荐：RDS + OSS

- RDS PostgreSQL 与 ECS 同地域、同 VPC，只使用内网地址。
- OSS Bucket 设为私有，通过 RAM 子账号给予最小读写权限。
- 设置 `PDP_MEDIA_STORAGE=oss` 并配置 OSS 环境变量。
- 不在 GitHub 或镜像中打包现有 SQLite 数据和媒体文件。

### 首次小流量验收：单机 PostgreSQL + 本地持久卷

`.env.production` 中使用：

```text
DATABASE_URL=postgresql://pdp_lab:<password>@postgres:5432/pdp_lab
PDP_MEDIA_STORAGE=filesystem
```

启动时增加 Profile：

```bash
docker compose -p pdp-lab \
  --profile local-infra \
  --env-file /srv/pdp-lab/shared/.env.production \
  -f compose.production.yml up -d
```

该方式适合验收，不等同于高可用。数据库和媒体卷都必须做定期快照/备份。

## 7. 首次发布

服务器已经存在 `/srv/pdp-lab/shared/.env.production` 且 self-hosted runner 在线后，可在 GitHub Actions 手动运行 `Deploy ECS`。工作流会在 ECS 本机：

1. 将当前 commit 上传到 `/srv/pdp-lab/releases/<commit>`。
2. 在 ECS 构建前后端镜像。
3. 执行数据库迁移和 `collectstatic`。
4. 启动 Nginx、Gunicorn、Celery、Redis。
5. 请求 `/healthz`；失败时输出服务日志并中止。
6. 成功后更新 `/srv/pdp-lab/current`，保留最近 5 个 release。

也可在服务器手动执行：

```bash
cd /srv/pdp-lab/current
PDP_ENV_FILE=/srv/pdp-lab/shared/.env.production ./deploy/deploy.sh
```

首次启动后创建独立生产管理员，不要沿用开发密码：

```bash
docker compose -p pdp-lab \
  --env-file /srv/pdp-lab/shared/.env.production \
  -f /srv/pdp-lab/current/compose.production.yml \
  exec web python manage.py createsuperuser
```

## 8. HTTPS

获得域名证书后，将证书放入：

```text
/srv/pdp-lab/shared/tls/fullchain.pem
/srv/pdp-lab/shared/tls/privkey.pem
```

然后修改 `.env.production`：

```text
PDP_ENABLE_TLS=1
DJANGO_SECURE_SSL_REDIRECT=1
```

重新执行 `deploy/deploy.sh`。TLS 配置仅启用 TLS 1.2/1.3，并将 HTTP 重定向到 HTTPS。中国大陆地域 ECS 使用域名公开服务前还需完成 ICP 备案；备案完成前可先用受限 IP 验收，但不得将 HTTP 验收状态视为正式上线。

## 9. 上线验收清单

1. `/healthz` 返回 200，数据库与缓存均为 `true`。
2. 注册新用户后项目列表为空。
3. 两个账号之间项目、上传、评分历史互不可见。
4. 上传 PNG/JPG，进入异步进度页，Celery Worker 实际收到任务。
5. 未配置模型或 Skill 失败时出现阻断弹窗，不生成 Mock 分数。
6. 完成 11 模块结构化输出后，服务端计算分数并自动锁定版本。
7. 首页卡片、项目总览、评分诊断和评分历史使用同一版本分值与封面。
8. 后台 AI API 与 PDP Skill 设置保持独立，Key 不出现在前端接口或日志。
9. iPhone/iPad/桌面关键页面无横向溢出。
10. 管理后台、用户菜单、项目切换和退出登录正常。

## 10. 回滚

应用回滚：

```bash
/srv/pdp-lab/current/deploy/rollback.sh /srv/pdp-lab/releases/<previous-commit>
```

应用回滚不能自动撤销不可逆数据库迁移。每次涉及数据库结构变更前，应先创建 RDS 快照；使用单机 PostgreSQL 时先执行 `pg_dump` 并把备份复制到 ECS 之外。

## 11. 当前仍需外部提供或完成

- GitHub 账号对 `powercwal-collab/PDPLAB` 的写权限和本机 SSH Key 授权。
- ECS 登录用户与 SSH 私钥；不要在聊天中发送服务器密码。
- 安全组 22/80/443 规则确认。
- 正式域名、DNS 与中国大陆 ICP 备案状态。
- RDS/OSS 是否立即启用；若不启用，需要接受单机备份与恢复责任。
- 新的生产模型 API Key，并从 ECS 网络重新跑模型能力验证。
- 监控与告警接收渠道；当前已有结构化控制台日志，但尚未接 Sentry/云监控告警。
