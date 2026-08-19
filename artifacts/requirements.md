# Requirements: Automated Documentation Sync

**Generated:** 2026-08-18
**Source:** Confluence  -  page 44498945 (space ~712020ff5ba6e8e09b44d0b6155976e4654329)
**JIRA Story:** EPMCDMETST-60340

---

## 1. User Story

**As a** developer maintaining a software project,
**I want** documentation to be automatically synchronized whenever source code changes,
**So that** project documentation remains accurate, consistent, and up to date without requiring manual effort.

---

## 2. Stakeholder Q&A

### Q1: What programming languages trigger documentation sync?
**Answer:** Python only (.py files)

### Q2: How should the system detect code changes?
**Answer:** Via git diff (comparing commits or branches)

### Q3: How are changed Python files mapped to documentation files?
**Answer:** Same filename, different folder  -  e.g., `src/sync_engine/mapper.py` -> `docs/mapper.md`

### Q4: When updating documentation, replace the whole file or only a section?
**Answer:** Update only a specific section; preserve all other manually written content

### Q5: What marker identifies the auto-managed section in a doc file?
**Answer:** `## Module Update` heading

### Q6: What content is written into the `## Module Update` section?
**Answer:** A summary of what changed in the Python file (functions added, removed, or modified)

### Q7: If no matching documentation file exists for a changed Python file, what happens?
**Answer:** Log a warning and skip  -  do not auto-create files

### Q8: What format is the sync report?
**Answer:** Both  -  a Markdown file written to disk and printed to stdout

### Q9: Performance expectations?
**Answer:** No specific limits  -  keep it simple

### Q10: CLI script only or also a Python library?
**Answer:** CLI script only

---

## Functional Requirements

## 3. Functional Requirements

1. The system shall accept a git diff (base ref and head ref) as input to identify changed files.
2. The system shall filter changed files to Python source files (`.py` extension) only.
3. The system shall map each changed Python file to a corresponding Markdown documentation file using the same filename in the configured `docs/` directory.
4. For each matched documentation file, the system shall locate the `## Module Update` section and replace its content with a summary of what changed (functions added, removed, or modified) in the Python file.
5. The system shall preserve all content in documentation files outside the `## Module Update` section unchanged.
6. If no matching documentation file exists for a changed Python file, the system shall log a warning and skip that file without failing.
7. The system shall validate that updated documentation files are complete and correctly formatted after writing.
8. If validation fails, the system shall notify the user and prevent the invalid documentation from being saved.
9. The system shall generate a synchronization report listing: updated documentation files, skipped files (with warnings), validation results, and overall processing status.
10. The report shall be both printed to stdout and written as a Markdown file to disk.
11. The system shall continue processing remaining files even if one file update fails; errors shall be logged with meaningful messages.
12. The system shall be invoked as a CLI script (`scripts/run_sync.py`) supporting `--mode manual` and `--mode pr` with `--base-ref` / `--head-ref` options.

---

## Non-Functional Requirements

## 4. Non-Functional Requirements

1. The implementation language is Python 3.
2. The system shall be simple and maintainable  -  no unnecessary complexity or external services.
3. The system shall produce clear, human-readable log output for all operations (changes detected, files updated, warnings, errors).
4. The system shall be idempotent  -  running it twice on the same diff produces the same result.
5. All errors shall be caught and logged; the process shall exit with a non-zero code if any file failed to update.
6. The codebase shall include a test suite runnable with `pytest`.

---

## 5. Constraints & Limitations

1. Only Markdown (`.md`) documentation is supported as the sync target.
2. Only Python (`.py`) source files trigger sync.
3. Source code and documentation must exist within the same git repository.
4. Documentation updates occur after code changes are detected (not real-time).
5. Manual approval of documentation changes is outside scope.
6. The system operates as a CLI script only  -  not importable as a library.

---

## 6. Acceptance Criteria

- [ ] AC1: The system detects Python source files added, modified, renamed, or deleted via git diff.
- [ ] AC2: The system determines which `docs/*.md` files are affected using filename-based mapping; reports missing mappings as warnings.
- [ ] AC3: The system updates only the `## Module Update` section of affected documentation; all other content is preserved.
- [ ] AC4: The system validates updated documentation for completeness and correct formatting; blocks save on failure.
- [ ] AC5: The system generates a sync report (stdout + Markdown file) listing updated files, skipped files, validation results, and processing status.
- [ ] AC6: The system continues processing after a single file failure; all errors are logged with meaningful messages.

---

## 7. Success Metrics

- All changed Python files with matching documentation are synced without data loss.
- No documentation content outside `## Module Update` is modified.
- The sync report accurately reflects the outcome of every file processed.
- All tests pass (`pytest tests/ -v`).

---

## 8. Dependencies

- Python 3.x
- `PyYAML`  -  for reading `config/sync_rules.yaml`
- `markdown-it-py`  -  for Markdown parsing and validation
- `python-dotenv`  -  for environment configuration
- `pytest`  -  for the test suite (dev dependency)
- Git  -  for diff-based change detection (`git diff` CLI)

---

## 9. Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Documentation file has no `## Module Update` section | Log a warning, skip the file; do not corrupt existing content |
| Git diff output format changes between versions | Pin to a stable `git diff --name-status` format; add integration test |
| Python AST parsing fails on syntax-error files | Catch parse errors, log them, and skip the affected file |

---

## 10. Out of Scope

- Multi-repository synchronization
- Real-time / filesystem-watch synchronization
- Support for non-Markdown documentation formats
- Support for non-Python source languages
- GUI-based application
- Auto-creation of missing documentation files
- Manual approval workflow for documentation changes
