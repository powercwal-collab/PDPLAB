---
name: pdp-detail-page-methodology
description: Diagnose, score, and improve ecommerce product detail pages (PDP/详情页) with a reusable UX strategy methodology. Use when the user asks for PDP/page scoring, detail-page audit, module maturity, star rating, conversion diagnosis, page structure template, improvement cases, or reusable methodology for sports outdoor, brand apparel, kidswear, shoes, 3C, health, beauty, bags, luxury, or other ecommerce categories.
---

# PDP Detail Page Methodology

Use this skill as a senior ecommerce UX strategy and creative visual director. Diagnose PDPs from screenshots, PDFs, Figma references, spreadsheets, or written briefs. Start with the conclusion, then give scoring logic, then provide executable improvement cases.

## Core Rule

Use **overall star rating** only for the whole page. Use **maturity** for individual modules.

- Module score coefficient: `0 = weak`, `0.5 = medium`, `1 = strong`.
- Module score: `module weight × coefficient`.
- Total score: sum all module scores.
- Overall star: map total score rate to star band.

Never call a single module "5-star" or "3-star"; call it `弱 / 中 / 强`.

Apply these hard zero-score gates before judging quality:

- `全部11个模块`: formal presence is not module existence. A heading, placeholder section, generic copy, repeated/decorative image, empty interaction shell, generic icon row, or templated service/recommendation block without product-specific decision value scores coefficient `0` and is `弱`. A module may enter coefficient `0.5` judgment only after it contains qualifying product-specific information or visual evidence that helps answer a concrete purchase question.
- `产品KV/封面故事`: copy alone does not constitute a KV. If the module has only product copy, slogans, or text without a corresponding product-led hero visual, score coefficient `0` and mark it `弱`.
- `沉浸式购物/场景化`: white/gray-background model photos, isolated studio try-on photos, and front/back model views alone do not constitute a scene. If these are the only assets, score coefficient `0` and mark it `弱`.

Do not upgrade any module to `中` merely because its formal container exists. First pass the global effective-existence gate and any module-specific hard gate, then judge information, visual quality, tier fit, and consumer fit.

## Standard Workflow

1. Identify category, target user, business goal, traffic context, and likely decision risk.
2. Identify case positioning and visual tier: T2 basic material PDP, T1 standard conversion PDP, or T0 benchmark growth PDP.
3. Score the page with the 11-module PDP scorecard.
4. Explain why the whole page belongs to its star band.
5. Identify the highest-impact weak or medium modules.
6. Give prioritized improvement cases, not generic suggestions.
7. Tie each action to user mind, brand expression, commercial conversion, and visual creativity.

## Required Output

When diagnosing a PDP, include:

1. **Core judgment**: one direct paragraph with total score and overall star.
2. **Scoring state table**: module, weight, coefficient, score, maturity, judgment.
3. **Business logic**: why the page belongs to its star band, and why it is not the next band.
4. **Improvement cases**: P0/P1/P2 actions with concrete module examples and expected score movement.
5. **Expected value**: conversion, trust, retention, basket size, or content efficiency impact.

Use this maturity mapping:

| coefficient | maturity | meaning |
|---:|---|---|
| 0 | 弱 | 无对应模块，用户无法在页面中获得该类购买决策信息 |
| 0.5 | 中 | 有对应模块，但信息浅或视觉弱，或偏信息维度、缺少视觉素材吸引力判断；设计信息与视觉素材任一维度不达标，都会影响消费者继续理解 |
| 1 | 强 | 有对应模块，且设计信息与视觉素材都围绕消费者需求展开，内容、证据、视觉表达与购买决策高度契合 |

Judge each module by this order:

1. Effective existence: ignore headings, placeholders, generic/repeated assets, and templated components that provide no product-specific purchase-decision value. If no qualifying content remains, mark the module `弱`.
2. Module-specific gates: apply any stricter zero-score condition, especially for KV and scenario modules.
3. Information and visual quality: only after effective existence is established, mark the module `中` when its useful information or visual evidence is present but shallow, incomplete, scattered, or visually weak.
4. Visual tier fit: judge whether the qualifying material and layout reach the expected T1/T0 standard for this case positioning.
5. Consumer fit: mark the module `强` only when its information plus visual assets clearly answer the target consumer's purchase questions.

## References

Read the relevant reference file only when needed:

- `references/scoring-standard.md`: full 11-module scoring standard, weights, star bands, and output table rules.
- `references/visual-tier-standard.md`: case positioning, T1/T0 visual tier standards, material direction, layout direction, and how visual quality enters module maturity scoring.
- `references/ya-kids-visual-tier-cases.md`: calibrated YA Kids visual tier case library across shoes, apparel, and accessories, including T2/T1/T0 examples.
- `references/page-structure.md`: reusable PDP structure template from first screen to closing recommendation.
- `references/category-lenses.md`: category-specific scoring lenses for kidswear, sports outdoor, apparel, 3C, wellness, beauty, bags, and luxury.
- `references/improvement-case-library.md`: concrete improvement case patterns for weak/medium modules.
- `references/reporting-method.md`: how to explain the method in a business report or client presentation.

## Assets

Reusable assets are bundled under `assets/`:

- `assets/PDP详情页诊断评分表_v3_含页面结构模板.xlsx`: editable scoring workbook.
- `assets/dynamic-html/index.html`: dynamic HTML explainer for teaching or sharing the methodology.
- `assets/dynamic-html/DESIGN.md`: visual identity notes for the explainer.

If the user asks to create or edit a workbook, use the spreadsheet skill and treat the bundled workbook as the template.
