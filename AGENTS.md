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
