# PDP Lab Design QA

- Source visual truth path: `browser://127.0.0.1:4173/` browser annotation screenshots supplied in the current task.
- Implementation screenshots:
  - `/Users/lixiao/Documents/人设背景提示词/outputs/pdp-lab-prototype/design-qa-project-menu.png`
  - `/Users/lixiao/Documents/人设背景提示词/outputs/pdp-lab-prototype/design-qa-score-card.png`
  - `/Users/lixiao/Documents/人设背景提示词/outputs/pdp-lab-prototype/design-qa-score-label-centered.png`
  - `/Users/lixiao/Documents/人设背景提示词/outputs/pdp-lab-prototype/design-qa-dynamic-diagnosis.png`
  - `/Users/lixiao/Documents/人设背景提示词/outputs/pdp-lab-prototype/design-qa-gap-panel-nike.png`
  - `/Users/lixiao/Documents/人设背景提示词/outputs/pdp-lab-prototype/design-qa-gap-panel-descente.png`
  - `/Users/lixiao/Documents/人设背景提示词/outputs/pdp-lab-prototype/design-qa-all-project-cards.png`
  - `/Users/lixiao/Documents/人设背景提示词/outputs/pdp-lab-prototype/design-qa-module-carousel-before.png`
  - `/Users/lixiao/Documents/人设背景提示词/outputs/pdp-lab-prototype/design-qa-module-carousel-page-1.png`
  - `/Users/lixiao/Documents/人设背景提示词/outputs/pdp-lab-prototype/design-qa-module-carousel-page-2.png`
- Viewports: 1093 × 898 for the earlier annotated regions; 1280 × 898 for the same-state before/after module-carousel comparison.
- States: project switcher open/closed, project overview score card, score diagnosis weak/medium/strong module selections, Nike/Descente dynamic gap and P0 task states, all-project cards, module table page 1/page 2.
- Final acceptance: user confirmed the interface is OK on 2026-07-14.

## Full-view comparison evidence

- The project switcher retains the existing white enterprise popover, border, radius, shadow, type scale, blue selected state, and top-bar placement from the annotated source.
- The score card retains the existing left score/right copy composition and five-stage scale while removing the obsolete T1 row and giving the explanation area enough space.
- The diagnosis screen retains its two-column list/detail layout while replacing repeated placeholder copy with module-specific content.
- The gap and P0 cards keep the accepted dashboard composition while their module names, gains, reasons, priorities, and projected score now follow the active project's diagnosis.
- The all-project view keeps its three-column card grid while separating real covers from genuine no-source placeholders and normalizing legacy ratings to the active star bands.
- The module card keeps the accepted six-row table density and fixed dashboard height; only the new pagination dots are added below the table, so adjacent card proportions and hierarchy remain unchanged.

## Focused region comparison evidence

- Project menu: all 7 backend projects render; each row is 32px; list max-height is 640px, giving an exact 20-row capacity; overflow is internal; the create action remains outside the scrolling list.
- Score card: copy-to-marker spacing is 16px; panel `clientHeight` equals `scrollHeight`; the reason row `clientHeight` equals `scrollHeight`; no T1-minus text remains.
- Score card bottom spacing: 46px remains below the reason row, so the full “为什么还不是” copy is visible without touching the card boundary.
- Score marker: at 6.5 stars, the “当前 6.5 星” label center and circular marker center both measure `615.72px`; horizontal center delta is `0px`.
- Diagnosis detail: weak `产品互动/动态内容`, medium `品牌/产品背书`, and strong `卖点与功能证明` each display different saved judgments, evidence reasons/OCR, evidence counts, maturity logic, and rule-based guidance.
- Nike overview: only two real gaps render — `产品互动/动态内容 +8` and `品牌/产品背书 +2.5`; the P0 card uses the same ordering and projects `89.5 → 100`.
- Descente overview: the top three gaps render as `产品互动/动态内容 +8`, `使用说明/服务事项 +5`, and `尺码/适配与对比选购 +5`; the P0 card uses the first two and projects `79.5 → 92.5`.
- Gap and P0 cards have no internal overflow at 1093 × 898; the inspected panels report equal client and scroll heights.
- All 7 project cards were inspected. Real sources use backend media covers; projects without a source show the neutral folder state. The legacy `4.9` rating is presented as the valid `5 星` band.
- Module carousel page 1 shows modules 1–6; page 2 shows modules 7–11. Both dots are keyboard-focusable buttons with page-specific accessible labels and `aria-current` on the active page.
- The module panel reports `clientHeight = scrollHeight = 388px` on both pages; the table remains `280px` high, so the second page does not collapse the dashboard row.

## Fidelity surfaces

