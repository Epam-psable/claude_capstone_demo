## Summary

This PR delivers the **Automated Documentation Sync** pipeline — a Python CLI that detects Python source-code changes via `git diff` and automatically updates the matching `## Module Update` section in each module's Markdown documentation file. All manually authored content in docs is preserved. The implementation was produced end-to-end through the Agentic SDLC pipeline (Stages 1–7): requirements captured from Confluence/JIRA, architecture and design reviewed, implementation planned, code written and reviewed, and the full test suite verified before this PR.

JIRA Story: [EPMCDMETST-60340](https://jiraeu.epam.com/browse/EPMCDMETST-60340)

---

## Changes Made

### Agentic SDLC Infrastructure
| File | Change |
|------|--------|
| `.claude/agents/*.md` | 8 per-stage agent definitions (requirements → PR) |
| `.claude/skills/*.md` | 3 slash-command skills: `/sdlc-status`, `/run-pipeline`, `/sync-docs` |
| `.claude/settings.json` | Hooks: PostToolUse (artifact log, pytest reminder), PreToolUse (push guard) |
| `scripts/hooks/pre-commit` | Validates SDLC artifact sections; blocks committed secrets |
| `scripts/hooks/post-commit` | Logs commits and suggests next stage |
| `mcp_server/server.py` | MCP 2.0 server: Confluence/JIRA read tools, Q&A capture, requirements generation |

### SDLC Artifacts
| File | Stage |
|------|-------|
| `artifacts/requirements.md` | Stage 1 — 12 FRs, 6 NFRs, 10 Q&A pairs from Confluence page 44498945 |
| `artifacts/architecture.md` | Stage 2 — Linear pipeline architecture, updated by Stage 3 review |
| `artifacts/design-review.md` | Stage 3 — 9 findings, all agreed, approved with conditions |
| `artifacts/impl-plan.md` | Stage 4 — 23 tasks across 8 phases, dependency table |
| `artifacts/code-review.md` | Stage 6 — 5 findings (CR-1 through CR-5), all applied |
| `artifacts/verification-report.md` | Stage 7 — 45/45 tests, 91% coverage, all ACs signed off |

### Sync Engine Source (`src/sync_engine/`)
| File | Purpose |
|------|---------|
| `models.py` | Dataclasses: `FileChange`, `DocMapping`, `SkippedFile`, `ChangeSummary`, `SyncReport` |
| `exceptions.py` | Exception hierarchy: `SyncError` → `ConfigurationError`, `AnalysisError`, `UpdateError`, `ValidationError` |
| `config_manager.py` | Loads and validates `sync_rules.yaml` before pipeline starts (fail-fast M-1) |
| `change_detector.py` | `git diff --name-status` with `shell=False` (S-1); handles added/modified/deleted/renamed files |
| `mapper.py` | Maps `.py` stem to `docs/{stem}.md`; returns `Union[DocMapping, SkippedFile]` (DR-2) |
| `analyser.py` | AST-based diff: extracts top-level function/class defs, compares by source text |
| `update_generator.py` | Formats `ChangeSummary` into Markdown (Added/Removed/Modified lists + last-synced date) |
| `doc_updater.py` | Regex replace of `## Module Update` section; atomic write via `.tmp` → `os.replace()` (MC-1) |
| `validator.py` | Validates heading presence and non-empty section body after write |
| `reporter.py` | 4-section Markdown report: Updated, Skipped-NoDoc, Skipped-NoSection, Failed (EH-1) |
| `orchestrator.py` | Full pipeline coordinator; exit 0 for skips, exit 1 for failures only (EH-2) |
| `utils.py` | Shared `rel_path()` utility and compiled `SECTION_RE` regex (CR-3/CR-4) |
| `__init__.py` | Exports `Orchestrator` only (MC-2) |

### CLI and Config
| File | Purpose |
|------|---------|
| `scripts/run_sync.py` | CLI entry point: `--mode manual/pr`, `--base-ref`, `--head-ref`, `--changed-files` |
| `config/sync_rules.yaml` | Runtime configuration: `docs_root`, `source_extensions` |
| `pyproject.toml` | Build metadata + pytest config (`pythonpath = ["src"]`) |

### Tests (`tests/`)
| File | Tests |
|------|-------|
| `conftest.py` | Shared fixtures: `repo_root`, `docs_dir`, `src_dir`, `sync_rules_yaml`, sample content |
| `test_config_manager.py` | 6 — valid load, missing file, empty file, invalid YAML, missing fields |
| `test_change_detector.py` | 6 — filter, added/deleted content, git error, manual list |
| `test_mapper.py` | 3 — found, no doc file, stem mapping |
| `test_analyser.py` | 6 — added/deleted/modified/no-change/syntax-error |
| `test_update_generator.py` | 6 — all change types, date stamp, no-change placeholder |
| `test_doc_updater.py` | 5 — replace, preserve, missing section, atomic cleanup, unreadable |
| `test_validator.py` | 4 — valid, missing heading, empty body, whitespace-only |
| `test_reporter.py` | 4 — four sections, file write, summary line, empty |
| `test_orchestrator.py` | 5 — full pipeline, no changes, no doc, syntax error exit 1, manual mode |

---

## Test Evidence

From `artifacts/verification-report.md` (Stage 7):

```
45 passed in 1.01s

Name                               Stmts   Miss  Cover
------------------------------------------------------
src\sync_engine\__init__.py            2      0   100%
src\sync_engine\analyser.py           33      0   100%
src\sync_engine\change_detector.py    63     22    65%   (subprocess I/O, correctly mocked)
src\sync_engine\config_manager.py     41      1    98%
src\sync_engine\doc_updater.py        37      6    84%
src\sync_engine\exceptions.py          6      0   100%
src\sync_engine\mapper.py             20      0   100%
src\sync_engine\models.py             54      0   100%
src\sync_engine\orchestrator.py       76     10    87%
src\sync_engine\reporter.py           71      3    96%
src\sync_engine\update_generator.py   29      0   100%
src\sync_engine\utils.py               9      0   100%
src\sync_engine\validator.py          24      0   100%
------------------------------------------------------
TOTAL                                465     42    91%
```

All 6 acceptance criteria signed off. See full report at `artifacts/verification-report.md`.

---

## Known Limitations

- **Manual mode baseline**: `--mode manual --changed-files` always sets `old_content=None` — no git ref is available, so the AST analyser reports all functions as "Added" rather than computing a true diff. This is by design for the manual workflow.
- **`change_detector.py` coverage 65%**: The live `subprocess.run()` calls for `git diff` and `git show` are mocked in unit tests. Full coverage requires an integration test against a real git repository (noted as recommendation in verification report).
- **No auto-creation of missing doc files**: By design per Q7/FR6 — if `docs/{stem}.md` does not exist, the file is skipped with a warning.
- **Python only**: Only `.py` source files trigger sync (by design per Q1/FR2).
- **Single-repo only**: Multi-repository synchronisation is out of scope per requirements section 10.
- **`markdown-it-py` not used**: Listed as a dependency in `requirements.md` but Markdown validation is implemented with `re` directly — the package was not needed.

---

## Reviewer Checklist

- [ ] `artifacts/requirements.md` — requirements are complete and traceable to implementation
- [ ] `artifacts/architecture.md` — architecture reflects the implemented design
- [ ] `artifacts/design-review.md` — all 9 findings have been applied to the implementation
- [ ] `artifacts/impl-plan.md` — all 23 tasks are accounted for in the committed code
- [ ] `artifacts/code-review.md` — all 5 CR findings (CR-1 through CR-5) are applied
- [ ] `artifacts/verification-report.md` — 45/45 tests pass, coverage ≥ 80% ✅ (91%)
- [ ] `src/sync_engine/` — 13 source files present and syntactically valid
- [ ] `scripts/run_sync.py` — CLI runs without error (`python scripts/run_sync.py --help`)
- [ ] `tests/` — `pytest tests/ -v` runs clean with no failures
- [ ] Security: no secrets committed; all `subprocess.run()` calls use `shell=False`
- [ ] Atomic writes confirmed: `doc_updater.py` uses `.tmp` → `os.replace()` pattern
- [ ] Exit codes: exit 0 for skips, exit 1 only for matched-file failures (EH-2)
- [ ] Branch: `feature/EPMCDMETST-60340-automated-doc-sync` → `main`

---

## Related

- Confluence page: `https://epam-team-pnqaof71.atlassian.net/wiki/spaces/~712020ff5ba6e8e09b44d0b6155976e4654329/pages/44498945`
- JIRA story: `EPMCDMETST-60340`
