# System Architecture: Automated Documentation Sync

**Stage:** 2 — Architecture
**Date:** 2026-08-18
**JIRA Story:** EPMCDMETST-60340
**Author:** architecture-agent
**Depends on:** `artifacts/requirements.md`

---

## System Overview

The Automated Documentation Sync system is a Python CLI tool that detects Python source file changes via `git diff`, maps each changed file to its corresponding Markdown documentation file, and updates only the `## Module Update` section of each matched doc file with a structured summary of what changed (functions/classes added, removed, or modified).

The system is entirely self-contained: no external services, no databases, no network calls. It runs as a one-shot CLI invocation and produces a Markdown sync report.

---

## Architecture Recommendation

**Style: Linear Processing Pipeline (Layered)**

Each stage of processing has a single responsibility and hands its output to the next stage. This matches the data flow perfectly: detect → map → analyse → generate → update → validate → report.

**Justification:**
- Requirements explicitly define a sequential, deterministic workflow (FR-1 → FR-12).
- Idempotency requirement (NFR-4) is easiest to guarantee with a stateless, single-pass pipeline.
- "Keep it simple" (NFR-2) rules out event-driven or reactive patterns.
- No concurrency required — no performance constraint (Q9).
- Clear separation of concerns makes each stage independently testable (NFR-6).

---

## Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     CLI Entry Point                          │
│                  scripts/run_sync.py                         │
│           --mode manual|pr  --base-ref  --head-ref           │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                      Orchestrator                            │
│              src/sync_engine/orchestrator.py                 │
│   Coordinates all stages; collects results; triggers report  │
└──┬────────────────────────────────────────────────────────┬─┘
   │                                                        │
   ▼                                                        ▼
┌──────────────────────┐              ┌─────────────────────────┐
│   Change Detector    │              │    Config Manager        │
│  change_detector.py  │              │   config_manager.py      │
│  Runs git diff;      │              │  Loads sync_rules.yaml   │
│  filters .py files   │              │  and .env settings       │
└──────────┬───────────┘              └─────────────────────────┘
           │
           ▼
┌──────────────────────┐
│     File Mapper      │
│      mapper.py       │
│  Maps .py → .md      │
│  by filename         │
└──────────┬───────────┘
           │ matched files
           │ (unmatched → warning → skip)
           ▼
┌──────────────────────┐
│    AST Analyser      │
│     analyser.py      │
│  Parses Python AST;  │
│  extracts changes    │
│  (add/remove/modify) │
└──────────┬───────────┘
           │ ChangeSummary
           ▼
┌──────────────────────┐
│   Update Generator   │
│  update_generator.py │
│  Formats the         │
│  ## Module Update    │
│  section content     │
└──────────┬───────────┘
           │ formatted Markdown block
           ▼
┌──────────────────────┐
│    Doc Updater       │
│    doc_updater.py    │
│  Replaces ## Module  │
│  Update section;     │
│  preserves all else  │
└──────────┬───────────┘
           │ updated file content
           ▼
┌──────────────────────┐
│     Validator        │
│    validator.py      │
│  Checks doc is       │
│  well-formed;        │
│  blocks save on fail │
└──────────┬───────────┘
           │ validation result
           ▼
┌──────────────────────┐
│      Reporter        │
│     reporter.py      │
│  Builds sync report; │
│  stdout + .md file   │
└──────────────────────┘
```

---

## Key Components and Their Responsibilities

| Component | File | Responsibility |
|-----------|------|---------------|
| **CLI Entry Point** | `scripts/run_sync.py` | Argument parsing (`--mode`, `--base-ref`, `--head-ref`, `--changed-files`); loads env; calls Orchestrator |
| **Orchestrator** | `src/sync_engine/orchestrator.py` | Coordinates the full pipeline; collects per-file results; triggers reporter; returns exit code |
| **Config Manager** | `src/sync_engine/config_manager.py` | Loads `config/sync_rules.yaml` and `.env`; provides typed config object |
| **Change Detector** | `src/sync_engine/change_detector.py` | Runs `git diff --name-status <base> <head>`; parses output; filters to `.py` files; returns list of `FileChange` objects |
| **File Mapper** | `src/sync_engine/mapper.py` | Maps `src/path/to/file.py` → `docs/file.md` by extracting the stem and looking it up in the configured docs root |
| **AST Analyser** | `src/sync_engine/analyser.py` | Uses Python `ast` stdlib to parse source; extracts top-level functions and classes; compares old vs new to produce a `ChangeSummary` |
| **Update Generator** | `src/sync_engine/update_generator.py` | Formats `ChangeSummary` into the Markdown content for the `## Module Update` section |
| **Doc Updater** | `src/sync_engine/doc_updater.py` | Reads the doc file; uses regex to locate and replace the `## Module Update` section; writes updated content atomically |
| **Validator** | `src/sync_engine/validator.py` | Checks updated content for structural completeness (e.g. heading present, section not empty); returns `ValidationResult` |
| **Reporter** | `src/sync_engine/reporter.py` | Collects all `SyncResult` objects; renders a Markdown report; prints to stdout and writes to `artifacts/sync-report.md` |
| **Models** | `src/sync_engine/models.py` | Typed dataclasses: `FileChange`, `DocMapping`, `ChangeSummary`, `ValidationResult`, `SyncResult`, `SyncReport` |
| **Exceptions** | `src/sync_engine/exceptions.py` | Custom exception hierarchy: `SyncError`, `MappingError`, `AnalysisError`, `ValidationError`, `UpdateError` |

---

## Technology Stack