- Typography: existing PDP Lab type scale and weights retained; no font-family change in this pass.
- Color: existing blue primary, amber warning, green success, red weak-state, gray borders, and white surface colors retained.
- Spacing: score-copy/marker gap fixed at 16px; reason row keeps 12px top and 14px bottom margins; 46px verified card-bottom clearance.
- Copy: obsolete `当前 T1-minus` text removed; stage title, score reason, module judgment, evidence, and guidance now reflect actual saved scoring data.
- Images: no image asset changes were required for the annotated regions.
- Image fidelity: persisted projects no longer borrow hardcoded example artwork when no backend source exists; the neutral folder state is used instead.
- Carousel assets/icons: no new raster, logo, illustration, or custom icon assets were introduced; the control is a native pagination indicator consistent with the existing blue/gray token set.

## Findings

- No remaining P0/P1/P2 visual or interaction defects in the annotated regions.
- P3: very long model judgments may wrap to three lines on narrower desktop widths; current panel height accommodates the verified samples.

## Comparison history

1. P1: project switcher was hardcoded to 3 examples. Fixed by binding all backend projects and adding a 20-row internal-scroll list.
2. P1: menu stayed open after clicking elsewhere. Fixed with outside-pointer and Escape handling.
3. P1: score explanation touched the star marker and the reason row risked clipping. Fixed by removing the T1 row, setting a 16px copy-to-marker gap, and preserving 46px bottom space.
4. P1: every diagnosis module reused the same static copy. Fixed by serializing saved evidence into diagnosis history and binding judgment/evidence/strong-standard content by selected module.
5. P2: the 6.5-star label used the right-edge fallback too early, shifting the label away from its circular marker. Fixed by reserving the edge fallback for 7 stars; revised browser measurement confirms a 0px center delta at 6.5 stars.
6. P1: the top-gap chart and P0 route reused static sample modules for every project. Fixed by deriving gaps as `max − score`, sorting by gain and maturity, binding each module's evidence/judgment, and deriving P0/P1/P2 tasks from the same ordered list. Post-fix Nike and Descente captures show different, internally consistent results.
7. P1: one legacy project exposed an invalid `4.9` star value and projects without uploaded sources could display example artwork. Fixed by normalizing serialized ratings against the active scoring standard and limiting persisted card covers to backend `cover_url` values. Post-fix all-project capture shows `5 星` and neutral folder placeholders.
8. P2: project card dates reflected only the project record, not the newest diagnosis or cover source. Fixed by serializing the latest activity timestamp; Nike and Descente now show `2026.7.14`.
9. P1: the maturity card rendered only `dashboardModules.slice(0, 6)`, hiding 5 of the 11 scored modules. Fixed with a two-page, six-row carousel and clickable pagination dots. Post-fix browser evidence confirms page 1 has 6 rows, page 2 has 5 rows, all 11 unique modules are reachable, and the panel has no overflow.

## Interaction and runtime checks

- Project selection: passed.
- Outside click closes project menu: passed.
- Escape closes project menu: passed.
- Weak/medium/strong diagnosis module switching: passed.
- Browser console errors: none in a fresh-page runtime check. One historical hot-reload error from before the fix remained in the older tab log and was excluded from the clean run.
- Django tests: 17/17 passed.
- Vite production build: passed.
- User visual acceptance: passed on 2026-07-14.
- 6.5-star label/marker center alignment: passed, 0px delta.
- Module pagination dot switching: passed in both directions.
- Switching projects from carousel page 2 resets the module card to page 1: passed.
- Module coverage: passed, 6 + 5 = 11 rows.
- Module panel overflow: passed, 388px client/scroll height on both pages.

## Implementation checklist

- [x] Complete backend project list.
- [x] 20-row menu capacity with internal scrolling.
- [x] Outside-click and Escape dismissal.
- [x] Score card text and scale spacing.
- [x] Full reason copy without overflow.
- [x] Per-module judgments and evidence.
- [x] Maturity-aware improvement or maintenance guidance.
- [x] Dynamic top-gap ranking and evidence text.
- [x] P0 route derived from the same gap source.
- [x] Valid star-band serialization for legacy ratings.
- [x] Backend-only covers for persisted projects; truthful no-source placeholders.
- [x] Latest diagnosis/source activity dates on project cards.
- [x] All 11 module scores available without increasing the visible row count.
- [x] Two-page dot navigation with active and keyboard-focus states.
- [x] Fixed card height and no module-panel overflow.

final result: passed

## 3.9 上传卡片与统一项目菜单增量 QA

- Source visual truth path: 2026-07-14 当前任务提供的上传页卡片批注截图与项目下拉菜单参考截图。
- Implementation screenshot path: `design-qa-upload-cards-aligned.png`、`design-qa-upload-project-menu.png`。
- State: 未选择项目默认态、项目菜单展开态、项目选中态。

### Alignment evidence

