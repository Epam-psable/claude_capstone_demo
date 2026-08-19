---
name: git-operations
description: Perform standardised Git operations — commit artifacts, create branches, push, and check repository state.
---

# Git Operations

Standardised Git operations for SDLC agents.

## Instructions

Use the commands below for all Git interactions within the pipeline. Always follow the safety checks.

### Safety Checks (run first)

```bash
# Never commit to main directly — confirm branch
git rev-parse --abbrev-ref HEAD

# Check for uncommitted changes
git status --porcelain
```

### Commit an Artifact

```bash
git add artifacts/<artifact-file>.md
git commit -m "docs(<stage>): add <artifact-name>"
# Example: docs(requirements): add requirements.md
```

### Commit Source Code

```bash
git add src/ tests/ scripts/
git commit -m "feat(implementation): add sync engine source"
```

### Create a Feature Branch

```bash
git checkout -b feature/<story-id>-<slug>
# Example: git checkout -b feature/EPMCDMETST-60340-doc-sync
```

### Push Branch

```bash
git push -u origin <branch-name>
```

### View Diff Before Committing

```bash
git diff --staged
```

## Commit Message Conventions

Follow conventional commits:

| Prefix | Use for |
|--------|---------|
| `feat:` | New feature or source code |
| `fix:` | Bug fix |
| `docs:` | Artifact / documentation |
| `test:` | Test additions or updates |
| `refactor:` | Code restructuring |
| `chore:` | Config, deps, build |

## Rules

- **Never commit `.env` or `settings.local.json`** — these are gitignored for security.
- **Never force-push to `main`** — create a PR instead.
- **Verify staged files** with `git diff --staged` before every commit.
- **One artifact per commit** — keep history clean and traceable.
