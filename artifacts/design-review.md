# Design Review: Automated Documentation Sync

**Stage:** 3 — Design Review
**Date:** 2026-08-18
**JIRA Story:** EPMCDMETST-60340
**Author:** design-review-agent
**Depends on:** `artifacts/architecture.md`

---

## Review Summary

The architecture document was reviewed against the requirements in `artifacts/requirements.md` acting as a senior engineer. 9 findings were identified across 6 categories (Design Risk, Missing Components, Security, Error Handling, Maintainability, and Performance). All 9 findings were confirmed by the user and incorporated into the updated architecture.

The overall design is sound: the linear pipeline style is appropriate for the problem, the technology stack is minimal and justified, and the error handling principle (never abort on single-file failure) is correctly reflected. The issues found were gaps in specification detail rather than fundamental architectural problems.

**Approval Status: Approved with Conditions** — conditions are the 9 agreed changes listed below, all incorporated into `artifacts/architecture.md`.

---

## Review Checklist

| Area | Status | Notes |
|------|--------|-------|
| Component responsibilities clear | ✅ | Each component has a single responsibility |
| Data flow end-to-end complete | ✅ (after DR-1 fix) | Old-file retrieval now explicit |
| Technology stack justified | ✅ | Minimal, all stdlib or already-required deps |
| Error handling strategy defined | ✅ (after EH-1, EH-2 fix) | Exit codes and skip categories now precise |
| Security concerns addressed | ✅ (after S-1 fix) | shell=False enforced; relative log paths |
| Folder structure matches components | ✅ | All modules listed |
| Test strategy implied | ✅ | One test file per component |
| No missing components | ✅ (after MC-1 fix) | Atomic write added to DocUpdater |

---

## Issues Identified

| # | Category | Severity | Problem | Impact |
|---|----------|----------|---------|--------|
| DR-1 | Design Risk | High | "Old file" retrieval for AST diff is implicit — architecture says "parse old + new" but never specifies how old content is fetched | Runtime bug: Analyser has no old file to diff against |
| DR-2 | Design Risk | Medium | `DocMapping` dataclass conflates "confirmed pair" with "file not found" path — both handled identically | Misleading model; harder to test the two branches separately |
| MC-1 | Missing | Medium | No atomic write strategy in DocUpdater — writes directly to doc file | Doc file corruption if process is interrupted mid-write |
| MC-2 | Missing | Low | `__init__.py` exports are undefined — public API boundary is implicit | Components may import each other's internals; coupling not visible |
| S-1 | Security | High | CLI args `--base-ref` / `--head-ref` flow into subprocess call — injection risk if `shell=True` used | Shell command injection with malicious ref values |
| S-2 | Security | Low | Absolute file paths in log messages | Compliance risk in enterprise environments |
| EH-1 | Error Handling | Medium | "No doc file" and "doc file exists but no `## Module Update` section" both reported as same warning | User cannot distinguish the two cases in the sync report |
| EH-2 | Error Handling | Medium | Exit code 1 boundary between WARNING (skip) and ERROR (fail) not defined | Unpredictable CI behaviour — skipped files should not fail the build |
| M-1 | Maintainability | Medium | No startup validation of `config/sync_rules.yaml` — config errors surface mid-pipeline | Some files may be processed before the config error is raised |

---

## Recommendations

1. **DR-1** — `ChangeDetector` fetches old file content using `git show <base_ref>:<filepath>` alongside detecting changed files. It passes both `old_content: Optional[str]` and `new_content: Optional[str]` in the `FileChange` model. For added files, `old_content` is `None`; for deleted files, `new_content` is `None`.

2. **DR-2** — Add a `SkippedFile` dataclass to `models.py` with fields `path`, `reason` (enum: `NO_DOC_FILE`, `NO_SECTION_MARKER`). `FileMapper.map()` returns `Union[DocMapping, SkippedFile]`. `DocMapping` is only returned when both source and doc file are confirmed.

3. **MC-1** — `DocUpdater` writes to a `.tmp` sibling file first (`doc_path.with_suffix('.md.tmp')`), then calls `os.replace(tmp_path, doc_path)` which is atomic on POSIX and Windows. If the write to `.tmp` fails, the original file is untouched.

4. **MC-2** — `src/sync_engine/__init__.py` re-exports only `Orchestrator`. All other modules (`analyser`, `mapper`, etc.) are internal and should not be imported directly from outside the package.

5. **S-1** — All `subprocess.run()` calls use a list argument (not a shell string): `subprocess.run(["git", "diff", "--name-status", base_ref, head_ref], shell=False, ...)`. This is an explicit constraint on every subprocess call in the codebase.

6. **S-2** — Log messages use `path.relative_to(repo_root)` when logging file paths. Absolute paths are never emitted in log output.

7. **EH-1** — `Reporter` renders two separate skip sections: "Skipped — no documentation file" and "Skipped — no `## Module Update` section". The `SkippedFile.reason` enum drives this separation.

8. **EH-2** — Exit code is determined as follows: `0` if all matched files were updated successfully (skipped files with no mapping or no section do not count as failures); `1` if one or more matched files failed validation or write. This is explicit in `Orchestrator.run()`.

9. **M-1** — `ConfigManager.load()` validates all required fields immediately on load and raises `ConfigurationError` before any pipeline stage executes. Required fields: `docs_root`, `source_extensions`.

---

## Agreed Design Decisions

All 9 recommendations above were confirmed by the user. The following decisions are binding for Stage 5 (Implementation):

| Decision | Binding Rule |
|----------|-------------|
| Old file retrieval | `ChangeDetector` fetches via `git show <base>:<path>`; `FileChange` carries `old_content` |
| Mapping model | `FileMapper` returns `Union[DocMapping, SkippedFile]`; `SkippedFile.reason` is an enum |
| Atomic writes | `DocUpdater` uses write-to-tmp + `os.replace()` pattern exclusively |
| Package boundary | `__init__.py` exports `Orchestrator` only |
| Subprocess safety | All `subprocess.run()` calls use `shell=False` with list args — no exceptions |
| Log path format | Relative paths only in all log messages |
| Skip categorisation | Report separates "no doc file" from "no section marker" |
| Exit code | `0` = success + skips; `1` = any matched-file failure |
| Config validation | `ConfigManager.load()` raises `ConfigurationError` on missing/invalid fields before pipeline starts |

---

## Approval Status

**Status: Approved with Conditions**

All 9 conditions (DR-1, DR-2, MC-1, MC-2, S-1, S-2, EH-1, EH-2, M-1) have been agreed by the user and incorporated into `artifacts/architecture.md`. The design is approved for Stage 4 (Implementation Planning).

---

## Changes Made to the Architecture

The following sections of `artifacts/architecture.md` were updated as a result of this review:

1. **Models section** — `FileChange` updated to include `old_content: Optional[str]`; `SkippedFile` dataclass added with `reason: SkipReason` enum.
2. **ChangeDetector** — description updated to include `git show` for old file content retrieval.
3. **FileMapper** — return type updated to `Union[DocMapping, SkippedFile]`.
4. **DocUpdater** — atomic write strategy (write-to-tmp + `os.replace()`) added explicitly.
5. **Security constraints** — new section added: `shell=False` rule and relative log paths.
6. **Exit code logic** — Data Flow section updated with precise exit code determination.
7. **Config Manager** — startup validation on `load()` added.
8. **Reporter** — skip categorisation (two distinct sections) added.