- 两张卡片内容宽度均为 330px，并在各自 453px 卡片中水平居中。
- 两侧步骤标签均为 `y=292 / h=16`，主标题均为 `y=317 / h=25`，底部控件均为 `y=368 / h=64`。
- 两侧内容组中心与卡片中心的垂直偏差均为 0px。
- 标题、项目选择框与文件拖入框的左、右边界差均为 0px。
- 项目选择文字与文件拖入主文案均为 `12px / 700`，颜色均为 `rgb(55, 64, 76)`。

### Menu evidence

- 上传页和工作台均渲染共享的 `ProjectMenuPanel`，避免两套列表视觉或交互分叉。
- 当前数据渲染 7 个真实项目；菜单列表支持内部滚动，并沿用最多 20 行的既有容量规则。
- 选中项目重新展开后只有 1 个 `.selected` 菜单项，并包含真实勾选图标。
- `Escape` 关闭：passed。
- 点击菜单外区域关闭：passed。
- 固定“新建诊断项目”操作：passed。

### Runtime checks

- Vite production build: passed。
- Django diagnosis tests: 18/18 passed。
- Browser console errors: none。

### Findings

- No remaining P0/P1/P2 defects in the upload-card alignment and project-menu scope.

final result: passed

## 3.8 评分记录管理增量 QA

- Source visual truth path: 2026-07-14 当前任务提供的评分记录浏览器批注截图，目标视口 1093 × 898。
- Implementation screenshot path: `design-qa-score-history-evidence.png`、`design-qa-score-history-evidence-modal.png`。
- Viewport: 目标 1093 × 898。
- State: 评分记录列表、选中版本、11 模块滚动明细、证据缩略图、完整证据弹窗、删除确认弹窗、删除后版本回退、切换版本后的项目总览与评分诊断。

### Full-view comparison evidence

- 源截图明确要求左侧版本列表不得高于右侧明细卡；实现将两侧统一为 653px，并将长列表改为内部滚动。
- 用户补充要求分数与删除按钮上下居右；实现改为独立右侧信息列，分数在右上、删除图标在右下。
- 用户补充要求切换版本后工作台内容联动；实现将选中记录写入 `latestDiagnosis`，使总览、诊断、缺口和任务使用同一版本对象。
- 用户补充要求模块切片可查看完整内容；实现只在弹窗中按自然宽高比呈现完整图，表格缩略图继续保持裁切和原有行密度。
- 修改后的浏览器全屏和弹窗截图均已取得；评分版本、模块列、证据列、固定摘要区与内部滚动区没有破坏既有卡片边界。

### Focused region comparison evidence

- Source focused region: 左侧评分版本列表及右侧 11 模块明细卡。
- Implementation focused region: `design-qa-score-history-evidence.png` 显示右侧固定摘要、固定五列表头和模块滚动区；`design-qa-score-history-evidence-modal.png` 显示遮罩、标题、完整证据图顶部与识别内容区。

### Fidelity surfaces

- Fonts and typography: 沿用既有 Inter / Noto Sans SC 字体和记录卡字号；浏览器截图确认右侧分数、星级与模块表头层级一致。
- Spacing and layout: 双侧 653px 高度、82px 记录卡、9px 卡间距；右侧摘要与表头固定，模块行只在内容区滚动。
- Colors and tokens: 沿用现有蓝色选中态、灰色图标和红色危险操作语义色。
- Image quality and assets: 缩略图来自后端保存的页面证据；缩略图 `48 × 36px`、`object-fit: cover`，弹窗图 `width: 100%`、`height: auto`、`object-fit: contain`，未生成替代图或占位假数据。
- Copy and content: 确认弹窗明确说明不可恢复以及总览将自动切换到剩余评分。
- Accessibility: 版本按钮使用 `aria-pressed`；删除按钮有版本化可访问名称；删除确认使用 `alertdialog`；证据预览使用 `dialog`、标题关联、可访问关闭按钮并支持 Escape。

### Interaction and runtime checks

- Django delete endpoint access control, latest-version response and last-record empty state: 18/18 automated tests passed.
- Vite production build: passed.
- 证据弹窗浏览器渲染: passed；图片自然尺寸 374 × 13342，渲染高度 29253px，弹窗图片区 520px，内部滚动成立。
- 缩略图与弹窗职责分离: passed；缩略图 `object-fit: cover`，弹窗图 `object-fit: contain`。
- 用户已于 2026-07-14 确认弹窗滑动正常，本轮不重复执行滚动手感测试。
- 控制台当前功能路径未出现新的运行时错误；日志中仅保留一次早于本轮修复的 Vite 热更新历史错误 `tasks is not defined`，当前构建与实际页面均未复现。

### Findings

- No remaining P0/P1/P2 defects in the evidence-thumbnail and evidence-modal scope.
- P3: macOS 默认使用覆盖式滚动条，静止时弹窗可能不显示常驻滚动轨；滚动内容和滚动行为均正常，保持系统原生表现。

final result: passed
