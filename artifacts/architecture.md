# System Architecture: Automated Documentation Sync

**Stage:** 2  -  Architecture
**Date:** 2026-08-18
**Updated:** 2026-08-18 (design-review-agent  -  9 agreed changes applied)
**JIRA Story:** EPMCDMETST-60340
**Author:** architecture-agent
**Reviewed by:** design-review-agent
**Depends on:** `artifacts/requirements.md`

---

## System Overview

The Automated Documentation Sync system is a Python CLI tool that detects Python source file changes via `git diff`, maps each changed file to its corresponding Markdown documentation file, and updates only the `## Module Update` section of each matched doc file with a structured summary of what changed (functions/classes added, removed, or modified).

The system is entirely self-contained: no external services, no databases, no network calls. It runs as a one-shot CLI invocation and produces a Markdown sync report.

---

## Architecture Recommendation

**Style: Linear Processing Pipeline (Layered)**

Each stage of processing has a single responsibility and hands its output to the next stage. This matches the data flow perfectly: detect -> map -> analyse -> generate -> update -> validate -> report.

**Justification:**
- Requirements explicitly define a sequential, deterministic workflow (FR-1 -> FR-12).
- Idempotency requirement (NFR-4) is easiest to guarantee with a stateless, single-pass pipeline.
- "Keep it simple" (NFR-2) rules out event-driven or reactive patterns.
- No concurrency required  -  no performance constraint (Q9).
- Clear separation of concerns makes each stage independently testable (NFR-6).

---

## Component Diagram

```
+-------------------------------------------------------------+
|                     CLI Entry Point                          |
|                  scripts/run_sync.py                         |
|           --mode manual|pr  --base-ref  --head-ref           |
+-------------------------+-----------------------------------+
                          |
                          v
+-------------------------------------------------------------+
|                      Orchestrator                            |
|              src/sync_engine/orchestrator.py                 |
|   Coordinates all stages; collects results; triggers report  |
+--+--------------------------------------------------------+-+
   |                                                        |
   v                                                        v
+----------------------+              +-------------------------+
|   Change Detector    |              |    Config Manager        |
|  change_detector.py  |              |   config_manager.py      |
|  Runs git diff;      |              |  Loads sync_rules.yaml   |
|  filters .py files   |              |  and .env settings       |
+----------+-----------+              +-------------------------+
           |
           v
+----------------------+
|     File Mapper      |
|      mapper.py       |
|  Maps .py -> .md      |
|  by filename         |
+----------+-----------+
           | matched files
           | (unmatched -> warning -> skip)
           v
+----------------------+
|    AST Analyser      |
|     analyser.py      |
|  Parses Python AST;  |
|  extracts changes    |
|  (add/remove/modify) |
+----------+-----------+
           | ChangeSummary
           v
+----------------------+
|   Update Generator   |
|  update_generator.py |
|  Formats the         |
|  ## Module Update    |
|  section content     |
+----------+-----------+
           | formatted Markdown block
           v
+----------------------+
|    Doc Updater       |
|    doc_updater.py    |
|  Replaces ## Module  |
|  Update section;     |
|  preserves all else  |
+----------+-----------+
           | updated file content
           v
+----------------------+
|     Validator        |
|    validator.py      |
|  Checks doc is       |
|  well-formed;        |
|  blocks save on fail |
+----------+-----------+
           | validation result
           v
+----------------------+
|      Reporter        |
|     reporter.py      |
|  Builds sync report; |
|  stdout + .md file   |
+----------------------+
```

---

## Key Components and Their Responsibilities

