# PDP Scoring Standard

Use this file when scoring a PDP or explaining the scoring logic.

## Score Formula

- `module score = module weight × coefficient`
- `total score = sum(module scores)`
- `coefficient = 0 / 0.5 / 1`

Module maturity:

| coefficient | maturity | definition |
|---:|---|---|
| 0 | 弱 | 无对应模块，用户无法在页面中获得该类购买决策信息 |
| 0.5 | 中 | 有对应模块，但信息浅或视觉弱，或偏信息维度、缺少视觉素材吸引力判断；设计信息与视觉素材任一维度不达标，都会影响消费者继续理解 |
| 1 | 强 | 有对应模块，且设计信息与视觉素材都围绕消费者需求展开，内容、证据、视觉表达与购买决策高度契合 |

`有对应模块` means effective existence, not formal presence. Do not treat a section title, placeholder, generic copy, repeated/decorative image, generic icon row, empty interaction shell, or templated component as an existing module when it provides no product-specific purchase-decision value.

Module maturity judgment order:

1. Global effective-existence gate: remove headings, placeholders, generic/repeated/decorative assets, empty shells, and templated content with no product-specific decision value from consideration. If nothing qualifying remains, score `0` and mark `弱`.
2. Module-specific hard gates: apply the KV and scenario gates below.
3. Design information and visual asset quality: only after the module passes the gates, score `0.5` and mark `中` when useful product-specific information or visual evidence exists but is shallow, scattered, incomplete, visually weak, or not sufficiently explanatory.
4. Visual tier fit: compare the qualifying material against the case positioning and expected T1/T0 standard. If a T0-positioned product only reaches T1-level material or layout, it should usually be `中`, not `强`.
5. Consumer-demand fit: score `1` and mark `强` only when the qualifying information plus visual assets clearly answer the target consumer's purchase questions.

## Hard Zero-Score Gates

These rules prevent formal presence from receiving coefficient `0.5`. Coefficient `0.5` means qualifying product-specific decision support exists but its depth, completeness, proof, or visual execution is insufficient.

| module | coefficient `0` condition | qualifying evidence required before any score is possible |
|---|---|---|
| 全部11个模块 | Only a heading, placeholder, generic copy, repeated/decorative image, generic icon row, empty interaction shell, or templated component is present, without product-specific decision value. | Product-specific information or visual evidence that helps answer at least one concrete purchase question assigned to the module. |
| 产品KV/封面故事 | Only copy, slogans, titles, selling-point text, or text blocks are present. Text alone is not a KV. | A product-led hero visual or composed campaign/cover image that works with the claim to establish product identity, hierarchy, and a visual focal point. |
| 沉浸式购物/场景化 | The only assets are white/gray-background model images, isolated studio try-on images, or front/back model views. These are fit/display assets, not scenes. | A recognizable real-use, lifestyle, sport, environment, movement, styling, or emotional context that lets the user imagine using or wearing the product. |

If a page fails a gate, mark the module `弱` even when the copy is polished or the studio model photography is high quality. Those assets may still support other modules such as selling points, details, or fit.

## Coefficient Boundary Test

Before assigning `0.5`, answer both questions:

1. What concrete purchase question does the visible content answer?
2. What product-specific information or visual evidence answers it?

If either answer cannot be named from the page, assign `0`, not `0.5`. If both can be named but the answer is shallow, incomplete, weakly evidenced, or visually underdeveloped, assign `0.5`.

When writing the judgment column, mention both:

- information quality: whether the module answers concrete purchase questions.
- visual quality: whether the module uses attractive, relevant, explanatory assets rather than plain listing or decorative images.
- visual tier fit: whether material and layout match the page's T1 or T0 case positioning.

## Overall Star Bands

Use stars only for the whole page.

| total score rate | overall star | page type | business meaning |
|---:|---|---|---|
| <10 | 1星 | 严重信息缺失页 | 几乎无法转化 |
| 10-20 | 1.5星 | 信息缺失页 | 很难转化 |
| 20-27.5 | 2星 | 基础陈列页 | 只能展示商品 |
| 27.5-35 | 2.5星 | 基础陈列增强页 | 商品展示更完整，但决策支持弱 |
| 35-42.5 | 3星 | 基础说明页 | 能看懂，但说服弱 |
| 42.5-50 | 3.5星 | 基础说明增强页 | 信息更完整，但证据和视觉吸引不足 |
| 50-57.5 | 4星 | 完整说明页 | 基本完整，但转化阻力多 |
| 57.5-65 | 4.5星 | 完整说明增强页 | 接近成熟转化，但关键模块仍偏中 |
| 65-72.5 | 5星 | 成熟转化页 | 能支撑大多数用户决策 |
| 72.5-80 | 5.5星 | 成熟转化增强页 | 转化链路成熟，少数专业证据仍待补强 |
| 80-85 | 6星 | 专业决策页 | 有强证据、强场景、强信任 |
| 85-90 | 6.5星 | 专业决策增强页 | 专业证据充分，接近标杆增长 |
| 90+ | 7星 | 标杆增长页 | 形成品牌级内容资产 |

## 11 Modules

| module | weight | strong standard |
|---|---:|---|
| 产品KV/封面故事 | 10 | 0.5-1屏内以产品主导的英雄视觉配合文案，讲清产品主张、系列定位和核心卖点；只有文案必须计 `0` |
| 沉浸式购物/场景化 | 18 | 场景覆盖真实使用、穿搭、运动状态和情绪代入；只有白/灰底模特图或正背面图必须计 `0` |
| 卖点与功能证明 | 14 | 核心卖点排序清楚，有技术、材料、对比或使用证据 |
| 产品互动/动态内容 | 8 | 视频、AR、3D或动效直接解释功能、结构或试穿效果 |
| 细节查阅 | 12 | 多角度、颜色、材质、结构、局部细节完整 |
| 尺码/适配与对比选购 | 10 | 测量方式、脚型/身型、版型建议、消费者荐言、系列对比完整 |
| 基础信息 | 8 | 面料、材质、成分、颜色、货号、规格结构化呈现 |
| 使用说明/服务事项 | 5 | 服务、护理、退换、售后能降低购买顾虑 |
| 关联推荐/延展购买 | 5 | 推荐基于系列、场景、穿搭、用户意图 |
| 品牌/产品背书 | 5 | 有认证、奖项、机构、科技来源、用户口碑或品牌资产 |
| 页面结构与节奏 | 5 | 封面-沉浸-卖点-细节-信息-服务-推荐-背书形成购买叙事 |

## Output Table

Use this table format for scoring state:

| 模块 | 权重 | 评分系数 | 得分 | 成熟度 | 判断 |
|---|---:|---:|---:|---|---|

Keep judgments specific. Name visible evidence from the page, not generic wording.
