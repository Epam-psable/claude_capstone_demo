# Implementation Plan: Automated Documentation Sync

**Stage:** 4  -  Implementation Planning
**Date:** 2026-08-18
**JIRA Story:** EPMCDMETST-60340
**Author:** implementation-planning-agent
**Depends on:** `artifacts/architecture.md`, `artifacts/design-review.md`

---

## Overview

The implementation covers 13 source files across 7 dependency-ordered phases, plus a 9-file test suite. All tasks are grounded in the approved architecture. Design decisions from the review (DR-1 through M-1) are embedded as constraints in the relevant tasks.

**Total tasks:** 23 (13 source + 1 CLI entry point + 9 tests)
**Estimated phases:** 8

---

## Implementation Steps

The implementation follows 8 dependency-ordered phases. Each phase must be committed before the next begins. See the detailed per-phase breakdown in the [Dependency-Ordered Implementation Plan](#dependency-ordered-implementation-plan) section below.

1. **Phase 1**  -  Foundation: `models.py`, `exceptions.py`
2. **Phase 2**  -  Configuration: `config_manager.py`
3. **Phase 3**  -  Discovery: `change_detector.py`, `mapper.py`
4. **Phase 4**  -  Analysis & Generation: `analyser.py`, `update_generator.py`
5. **Phase 5**  -  Document Processing: `doc_updater.py`, `validator.py`
6. **Phase 6**  -  Reporting: `reporter.py`
7. **Phase 7**  -  Orchestration & CLI: `orchestrator.py`, `__init__.py`, `scripts/run_sync.py`
8. **Phase 8**  -  Test Suite: `conftest.py` + 9 test files

---

## Prioritised Task List

| Task ID | Description | Phase | Priority | Dependencies | Expected Output |
|---------|-------------|-------|----------|--------------|-----------------|
| T01 | Implement `models.py` | 1 | P0 |  -  | `FileChange`, `DocMapping`, `SkippedFile`, `SkipReason`, `ChangeSummary`, `ValidationResult`, `SyncResult`, `SyncReport` dataclasses |
| T02 | Implement `exceptions.py` | 1 | P0 |  -  | `SyncError`, `ConfigurationError`, `MappingError`, `AnalysisError`, `ValidationError`, `UpdateError` |
| T03 | Implement `config_manager.py` | 2 | P0 | T01, T02 | `Config` dataclass; `ConfigManager.load()` validates `docs_root` + `source_extensions`; raises `ConfigurationError` |
| T04 | Implement `change_detector.py` | 3 | P1 | T01, T02 | `ChangeDetector.detect()` -> `list[FileChange]`; uses `git diff --name-status` + `git show` with `shell=False` |
| T05 | Implement `mapper.py` | 3 | P1 | T01, T02 | `FileMapper.map()` -> `Union[DocMapping, SkippedFile]`; maps `.py` stem -> `docs/<stem>.md` |
| T06 | Implement `analyser.py` | 4 | P1 | T01, T02 | `AstAnalyser.analyse()` -> `ChangeSummary`; compares `old_content` vs `new_content` using Python `ast` |
| T07 | Implement `update_generator.py` | 4 | P1 | T01, T06 | `UpdateGenerator.generate()` -> Markdown string for `## Module Update` section |
| T08 | Implement `doc_updater.py` | 5 | P1 | T01, T02, T07 | `DocUpdater.update()`  -  regex section replace; atomic write via `.tmp` + `os.replace()`; returns `SkippedFile` if section absent |
| T09 | Implement `validator.py` | 5 | P1 | T01, T02 | `Validator.validate()` -> `ValidationResult`; checks `## Module Update` present and non-empty after update |
| T10 | Implement `reporter.py` | 6 | P1 | T01 | `Reporter.generate()` -> `SyncReport`; renders 4 sections (updated / no_doc / no_section / failed); stdout + file write |
| T11 | Implement `orchestrator.py` | 7 | P0 | T03-T10 | `Orchestrator.run()` -> `int` exit code; coordinates all stages; enforces exit code rule (0 = skips OK, 1 = matched-file failure) |
| T12 | Implement `__init__.py` | 7 | P2 | T11 | Re-exports `Orchestrator` only; all other modules remain internal |
| T13 | Implement `scripts/run_sync.py` | 7 | P0 | T11 | CLI entry point: `argparse` for `--mode`, `--base-ref`, `--head-ref`, `--changed-files`; loads `.env`; calls `Orchestrator.run()` |
| T14 | `tests/conftest.py` | 8 | P1 | T01-T13 | Shared fixtures: tmp dir, sample `.py` files, sample `.md` files with/without section |
| T15 | `tests/test_change_detector.py` | 8 | P1 | T04, T14 | Unit tests: diff parsing, `.py` filter, `git show` for old content, `shell=False` guard |
| T16 | `tests/test_mapper.py` | 8 | P1 | T05, T14 | Unit tests: found mapping, `NO_DOC_FILE` skip, stem extraction |
| T17 | `tests/test_analyser.py` | 8 | P1 | T06, T14 | Unit tests: added func, removed func, modified func, added file (old=None), deleted file (new=None), syntax error |
| T18 | `tests/test_update_generator.py` | 8 | P1 | T07, T14 | Unit tests: Markdown output format, empty summary, all change types |
| T19 | `tests/test_doc_updater.py` | 8 | P1 | T08, T14 | Unit tests: section replace, section absent -> `NO_SECTION_MARKER`, atomic write (.tmp -> final), original file untouched on failure |
| T20 | `tests/test_validator.py` | 8 | P1 | T09, T14 | Unit tests: valid doc, missing heading, empty section |
| T21 | `tests/test_reporter.py` | 8 | P1 | T10, T14 | Unit tests: stdout output, Markdown file written, all 4 sections present |
| T22 | `tests/test_orchestrator.py` | 8 | P0 | T11, T14 | Integration tests: full pipeline (updated), all skipped (exit 0), one failure (exit 1), no `.py` changes |
| T23 | `tests/test_config_manager.py` | 8 | P1 | T03, T14 | Unit tests: valid config loads, missing `docs_root` raises `ConfigurationError`, missing file raises `ConfigurationError` |

---

## Dependency-Ordered Implementation Plan

### Phase 1  -  Foundation (no dependencies)

Implement the shared data contracts first. Nothing else can start until these exist.

| Task | File | Key Contracts |
|------|------|--------------|
| T01 | `src/sync_engine/models.py` | All dataclasses + `SkipReason` enum |
| T02 | `src/sync_engine/exceptions.py` | Full exception hierarchy |

**Commit after Phase 1:**
```bash
git add src/sync_engine/models.py src/sync_engine/exceptions.py
git commit -m "feat: implement foundation models and exceptions"
```

---

### Phase 2  -  Configuration (depends on Phase 1)

Config must be validated before any pipeline stage runs (design decision M-1).

| Task | File | Key Contracts |
|------|------|--------------|
| T03 | `src/sync_engine/config_manager.py` | `ConfigManager.load()` validates at startup |

**Commit after Phase 2:**
```bash
git add src/sync_engine/config_manager.py
git commit -m "feat: implement config manager with startup validation"
```

---

### Phase 3  -  Discovery (depends on Phase 1, parallel)

Change detection and file mapping are independent of each other  -  implement in any order.

| Task | File | Key Contracts |
|------|------|--------------|
| T04 | `src/sync_engine/change_detector.py` | `ChangeDetector.detect()` with `shell=False`; fetches `old_content` via `git show` (DR-1) |
| T05 | `src/sync_engine/mapper.py` | `FileMapper.map()` -> `Union[DocMapping, SkippedFile]` (DR-2) |

**Commit after Phase 3:**
```bash
git add src/sync_engine/change_detector.py src/sync_engine/mapper.py
git commit -m "feat: implement change detector and file mapper"
```

---

### Phase 4  -  Analysis & Generation (depends on Phase 1)

AST analysis and update generation are independent of discovery  -  can overlap with Phase 3.

| Task | File | Key Contracts |
|------|------|--------------|
| T06 | `src/sync_engine/analyser.py` | `AstAnalyser.analyse(old_content, new_content)` -> `ChangeSummary` |
| T07 | `src/sync_engine/update_generator.py` | `UpdateGenerator.generate(summary)` -> Markdown string |

**Commit after Phase 4:**
```bash
git add src/sync_engine/analyser.py src/sync_engine/update_generator.py
git commit -m "feat: implement AST analyser and update generator"
```

---

### Phase 5  -  Document Processing (depends on Phases 1, 4)

Doc updating and validation act on the Markdown file. Validator is called after DocUpdater generates content.

| Task | File | Key Contracts |
|------|------|--------------|
| T08 | `src/sync_engine/doc_updater.py` | Regex section replace; atomic write (MC-1); `NO_SECTION_MARKER` skip (EH-1) |
| T09 | `src/sync_engine/validator.py` | `Validator.validate(content)` -> `ValidationResult` |

**Commit after Phase 5:**
```bash
git add src/sync_engine/doc_updater.py src/sync_engine/validator.py
git commit -m "feat: implement doc updater with atomic write and validator"
```

---

### Phase 6  -  Reporting (depends on Phase 1)

Reporter is independent of discovery/analysis  -  depends only on the model types.

| Task | File | Key Contracts |
|------|------|--------------|
| T10 | `src/sync_engine/reporter.py` | 4-section report; stdout + file; relative paths only (S-2) |

**Commit after Phase 6:**
```bash
git add src/sync_engine/reporter.py
git commit -m "feat: implement sync reporter"
```

---

### Phase 7  -  Orchestration & CLI (depends on all previous phases)

The orchestrator wires all components together. The CLI entry point is the outermost layer.

| Task | File | Key Contracts |
|------|------|--------------|
| T11 | `src/sync_engine/orchestrator.py` | `Orchestrator.run()` -> `int`; exit code precision (EH-2); calls all components in order |
| T12 | `src/sync_engine/__init__.py` | `from .orchestrator import Orchestrator`  -  only public export (MC-2) |
| T13 | `scripts/run_sync.py` | `argparse` CLI; `--mode manual|pr`; `--base-ref`; `--head-ref`; `--changed-files`; `sys.exit(Orchestrator.run(...))` |

**Commit after Phase 7:**
```bash
git add src/sync_engine/orchestrator.py src/sync_engine/__init__.py scripts/run_sync.py
git commit -m "feat: implement orchestrator and CLI entry point"
```

---

### Phase 8  -  Test Suite (depends on Phase 7)

Write one test file per component. Start with `conftest.py` to define shared fixtures.

| Task | File |
|------|------|
| T14 | `tests/conftest.py` |
| T15 | `tests/test_change_detector.py` |
| T16 | `tests/test_mapper.py` |
| T17 | `tests/test_analyser.py` |
| T18 | `tests/test_update_generator.py` |
| T19 | `tests/test_doc_updater.py` |
| T20 | `tests/test_validator.py` |
| T21 | `tests/test_reporter.py` |
| T22 | `tests/test_orchestrator.py` |
| T23 | `tests/test_config_manager.py` |

**Commit after Phase 8:**
```bash
git add tests/
git commit -m "test: add full test suite for sync engine"
```

---

## Task Dependencies

| Task ID | Depends On | Dependency Rationale |
|---------|------------|---------------------|
| T03 | T01, T02 | Config returns `Config` dataclass (T01); raises `ConfigurationError` (T02) |
| T04 | T01, T02 | Returns `list[FileChange]` (T01); raises `SyncError` subclass (T02) |
| T05 | T01, T02 | Returns `Union[DocMapping, SkippedFile]` (T01); raises `MappingError` (T02) |
| T06 | T01, T02 | Returns `ChangeSummary` (T01); raises `AnalysisError` (T02) |
| T07 | T01, T06 | Consumes `ChangeSummary` (T01); depends on analyser output contract (T06) |
| T08 | T01, T02, T07 | Writes doc content from `UpdateGenerator` (T07); raises `UpdateError` (T02); returns `SkippedFile` (T01) |
| T09 | T01, T02 | Returns `ValidationResult` (T01); raises `ValidationError` (T02) |
| T10 | T01 | Consumes `SyncReport` and all result types (T01) |
| T11 | T03-T10 | Orchestrator instantiates and calls every component |
| T12 | T11 | Re-exports only `Orchestrator` |
| T13 | T11 | CLI calls `Orchestrator.run()` |
| T14-T23 | T01-T13 | Tests require all source files to be complete |

---

## Blocked Tasks and Their Prerequisites

| Blocked Task | Blocked By | Unblock Condition |
|--------------|------------|-------------------|
| T03 (config_manager) | T01, T02 | `Config` dataclass and `ConfigurationError` defined |
| T04 (change_detector) | T01, T02 | `FileChange` dataclass and `SyncError` defined |
| T05 (mapper) | T01, T02 | `DocMapping`, `SkippedFile`, `MappingError` defined |
| T06 (analyser) | T01, T02 | `ChangeSummary`, `AnalysisError` defined |
| T07 (update_generator) | T06 | `ChangeSummary` output contract confirmed by T06 |
| T08 (doc_updater) | T07 | `UpdateGenerator.generate()` signature confirmed |
| T11 (orchestrator) | T03-T10 | All component public interfaces confirmed |
| T13 (run_sync.py) | T11 | `Orchestrator.run()` signature confirmed |
| T22 (test_orchestrator) | T11 | Full pipeline wired up |

---

## File Structure

```
src/sync_engine/
+-- __init__.py            <- exports Orchestrator only
+-- models.py              <- T01
+-- exceptions.py          <- T02
+-- config_manager.py      <- T03
+-- change_detector.py     <- T04
+-- mapper.py              <- T05
+-- analyser.py            <- T06
+-- update_generator.py    <- T07
+-- doc_updater.py         <- T08
+-- validator.py           <- T09
+-- reporter.py            <- T10
+-- orchestrator.py        <- T11

scripts/
+-- run_sync.py            <- T13

tests/
+-- conftest.py            <- T14
+-- test_config_manager.py <- T23
+-- test_change_detector.py<- T15
+-- test_mapper.py         <- T16
+-- test_analyser.py       <- T17
+-- test_update_generator.py<- T18
+-- test_doc_updater.py    <- T19
+-- test_validator.py      <- T20
+-- test_reporter.py       <- T21
+-- test_orchestrator.py   <- T22
```

---

## Dependencies

Runtime:
```
PyYAML>=6.0
python-dotenv>=1.0.0
```

Development:
```
pytest>=7.0
pytest-cov>=4.0
```

All other dependencies (`ast`, `re`, `subprocess`, `pathlib`, `dataclasses`, `logging`, `argparse`) are Python stdlib.

---

## Test Strategy

| Test Type | Scope | Target Coverage |
|-----------|-------|----------------|
| Unit | Each component in isolation (mocked filesystem, mocked subprocess) | >= 80% per module |
| Integration | `test_orchestrator.py`  -  full pipeline end-to-end using real tmp files | Full happy path + 3 error paths |

**Coverage target:** >= 80% overall (`pytest --cov=src/sync_engine --cov-report=term-missing`)

**Key test scenarios:**

| Scenario | Expected Result | Exit Code |
|----------|----------------|-----------|
| 1 changed `.py`, matching doc with section | Doc updated, report shows 1 updated | 0 |
| 1 changed `.py`, no matching doc file | Report shows 1 skipped (NO_DOC_FILE) | 0 |
| 1 changed `.py`, doc exists, no section | Report shows 1 skipped (NO_SECTION_MARKER) | 0 |
| 1 changed `.py`, validation fails | Report shows 1 failed, doc not written | 1 |
| `.py` file with syntax error | Report shows 1 failed (AnalysisError) | 1 |
| Mix: 1 updated + 1 skipped + 1 failed | All reported; exit 1 (due to failure) | 1 |
| No `.py` files changed | "Nothing to sync" report | 0 |
| Config file missing | `ConfigurationError` before pipeline | 1 |

---

## Notes

1. **Design decisions are constraints, not suggestions.** Every task above includes the relevant design review decision (DR-1, S-1, etc.) as a hard constraint. The implementation-agent must not deviate.
2. **`shell=False` is non-negotiable** in `change_detector.py`  -  enforced by security constraint S-1.
3. **Phase 3 and Phase 4 are independent**  -  they can be implemented in any order within those phases.
4. **Atomic write pattern** for `doc_updater.py`: write to `<path>.md.tmp`, then `os.replace(tmp, original)`. If the `.tmp` write fails, the original is untouched.
5. **Old file content** is fetched by `ChangeDetector` via `git show <base_ref>:<filepath>`. For added files, `old_content=None`. For deleted files, `new_content=None`. The Analyser handles both None cases.
6. **The test suite is part of the implementation**  -  Stage 7 (Verify) cannot run without it.
