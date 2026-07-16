# Score Diagnosis Design QA

- Source visual truth: `/var/folders/7s/qqmq1xlx4jv330_r04qc6hb80000gn/T/codex-clipboard-25a5ac09-a170-4609-8d7d-d91b636246e1.png`
- Implementation screenshot: `/Users/lixiao/Documents/人设背景提示词/outputs/pdp-lab-prototype/qa-score-diagnosis-final.png`
- Side-by-side comparison: `/Users/lixiao/Documents/人设背景提示词/outputs/pdp-lab-prototype/qa-score-diagnosis-comparison.png`
- Viewport: 1280 × 720
- State: Nike Vomero 18 / 评分诊断 / 卖点与功能证明

## Full-view comparison evidence

The implementation preserves the source two-column diagnostic hierarchy, module selection state, title/button placement, score, judgment, evidence copy, and maintenance guidance. The intentional addition is a compact evidence row beneath the score, replacing the earlier oversized image preview.

## Focused region comparison evidence

- Header: priority badge, module title, and review button retain the original alignment while using tighter vertical spacing.
- Evidence: thumbnail height is 50px, uses the model evidence `page_index + bbox` to locate the corresponding source slice, and provides one explicit “查看” action per image.
- Long content: the complete judgment/evidence/guidance region is one vertical scroll container; individual titles and paragraphs do not create nested scrollbars.
- Image modal: opens from the evidence row, supports full long-image vertical scrolling, closes by the close control or backdrop, and has no horizontal page overflow.

## Required fidelity surfaces

- Fonts and typography: existing Source Han/system font stack, weights, sizes, line heights, and wrapping retained.
- Spacing and layout rhythm: source card proportions retained; header and score spacing tightened without changing the information order.
- Colors and visual tokens: existing PDP Lab blue, semantic maturity colors, borders, and neutral backgrounds reused.
- Image quality and asset fidelity: real uploaded PDP source image is used; thumbnail positioning follows stored evidence coordinates rather than a generic crop.
- Copy and content: original diagnostic logic and all evidence text entries remain unchanged.

## Interaction checks

- Module switching updates title, score, maturity, copy, and evidence thumbnail.
- “查看” opens the complete evidence modal.
- Long image container: 520px visible height / 29,253px scroll height; vertical scrolling available.
- Page horizontal overflow: none.
- Frontend production build: passed.
- Django system check: passed.

## Comparison history

1. P2: oversized evidence preview increased card height and displaced the diagnostic copy. Fixed by replacing it with a 64px evidence row and 50px thumbnail.
2. P2: individual headings and paragraphs had nested scroll behavior. Fixed by making the complete copy area the single vertical scroll container.
3. P1: generic thumbnail crop did not reliably match the stored evidence slice. Fixed by deriving object position from `page_index`, normalized `bbox`, and the model's 1400px slicing rules.

## Findings

No remaining actionable P0/P1/P2 mismatch in the requested scope.

## Follow-up polish

- P3: future diagnosis jobs can persist physical crop files to remove all client-side crop estimation.

final result: passed