| Component | File | Responsibility |
|-----------|------|---------------|
| **CLI Entry Point** | `scripts/run_sync.py` | Argument parsing (`--mode`, `--base-ref`, `--head-ref`, `--changed-files`); loads env; calls Orchestrator |
| **Orchestrator** | `src/sync_engine/orchestrator.py` | Coordinates the full pipeline; collects per-file results; triggers reporter; returns exit code |
| **Config Manager** | `src/sync_engine/config_manager.py` | Loads `config/sync_rules.yaml` and `.env`; validates required fields (`docs_root`, `source_extensions`) at load time; raises `ConfigurationError` before pipeline starts if invalid |
| **Change Detector** | `src/sync_engine/change_detector.py` | Runs `git diff --name-status <base> <head>`; parses output; filters to `.py` files; fetches old file content via `git show <base>:<path>`; returns list of `FileChange` objects (each carrying `old_content` and `new_content`) |
| **File Mapper** | `src/sync_engine/mapper.py` | Maps `src/path/to/file.py` -> `docs/file.md` by extracting the stem; returns `DocMapping` if doc exists, `SkippedFile(reason=NO_DOC_FILE)` if not |
| **AST Analyser** | `src/sync_engine/analyser.py` | Uses Python `ast` stdlib to parse source; extracts top-level functions and classes; compares old vs new to produce a `ChangeSummary` |
| **Update Generator** | `src/sync_engine/update_generator.py` | Formats `ChangeSummary` into the Markdown content for the `## Module Update` section |
| **Doc Updater** | `src/sync_engine/doc_updater.py` | Reads the doc file; uses regex to locate and replace the `## Module Update` section; writes atomically via write-to-`.tmp` + `os.replace()` |
| **Validator** | `src/sync_engine/validator.py` | Checks updated content for structural completeness (e.g. heading present, section not empty); returns `ValidationResult` |
| **Reporter** | `src/sync_engine/reporter.py` | Collects all `SyncResult` objects; renders a Markdown report with separate sections for "updated", "skipped  -  no doc file", and "skipped  -  no section marker"; prints to stdout and writes to `artifacts/sync-report.md` |
| **Models** | `src/sync_engine/models.py` | Typed dataclasses: `FileChange(path, status, old_content, new_content)`, `DocMapping`, `SkippedFile(path, reason: SkipReason)`, `ChangeSummary`, `ValidationResult`, `SyncResult`, `SyncReport`; `SkipReason` enum: `NO_DOC_FILE`, `NO_SECTION_MARKER` |
| **Exceptions** | `src/sync_engine/exceptions.py` | Custom exception hierarchy: `SyncError`, `ConfigurationError`, `MappingError`, `AnalysisError`, `ValidationError`, `UpdateError` |

---

## Technology Stack

| Layer | Technology | Version | Justification |
|-------|-----------|---------|---------------|
| Language | Python | 3.10+ | Requirement NFR-1; `ast`, `pathlib`, `dataclasses` available |
| Change detection | `git` CLI via `subprocess` | >= 2.30 | No library needed; `git diff --name-status` is stable |
| AST parsing | `ast` (stdlib) | built-in | No extra dependency; reliable for `.py` files |
| Section replacement | `re` (stdlib) | built-in | Regex replace is sufficient for heading-delimited section |
| Config | `PyYAML` | >= 6.0 | Already listed in requirements; parses `sync_rules.yaml` |
| Environment | `python-dotenv` | >= 1.0 | Already listed; loads `.env` |
| Testing | `pytest` + `pytest-cov` | >= 7.0 | Requirement NFR-6 |
| Type checking | `dataclasses` (stdlib) | built-in | Typed models without extra deps |

No web frameworks, databases, or message queues are used  -  consistent with NFR-2 (simplicity).

---

## Data Flow

```
Input: CLI args (--mode, --base-ref, --head-ref)
         |
         v
1. Config Manager loads sync_rules.yaml + .env
         |
         v
2. Change Detector runs (shell=False, list args):
     git diff --name-status <base> <head>  -> filters .py files
     git show <base>:<path>               -> fetches old_content per file
   Output: [FileChange(path, status, old_content, new_content), ...]
         |
         v
3. File Mapper for each FileChange:
     stem = "mapper"
     doc_path = docs_root / "mapper.md"
     if doc_path.exists() -> DocMapping(src=..., doc=...)
     else                 -> SkippedFile(reason=NO_DOC_FILE) -> log WARNING
         | DocMapping only
         v
4. For each DocMapping:
   a. AST Analyser: parse old_content + new_content from FileChange
      -> ChangeSummary(added=["new_func"], removed=[], modified=["existing_func"])
   b. Update Generator: format ChangeSummary -> Markdown string
   c. Doc Updater: read doc file -> locate ## Module Update section
      if section absent -> SkippedFile(reason=NO_SECTION_MARKER) -> log WARNING
      if present        -> replace block -> write to .tmp -> os.replace() (atomic)
   d. Validator: check updated content is well-formed
      -> if FAIL: log ERROR, do NOT write, add to failed list
      -> if PASS: commit atomic write, add to updated list
         |
         v
5. Reporter: collect (updated, skipped_no_doc, skipped_no_section, failed) -> SyncReport
   Output: print Markdown table to stdout (3 separate skip sections)
           write artifacts/sync-report.md
         |
         v
Exit code:
  0  -  all matched files updated successfully (skipped files do not count as failure)
  1  -  one or more matched files failed validation or write (NFR-5)
```

