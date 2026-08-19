# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- Automated documentation synchronisation pipeline (`src/sync_engine/`)
- Linear pipeline: detect -> map -> analyse -> generate -> update -> validate -> report
- `ChangeDetector`  -  detects added/modified/deleted/renamed Python files via `git diff --name-status` with `shell=False` (security constraint S-1)
- `FileMapper`  -  maps each `.py` file stem to `docs/{stem}.md`; returns `Union[DocMapping, SkippedFile]`
- `AstAnalyser`  -  AST-based comparison of top-level function and class definitions between old and new source versions
- `UpdateGenerator`  -  formats `ChangeSummary` into Markdown listing (Added/Removed/Modified + last-synced date)
- `DocUpdater`  -  replaces `## Module Update` section using regex; atomic write via `.tmp` -> `os.replace()`
- `Validator`  -  validates heading presence and non-empty section body after each write
- `Reporter`  -  4-section Markdown sync report (Updated, Skipped-NoDoc, Skipped-NoSection, Failed) written to disk and stdout
- `Orchestrator`  -  full pipeline coordinator; exit 0 for skips, exit 1 only for failures
- `ConfigManager`  -  loads and validates `sync_rules.yaml` before pipeline starts (fail-fast)
- `scripts/run_sync.py`  -  CLI entry point supporting `--mode manual/pr`, `--base-ref`, `--head-ref`, `--changed-files`
- Full test suite: 45 tests across 9 test files, 91% code coverage
- Agentic SDLC pipeline infrastructure: 8 Claude agents, 3 skills, pre/post-commit hooks, MCP server
- SDLC artifacts: requirements, architecture, design-review, impl-plan, code-review, verification-report

### JIRA
- EPMCDMETST-60340
