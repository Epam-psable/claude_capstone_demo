---
name: sdlc-status
description: Show the current status of the Agentic SDLC pipeline — which stages are complete, which is next, and what artifacts exist.
---

# SDLC Pipeline Status

Check the status of all 8 pipeline stages by looking for their output artifacts.

## Instructions

1. List the contents of `artifacts/` to see which stage outputs exist.
2. Check `src/sync_engine/` for Stage 5 output (source code).
3. Check `tests/` for Stage 7 output (test suite).
4. Report a status table:

| Stage | Agent | Artifact | Status |
|-------|-------|----------|--------|
| 1 – Requirements | `requirement-agent` | `artifacts/requirements.md` | ✅ / ❌ |
| 2 – Architecture | `architecture-agent` | `artifacts/architecture.md` | ✅ / ❌ |
| 3 – Design Review | `design-review-agent` | `artifacts/design-review.md` | ✅ / ❌ |
| 4 – Impl Planning | `implementation-planning-agent` | `artifacts/impl-plan.md` | ✅ / ❌ |
| 5 – Implementation | `implementation-agent` | `src/sync_engine/*.py` | ✅ / ❌ |
| 6 – Code Review | `code-review-agent` | `artifacts/code-review.md` | ✅ / ❌ |
| 7 – Verify | `verify-agent` | `artifacts/verification-report.md` | ✅ / ❌ |
| 8 – Create PR | `create-pr-agent` | GitHub PR | ✅ / ❌ |

5. Identify the **next stage** to run and show the command to invoke it.
6. Show the most recent git commit for each artifact (use `git log --oneline -- <file>`).
