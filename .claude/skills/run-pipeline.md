---
name: run-pipeline
description: Orchestrate the full Agentic SDLC pipeline from the current stage to completion. Runs each agent in order, waits for its artifact, then proceeds to the next.
---

# Run SDLC Pipeline

Orchestrate all remaining stages of the Agentic SDLC pipeline in order.

## Instructions

1. First invoke `/sdlc-status` to identify the next incomplete stage.
2. For each incomplete stage (in order), invoke the corresponding agent:
   - Stage 1 → `@requirement-agent`
   - Stage 2 → `@architecture-agent`
   - Stage 3 → `@design-review-agent`
   - Stage 4 → `@implementation-planning-agent`
   - Stage 5 → `@implementation-agent`
   - Stage 6 → `@code-review-agent`
   - Stage 7 → `@verify-agent`
   - Stage 8 → `@create-pr-agent`
3. After each stage completes, verify its artifact exists and is committed before proceeding.
4. If a stage fails or requires user input, pause and report clearly.
5. After all stages complete, run `/sdlc-status` to confirm all ✅.

## Dependency Rules

- Stage 2 requires `artifacts/requirements.md`
- Stage 3 requires `artifacts/architecture.md`
- Stage 4 requires `artifacts/design-review.md`
- Stage 5 requires `artifacts/impl-plan.md`
- Stage 6 requires `src/sync_engine/` to contain source files
- Stage 7 requires `artifacts/code-review.md`
- Stage 8 requires `artifacts/verification-report.md`

Do NOT skip stages or proceed if a dependency artifact is missing.
