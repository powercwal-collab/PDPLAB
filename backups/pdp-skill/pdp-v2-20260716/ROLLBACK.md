# PDP Skill `pdp-v2` 备份与回滚

本目录是 2026-07-16 当前生产评分能力的只读恢复点，包含完整本地 Skill、参考资料、评分工作簿、运行时证据门禁代码和生产状态摘要。

## 恢复点

- 应用版本：`e4d7ccf6b2c5d53a614cdc295ba8b23d8095a3ce`
- 应用标签：`pdp-lab-v3.18`
- Skill 标签：`pdp-skill-v2-20260716`
- 评分标准：`pdp-v2`
- 规则修订：`sha256:19843d4c2a4c2ae889e13d0245800336fe3adc145253314f5e277ddf5eb9e78c`

## 1. 校验备份完整性

在本目录执行：

```bash
shasum -a 256 -c SHA256SUMS.txt
```

全部文件必须返回 `OK`。任何一项不一致都不要用于生产回滚。

## 2. 恢复本地 Codex Skill

先另存当前 Skill，再用本备份覆盖：

```bash
mv ~/.codex/skills/pdp-detail-page-methodology ~/.codex/skills/pdp-detail-page-methodology.before-rollback
cp -R skill ~/.codex/skills/pdp-detail-page-methodology
```

重新启动 Codex 后，再核对 `references/scoring-standard.md` 的 SHA-256 为：

```text
19843d4c2a4c2ae889e13d0245800336fe3adc145253314f5e277ddf5eb9e78c
```

## 3. 恢复应用代码

不要强制覆盖 `main`。从标签创建恢复分支并跑完整验证：

```bash
git fetch --tags origin
git switch -c restore/pdp-lab-v3.18 pdp-lab-v3.18
npm run build
npm run check:api
```

验证通过后再按正式发布流程合并或推送该恢复分支。

## 4. 恢复生产评分标准

当前数据库同时保留历史标准。优先通过 Django 管理后台将 `pdp-v2` 设为唯一启用版本；不得删除历史 `DiagnosisVersion` 或覆盖其原评分标准关联。

若后台不可用，可在完成数据库快照后执行：

```python
from diagnosis.models import ScoringStandard
ScoringStandard.objects.update(is_active=False)
ScoringStandard.objects.filter(version="pdp-v2").update(is_active=True)
```

恢复后确认：

- `/api/diagnosis-config/` 返回 `version=pdp-v2`；
- `source_revision` 与本备份一致；
- 11 个模块、13 个星级区间完整；
- KV、场景化与全局有效存在性门禁回归测试通过；
- 新建一次非 Mock 小图诊断，历史评分版本不发生变化。

## 5. 回滚边界

- 标签只恢复代码和规则，不自动回滚数据库迁移或用户数据。
- 不要把历史锁定评分重算成新规则。
- 不要在没有数据库快照的情况下执行不可逆迁移。
- AI 模型配置、API Key 与 Skill Token 不在本备份中，继续由生产密钥系统管理。
