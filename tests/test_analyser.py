import pytest
from pathlib import Path

from sync_engine.analyser import AstAnalyser
from sync_engine.exceptions import AnalysisError

_PATH = Path("src/module.py")


def test_detects_added_function(sample_py_old, sample_py_new):
    result = AstAnalyser().analyse(_PATH, sample_py_old, sample_py_new)
    assert "new_func" in result.added
    assert "to_be_removed" in result.removed


def test_detects_modified_function():
    old = "def foo():\n    pass\n"
    new = "def foo():\n    return 1\n"
    result = AstAnalyser().analyse(_PATH, old, new)
    assert "foo" in result.modified
    assert not result.added
    assert not result.removed


def test_new_file_old_is_none(sample_py_new):
    result = AstAnalyser().analyse(_PATH, None, sample_py_new)
    assert set(result.added) == {"existing_func", "new_func"}
    assert not result.removed


def test_deleted_file_new_is_none(sample_py_old):
    result = AstAnalyser().analyse(_PATH, sample_py_old, None)
    assert set(result.removed) == {"existing_func", "to_be_removed"}
    assert not result.added


def test_no_changes_same_content():
    src = "def foo():\n    pass\n"
    result = AstAnalyser().analyse(_PATH, src, src)
    assert not result.has_changes


def test_syntax_error_raises():
    with pytest.raises(AnalysisError, match="Syntax error"):
        AstAnalyser().analyse(_PATH, "def broken(:\n    pass\n", "def ok(): pass\n")
