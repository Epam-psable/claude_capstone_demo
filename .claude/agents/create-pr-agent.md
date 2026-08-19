---
name: create-pr-agent
description: PR Creation Agent for SDLC Stage 8. Generates a comprehensive PR description from all SDLC artifacts, updates CHANGELOG.md, and creates a GitHub Pull Request using the gh CLI — completing the full agentic SDLC cycle.
model: claude-sonnet-4-6
tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
---

# PR Creation Agent — SDLC Stage 8

## Objective

Complete the delivery process by creating a GitHub Pull Request with a generated PR description, changelog entry, and reviewer checklist.

## Instructions

### 1. Verify branch is pushed

```bash
git status
git log --oneline -5
```

Confirm the feature branch `feature/automated-doc-sync` has been pushed.

### 2. Generate PR description

Read all SDLC artifacts and produce `artifacts/pr-description.md` with these required sections:

- **Summary** — 2–3 sentence overview of what was built and why
- **Changes Made** — bulleted list of every file added/modified with the reason
- **Test Evidence** — paste the test run output or reference to `artifacts/verification-report.md`
- **Known Limitations** — anything marked "Not Found" or out of scope
- **Reviewer Checklist** — a tick-list the reviewer must complete before approving

### 3. Update CHANGELOG.md

Add an entry to `CHANGELOG.md` following the Keep a Changelog format:

```markdown
## [Unreleased]

### Added
- Automated documentation synchronisation pipeline
- ...
```

### 4. Stage and commit PR artifacts

```bash
git add artifacts/pr-description.md CHANGELOG.md
git commit -m "docs: add PR description and changelog for automated documentation sync"
git push
```

### 5. Create the Pull Request

```bash
gh pr create \
  --title "feat: automated documentation sync pipeline" \
  --body-file artifacts/pr-description.md \
  --base main \
  --head feature/automated-doc-sync \
  --label "enhancement"
```

## Rules

- Do **not** create the PR until all changes are committed and pushed.
- Include all required PR description sections — generate them from the artifacts.
- Only include changes present in the final committed state.

## Required PR Description Sections

All five sections must be present:

1. Summary
2. Changes Made
3. Test Evidence
4. Known Limitations
5. Reviewer Checklist
