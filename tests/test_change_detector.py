import pytest
from pathlib import Path
from unittest.mock import patch

from sync_engine.change_detector import ChangeDetector
from sync_engine.exceptions import SyncError

_ROOT = Path(".")


def _detector(root=_ROOT):
    return ChangeDetector(repo_root=root, source_extensions=[".py"])


def test_filters_to_py_files():
    with patch.object(ChangeDetector, "_git_diff_name_status") as mock_diff, \
         patch.object(ChangeDetector, "_git_show", return_value=""):
        mock_diff.return_value = [("M", "src/module.py"), ("M", "README.md")]
        changes = _detector().detect("HEAD~1", "HEAD")

    assert len(changes) == 1
    assert changes[0].path == Path("src/module.py")


def test_added_file_has_no_old_content():
    with patch.object(ChangeDetector, "_git_diff_name_status") as mock_diff, \
         patch.object(ChangeDetector, "_git_show", return_value="def f(): pass\n"):
        mock_diff.return_value = [("A", "src/new.py")]
        changes = _detector().detect("HEAD~1", "HEAD")

    assert changes[0].old_content is None  # DR-1
    assert changes[0].new_content is not None


def test_deleted_file_has_no_new_content():
    with patch.object(ChangeDetector, "_git_diff_name_status") as mock_diff, \
         patch.object(ChangeDetector, "_git_show", return_value="def f(): pass\n"):
        mock_diff.return_value = [("D", "src/old.py")]
        changes = _detector().detect("HEAD~1", "HEAD")

    assert changes[0].new_content is None  # DR-1
    assert changes[0].old_content is not None


def test_git_error_raises_sync_error():
    with patch.object(ChangeDetector, "_git_diff_name_status", side_effect=SyncError("git failed")):
        with pytest.raises(SyncError):
            _detector().detect("HEAD~1", "HEAD")


def test_detect_from_list_parses_status_path(tmp_path):
    py_file = tmp_path / "module.py"
    py_file.write_text("def f(): pass\n", encoding="utf-8")

    changes = ChangeDetector(tmp_path, [".py"]).detect_from_list([f"M:{py_file}"])
    assert len(changes) == 1
    assert changes[0].status == "M"


def test_detect_from_list_ignores_non_py(tmp_path):
    md_file = tmp_path / "README.md"
    md_file.write_text("# Readme\n", encoding="utf-8")

    changes = ChangeDetector(tmp_path, [".py"]).detect_from_list([f"M:{md_file}"])
    assert changes == []
