# Prototype Instructions

Version history, restore instructions, current Figma node references, and ready-to-use continuation prompts are documented in `agent.md`. Read both files before restoring or extending the project.

Run the local server yourself and open the preview in the browser available to this environment. Do not give the user server-start instructions when you can run it.

Before making substantial visual changes, use the Product Design plugin's `get-context` skill when the visual source is unclear or no longer matches the current goal. When the user gives durable prototype-specific design feedback, preferences, or decisions, record them in `AGENTS.md`.

When implementing from a selected generated mock, treat that image as the source of truth for layout, component anatomy, density, spacing, color, typography, visible content, and hierarchy.

## Durable design direction

- Match the supplied GEOBase dashboard references: white rounded app canvas, pale blue-gray surround, grouped left navigation, pale-blue active rows with electric-blue right rule, thin gray panel borders, generous radii, restrained enterprise analytics.
- Product-specific rule: overall PDP uses stars; individual modules use only 弱 / 中 / 强.
- Keep the first screen conclusion-led and focused on score, gaps, module maturity, and the P0 route.
- Overall diagnosis card must keep a spacious left/right composition: numeric score on the left; overall stars, page type, explanation, and T1 target on the right.
- The pre-upload starting state should contain only project selection and PDP content upload as its core tasks.
- The default product entry is a spacious home screen inspired by the supplied Lovart layout: one prominent PDP upload action plus recent project cards. Only after choosing a project or completing an import should the user enter 项目总览.
- Home is structurally independent from the project workbench and must not show the workbench sidebar. Once inside a project, the top bar must provide an explicit 返回首页 action.
- The project workbench top bar must also provide a fast project switcher so users can jump among recent projects without returning home.
- After a PDP upload completes, always show an independent diagnosis progress screen before score review; do not jump directly into the project overview.
- Keep a lightweight circular user-management entry in the top-right of the standalone homepage because the workbench sidebar is hidden there; it must reuse the same account menu as the sidebar user card.
- Current delivery priority is the evaluation loop: module review, score adjustment, completeness validation, locked score versions, history, and overview synchronization must remain functional.
- AI diagnosis versions are auto-confirmed and locked after all 11 modules and their evidence pass server validation; do not insert a mandatory human confirmation step. Manual review remains an optional correction flow that creates a new version.
- Keep model output and trusted scoring separate: model adapters may return evidence, judgments, confidence, and only the discrete coefficient `0 / 0.5 / 1`; the versioned backend scoring standard calculates module scores, total score, and overall stars.
- Treat `/api/diagnosis-config/` as the frontend source of truth for PDP module names, weights, maturity definitions, rule revision, and star bands. Never introduce a second hardcoded scoring scale in dashboard or review flows.
- Runtime AI model settings and PDP Skill settings must remain separate Django admin models and separate menu entries. Keep API keys and Skill tokens server-side and encrypted; the frontend may show only configured/unconfigured state, active model, rule version, source revision, and safe endpoint metadata.
- Never reuse or scrape local Codex/ChatGPT login sessions, cookies, tokens, or credential files as an OpenAI API key. Production model calls require an independently configured OpenAI Platform credential; Codex-session reviews must be labeled `codex_verified`, not `ai_auto`.
- Project cards must prefer backend `score_label` and `cover_url`; the selected project overview and score history must resolve to the same latest diagnosis version.
- Persisted project cards must never borrow static example artwork or example scores. When no backend cover exists, show the neutral no-source state; normalize legacy ratings through the active backend star bands before serialization; card dates use the newest project, diagnosis, or cover-source activity.
- Dashboard gap ranking, “为什么还不是” copy, P0 cards, and the full optimization route must derive from the selected project's latest module assessments. Use `max - score`, omit zero gaps, sort by gain then maturity/rule order, and bind the selected module's judgment/evidence; never restore hardcoded gap or task examples.
- The dashboard maturity card must expose all 11 modules without increasing its accepted six-row density. Use two manual pages (6 + 5 rows) with clickable pagination dots below the table, retain a fixed table/card height, and reset to page 1 when the active diagnosis data changes.
- The workbench project switcher must render the complete backend project list, fit up to 20 compact rows before internal scrolling, keep the create-project action outside the scroll region, and close on outside click or Escape.
- The score-diagnosis detail panel must never reuse static example copy across modules. It must bind the selected module's saved `judgment`, page evidence reason/OCR, maturity logic, and current scoring rule `strong_standard`; strong modules show maintenance/validation guidance while weak and medium modules show improvement guidance.
- The score-history version list must never grow taller than the adjacent module-detail card. Keep its accepted record density fixed, use internal vertical scrolling for longer histories, and provide a separate delete icon on every version with an irreversible-action confirmation modal before calling the backend delete endpoint.
- The selected score-history version is the active workbench diagnosis context. Switching versions must update project overview, score diagnosis, gap ranking, and optimization tasks; deleting a selected version falls forward to the first remaining record, while deleting another version preserves the current selection.
- Overall-score visualization uses the five priority whole-star stages 3/4/5/6/7 with their backend-configured page names. The marker moves on the visible 3–7 scale, while half-star ratings remain available as the current floating value.
- If diagnosis job creation or execution cannot reach the configured model or PDP Skill, show a blocking failure modal with the backend error and a route back to upload; never silently replace a forced production adapter with mock.
- Mock is test-only. Normal upload flows must block before job creation when `active_adapter=mock`; the backend must independently reject the request unless `PDP_ALLOW_MOCK_DIAGNOSIS=1` is explicitly set for automated tests.
- A configured API key is not proof of PDP readiness. Model verification must separately pass authentication, model discovery, text protocol, image/file ingestion, and structured 11-module output before the UI may call it usable for formal scoring.
- ModelVerse MiMo uses the OpenAI-compatible `chat_completions` protocol with image Data URLs. This path supports PNG/JPG but must reject PDF with a clear upload-format error; do not silently route PDFs through a non-working Files API.
- Keep Pydantic plus the server scoring engine as the hard safety boundary for every provider. Do not coerce malformed model fields or derive scores heuristically; a provider is ready only after all 11 modules, evidence coverage, and discrete coefficients validate.
- Preserve the legacy `/admin/diagnosis/integrationsettings/` redirect while SimpleUI users may still have the retired combined-settings tab cached; it must resolve to the independent AI model settings list instead of returning 404.
- Brand asset matching and AI image/page generation are deferred. Keep their information architecture visible only as clearly labeled gray disabled controls; do not present mock actions as usable capabilities.
- Login, registration, session recovery, profile editing, notification preferences, project creation, and PDP upload are baseline functions and must remain operational while the evaluation loop evolves.