---

## Folder Structure

```
claude_capstone_demo/
+-- scripts/
|   +-- run_sync.py               <- CLI entry point
+-- src/
|   +-- sync_engine/
|       +-- __init__.py           <- public API: exports Orchestrator only; all other modules are internal
|       +-- models.py             <- dataclasses (FileChange, SkippedFile, SkipReason, SyncResult, ...)
|       +-- exceptions.py         <- custom exception hierarchy
|       +-- config_manager.py     <- loads sync_rules.yaml + .env
|       +-- change_detector.py    <- git diff -> list[FileChange]
|       +-- mapper.py             <- FileChange -> Union[DocMapping, SkippedFile]
|       +-- analyser.py           <- Python AST -> ChangeSummary
|       +-- update_generator.py   <- ChangeSummary -> Markdown block
|       +-- doc_updater.py        <- replaces ## Module Update in doc file
|       +-- validator.py          <- validates updated doc content
|       +-- reporter.py           <- builds and writes SyncReport
|       +-- orchestrator.py       <- coordinates all stages
+-- tests/
|   +-- conftest.py
|   +-- test_change_detector.py
|   +-- test_mapper.py
|   +-- test_analyser.py
|   +-- test_update_generator.py
|   +-- test_doc_updater.py
|   +-- test_validator.py
|   +-- test_reporter.py
|   +-- test_orchestrator.py
+-- docs/                         <- Markdown documentation files (sync targets)
+-- config/
|   +-- sync_rules.yaml           <- mapping and filtering rules
|   +-- doc_template.yaml         <- section templates
+-- artifacts/
    +-- sync-report.md            <- generated at runtime
```

---

## Error Handling Strategy

| Error Scenario | Behaviour | Exit Code |
|----------------|-----------|-----------|
| No `.py` files changed in diff | Report "nothing to sync", exit cleanly | 0 |
| No matching doc file (`SkippedFile: NO_DOC_FILE`) | Log WARNING, add to skipped list, continue | 0 |
| Doc file exists but no `## Module Update` section (`SkippedFile: NO_SECTION_MARKER`) | Log WARNING, add to skipped list, continue | 0 |
| Config file missing or invalid fields | Raise `ConfigurationError` before pipeline starts | 1 |
| Python AST parse error (syntax error in source) | Log ERROR, skip file, continue | 1 |
| Validation fails after update generation | Log ERROR, do NOT write doc file, continue | 1 |
| Doc `.tmp` write fails (permission, disk) | Log ERROR, original file untouched, continue | 1 |
| Any matched file fails | Continue all remaining; exit code 1 at end | 1 |

**Principle:** never abort the pipeline on a single-file failure (FR-11). Collect all errors and surface them in the report.
**Exit code precision:** only matched files that fail validation or write count toward exit code 1. Skip events (no doc file, no section) -> exit code 0.

---

## Logging Strategy

- Logger: Python stdlib `logging` module, configured via `LOG_LEVEL` env var (default `INFO`).
- Format: `%(asctime)s [%(levelname)s] %(name)s: %(message)s`
- Each component uses its own named logger: `sync_engine.mapper`, `sync_engine.analyser`, etc.
- **All file paths in log messages use `path.relative_to(repo_root)`  -  absolute paths are never emitted.**
- Log levels:
  - `DEBUG`  -  per-file detail (path being processed, section boundaries found)
  - `INFO`  -  normal progress (file updated, report written)
  - `WARNING`  -  skipped files (no doc mapping, no section marker)
  - `ERROR`  -  failed files (AST error, validation failure, write error)

---

## Security Constraints

These constraints are binding for all implementation stages:

| Constraint | Rule |
|------------|------|
| Subprocess safety | All `subprocess.run()` calls use a **list** argument and `shell=False`  -  no string interpolation of user-supplied values |
| Ref validation | `--base-ref` and `--head-ref` values are passed only as elements of a list to subprocess; never concatenated into a shell string |
| Log path format | All file paths in log output are relative to the repo root; absolute paths are never emitted |
| No secrets in source | No API tokens, passwords, or credentials in any source file  -  loaded from `.env` only |

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