| Layer | Technology | Version | Justification |
|-------|-----------|---------|---------------|
| Language | Python | 3.10+ | Requirement NFR-1; `ast`, `pathlib`, `dataclasses` available |
| Change detection | `git` CLI via `subprocess` | ≥ 2.30 | No library needed; `git diff --name-status` is stable |
| AST parsing | `ast` (stdlib) | built-in | No extra dependency; reliable for `.py` files |
| Section replacement | `re` (stdlib) | built-in | Regex replace is sufficient for heading-delimited section |
| Config | `PyYAML` | ≥ 6.0 | Already listed in requirements; parses `sync_rules.yaml` |
| Environment | `python-dotenv` | ≥ 1.0 | Already listed; loads `.env` |
| Testing | `pytest` + `pytest-cov` | ≥ 7.0 | Requirement NFR-6 |
| Type checking | `dataclasses` (stdlib) | built-in | Typed models without extra deps |

No web frameworks, databases, or message queues are used — consistent with NFR-2 (simplicity).

---

## Data Flow

```
Input: CLI args (--mode, --base-ref, --head-ref)
         │
         ▼
1. Config Manager loads sync_rules.yaml + .env
         │
         ▼
2. Change Detector runs: git diff --name-status <base> <head>
   Output: [FileChange(path="src/sync_engine/mapper.py", status="M"), ...]
         │
         ▼
3. File Mapper for each FileChange:
     stem = "mapper"
     doc_path = docs_root / "mapper.md"
     if doc_path.exists() → DocMapping(src=..., doc=...)
     else                 → log WARNING, add to skipped list
         │
         ▼
4. For each DocMapping:
   a. AST Analyser: parse src file from git (old HEAD + new HEAD)
      → ChangeSummary(added=["new_func"], removed=[], modified=["existing_func"])
   b. Update Generator: format ChangeSummary → Markdown string
   c. Doc Updater: read doc file → replace ## Module Update block → stage write
   d. Validator: check updated content is well-formed
      → if FAIL: log error, do NOT write, add to failed list
      → if PASS: write file, add to updated list
         │
         ▼
5. Reporter: collect (updated, skipped, failed) → SyncReport
   Output: print Markdown table to stdout
           write artifacts/sync-report.md
         │
         ▼
Exit: 0 if no failures, 1 if any file failed (NFR-5)
```

---

## Folder Structure

```
claude_capstone_demo/
├── scripts/
│   └── run_sync.py               ← CLI entry point
├── src/
│   └── sync_engine/
│       ├── __init__.py
│       ├── models.py             ← dataclasses (FileChange, SyncResult, …)
│       ├── exceptions.py         ← custom exception hierarchy
│       ├── config_manager.py     ← loads sync_rules.yaml + .env
│       ├── change_detector.py    ← git diff → list[FileChange]
│       ├── mapper.py             ← FileChange → Optional[DocMapping]
│       ├── analyser.py           ← Python AST → ChangeSummary
│       ├── update_generator.py   ← ChangeSummary → Markdown block
│       ├── doc_updater.py        ← replaces ## Module Update in doc file
│       ├── validator.py          ← validates updated doc content
│       ├── reporter.py           ← builds and writes SyncReport
│       └── orchestrator.py       ← coordinates all stages
├── tests/
│   ├── conftest.py
│   ├── test_change_detector.py
│   ├── test_mapper.py
│   ├── test_analyser.py
│   ├── test_update_generator.py
│   ├── test_doc_updater.py
│   ├── test_validator.py
│   ├── test_reporter.py
│   └── test_orchestrator.py
├── docs/                         ← Markdown documentation files (sync targets)
├── config/
│   ├── sync_rules.yaml           ← mapping and filtering rules
│   └── doc_template.yaml         ← section templates
└── artifacts/
    └── sync-report.md            ← generated at runtime
```

---

## Error Handling Strategy

| Error Scenario | Behaviour | Exit Code |
|----------------|-----------|-----------|
| No `.py` files changed in diff | Report "nothing to sync", exit cleanly | 0 |
| No matching doc file for a changed `.py` | Log WARNING, add to skipped list, continue | 0 (unless all fail) |
| Doc file exists but has no `## Module Update` section | Log WARNING, skip that file, continue | 0 |
| Python AST parse error (syntax error in source) | Log ERROR, skip file, continue | 1 |
| Validation fails after update generation | Log ERROR, do NOT write doc file, continue | 1 |
| Doc file write fails (permission, disk) | Log ERROR, continue remaining files | 1 |
| Any file in the pipeline fails | Continue all remaining; exit code 1 at end | 1 |

**Principle:** never abort the pipeline on a single-file failure (FR-11). Collect all errors and surface them in the report.

---

## Logging Strategy

- Logger: Python stdlib `logging` module, configured via `LOG_LEVEL` env var (default `INFO`).
- Format: `%(asctime)s [%(levelname)s] %(name)s: %(message)s`
- Each component uses its own named logger: `sync_engine.mapper`, `sync_engine.analyser`, etc.
- Log levels:
  - `DEBUG` — per-file detail (path being processed, section boundaries found)
  - `INFO` — normal progress (file updated, report written)
  - `WARNING` — skipped files (no doc mapping, no section marker)
  - `ERROR` — failed files (AST error, validation failure, write error)

---

## Future Scalability

The following extensions are explicitly **out of scope** for this implementation but are accommodated by the architecture:

| Potential Extension | How Current Architecture Supports It |
|--------------------|--------------------------------------|
| Support other source languages | Add a language-specific Analyser; Orchestrator selects by file extension |
| Support other doc formats (RST, AsciiDoc) | Add format-specific DocUpdater; FileMapper returns format hint |
| Filesystem watch / real-time sync | Replace ChangeDetector with a watch-based implementation; Orchestrator unchanged |
| Multi-repository sync | Orchestrator accepts a list of repo roots; all other components unchanged |
| Parallel file processing | Orchestrator wraps per-file pipeline in `concurrent.futures`; components are stateless |
