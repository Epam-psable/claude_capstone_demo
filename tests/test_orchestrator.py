"""Integration tests for the Orchestrator (full pipeline)."""

import pytest
from pathlib import Path
from unittest.mock import patch

from sync_engine.orchestrator import Orchestrator


def _setup(repo_root: Path, docs_dir: Path, src_dir: Path, sync_rules_yaml: Path):
    """Create a doc file with a ## Module Update section."""
    doc = docs_dir / "module.md"
    doc.write_text(
        "# Module\n\nManual text.\n\n## Module Update\n\nOld content.\n\n## Other\n\nKept.\n",
        encoding="utf-8",
    )
    src = src_dir / "module.py"
    src.write_text("def my_func():\n    pass\n", encoding="utf-8")
    return src, doc


def _orchestrator(repo_root: Path, sync_rules_yaml: Path) -> Orchestrator:
    return Orchestrator(repo_root=repo_root, config_path=sync_rules_yaml)


def test_full_pipeline_updated(repo_root, docs_dir, src_dir, sync_rules_yaml):
    src, doc = _setup(repo_root, docs_dir, src_dir, sync_rules_yaml)

    with patch("sync_engine.change_detector.ChangeDetector._git_diff_name_status") as mock_diff, \
         patch("sync_engine.change_detector.ChangeDetector._git_show") as mock_show:
        mock_diff.return_value = [("M", str(src))]
        mock_show.side_effect = lambda ref, path: "def my_func():\n    pass\n"

        exit_code = _orchestrator(repo_root, sync_rules_yaml).run(
            base_ref="HEAD~1", head_ref="HEAD"
        )

    assert exit_code == 0
    updated = doc.read_text(encoding="utf-8")
    assert "Manual text" in updated
    assert "Kept" in updated


def test_no_python_changes_exit_zero(repo_root, docs_dir, src_dir, sync_rules_yaml):
    _setup(repo_root, docs_dir, src_dir, sync_rules_yaml)

    with patch("sync_engine.change_detector.ChangeDetector._git_diff_name_status") as mock_diff:
        mock_diff.return_value = []
        exit_code = _orchestrator(repo_root, sync_rules_yaml).run(
            base_ref="HEAD~1", head_ref="HEAD"
        )

    assert exit_code == 0


def test_no_doc_file_exit_zero(repo_root, docs_dir, src_dir, sync_rules_yaml):
    src = src_dir / "unknown.py"
    src.write_text("def f(): pass\n", encoding="utf-8")

    with patch("sync_engine.change_detector.ChangeDetector._git_diff_name_status") as mock_diff, \
         patch("sync_engine.change_detector.ChangeDetector._git_show") as mock_show:
        mock_diff.return_value = [("M", str(src))]
        mock_show.return_value = "def f(): pass\n"

        exit_code = _orchestrator(repo_root, sync_rules_yaml).run(
            base_ref="HEAD~1", head_ref="HEAD"
        )

    assert exit_code == 0  # EH-2: skips do not cause exit 1


def test_syntax_error_in_source_exit_one(repo_root, docs_dir, src_dir, sync_rules_yaml):
    doc = docs_dir / "module.md"
    doc.write_text("# M\n\n## Module Update\n\nOld.\n", encoding="utf-8")
    src = src_dir / "module.py"

    with patch("sync_engine.change_detector.ChangeDetector._git_diff_name_status") as mock_diff, \
         patch("sync_engine.change_detector.ChangeDetector._git_show") as mock_show:
        mock_diff.return_value = [("M", str(src))]
        mock_show.return_value = "def broken(:\n    pass\n"  # syntax error

        exit_code = _orchestrator(repo_root, sync_rules_yaml).run(
            base_ref="HEAD~1", head_ref="HEAD"
        )

    assert exit_code == 1  # EH-2: matched file failure → exit 1


def test_manual_mode_changed_files(repo_root, docs_dir, src_dir, sync_rules_yaml):
    src, doc = _setup(repo_root, docs_dir, src_dir, sync_rules_yaml)

    exit_code = _orchestrator(repo_root, sync_rules_yaml).run(
        changed_files=[f"M:{src}"]
    )

    assert exit_code == 0
