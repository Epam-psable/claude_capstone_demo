from pathlib import Path

from sync_engine.models import ChangeSummary
from sync_engine.update_generator import UpdateGenerator

_PATH = Path("src/module.py")


def test_generates_added_section():
    summary = ChangeSummary(src_path=_PATH, added=["new_func"])
    content = UpdateGenerator().generate(summary)
    assert "### Added" in content
    assert "`new_func`" in content


def test_generates_removed_section():
    summary = ChangeSummary(src_path=_PATH, removed=["old_func"])
    content = UpdateGenerator().generate(summary)
    assert "### Removed" in content
    assert "`old_func`" in content


def test_generates_modified_section():
    summary = ChangeSummary(src_path=_PATH, modified=["changed_func"])
    content = UpdateGenerator().generate(summary)
    assert "### Modified" in content
    assert "`changed_func`" in content


def test_no_changes_placeholder():
    summary = ChangeSummary(src_path=_PATH)
    content = UpdateGenerator().generate(summary)
    assert "No API-level changes" in content
    assert "### Added" not in content


def test_includes_last_synced_date():
    summary = ChangeSummary(src_path=_PATH, added=["f"])
    content = UpdateGenerator().generate(summary)
    assert "*Last synced:" in content


def test_all_change_types():
    summary = ChangeSummary(
        src_path=_PATH, added=["a"], removed=["b"], modified=["c"]
    )
    content = UpdateGenerator().generate(summary)
    assert "### Added" in content
    assert "### Removed" in content
    assert "### Modified" in content
