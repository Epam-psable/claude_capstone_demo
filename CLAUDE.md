# Claude Code Capstone: Agentic SDLC Pipeline

This project implements a full **Agentic SDLC Pipeline** using Claude Code  -  mirroring the GitHub Copilot capstone but driven entirely through Claude Code agents, skills, and hooks.

## Use Case

**Automated Documentation Sync**  -  a Python pipeline that detects source code changes and synchronises the affected Markdown documentation automatically.

## Agentic SDLC Stages

Work through the pipeline in order. Each stage has a dedicated Claude agent defined in `.claude/agents/`.

| Stage | Agent | Output | Status |
|-------|-------|--------|--------|
| 1 - Requirements   | `requirement-agent`            | `artifacts/requirements.md`         | ✅ Complete |
| 2 - Architecture   | `architecture-agent`           | `artifacts/architecture.md`         | ✅ Complete |
| 3 - Design Review  | `design-review-agent`          | `artifacts/design-review.md`        | ✅ Complete |
| 4 - Impl Planning  | `implementation-planning-agent`| `artifacts/impl-plan.md`            | ✅ Complete |
| 5 - Implementation | `implementation-agent`         | source code in `src/`               | ✅ Complete |
| 6 - Code Review    | `code-review-agent`            | `artifacts/code-review.md`          | ✅ Complete |
| 7 - Verify         | `verify-agent`                 | `artifacts/verification-report.md`  | ✅ Complete |
| 8 - Create PR      | `create-pr-agent`              | PR on GitHub                        | ✅ Complete |

## Available Skills

| Skill | Command | Purpose |
|-------|---------|---------|
| Pipeline status | `/sdlc-status` | Show which stages are complete and what's next |
| Run full pipeline | `/run-pipeline` | Orchestrate all remaining stages in order |
| Run sync engine | `/sync-docs` | Execute the documentation sync CLI |

## Available MCP Tools

The **Capstone MCP server** is at `mcp_server/server.py` and provides:

| Tool | Purpose |
|------|---------|
| `read_user_story` | Read user story from Confluence (page_id or space+title) or JIRA |
| `generate_questions` | Generate clarifying questions from the story |
| `record_answer` | Record Q&A answers into the session |
| `capture_requirements` | Generate structured requirements markdown |
| `get_session_status` | Check Q&A session progress |
| `list_active_sessions` | List all open sessions |
| `create_jira_story` | Create a new Story in JIRA project EPMCDMETST |

**Confluence details:**
- URL: `https://epam-team-pnqaof71.atlassian.net/wiki`
- Space: `~712020ff5ba6e8e09b44d0b6155976e4654329`
- User story page ID: `44498945`

**JIRA details:**
- URL: `https://jiraeu.epam.com`
- Project: `EPMCDMETST`
- Story: `EPMCDMETST-60340`

The **GitHub CLI** (`gh`) is available for PR operations in Stage 8.

## Git Hooks Setup

The repository ships with pre-commit and post-commit git hooks. Run this once after cloning:

```bash
bash scripts/setup-hooks.sh
```

This installs `scripts/hooks/pre-commit` (validates SDLC artifact sections, blocks secrets) and `scripts/hooks/post-commit` (logs commits, suggests next stage) into `.git/hooks/`.

## Hooks

Hooks are configured in `.claude/settings.json`:

| Event | Trigger | Action |
|-------|---------|--------|
| `PostToolUse` | `Write` to `artifacts/` | Log artifact path |
| `PostToolUse` | `Bash` with `pytest` | Remind to check test output |
| `PreToolUse` | `Bash` with `git push` | Safety reminder before push |

## Environment Variables

See `.env` at project root. Key vars:

```
DOCS_ROOT=docs
SRC_ROOT=src/sync_engine
SYNC_REPORT_OUTPUT=artifacts/sync-report.md
LOG_LEVEL=INFO
CONFLUENCE_PAGE_ID=44498945
JIRA_STORY_KEY=EPMCDMETST-60340
```

MCP server credentials are in `mcp_server/.env` (gitignored).

## Project Layout

