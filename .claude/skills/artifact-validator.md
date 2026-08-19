---
name: artifact-validator
description: Validate SDLC artifacts for completeness, required sections, and quality standards before proceeding to the next stage.
---

# Artifact Validator

Ensure every SDLC artifact meets quality gates before the next stage begins.

## Instructions

1. Identify which artifact to validate from the context (or from the file path provided).
2. Read the artifact file.
3. Run the checks listed below for that artifact type.
4. Report a pass/fail table — list every failing check explicitly.
5. If any required check fails, do NOT proceed to the next stage. Ask the current agent to fix the artifact.

## Validation Checklist

### `artifacts/requirements.md`
- [ ] `## Functional Requirements` section present
- [ ] `## Non-Functional Requirements` section present
- [ ] At least 5 functional requirements documented
- [ ] At least 3 non-functional requirements documented
- [ ] Requirements are numbered and specific (no vague terms like "should maybe", "possibly")

### `artifacts/architecture.md`
- [ ] `## System Overview` section present
- [ ] `## Technology Stack` section present
- [ ] `## Component Architecture` section present
- [ ] `## Design Decisions` section present
- [ ] At least 3 distinct components described

### `artifacts/design-review.md`
- [ ] `## Review Checklist` section present
- [ ] `## Issues Identified` section present
- [ ] `## Recommendations` section present
- [ ] `## Approval Status` section present — must be one of: Approved / Approved with Conditions / Rejected

### `artifacts/impl-plan.md`
- [ ] `## Implementation Steps` section present (minimum 5 steps)
- [ ] `## File Structure` section present
- [ ] `## Dependencies` section present
- [ ] `## Test Strategy` section present
- [ ] File paths are specified, dependency versions listed

### `artifacts/code-review.md`
- [ ] `## Code Quality` section present
- [ ] `## Test Coverage` section present
- [ ] `## Security Review` section present
- [ ] `## Performance Analysis` section present
- [ ] `## Approval Status` section present
- [ ] Test coverage >= 80 % stated

### `artifacts/verification-report.md`
- [ ] `## Test Results` section present
- [ ] `## Coverage Report` section present
- [ ] `## Requirements Traceability` section present
- [ ] `## Known Issues` section present
- [ ] All tests passing (or failures documented)

## Output

Report results as a table:

| Check | Status |
|-------|--------|
| Functional Requirements section | ✅ PASS |
| ... | ... |

End with one of:
- **VALIDATION PASSED** — proceed to next stage.
- **VALIDATION FAILED** — list blocking issues; do not proceed.
