import pytest
from pathlib import Path

from sync_engine.doc_updater import DocUpdater
from sync_engine.exceptions import UpdateError
from sync_engine.models import DocMapping, SkippedFile, SkipReason


def _make_mapping(src: Path, doc: Path) -> DocMapping:
    return DocMapping(src_path=src, doc_path=doc)


def test_replaces_section(repo_root, docs_dir, src_dir, doc_with_section):
    doc = docs_dir / "module.md"
    doc.write_text(doc_with_section, encoding="utf-8")
    src = src_dir / "module.py"

    mapping = _make_mapping(src, doc)
    result = DocUpdater(repo_root).update(mapping, "*Last synced: 2026-08-18*\n\n### Added\n- `new_func`\n")

    assert result is None
    updated = doc.read_text(encoding="utf-8")
    assert "new_func" in updated
    assert "Old content here" not in updated


def test_preserves_content_outside_section(repo_root, docs_dir, src_dir, doc_with_section):
    doc = docs_dir / "module.md"
    doc.write_text(doc_with_section, encoding="utf-8")
    src = src_dir / "module.py"

    DocUpdater(repo_root).update(_make_mapping(src, doc), "new content\n")

    updated = doc.read_text(encoding="utf-8")
    assert "Some manual documentation" in updated
    assert "More manual content" in updated


def test_missing_section_returns_skipped(repo_root, docs_dir, src_dir, doc_without_section):
    doc = docs_dir / "module.md"
    doc.write_text(doc_without_section, encoding="utf-8")
    src = src_dir / "module.py"

    result = DocUpdater(repo_root).update(_make_mapping(src, doc), "content\n")

    assert isinstance(result, SkippedFile)
    assert result.reason == SkipReason.NO_SECTION_MARKER


def test_atomic_write_leaves_no_tmp(repo_root, docs_dir, src_dir, doc_with_section):
    doc = docs_dir / "module.md"
    doc.write_text(doc_with_section, encoding="utf-8")
    src = src_dir / "module.py"

    DocUpdater(repo_root).update(_make_mapping(src, doc), "updated\n")

    assert not (docs_dir / "module.md.tmp").exists()


def test_unreadable_doc_raises(repo_root, docs_dir, src_dir):
    doc = docs_dir / "ghost.md"  # does not exist
    src = src_dir / "ghost.py"
    with pytest.raises(UpdateError):
        DocUpdater(repo_root).update(_make_mapping(src, doc), "content\n")