```
claude_capstone_demo/
+-- CLAUDE.md                        <- you are here
+-- CHANGELOG.md                     <- Keep a Changelog format
+-- README.md
+-- .env                             <- sync engine environment variables (gitignored)
+-- .env.example                     <- env var template (committed)
+-- .gitignore
+-- pyproject.toml                   <- build metadata + pytest config
+-- requirements.txt
+-- requirements-dev.txt
+-- .claude/
|   +-- agents/                      <- per-stage agent definitions (8 agents)
|   +-- skills/                      <- slash-command skills
|   |   +-- sdlc-status.md           <- /sdlc-status
|   |   +-- run-pipeline.md          <- /run-pipeline
|   |   +-- sync-docs.md             <- /sync-docs
|   |   +-- artifact-validator.md    <- /artifact-validator
|   |   +-- git-operations.md        <- /git-operations
|   |   +-- read-user-story.md       <- /read-user-story
|   +-- settings.json                <- Claude Code hooks configuration
|   +-- settings.local.json          <- MCP server config (gitignored)
+-- mcp_server/                      <- capstone MCP server (MCP 2.0)
|   +-- server.py
|   +-- requirements.txt
|   +-- .env                         <- credentials (gitignored)
+-- artifacts/                       <- SDLC documents produced by agents
|   +-- requirements.md              ✅ Stage 1
|   +-- architecture.md              ✅ Stage 2
|   +-- design-review.md             ✅ Stage 3
|   +-- impl-plan.md                 ✅ Stage 4
|   +-- code-review.md               ✅ Stage 6
|   +-- verification-report.md       ✅ Stage 7
|   +-- pr-description.md            ✅ Stage 8
|   +-- user_story.md                <- captured from Confluence (Stage 1)
|   +-- sync-report.md               <- generated at runtime by sync engine
+-- config/
|   +-- sync_rules.yaml              <- source extensions, docs_root
|   +-- doc_template.yaml
|   +-- pipeline-config.yaml
|   +-- validation-rules.yaml
+-- docs/                            <- Markdown documentation (sync target)
+-- src/
|   +-- sync_engine/                 <- ✅ Stage 5  -  13 source modules
|       +-- __init__.py
|       +-- models.py
|       +-- exceptions.py
|       +-- utils.py
|       +-- config_manager.py
|       +-- change_detector.py
|       +-- mapper.py
|       +-- analyser.py
|       +-- update_generator.py
|       +-- doc_updater.py
|       +-- validator.py
|       +-- reporter.py
|       +-- orchestrator.py
+-- scripts/
|   +-- run_sync.py                  <- CLI entry point (Stage 5)
|   +-- setup-hooks.sh               <- install git hooks (run once after clone)
|   +-- hooks/
|       +-- pre-commit               <- validates artifacts, blocks secrets
|       +-- post-commit              <- logs commits, suggests next stage
+-- tests/                           <- ✅ Stage 5/7  -  45 tests, 91% coverage
    +-- conftest.py
    +-- test_config_manager.py
    +-- test_change_detector.py
    +-- test_mapper.py
    +-- test_analyser.py
    +-- test_update_generator.py
    +-- test_doc_updater.py
    +-- test_validator.py
    +-- test_reporter.py
    +-- test_orchestrator.py
```

## Agentic Pipeline Orchestration

### Handoff protocol between stages

Each agent MUST:
1. Read all prerequisite artifacts listed in its dependency chain.
2. Produce its output artifact and write it to `artifacts/` (or `src/` for Stage 5).
3. Validate its output is complete before committing.
4. Commit with message: `docs: <stage-name> artifact` or `feat: implement sync engine`.
5. Confirm completion with a one-line summary before the next stage starts.

### Stage dependency chain

```
[Confluence] -> Stage 1 (requirements.md)
                    |
              Stage 2 (architecture.md)
                    |
              Stage 3 (design-review.md)
                    |
              Stage 4 (impl-plan.md)
                    |
              Stage 5 (src/sync_engine/*.py + scripts/run_sync.py)
                    |
              Stage 6 (code-review.md)
                    |
              Stage 7 (verification-report.md + tests/)
                    |
              Stage 8 (GitHub PR)
```

### If a stage fails

- Do **not** skip to the next stage.
- Report the specific failure with file and line number.
- Ask the user whether to retry, fix manually, or abort.

## Running the Sync Engine

```bash
# Manual mode  -  sync against current git working tree changes
python scripts/run_sync.py --mode manual

# PR mode  -  sync against a git diff range
python scripts/run_sync.py --mode pr --base-ref HEAD~1 --head-ref HEAD

# Provide explicit changed files
python scripts/run_sync.py --mode manual --changed-files "modified:src/sync_engine/mapper.py"
```

## Running Tests

```bash
pip install -r requirements-dev.txt
pytest tests/ -v --cov=src
```

## General Rules for Agents

- Read existing artifacts before proposing new content.
- Do **not** assume or invent requirements that are not documented or confirmed by the user.
- Ask only the questions necessary to remove ambiguity.
- Commit each artifact to git after it is finalised.
- Follow dependency order: each stage depends on the outputs of previous stages.
- Never overwrite an artifact from a previous stage.
